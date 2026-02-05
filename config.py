import os
from datetime import timedelta

class Config:
    """Application configuration class"""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'cinemapulse-secret-key-2024'
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///cinemapulse.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Application Configuration
    APP_NAME = 'CinemaPulse'
    APP_VERSION = '1.0.0'
    
    # Pagination
    MOVIES_PER_PAGE = 12
    FEEDBACK_PER_PAGE = 20
    
    # File Upload (for future use)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'static/uploads'