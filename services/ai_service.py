import re
import json
import math
import logging
import random
import requests
import time
from collections import Counter
from config import settings
from openai import OpenAI

logger = logging.getLogger(__name__)

ARABIC_STOPWORDS = {
    'في', 'من', 'على', 'و', 'إلى', 'عن', 'أن', 'إن', 'ما', 'لا', 'لم', 'كان', 'كانت',
    'مع', 'هذا', 'هذه', 'هناك', 'كل', 'أي', 'أو', 'كما', 'لقد', 'بعد', 'قبل', 'حتى',
    'أكثر', 'أقل', 'بين', 'عند', 'فيها', 'ذلك', 'هذه', 'هذه', 'التي', 'اللتي', 'الذي',
    'هو', 'هي', 'هم', 'هن', 'كانت', 'يكون', 'يمكن'
}
ENGLISH_STOPWORDS = {
    'the', 'and', 'or', 'is', 'in', 'to', 'of', 'a', 'an', 'that', 'this', 'for', 'with',
    'on', 'as', 'it', 'by', 'from', 'at', 'are', 'was', 'were', 'be', 'have', 'has', 'had',
    'not', 'but', 'if', 'they', 'their', 'them', 'you', 'your'
}

class AIService:
    def __init__(self):
        self.gemini_api_key = settings.gemini_api_key
        self.gemini_model = settings.gemini_model
        self.gemini_endpoint = settings.gemini_endpoint.rstrip('/')
        self.openai_api_key = settings.openai_api_key
        self.openai_model = settings.openai_model
        self.ai_provider = settings.ai_provider or 'gemini'
        self.chunk_size = 3800
        self.max_retries = 3
        self.requests_session = requests.Session()
        self.requests_session.verify = settings.verify_ssl
        if not self.requests_session.verify:
            logger.warning('SSL verification is disabled (VERIFY_SSL=False). This is insecure; set VERIFY_SSL=True to enforce certificate verification.')
        self.openai_client = None
        self.last_used_provider = None

        if self.openai_api_key:
            try:
                self.openai_client = OpenAI(api_key=self.openai_api_key)
                logger.info(f"OpenAI fallback client initialized with model {self.openai_model}")
            except Exception as ex:
                logger.warning(f"OpenAI fallback initialization failed: {ex}")

        logger.info(f"AI service initialized: provider={self.ai_provider}, gemini_model={self.gemini_model}")

    def _split_text_into_chunks(self, text: str) -> list:
        if not text:
            return []
        sentences = re.split(r'(?<=[.!?؟])\s+', text)
        chunks = []
        current = ''
        for sentence in sentences:
            if len(current) + len(sentence) < self.chunk_size:
                current += ' ' + sentence
            else:
                if current.strip():
                    chunks.append(current.strip())
                current = sentence
        if current.strip():
            chunks.append(current.strip())
        return chunks if chunks else [text.strip()]

    async def analyze_text(self, text: str, analysis_type: str = 'both', target_language: str = 'ar') -> dict:
        if not text or not text.strip():
            return {
                'summary': 'النص المقدم فارغ أو غير صالح.',
                'key_points': [],
                'quizzes': [],
                'provider': 'local',
                'used_fallback': True
            }

        analysis_type = (analysis_type or 'both').lower()
        if analysis_type not in {'summary', 'quiz', 'both'}:
            analysis_type = 'both'

        target_language = self._normalize_language(target_language)
        chunks = self._split_text_into_chunks(text)
        logger.info(f"analyze_text: {len(chunks)} chunk(s) for analysis")

        all_summaries = []
        all_key_points = []
        all_quizzes = []

        for idx, chunk in enumerate(chunks, start=1):
            logger.info(f"Processing chunk {idx}/{len(chunks)}")
            prompt = self._build_analysis_prompt(chunk, analysis_type, target_language)
            response = self._call_ai(prompt, chunk, analysis_type, target_language)
            if not response:
                logger.warning('AI response empty, switching to local fallback')
                return self._local_fallback(text, analysis_type, target_language)

            if analysis_type in {'summary', 'both'}:
                all_summaries.append(response.get('summary', '') or '')
                all_key_points.extend(response.get('key_points', []))
            if analysis_type in {'quiz', 'both'}:
                all_quizzes.extend(response.get('quizzes', []))

        final_summary = ''
        if analysis_type in {'summary', 'both'}:
            if len(all_summaries) == 1:
                final_summary = all_summaries[0]
            else:
                combined = '\n\n'.join([s for s in all_summaries if s])
                final_summary = combined[:5000] if combined else ''

        return {
            'summary': final_summary or (text[:1000] + ('...' if len(text) > 1000 else '')),
            'key_points': list(dict.fromkeys(all_key_points))[:12],
            'quizzes': self._dedupe_quizzes(all_quizzes)[:10],
            'provider': self.last_used_provider or ('gemini' if self._provider_available('gemini') else 'openai' if self._provider_available('openai') else 'local'),
            'used_fallback': False
        }

    def _provider_available(self, provider: str) -> bool:
        if provider == 'gemini':
            return bool(self.gemini_api_key)
        if provider == 'openai':
            return bool(self.openai_api_key and self.openai_client)
        return False

    def _normalize_language(self, language: str) -> str:
        if not language:
            return 'ar'
        return 'en' if language.strip().lower().startswith('en') else 'ar'

    def _build_analysis_prompt(self, chunk: str, analysis_type: str, target_language: str) -> str:
        lang = 'English' if target_language == 'en' else 'Arabic'
        output_lang_label = 'الإنجليزية' if target_language == 'en' else 'العربية'
        summary_instruction = 'اكتب ملخصًا واضحًا وشاملاً.' if target_language == 'ar' else 'Write a concise and comprehensive summary.'
        quiz_instruction = 'اخرج أسئلة اختبار دقيقة مع 4 خيارات.' if target_language == 'ar' else 'Generate precise multiple-choice quiz questions.'
        key_points_instruction = 'استخرج النقاط الرئيسية المهمة من النص.' if target_language == 'ar' else 'Extract the most important key points from the text.'

        if analysis_type == 'summary':
            task_description = summary_instruction
        elif analysis_type == 'quiz':
            task_description = quiz_instruction
        else:
            task_description = f"{summary_instruction} {key_points_instruction} {quiz_instruction}"

        schema = {
            'summary': 'string',
            'key_points': ['string'],
            'quizzes': [
                {
                    'question': 'string',
                    'options': ['string', 'string', 'string', 'string'],
                    'correct_answer': 0
                }
            ]
        }

        prompt = (
            f"You are an advanced educational AI assistant. Respond only in {lang}.\n"
            f"Task: {analysis_type}\n"
            f"Requirements: {task_description} Output MUST be valid JSON only, without any extra explanation.\n"
            f"JSON schema: {json.dumps(schema, ensure_ascii=False)}\n\n"
            f"Text:\n{chunk}\n"
        )
        return prompt

    def _parse_json(self, raw: str) -> dict:
        if not raw:
            return {}
        cleaned = re.sub(r'```json|```', '', raw, flags=re.IGNORECASE).strip()
        match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        payload = match.group() if match else cleaned
        try:
            return json.loads(payload)
        except Exception as exc:
            logger.warning(f'JSON parse failed: {exc}; content={payload[:200]}')
            return {}

    def _is_valid_ai_response(self, data: dict) -> bool:
        if not isinstance(data, dict):
            return False
        return bool(data.get('summary') or data.get('key_points') or data.get('quizzes'))

    def _call_local(self, text: str, analysis_type: str, target_language: str, used_fallback: bool = False) -> dict:
        return {
            'summary': self._summarize_local(text, target_language),
            'key_points': self._extract_keywords_local(text, target_language),
            'quizzes': self._generate_local_quizzes(text, target_language) if analysis_type in {'quiz', 'both'} else [],
            'provider': 'local',
            'used_fallback': used_fallback
        }

    def _call_ai(self, prompt: str, original_text: str, analysis_type: str, target_language: str) -> dict:
        if self.ai_provider == 'local':
            logger.info('Using local summarization as primary provider.')
            return self._call_local(original_text, analysis_type, target_language, used_fallback=False)

        providers = []
        if self.ai_provider == 'gemini':
            providers = ['gemini', 'openai', 'local']
        elif self.ai_provider == 'openai':
            providers = ['openai', 'gemini', 'local']
        else:
            providers = ['local', 'gemini', 'openai']

        for provider in providers:
            if provider == 'local':
                return self._call_local(original_text, analysis_type, target_language, used_fallback=True)

            if provider == 'gemini' and self._provider_available('gemini'):
                result = self._call_gemini(prompt)
                if result is not None:
                    parsed = self._parse_json(result)
                    if self._is_valid_ai_response(parsed):
                        self.last_used_provider = 'gemini'
                        return parsed
                    logger.warning('Gemini response invalid or incomplete, falling back to local summarization.')
                    return self._call_local(original_text, analysis_type, target_language, used_fallback=True)
            elif provider == 'openai' and self._provider_available('openai'):
                result = self._call_openai(prompt)
                if result is not None:
                    parsed = self._parse_json(result)
                    if self._is_valid_ai_response(parsed):
                        self.last_used_provider = 'openai'
                        return parsed
                    logger.warning('OpenAI response invalid or incomplete, falling back to local summarization.')
                    return self._call_local(original_text, analysis_type, target_language, used_fallback=True)

        logger.warning('No external AI provider available or all providers failed. Using local summarization.')
        return self._call_local(original_text, analysis_type, target_language, used_fallback=True)

    def _build_gemini_url(self) -> str:
        endpoint = self.gemini_endpoint.rstrip('/')
        if endpoint.endswith(':generateText'):
            return endpoint
        if endpoint.endswith('/models'):
            return f"{endpoint}/{self.gemini_model}:generateText"
        if '/models/' in endpoint:
            if endpoint.endswith(self.gemini_model):
                return f"{endpoint}:generateText"
            if endpoint.endswith(f"{self.gemini_model}:generateText"):
                return endpoint
        if endpoint.endswith('/v1') or endpoint.endswith('/v1beta2'):
            return f"{endpoint}/models/{self.gemini_model}:generateText"
        return f"{endpoint}/{self.gemini_model}:generateText"

    def _call_gemini(self, prompt: str) -> str:
        url = self._build_gemini_url()
        headers = {'Content-Type': 'application/json'}
        url_with_key = url
        if self.gemini_api_key:
            key = self.gemini_api_key.strip()
            if key.startswith('ya29.') or key.startswith('ya29_'):
                headers['Authorization'] = f'Bearer {key}'
            else:
                url_with_key = f"{url}?key={key}"
                headers['x-goog-api-key'] = key

        payload = {
            'prompt': {
                'text': prompt
            },
            'temperature': 0.2,
            'maxOutputTokens': 1200,
            'topP': 0.95,
            'topK': 40
        }

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.requests_session.post(url_with_key, json=payload, headers=headers, timeout=60)
                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get('candidates') or []
                    if candidates:
                        return candidates[0].get('content', '')
                    return ''
                elif response.status_code == 401:
                    logger.warning(
                        'Gemini call failed status=401: invalid authentication credentials.\n'
                        'Ensure you provided a valid OAuth2 access token (starts with "ya29.") or a valid API key.\n'
                        'If using a service account, obtain an access token and set it as GEMINI_API_KEY, or set GEMINI_API_KEY to your API key and use it as a query param.\n'
                        f'Response: {response.text[:400]}'
                    )
                    break
                elif response.status_code == 404:
                    logger.warning(
                        'Gemini call failed status=404: requested model or endpoint not found.\n'
                        'Check GEMINI_ENDPOINT and GEMINI_MODEL configuration, and ensure your account has access to the requested model.\n'
                        f'URL={url_with_key} Response={response.text[:400]}'
                    )
                    break
                else:
                    logger.warning(f'Gemini call failed status={response.status_code} message={response.text[:400]}')
            except Exception as exc:
                logger.warning(f'Gemini attempt {attempt} error: {exc}')
            if attempt < self.max_retries:
                time.sleep(2 ** attempt)
        return None

    def _call_openai(self, prompt: str) -> str:
        if not self.openai_client:
            return None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.openai_client.chat.completions.create(
                    model=self.openai_model,
                    messages=[{'role': 'user', 'content': prompt}],
                    temperature=0.2,
                    max_completion_tokens=1200,
                    timeout=60
                )
                message = response.choices[0].message
                if hasattr(message, 'content'):
                    return message.content
                return message.get('content', '') if isinstance(message, dict) else ''
            except Exception as exc:
                logger.warning(f'OpenAI attempt {attempt} failed: {exc}')
                if attempt >= self.max_retries:
                    break
                # Only retry on transient server or rate-limit issues, otherwise fallback quickly.
                error_text = str(exc).lower()
                if 'invalid_request_error' in error_text or 'unsupported_parameter' in error_text or 'invalid_api_key' in error_text:
                    logger.warning('OpenAI returned a non-retryable error; falling back to local summarization.')
                    break
                time.sleep(2 ** attempt)
        return None

    def _dedupe_quizzes(self, quizzes: list) -> list:
        unique = []
        seen = set()
        for quiz in quizzes:
            key = (quiz.get('question', '').strip(), tuple(quiz.get('options', [])))
            if key not in seen and quiz.get('question'):
                seen.add(key)
                unique.append(quiz)
        return unique

    def _clean_text(self, text: str) -> str:
        return re.sub(r'\s+', ' ', text.replace('\n', ' ').strip())

    def _tokenize_sentences(self, text: str) -> list:
        return [s.strip() for s in re.split(r'(?<=[.!?؟])\s+', text) if s.strip()]

    def _tokenize_words(self, text: str, target_language: str) -> list:
        text = self._clean_text(text.lower())
        words = re.findall(r"[\w\u0600-\u06FF']+", text)
        stopwords = ARABIC_STOPWORDS if target_language == 'ar' else ENGLISH_STOPWORDS
        return [w for w in words if w not in stopwords and len(w) > 2]

    def _frequency_scores(self, words: list) -> dict:
        counts = Counter(words)
        total = sum(counts.values()) or 1
        return {word: count / total for word, count in counts.items()}

    def _summarize_local(self, text: str, target_language: str) -> str:
        sentences = self._tokenize_sentences(text)
        if not sentences:
            return text[:600] + ('...' if len(text) > 600 else '')

        words = self._tokenize_words(text, target_language)
        freq = self._frequency_scores(words)
        scores = []
        for sentence in sentences:
            words_in_sentence = self._tokenize_words(sentence, target_language)
            score = sum(freq.get(w, 0) for w in words_in_sentence)
            scores.append((score / max(len(words_in_sentence), 1), sentence))

        scores.sort(reverse=True)
        top = [s for _, s in scores[:min(5, len(scores))]]
        return ' '.join(top).strip() or sentences[0]

    def _extract_keywords_local(self, text: str, target_language: str) -> list:
        words = self._tokenize_words(text, target_language)
        freq = Counter(words)
        return [word for word, _ in freq.most_common(10)]

    def _generate_local_quizzes(self, text: str, target_language: str) -> list:
        sentences = self._tokenize_sentences(text)
        quizzes = []
        for i, sentence in enumerate(sentences[:3]):
            if len(sentence) < 30:
                continue
            if target_language == 'ar':
                question = f"ما هي الفكرة الرئيسية في الجملة التالية؟ {sentence[:80]}"
                options = [sentence[:40], sentence[-40:], 'معلومة غير صحيحة', 'لا يوجد خيار صحيح']
            else:
                question = f"What is the main idea in the following sentence? {sentence[:80]}"
                options = [sentence[:40], sentence[-40:], 'Incorrect statement', 'None of the above']
            quizzes.append({
                'question': question,
                'options': options,
                'correct_answer': 0
            })
        return quizzes[:5]

    def _local_fallback(self, text: str, analysis_type: str, target_language: str) -> dict:
        return self._call_local(text, analysis_type, target_language, used_fallback=True)


ai_service = AIService()
