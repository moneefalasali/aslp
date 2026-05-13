from sqlalchemy.orm import Session
from models import User, Admin, UserSession
from schemas import UserCreate, UserUpdate, AdminCreate
from .auth_service import auth_service
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class UserService:
    """Service for user management"""
    
    @staticmethod
    def create_user(db: Session, user_create: UserCreate) -> User:
        """Create a new user"""
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.email == user_create.email) | (User.username == user_create.username)
        ).first()
        
        if existing_user:
            raise ValueError("البريد الإلكتروني أو اسم المستخدم موجود بالفعل")
        
        # Hash password
        hashed_password = auth_service.hash_password(user_create.password)
        
        # Create user
        db_user = User(
            username=user_create.username,
            email=user_create.email,
            password_hash=hashed_password,
            full_name=user_create.full_name,
            is_active=True,
            is_admin=False
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"User created: {db_user.username}")
        return db_user
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> User:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> User:
        """Get user by username"""
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> User:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> User:
        """Authenticate user with username and password"""
        user = UserService.get_user_by_username(db, username)
        
        if not user:
            return None
        
        if not auth_service.verify_password(password, user.password_hash):
            return None
        
        if not user.is_active:
            raise ValueError("حساب المستخدم غير مفعل")
        
        return user
    
    @staticmethod
    def update_user(db: Session, user_id: int, user_update: UserUpdate) -> User:
        """Update user information"""
        user = UserService.get_user_by_id(db, user_id)
        
        if not user:
            raise ValueError("المستخدم غير موجود")
        
        update_data = user_update.dict(exclude_unset=True)
        
        # Hash password if provided
        if "password" in update_data:
            update_data["password_hash"] = auth_service.hash_password(update_data.pop("password"))
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        
        logger.info(f"User updated: {user.username}")
        return user
    
    @staticmethod
    def deactivate_user(db: Session, user_id: int) -> User:
        """Deactivate a user account"""
        user = UserService.get_user_by_id(db, user_id)
        
        if not user:
            raise ValueError("المستخدم غير موجود")
        
        user.is_active = False
        db.commit()
        db.refresh(user)
        
        logger.info(f"User deactivated: {user.username}")
        return user
    
    @staticmethod
    def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> list:
        """Get all users with pagination"""
        return db.query(User).offset(skip).limit(limit).all()
    
    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        """Delete a user"""
        user = UserService.get_user_by_id(db, user_id)
        
        if not user:
            raise ValueError("المستخدم غير موجود")
        
        db.delete(user)
        db.commit()
        
        logger.info(f"User deleted: {user.username}")
        return True


class AdminService:
    """Service for admin management"""
    
    @staticmethod
    def create_admin(db: Session, admin_create: AdminCreate) -> Admin:
        """Create a new admin"""
        # Check if admin already exists
        existing_admin = db.query(Admin).filter(
            (Admin.email == admin_create.email) | (Admin.username == admin_create.username)
        ).first()
        
        if existing_admin:
            raise ValueError("البريد الإلكتروني أو اسم المستخدم موجود بالفعل")
        
        # Hash password
        hashed_password = auth_service.hash_password(admin_create.password)
        
        # Create admin
        db_admin = Admin(
            username=admin_create.username,
            email=admin_create.email,
            password_hash=hashed_password,
            full_name=admin_create.full_name,
            role=admin_create.role or "admin",
            permissions=admin_create.permissions or {},
            is_active=True
        )
        
        db.add(db_admin)
        db.commit()
        db.refresh(db_admin)
        
        logger.info(f"Admin created: {db_admin.username}")
        return db_admin
    
    @staticmethod
    def get_admin_by_username(db: Session, username: str) -> Admin:
        """Get admin by username"""
        return db.query(Admin).filter(Admin.username == username).first()
    
    @staticmethod
    def get_admin_by_id(db: Session, admin_id: int) -> Admin:
        """Get admin by ID"""
        return db.query(Admin).filter(Admin.id == admin_id).first()
    
    @staticmethod
    def authenticate_admin(db: Session, username: str, password: str) -> Admin:
        """Authenticate admin with username and password"""
        admin = AdminService.get_admin_by_username(db, username)
        
        if not admin:
            return None
        
        if not auth_service.verify_password(password, admin.password_hash):
            return None
        
        if not admin.is_active:
            raise ValueError("حساب الإدارة غير مفعل")
        
        # Update last login
        admin.last_login = datetime.utcnow()
        db.commit()
        
        return admin
    
    @staticmethod
    def get_all_admins(db: Session) -> list:
        """Get all admins"""
        return db.query(Admin).all()
    
    @staticmethod
    def update_admin(db: Session, admin_id: int, admin_update: dict) -> Admin:
        """Update admin information"""
        admin = AdminService.get_admin_by_id(db, admin_id)
        
        if not admin:
            raise ValueError("الإدارة غير موجودة")
        
        for field, value in admin_update.items():
            if field == "password":
                setattr(admin, "password_hash", auth_service.hash_password(value))
            else:
                setattr(admin, field, value)
        
        admin.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(admin)
        
        logger.info(f"Admin updated: {admin.username}")
        return admin
    
    @staticmethod
    def delete_admin(db: Session, admin_id: int) -> bool:
        """Delete an admin"""
        admin = AdminService.get_admin_by_id(db, admin_id)
        
        if not admin:
            raise ValueError("الإدارة غير موجودة")
        
        db.delete(admin)
        db.commit()
        
        logger.info(f"Admin deleted: {admin.username}")
        return True


class SessionService:
    """Service for session management"""
    
    @staticmethod
    def create_session(db: Session, user_id: int, token: str, ip_address: str, user_agent: str) -> UserSession:
        """Create a new session"""
        expires_at = datetime.utcnow() + timedelta(days=7)
        
        session = UserSession(
            user_id=user_id,
            token=token,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        return session
    
    @staticmethod
    def get_session_by_token(db: Session, token: str) -> UserSession:
        """Get session by token"""
        return db.query(UserSession).filter(UserSession.token == token).first()
    
    @staticmethod
    def delete_session(db: Session, token: str) -> bool:
        """Delete a session"""
        session = SessionService.get_session_by_token(db, token)
        
        if not session:
            return False
        
        db.delete(session)
        db.commit()
        
        return True
    
    @staticmethod
    def get_user_sessions(db: Session, user_id: int) -> list:
        """Get all sessions for a user"""
        return db.query(UserSession).filter(UserSession.user_id == user_id).all()
    
    @staticmethod
    def cleanup_expired_sessions(db: Session) -> int:
        """Delete all expired sessions"""
        expired_sessions = db.query(UserSession).filter(
            UserSession.expires_at < datetime.utcnow()
        ).all()
        
        count = len(expired_sessions)
        
        for session in expired_sessions:
            db.delete(session)
        
        db.commit()
        
        logger.info(f"Cleaned up {count} expired sessions")
        return count
