from flask import Blueprint, request, jsonify
from database import SessionLocal
from models import User, Admin, AnalysisResult
from services.user_service import UserService, AdminService
from services.auth_service import auth_service
import logging

logger = logging.getLogger(__name__)
admin_bp = Blueprint('admin', __name__)

def verify_admin_token():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None, "توكن غير موجود"
    
    token = auth_header.split(' ')[1]
    payload = auth_service.verify_token(token)
    
    if not payload or not payload.get("is_admin"):
        return None, "غير مصرح لك بالوصول"
    
    db = SessionLocal()
    try:
        admin_id = int(payload.get("sub"))
        admin = AdminService.get_admin_by_id(db, admin_id)
        if not admin or not admin.is_active:
            return None, "حساب المسؤول غير نشط"
        return admin, None
    finally:
        db.close()

@admin_bp.route('/users', methods=['GET'])
def get_users():
    admin, error = verify_admin_token()
    if error: return jsonify({"detail": error}), 401
    
    db = SessionLocal()
    try:
        users = UserService.get_all_users(db)
        return jsonify([{
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "full_name": u.full_name,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None
        } for u in users])
    finally:
        db.close()

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    admin, error = verify_admin_token()
    if error: return jsonify({"detail": error}), 401
    
    db = SessionLocal()
    try:
        success = UserService.delete_user(db, user_id)
        if success:
            return jsonify({"message": "تم حذف المستخدم بنجاح"})
        return jsonify({"detail": "المستخدم غير موجود"}), 404
    finally:
        db.close()

@admin_bp.route('/statistics', methods=['GET'])
def get_statistics():
    admin, error = verify_admin_token()
    if error: return jsonify({"detail": error}), 401
    
    db = SessionLocal()
    try:
        user_count = db.query(User).count()
        analysis_count = db.query(AnalysisResult).count()
        admin_count = db.query(Admin).count()
        
        return jsonify({
            "total_users": user_count,
            "total_analyses": analysis_count,
            "total_admins": admin_count,
            "system_health": "نشطة"
        })
    finally:
        db.close()

@admin_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "admin-api"})
