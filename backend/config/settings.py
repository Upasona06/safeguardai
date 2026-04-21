"""
Application configuration — loaded from environment variables.
All secrets must live in .env; never hardcode.
"""

import json
from pathlib import Path
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[
            str(PROJECT_ROOT / ".env"),                       
            str(PROJECT_ROOT / ".env.local"),                   
        ],
        env_file_encoding="utf-8",
        extra="ignore",
    )

                                                                   
    APP_ENV: str = "development"
    DEBUG: bool = False
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "https://safeguard.ai",
        "https://safeguard-ai-omega.vercel.app",
    ]

                                                                   
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "safeguard_ai"

                                                                   
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

                                                                   
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

                                                                   
    HF_MODEL_NAME: str = "microsoft/deberta-v3-base"
    HF_CACHE_DIR: str = "/tmp/hf_cache"
    HF_DEVICE: str = "cpu"                            
    HF_ENABLE_MODEL: bool = False                                                  
    HF_USE_QUANTIZATION: bool = True                                      
    HF_ALLOW_DOWNLOAD: bool = False                                              
    HF_MAX_SEQUENCE_LENGTH: int = 512
    HF_BATCH_SIZE: int = 32
    EXPLAINABILITY_USE_MODEL: bool = False                                           

                                                                   
                                                
    HF_ENABLE_GATE_MODEL: bool = False
    TOXIC_GATE_MODEL_NAME: str = "microsoft/mdeberta-v3-base"
    TOXIC_GATE_THRESHOLD: float = 0.35

                                                                 
    HF_ENABLE_MULTILABEL_MODEL: bool = False
    TOXIC_MULTILABEL_MODEL_NAME: str = "xlm-roberta-large"

                                                                           
    CONTEXT_LLM_ENABLED: bool = False
    CONTEXT_LLM_ENDPOINT: str = ""
    CONTEXT_LLM_MODEL: str = "Qwen/Qwen2.5-7B-Instruct"
    CONTEXT_LLM_TIMEOUT_MS: int = 4000
    CONTEXT_ESCALATION_MIN_SCORE: float = 0.55

                                                                   
    GROOMING_MODEL: str = "models/grooming_classifier"

                                                                   
    MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024         

    # OCR performance controls
    OCR_MAX_DIM: int = 1800
    OCR_UPSCALE_MIN_DIM: int = 900
    OCR_UPSCALE_FACTOR: float = 1.5
    OCR_ENABLE_EASYOCR_FALLBACK: bool = True
    OCR_FALLBACK_TIME_BUDGET_SEC: float = 8.0

    # Image-only harmful-content detection
    IMAGE_ENABLE_SAFETY_MODEL: bool = True
    IMAGE_SAFETY_MODEL_NAME: str = "Falconsai/nsfw_image_detection"
    IMAGE_ENABLE_CLIP_ZEROSHOT: bool = False
    IMAGE_CLIP_MODEL_NAME: str = "openai/clip-vit-base-patch32"

                                                                   
    FIR_OUTPUT_DIR: str = "/tmp/fir_pdfs"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value):
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return []
            if stripped.startswith("["):
                return json.loads(stripped)
            return [origin.strip() for origin in stripped.split(",") if origin.strip()]
        return value


settings = Settings()
