import os
from datetime import timedelta
import logging


class Config:
    """Cấu hình chung cho ứng dụng Flask."""
    # Cấu hình cơ sở dữ liệu
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'mysql+pymysql://root:lam27072004Aa@localhost/dbsaas?charset=utf8mb4'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Tắt theo dõi sự thay đổi để giảm overhead

    # Cấu hình Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-default-secret-key')  # Lấy từ biến môi trường
    SESSION_COOKIE_SECURE = True  # Bảo mật cookie
    SESSION_COOKIE_HTTPONLY = True  # Chỉ cho phép cookie được sử dụng bởi HTTP
    SESSION_COOKIE_SAMESITE = 'Lax'  # Chống tấn công CSRF

    # Giới hạn thời gian session
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)  # Session tồn tại trong 1 ngày

    # Các cấu hình khác
    DEBUG = False  # Tắt debug mặc định
    TESTING = False  # Tắt chế độ kiểm thử mặc định

    # Logging mặc định
    LOGGING_LEVEL = logging.INFO

class DevelopmentConfig(Config):
    """Cấu hình cho môi trường phát triển."""
    DEBUG = True  # Bật debug
    SQLALCHEMY_ECHO = True  # Hiển thị câu lệnh SQL để debug

class TestingConfig(Config):
    """Cấu hình cho môi trường kiểm thử."""
    TESTING = True  # Bật chế độ kiểm thử
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'TEST_DATABASE_URL',
        'sqlite:///:memory:'  # Sử dụng SQLite in-memory cho kiểm thử
    )
    SESSION_COOKIE_SECURE = False  # Không cần cookie bảo mật trong kiểm thử

class ProductionConfig(Config):
    """Cấu hình cho môi trường sản xuất."""
    DEBUG = False  # Tắt debug
    SESSION_COOKIE_SECURE = True  # Bật bảo mật cho cookie
    LOGGING_LEVEL = logging.ERROR  # Chỉ log lỗi

# Lựa chọn cấu hình dựa trên biến môi trường
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}

def get_config():
    """Lấy cấu hình dựa trên biến môi trường FLASK_ENV."""
    env = os.getenv('FLASK_ENV', 'development').lower()
    return config_by_name.get(env, DevelopmentConfig)