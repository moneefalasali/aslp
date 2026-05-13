from flask import Blueprint, request, jsonify
from database import SessionLocal
from schemas import LoginRequest, UserCreate, AdminCreate
from services.user_service import UserService, AdminService
from services.auth_service import auth_service
import logging
from pydantic import ValidationError

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)

# ==================== User Authentication ====================

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    db = SessionLocal()
    try:
        data = request.get_json()
        user_create = UserCreate(**data)
        user = UserService.create_user(db, user_create)
        return jsonify({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_admin": user.is_admin
        })
    except ValidationError as e:
        return jsonify({"detail": e.errors()}), 400
    except ValueError as e:
        return jsonify({"detail": str(e)}), 400
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({"detail": "فشل إنشاء الحساب"}), 500
    finally:
        db.close()

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user with username and password"""
    db = SessionLocal()
    try:
        data = request.get_json()
        login_request = LoginRequest(**data)
        user = UserService.authenticate_user(db, login_request.username, login_request.password)
        
        if not user:
            return jsonify({"detail": "اسم المستخدم أو كلمة المرور غير صحيحة"}), 401
        
        # Create tokens
        tokens = auth_service.create_tokens(user.id, user.username, user.is_admin)
        
        return jsonify({
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": tokens["token_type"],
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "is_admin": user.is_admin
            }
        })
    except ValidationError as e:
        return jsonify({"detail": e.errors()}), 400
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({"detail": "فشل تسجيل الدخول"}), 500
    finally:
        db.close()

@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """Refresh access token using refresh token"""
    db = SessionLocal()
    try:
        data = request.get_json()
        refresh_token_str = data.get("refresh_token")
        if not refresh_token_str:
            return jsonify({"detail": "توكن غير موجود"}), 401

        payload = auth_service.verify_token(refresh_token_str)
        
        if not payload or payload.get("type") != "refresh":
            return jsonify({"detail": "توكن غير صالح"}), 401
        
        user_id = int(payload.get("sub"))
        user = UserService.get_user_by_id(db, user_id)
        
        if not user:
            return jsonify({"detail": "المستخدم غير موجود"}), 401
        
        tokens = auth_service.create_tokens(user.id, user.username, user.is_admin)
        
        return jsonify(tokens)
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return jsonify({"detail": "فشل تحديث التوكن"}), 500
    finally:
        db.close()

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """Get current user information"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"detail": "توكن غير موجود"}), 401
    
    token = auth_header.split(' ')[1]
    db = SessionLocal()
    try:
        payload = auth_service.verify_token(token)
        
        if not payload:
            return jsonify({"detail": "توكن غير صالح"}), 401
        
        user_id = int(payload.get("sub"))
        user = UserService.get_user_by_id(db, user_id)
        
        if not user:
            return jsonify({"detail": "المستخدم غير موجود"}), 401
        
        return jsonify({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_admin": user.is_admin
        })
    except Exception as e:
        logger.error(f"Get current user error: {str(e)}")
        return jsonify({"detail": "فشل الحصول على بيانات المستخدم"}), 500
    finally:
        db.close()

# ==================== Admin Authentication ====================

@auth_bp.route('/admin/register', methods=['POST'])
def register_admin():
    """Register a new admin"""
    db = SessionLocal()
    try:
        data = request.get_json()
        admin_create = AdminCreate(**data)
        admin = AdminService.create_admin(db, admin_create)
        tokens = auth_service.create_tokens(admin.id, admin.username, True)
        
        return jsonify({
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": tokens["token_type"],
            "admin": {
                "id": admin.id,
                "username": admin.username,
                "email": admin.email,
                "full_name": admin.full_name,
                "role": admin.role,
                "is_active": admin.is_active
            }
        })
    except ValidationError as e:
        return jsonify({"detail": e.errors()}), 400
    except ValueError as e:
        return jsonify({"detail": str(e)}), 400
    except Exception as e:
        logger.error(f"Admin registration error: {str(e)}")
        return jsonify({"detail": "فشل إنشاء حساب الإدارة"}), 500
    finally:
        db.close()

@auth_bp.route('/admin/login', methods=['POST'])
def admin_login():
    """Login admin with username and password"""
    db = SessionLocal()
    try:
        data = request.get_json()
        login_request = LoginRequest(**data)
        admin = AdminService.authenticate_admin(db, login_request.username, login_request.password)
        
        if not admin:
            return jsonify({"detail": "اسم المستخدم أو كلمة المرور غير صحيحة"}), 401
        
        tokens = auth_service.create_tokens(admin.id, admin.username, True)
        
        return jsonify({
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": tokens["token_type"],
            "admin": {
                "id": admin.id,
                "username": admin.username,
                "email": admin.email,
                "full_name": admin.full_name,
                "role": admin.role,
                "is_active": admin.is_active
            }
        })
    except ValidationError as e:
        return jsonify({"detail": e.errors()}), 400
    except Exception as e:
        logger.error(f"Admin login error: {str(e)}")
        return jsonify({"detail": "فشل تسجيل دخول الإدارة"}), 500
    finally:
        db.close()

from functools import wraps

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"detail": "توكن غير موجود"}), 401
        
        token = auth_header.split(' ')[1]
        db = SessionLocal()
        try:
            payload = auth_service.verify_token(token)
            if not payload:
                return jsonify({"detail": "توكن غير صالح"}), 401
            
            user_id = int(payload.get("sub"))
            user = UserService.get_user_by_id(db, user_id)
            if not user:
                return jsonify({"detail": "المستخدم غير موجود"}), 401
            
            return f(user, *args, **kwargs)
        except Exception as e:
            return jsonify({"detail": str(e)}), 401
        finally:
            db.close()
    return decorated
