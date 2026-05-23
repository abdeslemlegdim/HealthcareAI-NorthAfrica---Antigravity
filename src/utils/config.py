"""
Configuration management using Pydantic Settings
"""
from typing import List, Any
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "Healthcare AI Assistant"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4
    API_RELOAD: bool = True
    CORS_ORIGINS: str = (
        "http://localhost:3000,"
        "http://localhost:5173,"
        "http://localhost:5174,"
        "http://localhost:5175,"
        "http://localhost:5176,"
        "http://localhost:5177,"
        "http://localhost:8501,"
        "http://127.0.0.1:5173,"
        "http://127.0.0.1:5174,"
        "http://127.0.0.1:5175,"
        "http://127.0.0.1:5176,"
        "http://127.0.0.1:5177"
    )
    
    # Security
    SECRET_KEY: str = Field(..., description="Secret key for encryption")
    JWT_SECRET_KEY: str = Field(..., description="JWT signing key")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REFRESH_TOKEN_REMEMBER_ME_DAYS: int = 30  # Extended refresh token expiry with "remember me"
    
    # HTTPS and Security Headers
    HTTPS_ONLY: bool = False  # Enforce HTTPS in production
    SECURE_COOKIES: bool = False  # Set secure flag on cookies (requires HTTPS)
    HTTPONLY_COOKIES: bool = True  # Set HttpOnly flag on cookies
    SAMESITE_COOKIES: str = "lax"  # SameSite cookie policy: "strict", "lax", or "none"
    
    # Rate Limiting
    RATE_LIMIT_LOGIN_ATTEMPTS: int = 5  # Max login attempts per email per window
    RATE_LIMIT_LOGIN_WINDOW_MINUTES: int = 15  # Login rate limit window
    RATE_LIMIT_REGISTER_ATTEMPTS: int = 10  # Max registrations per IP per window
    RATE_LIMIT_REGISTER_WINDOW_MINUTES: int = 60  # Registration rate limit window
    RATE_LIMIT_REFRESH_ATTEMPTS: int = 20  # Max token refreshes per user per window
    RATE_LIMIT_REFRESH_WINDOW_MINUTES: int = 60  # Refresh rate limit window
    
    # Database
    DATABASE_URL: str = Field(default="sqlite:///./healthcare_ai.db", description="Database connection string")
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: str = ""
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str = ""
    
    # ML Models
    MEDICAL_IMAGE_MODEL_PATH: str = "models/efficientnet_chest.pt"
    GRADCAM_LAYER_NAME: str = "features.7"
    EMBEDDING_MODEL: str = "sentence-transformers/biomed_roberta_base"
    EMBEDDING_FALLBACK_MODEL: str = "intfloat/multilingual-e5-base"
    RERANK_MODEL: str = "cross-encoder/biomed-roberta-base"
    LLM_MODEL: str = "Qwen/Qwen2.5-7B-Instruct"
    # Backward-compatible aliases used by older modules.
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/biomed_roberta_base"
    LLM_MODEL_NAME: str = "Qwen/Qwen2.5-7B-Instruct"
    RERANKER_MODEL_NAME: str = "cross-encoder/biomed-roberta-base"
    RPPG_MODEL_PATH: str = "models/rppg_model.pt"
    
    # Paths
    DATA_RAW_DIR: str = "data/raw"
    DATA_PROCESSED_DIR: str = "data/processed"
    MEDICAL_KG_DIR: str = "data/medical_kg"
    MODELS_DIR: str = "models"
    
    # Knowledge Graph
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = Field(default="neo4j", description="Neo4j password")
    
    # MLOps
    MLFLOW_TRACKING_URI: str = "http://localhost:5000"
    MLFLOW_EXPERIMENT_NAME: str = "healthcare-ai-experiments"
    WANDB_API_KEY: str = ""
    WANDB_PROJECT: str = "healthcare-ai-north-africa"
    WANDB_ENTITY: str = ""
    
    # External APIs
    OPENAI_API_KEY: str = ""
    HUGGINGFACE_TOKEN: str = ""
    OPENAI_BASE_URL: str = ""
    OPENROUTER_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    OPENROUTER_SITE_URL: str = ""
    OPENROUTER_APP_NAME: str = "Healthcare AI Assistant"

    # Model execution mode flags (Phase 1 API-first, Phase 2 local models)
    LLM_ENABLED: bool = True
    USE_RAG: bool = True
    USE_LLM_API: bool = False
    USE_EMBEDDING_API: bool = False
    USE_RERANK_API: bool = False
    USE_IMAGING_API: bool = False

    # Optional explicit API endpoints (OpenAI-compatible or HF Inference)
    EMBEDDING_API_ENDPOINT: str = ""
    RERANK_API_ENDPOINT: str = ""
    LLM_API_ENDPOINT: str = ""
    LLM_API_MODELS: str = ""
    IMAGING_API_ENDPOINT: str = ""
    IMAGING_EXPLAIN_API_ENDPOINT: str = ""
    IMAGING_API_KEY: str = ""
    
    # Monitoring
    PROMETHEUS_PORT: int = 9090
    GRAFANA_PORT: int = 3000
    
    # Languages
    SUPPORTED_LANGUAGES: str = "ar,fr,en"
    DEFAULT_LANGUAGE: str = "ar"
    
    # Datasets
    CHEST_XRAY_DATASET_PATH: str = "data/raw/chest_xray"
    COVID_DATASET_PATH: str = "data/raw/covid19"
    TBX11K_DATASET_PATH: str = "data/raw/tbx11k"
    
    # Deployment
    DOCKER_REGISTRY: str = ""
    DOCKER_IMAGE_TAG: str = "latest"
    
    # Feature Flags
    ENABLE_MEDICAL_IMAGING: bool = True
    ENABLE_RAG_SYSTEM: bool = True
    ENABLE_VITAL_SIGNS: bool = True
    ENABLE_KNOWLEDGE_GRAPH: bool = True
    ENABLE_EXPLAINABILITY: bool = True
    ENABLE_AUTHENTICATION: bool = True  # Enable/disable authentication system
    
    # Performance
    MAX_BATCH_SIZE: int = 32
    NUM_WORKERS: int = 4
    DEVICE: str = "cuda"
    MIXED_PRECISION: bool = True
    
    # HIPAA Compliance
    ENABLE_AUDIT_LOGGING: bool = True
    ENABLE_DATA_ENCRYPTION: bool = True
    PHI_ANONYMIZATION: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    @field_validator("DEBUG", mode="before")
    @classmethod
    def _normalize_debug_flag(cls, value: Any) -> Any:
        """Accept common environment-style debug values such as release/production."""
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"release", "prod", "production"}:
                return False
            if lowered in {"dev", "debug", "development"}:
                return True
        return value


# Global settings instance
settings = Settings()
