"""설정 관리 모듈"""

import os
from enum import Enum
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class ModelProvider(str, Enum):
    """LLM 제공자"""
    OPENAI = "openai"
    GEMINI = "gemini"


class Settings(BaseModel):
    """전체 애플리케이션 설정"""

    # API Keys
    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    google_api_key: str = Field(default_factory=lambda: os.getenv("GOOGLE_API_KEY", ""))

    # 모델 설정
    model_provider: ModelProvider = Field(
        default_factory=lambda: ModelProvider(os.getenv("MODEL_PROVIDER", "gemini"))
    )
    openai_model: str = Field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o"))
    gemini_model: str = Field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-2.0-flash"))


# 전역 설정 인스턴스
settings = Settings()
