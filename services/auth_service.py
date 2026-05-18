import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict
from config import settings
import logging

logger = logging.getLogger(__name__)

class AuthService:
    """Service for authentication and authorization"""
    
    def __init__(self):
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify a JWT token and return the payload"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None

    def verify_token_verbose(self, token: str) -> Dict:
        """Verify a JWT token and return a verbose result with error info.

        Returns: {"payload": dict|None, "error": "expired"|"invalid"|None}
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return {"payload": payload, "error": None}
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return {"payload": None, "error": "expired"}
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return {"payload": None, "error": "invalid"}
    
    def create_refresh_token(self, user_id: int) -> str:
        """Create a refresh token"""
        data = {"sub": str(user_id), "type": "refresh"}
        expires_delta = timedelta(days=7)
        return self.create_access_token(data, expires_delta)
    
    def create_tokens(self, user_id: int, username: str, is_admin: bool = False) -> Dict[str, str]:
        """Create both access and refresh tokens"""
        access_token_data = {
            "sub": str(user_id),
            "username": username,
            "is_admin": is_admin,
            "type": "access"
        }
        
        access_token = self.create_access_token(access_token_data)
        refresh_token = self.create_refresh_token(user_id)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

# Create singleton instance
auth_service = AuthService()
