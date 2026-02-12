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
    LOCAL = "local"  # 로컬 모델 (GLM-4.6V-Flash)
    VLLM = "vllm"    # vLLM 서버 (OpenAI 호환 API)


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
    local_model_path: str = Field(
        default_factory=lambda: os.getenv(
            "LOCAL_MODEL_PATH",
            "/home/ondamlab/.cache/huggingface/hub/models--zai-org--GLM-4.6V-Flash/snapshots/main"
        )
    )

    # vLLM 설정
    vllm_base_url: str = Field(
        default_factory=lambda: os.getenv("VLLM_BASE_URL", "http://localhost:8001/v1")
    )
    vllm_model: str = Field(
        default_factory=lambda: os.getenv("VLLM_MODEL", "qwen3-next-80b")
    )

    # 쿠팡 파트너스 설정
    coupang_access_key: str = Field(default_factory=lambda: os.getenv("COUPANG_ACCESS_KEY", ""))
    coupang_secret_key: str = Field(default_factory=lambda: os.getenv("COUPANG_SECRET_KEY", ""))

    # 네이버 쇼핑 API 설정
    naver_client_id: str = Field(default_factory=lambda: os.getenv("NAVER_CLIENT_ID", ""))
    naver_client_secret: str = Field(default_factory=lambda: os.getenv("NAVER_CLIENT_SECRET", ""))


# 전역 설정 인스턴스
settings = Settings()
