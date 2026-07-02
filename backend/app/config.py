import os
from dotenv import load_dotenv

load_dotenv()


class BaseConfig:
    """Base configuration with shared settings."""
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    JSON_SORT_KEYS = False  # Preserve Pydantic field order in JSON responses

    # LLM settings
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")
    USE_MOCK = os.getenv("USE_MOCK", "false").lower() == "true"


class DevelopmentConfig(BaseConfig):
    """Development configuration."""
    DEBUG = True
    TESTING = False


class TestingConfig(BaseConfig):
    """Testing configuration — always uses mock, never hits real API."""
    DEBUG = False
    TESTING = True
    USE_MOCK = True  # Force mock mode in tests


class ProductionConfig(BaseConfig):
    """Production configuration — never run with DEBUG=True."""
    DEBUG = False
    TESTING = False


# Map string names to config classes for easy lookup
config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
