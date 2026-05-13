from openai import OpenAI
from config import settings
import logging
import requests
import os
from io import BytesIO

logger = logging.getLogger(__name__)

class AudioService:
    def __init__(self):
        # Whisper still requires OpenAI API key even if using Ollama for text
        self.client = None
        if settings.openai_api_key:
            try:
                self.client = OpenAI(api_key=settings.openai_api_key)
                logger.info("Audio service (Whisper) initialized.")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client for audio: {e}")

    async def transcribe_audio(self, file_path: str, language: str = "ar") -> dict:
        """
        Transcribe audio file using OpenAI Whisper API.
        Supports local paths and URLs.
        """
        if not self.client:
            raise RuntimeError("OpenAI API key is required for audio transcription.")

        try:
            # Handle URL or local path
            if file_path.startswith(('http://', 'https://')):
                response = requests.get(file_path)
                response.raise_for_status()
                file_content = response.content
                file_name = file_path.split('/')[-1]
            else:
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"Audio file not found: {file_path}")
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                file_name = os.path.basename(file_path)

            # Create a file-like object with a name attribute (required by OpenAI)
            audio_file = BytesIO(file_content)
            audio_file.name = file_name

            # Transcribe using Whisper API
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language
            )
            
            logger.info(f"Audio transcribed successfully: {file_name}")
            
            return {
                "text": transcript.text,
                "language": language,
                "file_name": file_name
            }
        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            raise Exception(f"Failed to transcribe audio: {str(e)}")

audio_service = AudioService()
