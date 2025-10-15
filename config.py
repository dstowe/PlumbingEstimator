"""
Application Configuration
"""
import os

class Config:
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # File Upload
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
    ALLOWED_EXTENSIONS = {'pdf', 'tif', 'tiff'}
    
    # Database
    DATABASE_PATH = 'data/estimator.db'
    
    # Application
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 5000
    
    # Detection Settings
    PDF_DPI = 150  # DPI for PDF to image conversion
    DETECTION_MIN_RADIUS = 10
    DETECTION_MAX_RADIUS = 50
    
    @staticmethod
    def init_app(app):
        """Initialize application with this config"""
        # Create necessary directories
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs('data', exist_ok=True)