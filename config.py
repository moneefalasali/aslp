import os
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

def parse_comma_separated_list(value: Optional[str], default: List[str]) -> List[str]:
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]

class Settings:
    # Ollama Cloud Configuration
    ollama_api_key: str = os.getenv("OLLAMA_API_KEY", "")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "https://api.ollama.cloud/v1")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen3:8b")

    # Gemini Configuration
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
    gemini_endpoint: str = os.getenv("GEMINI_ENDPOINT", "https://generativelanguage.googleapis.com/v1")

    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    # Wasabi S3 Configuration
    wasabi_access_key: str = os.getenv("WASABI_ACCESS_KEY", "")
    wasabi_secret_key: str = os.getenv("WASABI_SECRET_KEY", "")
    wasabi_bucket_name: str = os.getenv("WASABI_BUCKET_NAME", "")
    wasabi_region: str = os.getenv("WASABI_REGION", "us-east-1")
    wasabi_endpoint_url: str = os.getenv("WASABI_ENDPOINT_URL", "https://s3.wasabisys.com")
    use_local_storage: bool = os.getenv("USE_LOCAL_STORAGE", "False").lower() == "true"
    upload_folder: str = os.getenv("UPLOAD_FOLDER", "uploads")
    local_base_url: str = os.getenv("LOCAL_BASE_URL", "http://localhost:5000")
    
    # Database Configuration
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./smart_learning.db")
    
    # Server Configuration
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    allowed_origins: List[str] = parse_comma_separated_list(
        os.getenv("ALLOWED_ORIGINS"),
        ["http://localhost:5173", "http://localhost:3000"],
    )
    verify_ssl: bool = os.getenv("VERIFY_SSL", "True").lower() in ("1", "true", "yes")
    ai_provider: str = os.getenv("AI_PROVIDER", "local").lower()
    
    # File Upload Configuration
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_pdf_extensions: List[str] = [".pdf"]
    allowed_audio_extensions: List[str] = [".mp3", ".wav", ".m4a", ".ogg"]
    
    # Authentication Configuration
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # Admin Configuration
    admin_email: str = os.getenv("ADMIN_EMAIL", "admin@smartlearning.com")
    admin_username: str = os.getenv("ADMIN_USERNAME", "admin")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "admin123")
    
settings = Settings()
