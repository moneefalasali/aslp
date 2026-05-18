from flask import Blueprint, request, jsonify, Response
import logging
import os
import asyncio
from sqlalchemy import desc
from config import settings
from database import SessionLocal
from models import FileRecord, AnalysisResult, FileTypeEnum
from routes.auth import token_required
from services import storage_service, audio_service, pdf_service, ai_service
from schemas import (
    FileUploadResponse, AudioProcessRequest, AudioProcessResponse,
    PDFProcessRequest, PDFProcessResponse, AnalyzeRequest, AnalyzeResponse
)
from pydantic import ValidationError

logger = logging.getLogger(__name__)
main_bp = Blueprint('main', __name__)

def run_async(coro):
    """Helper to run async functions in sync Flask routes"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

@main_bp.route('/upload', methods=['POST'])
@token_required
def upload_file(current_user):
    """Upload a file (PDF, DOCX, or Audio)"""
    db = SessionLocal()
    try:
        if 'file' not in request.files:
            return jsonify({"detail": "No file part"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"detail": "No selected file"}), 400
            
        file_extension = "." + file.filename.split(".")[-1].lower()
        
        # Determine file type
        if file_extension in settings.allowed_pdf_extensions or file_extension in ['.docx', '.doc']:
            file_type = FileTypeEnum.PDF # Using PDF enum for all documents for simplicity in current DB schema
        elif file_extension in settings.allowed_audio_extensions:
            file_type = FileTypeEnum.AUDIO
        else:
            return jsonify({"detail": f"File type not supported. Allowed: PDF, DOCX, Audio"}), 400
        
        file_content = file.read()
        if len(file_content) > settings.max_file_size:
            return jsonify({"detail": f"File size exceeds limit"}), 413
        
        # Upload
        upload_result = run_async(storage_service.upload_file(
            file_content,
            file.filename,
            file_type.value
        ))
        
        # Save to DB
        file_record = FileRecord(
            file_id=upload_result["file_id"],
            file_name=file.filename,
            file_type=file_type,
            file_url=upload_result["file_url"],
            file_size=len(file_content)
        )
        db.add(file_record)
        db.commit()
        
        return jsonify(upload_result)
    
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({"detail": str(e)}), 500
    finally:
        db.close()

@main_bp.route('/process-audio', methods=['POST'])
@token_required
def process_audio(current_user):
    """Transcribe audio file"""
    try:
        data = request.get_json()
        # Support both URL and local path if provided
        file_path = data.get('file_url') or data.get('file_path')
        if not file_path:
            return jsonify({"detail": "file_url or file_path is required"}), 400
            
        language = data.get('language', 'ar')
        
        result = run_async(audio_service.transcribe_audio(file_path, language))
        return jsonify(result)
    except Exception as e:
        logger.error(f"Audio processing error: {e}")
        return jsonify({"detail": str(e)}), 500

@main_bp.route('/process-pdf', methods=['POST'])
@token_required
def process_pdf(current_user):
    """Extract text from PDF/DOCX"""
    try:
        data = request.get_json()
        file_path = data.get('file_url') or data.get('file_path')
        if not file_path:
            return jsonify({"detail": "file_url or file_path is required"}), 400
            
        result = run_async(pdf_service.extract_text(file_path))
        return jsonify(result)
    except Exception as e:
        logger.error(f"PDF processing error: {e}")
        return jsonify({"detail": str(e)}), 500

@main_bp.route('/analyze', methods=['POST'])
@token_required
def analyze_text(current_user):
    """Analyze text using AI"""
    db = SessionLocal()
    try:
        data = request.get_json()
        text = data.get('text')
        if not text:
            return jsonify({"detail": "text is required"}), 400
            
        analysis_type = data.get('analysis_type', 'both')
        target_language = data.get('target_language', 'ar')
        file_id = data.get('file_id', 'manual')
        file_name = data.get('file_name', 'text_input')
        
        analysis_result = run_async(ai_service.analyze_text(text, analysis_type, target_language))
        
        # Save result
        db_result = AnalysisResult(
            file_id=file_id,
            file_name=file_name,
            file_type=FileTypeEnum.PDF, # Default
            original_text=text[:5000],
            summary=analysis_result.get("summary", ""),
            key_points=analysis_result.get("key_points", []),
            quizzes=analysis_result.get("quizzes", [])
        )
        db.add(db_result)
        db.commit()
        
        result_payload = analysis_result.copy()
        result_payload['provider'] = analysis_result.get('provider', 'local')
        result_payload['used_fallback'] = analysis_result.get('used_fallback', False)
        return jsonify(result_payload)
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return jsonify({"detail": str(e)}), 500
    finally:
        db.close()

@main_bp.route('/download-summary/<file_id>', methods=['GET'])
@token_required
def download_summary(current_user, file_id):
    db = SessionLocal()
    try:
        result = db.query(AnalysisResult).filter(AnalysisResult.file_id == file_id).first()
        if not result:
            return jsonify({"detail": "Not found"}), 404

        pdf_bytes = pdf_service.create_summary_pdf(
            title=result.file_name,
            summary=result.summary,
            key_points=result.key_points or [],
            quizzes=result.quizzes or []
        )

        return Response(
            pdf_bytes, 
            mimetype='application/pdf',
            headers={'Content-Disposition': f'attachment; filename=summary-{file_id}.pdf'}
        )
    except Exception as e:
        return jsonify({"detail": str(e)}), 500
    finally:
        db.close()

@main_bp.route('/results/<file_id>', methods=['GET'])
@token_required
def get_results(current_user, file_id):
    db = SessionLocal()
    try:
        result = db.query(AnalysisResult).filter(AnalysisResult.file_id == file_id).first()
        if not result:
            return jsonify({"detail": "Not found"}), 404
        
        return jsonify({
            "file_id": result.file_id,
            "file_name": result.file_name,
            "summary": result.summary,
            "key_points": result.key_points,
            "quizzes": result.quizzes
        })
    finally:
        db.close()

@main_bp.route('/history', methods=['GET'])
@token_required
def get_history(current_user):
    db = SessionLocal()
    try:
        history_items = db.query(AnalysisResult).order_by(desc(AnalysisResult.created_at)).limit(50).all()
        return jsonify([
            {
                "file_id": item.file_id,
                "file_name": item.file_name,
                "file_type": item.file_type.value if item.file_type else None,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "summary": (item.summary or '')[:200]
            }
            for item in history_items
        ])
    finally:
        db.close()

@main_bp.route('/ai-status', methods=['GET'])
def get_ai_status():
    return jsonify({
        "preferred_provider": ai_service.ai_provider,
        "ollama_active": bool(ai_service.client),
        "openai_active": bool(ai_service.openai_client),
        "model": ai_service.openai_model if ai_service.ai_provider == 'openai' else ai_service.ollama_model
    })
