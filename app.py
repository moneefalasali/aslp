import logging
import os
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables before importing config
load_dotenv(override=True)
from config import settings
from database import init_db, SessionLocal
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.main_routes import main_bp

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = settings.secret_key

    # Configure UTF-8 encoding
    app.config['JSON_AS_ASCII'] = False
    
    # Configure CORS
    CORS(app, resources={r"/api/*": {"origins": settings.allowed_origins}}, supports_credentials=True)
    
    # Initialize database
    with app.app_context():
        init_db()
        logger.info("Database initialized")
    
    # Register Blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(main_bp, url_prefix='/api')
    
    @app.route('/', methods=['GET'])
    def index():
        return render_template('index.html')

    @app.route('/login', methods=['GET'])
    def login_page():
        return render_template('login.html')

    @app.route('/register', methods=['GET'])
    def register_page():
        return render_template('register.html')

    @app.route('/admin-login', methods=['GET'])
    def admin_login_page():
        return render_template('admin_login.html')

    @app.route('/admin-dashboard', methods=['GET'])
    def admin_dashboard_page():
        return render_template('admin_dashboard.html')

    @app.route('/uploads/<path:filename>', methods=['GET'])
    def serve_upload(filename):
        uploads_path = os.path.abspath(settings.upload_folder)
        return send_from_directory(uploads_path, filename)

    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({"status": "healthy", "version": "1.0.0"})

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=settings.debug)
