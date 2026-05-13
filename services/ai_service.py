import openai
from openai import OpenAI
import httpx
from config import settings
import logging
import json
import re
import time
import asyncio

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.ollama_api_key = settings.ollama_api_key
        self.ollama_base_url = settings.ollama_base_url
        self.ollama_model = settings.ollama_model
        
        self.openai_api_key = settings.openai_api_key
        self.openai_model = settings.openai_model
        self.ai_provider = settings.ai_provider
        
        self.chunk_size = 4000  # Characters per chunk
        self.max_retries = 3
        
        # Shared HTTP client for AI service
        self.http_client = httpx.Client(verify=settings.verify_ssl)
        logger.info(f"AI HTTP client SSL verify={settings.verify_ssl}")

        # Initialize Ollama Client (using OpenAI compatible API)
        self.client = None
        if self.ollama_api_key:
            try:
                self.client = OpenAI(
                    api_key=self.ollama_api_key,
                    base_url=self.ollama_base_url,
                    http_client=self.http_client
                )
                logger.info(f"Ollama Cloud client initialized with model: {self.ollama_model}")
            except Exception as e:
                logger.error(f"Failed to initialize Ollama client: {e}")
        
        # Fallback OpenAI Client
        self.openai_client = None
        if self.openai_api_key:
            try:
                self.openai_client = OpenAI(
                    api_key=self.openai_api_key,
                    http_client=self.http_client
                )
                logger.info(f"OpenAI fallback client initialized with model: {self.openai_model}")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")

    def _split_text_into_chunks(self, text: str) -> list:
        """Split text into manageable chunks while preserving sentence integrity"""
        if not text:
            return []
        
        chunks = []
        # Split by sentences (supporting Arabic and English)
        sentences = re.split(r'(?<=[.!?؟])\s+', text)
        
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < self.chunk_size:
                current_chunk += " " + sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks if chunks else [text]

    async def analyze_text(self, text: str, analysis_type: str = 'both', target_language: str = 'ar') -> dict:
        """
        Analyze text and generate summary or quiz questions.
        """
        if not text or not text.strip():
            return {
                "summary": "النص المقدم فارغ.",
                "key_points": [],
                "quizzes": []
            }

        try:
            analysis_type = (analysis_type or 'both').lower()
            target_language = self._normalize_language(target_language)
            if not self.client and not self.openai_client:
                logger.warning('No AI client configured, using local fallback.');
                return self._local_fallback(text, analysis_type)

            chunks = self._split_text_into_chunks(text)
            
            all_summaries = []
            all_key_points = []
            all_quizzes = []

            # Process chunks (can be parallelized but sequential is safer for rate limits)
            for i, chunk in enumerate(chunks):
                logger.info(f"Processing chunk {i+1}/{len(chunks)}")
                prompt = self._build_analysis_prompt(chunk, analysis_type, target_language)
                
                result = await self._call_ai_with_retry(prompt)
                
                if result:
                    if analysis_type in {'summary', 'both'}:
                        if "summary" in result:
                            all_summaries.append(result["summary"])
                        if "key_points" in result:
                            all_key_points.extend(result["key_points"])
                    if analysis_type in {'quiz', 'both'}:
                        if "quizzes" in result:
                            all_quizzes.extend(result["quizzes"])

            # Finalize Summary
            final_summary = ""
            if analysis_type in {'summary', 'both'}:
                if len(all_summaries) == 1:
                    final_summary = all_summaries[0]
                elif len(all_summaries) > 1:
                    combined = "\n\n".join(all_summaries)
                    final_summary = await self._refine_summary(combined, target_language)
                else:
                    final_summary = text[:1200] + ('...' if len(text) > 1200 else '')

            # Finalize Key Points
            unique_key_points = list(dict.fromkeys(all_key_points))[:15]

            # Finalize Quizzes
            unique_quizzes = self._dedupe_quizzes(all_quizzes)[:15]

            return {
                "summary": final_summary,
                "key_points": unique_key_points,
                "quizzes": unique_quizzes
            }

        except Exception as e:
            logger.error(f"Critical error in analyze_text: {e}")
            return self._local_fallback(text, analysis_type)

    def _normalize_language(self, language: str) -> str:
        if not language: return 'ar'
        lang = language.strip().lower()
        return 'en' if lang.startswith('en') else 'ar'

    def _build_analysis_prompt(self, chunk: str, analysis_type: str, target_language: str) -> str:
        lang_name = "Arabic" if target_language == 'ar' else "English"
        
        schema = {
            "summary": "A concise summary of the text",
            "key_points": ["point 1", "point 2"],
            "quizzes": [
                {
                    "question": "Question text",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": 0,
                    "explanation": "Why this is correct"
                }
            ]
        }

        prompt = f"""
        You are an expert educational assistant. Analyze the following text and provide the output in {lang_name}.
        
        Task: {analysis_type}
        
        Requirements:
        1. Summary: Professional, clear, and informative.
        2. Key Points: Extract the most important concepts.
        3. Quizzes: Generate high-quality multiple-choice questions.
        
        Output MUST be a valid JSON object following this structure:
        {json.dumps(schema, indent=2)}
        
        Text to analyze:
        {chunk}
        """
        return prompt

    async def _call_ai_with_retry(self, prompt: str) -> dict:
        for attempt in range(self.max_retries):
            try:
                provider_order = []
                if self.ai_provider == 'openai':
                    provider_order = ['openai', 'ollama']
                elif self.ai_provider == 'ollama':
                    provider_order = ['ollama', 'openai']
                else:
                    provider_order = ['openai', 'ollama'] if self.openai_client else ['ollama', 'openai']

                if 'openai' in provider_order and self.openai_client:
                    logger.info(f"Attempting AI request via OpenAI (attempt {attempt+1})")
                    response = self.openai_client.chat.completions.create(
                        model=self.openai_model,
                        messages=[{"role": "user", "content": prompt}],
                        max_completion_tokens=1000,
                        timeout=60
                    )
                    content = getattr(response.choices[0].message, 'content', None)
                    if content is None:
                        content = response.choices[0].message.get('content') if hasattr(response.choices[0].message, 'get') else ''
                    return self._parse_json(content or '')

                if 'ollama' in provider_order and self.client:
                    logger.info(f"Attempting AI request via Ollama (attempt {attempt+1})")
                    response = self.client.chat.completions.create(
                        model=self.ollama_model,
                        messages=[{"role": "user", "content": prompt}],
                        response_format={"type": "json_object"},
                        timeout=90
                    )
                    return self._parse_json(response.choices[0].message.content)
                    content = getattr(response.choices[0].message, 'content', None)
                    if content is None:
                        content = response.choices[0].message.get('content') if hasattr(response.choices[0].message, 'get') else ''
                    return self._parse_json(content or '')

            except Exception as e:
                logger.warning(f"AI call attempt {attempt+1} failed: {e}")
                await asyncio.sleep(2 ** attempt)
        
        return None

    def _parse_json(self, content: str) -> dict:
        try:
            # Clean content from markdown code blocks if present
            clean_content = re.sub(r'```json\s*|\s*```', '', content).strip()
            return json.loads(clean_content)
        except Exception as e:
            logger.error(f"JSON parsing failed: {e}")
            # Try to find JSON-like structure
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except:
                    pass
            return {}

    async def _refine_summary(self, combined_text: str, target_language: str) -> str:
        lang_name = "Arabic" if target_language == 'ar' else "English"
        prompt = f"Combine and refine the following partial summaries into one professional, cohesive summary in {lang_name}:\n\n{combined_text}"
        
        try:
            result = await self._call_ai_with_retry(prompt)
            if result and "summary" in result:
                return result["summary"]
            return combined_text[:2000] # Fallback to truncated combined text
        except:
            return combined_text[:2000]

    def _dedupe_quizzes(self, quizzes: list) -> list:
        seen = set()
        unique = []
        for q in quizzes:
            txt = q.get('question', '').strip()
            if txt and txt not in seen:
                seen.add(txt)
                unique.append(q)
        return unique

    def _local_fallback(self, text: str, analysis_type: str) -> dict:
        # Simple local logic if AI fails completely
        return {
            "summary": text[:500] + "...",
            "key_points": ["فشل الاتصال بالذكاء الاصطناعي، تم عرض ملخص محلي."],
            "quizzes": []
        }

ai_service = AIService()
