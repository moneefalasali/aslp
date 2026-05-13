from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict
from datetime import datetime

class FileUploadResponse(BaseModel):
    file_id: str
    file_url: str
    s3_key: str
    file_name: str

class AudioProcessRequest(BaseModel):
    file_url: str
    file_id: str
    language: Optional[str] = "ar"

class AudioProcessResponse(BaseModel):
    text: str
    language: str
    duration: Optional[float] = None
    segments: Optional[List] = None

class PDFProcessRequest(BaseModel):
    file_url: str
    file_id: str

class PDFProcessResponse(BaseModel):
    text: str
    page_count: int
    file_size: int

class QuizOption(BaseModel):
    text: str
    is_correct: bool

class QuizQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: int

class AnalyzeRequest(BaseModel):
    text: str
    file_id: str
    file_name: str
    file_type: str
    analysis_type: Optional[str] = 'both'
    target_language: Optional[str] = 'ar'

class AnalyzeResponse(BaseModel):
    summary: str
    key_points: List[str]
    quizzes: List[QuizQuestion]

class AnalysisResultResponse(BaseModel):
    id: int
    file_id: str
    file_name: str
    file_type: str
    summary: str
    key_points: List[str]
    quizzes: List[QuizQuestion]
    created_at: datetime

    class Config:
        from_attributes = True

# ==================== User Schemas ====================

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool
    is_admin: bool
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserListResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool
    is_admin: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# ==================== Admin Schemas ====================

class AdminCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    role: Optional[str] = "admin"
    permissions: Optional[Dict] = None

class AdminResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    permissions: Dict
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class AdminListResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# ==================== Authentication Schemas ====================

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: UserResponse

class AdminLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    admin: AdminResponse

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

# ==================== Statistics Schemas ====================

class UserStatistics(BaseModel):
    total_users: int
    active_users: int
    admin_users: int
    total_files_processed: int
    total_analyses: int

class AdminStatistics(BaseModel):
    total_admins: int
    active_admins: int
    total_users: int
    total_files_processed: int
    total_analyses: int
    system_health: str

# ==================== Error Response Schemas ====================

class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = None
