import os
from pathlib import Path


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "komiko-dev-key-change-in-production")
    BASE_DIR = Path(__file__).parent
    DATA_DIR = Path(os.environ.get("KOMIKO_DATA_DIR", str(BASE_DIR / "data")))
    DB_PATH = DATA_DIR / "komiko.db"
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{DB_PATH}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    COVER_DIR = DATA_DIR / "covers"
    MAX_CONTENT_LENGTH = 64 * 1024 * 1024
    HOST = os.environ.get("KOMIKO_HOST", "0.0.0.0")
    PORT = int(os.environ.get("KOMIKO_PORT", 5000))


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}