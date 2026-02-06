"""한국 음식 에이전트 - LangGraph 기반 (멀티모달 지원)"""

import os
import re
import uuid
import base64
from pathlib import Path
from typing import Optional, List, Dict, Any
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from .config import settings, ModelProvider
from .tools import ALL_TOOLS


# 시스템 프롬프트
SYSTEM_PROMPT = """한국 음식 전문가 AI입니다. 반드시 도구를 호출해서 답변하세요.
- 식당/맛집 → search_restaurant_info
- 레시피 → search_recipe_online
- 영양정보 → get_nutrition_info
- 이미지 분석 → search_food_by_image
- 후기 → get_restaurant_reviews
도구 결과 기반으로만 답변하고 URL은 도구 결과 그대로 복사하세요.
[MAP:...] 태그도 수정없이 그대로 응답에 포함하세요.
한국어로 자연스럽게 이모지와 함께 답변하세요."""


def get_llm(provider: Optional[str] = None, model_name: Optional[str] = None) -> BaseChatModel:
    """
    설정에 따라 LLM 모델을 가져옵니다.

    Args:
        provider: 모델 제공자 (openai, gemini, local). None이면 설정 파일 사용.
        model_name: 모델 이름. None이면 설정 파일 사용.

    Returns:
        LLM 모델 인스턴스
    """
    if provider is None:
        provider = settings.model_provider.value

    if provider == "openai" or provider == ModelProvider.OPENAI:
        return ChatOpenAI(
            model=model_name or settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.7,
            streaming=True,  # 🔥 실시간 스트리밍 활성화
        )
    elif provider == "gemini" or provider == ModelProvider.GEMINI:
        return ChatGoogleGenerativeAI(
            model=model_name or settings.gemini_model,
            google_api_key=settings.google_api_key,
            temperature=0.7,
            streaming=True,  # 🔥 실시간 스트리밍 활성화
        )
    elif provider == "local" or provider == ModelProvider.LOCAL:
        from .local_llm import get_local_glm
        return get_local_glm(
            model_path=model_name or settings.local_model_path,
            temperature=0.7,
            max_new_tokens=2048
        )
    elif provider == "vllm" or provider == ModelProvider.VLLM:
        return ChatOpenAI(
            model=model_name or settings.vllm_model,
            base_url=settings.vllm_base_url,
            api_key="not-needed",
            temperature=0.7,
            streaming=True,
        )
    else:
        raise ValueError(f"지원하지 않는 모델 제공자: {provider}")


def create_food_agent(
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
    checkpointer: Optional[MemorySaver] = None
):
    """
    한국 음식 에이전트를 생성합니다.

    Args:
        provider: 모델 제공자 (openai, gemini)
        model_name: 사용할 모델 이름
        checkpointer: 메모리 체크포인터 (대화 히스토리 자동 관리)

    Returns:
        LangGraph 에이전트
    """
    llm = get_llm(provider, model_name)

    agent = create_react_agent(
        model=llm,
        tools=ALL_TOOLS,
        prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )

    return agent


def load_image_as_base64(image_path: str) -> Optional[str]:
    """
    이미지 파일을 base64로 인코딩합니다.

    Args:
        image_path: 이미지 파일 경로

    Returns:
        base64 인코딩된 이미지 문자열
    """
    if not os.path.exists(image_path):
        return None

    with open(image_path, "rb") as f:
        image_data = f.read()

    return base64.b64encode(image_data).decode("utf-8")


def get_image_mime_type(image_path: str) -> str:
    """이미지 파일의 MIME 타입을 반환합니다."""
    ext = Path(image_path).suffix.lower()
    mime_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    return mime_types.get(ext, "image/jpeg")


def extract_image_paths(message: str) -> List[str]:
    """
    메시지에서 이미지 경로를 추출합니다.

    Args:
        message: 사용자 메시지

    Returns:
        이미지 경로 리스트
    """
    image_paths = []

    # 파일 경로 패턴 (절대 경로)
    path_pattern = r'(/[^\s]+\.(?:jpg|jpeg|png|gif|webp))'
    matches = re.findall(path_pattern, message, re.IGNORECASE)

    for match in matches:
        if os.path.exists(match):
            image_paths.append(match)

    return image_paths


def create_multimodal_content(message: str, image_paths: List[str]) -> List[Dict[str, Any]]:
    """
    텍스트와 이미지를 포함한 멀티모달 콘텐츠를 생성합니다.

    Args:
        message: 텍스트 메시지 (이미지 경로 포함)
        image_paths: 이미지 경로 리스트

    Returns:
        멀티모달 콘텐츠 리스트
    """
    content = []

    # 이미지 추가
    for image_path in image_paths:
        base64_image = load_image_as_base64(image_path)
        if base64_image:
            mime_type = get_image_mime_type(image_path)
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{base64_image}"
                }
            })

    # 텍스트 추가 (경로 유지 - 도구에서 사용)
    content.append({
        "type": "text",
        "text": message
    })

    return content


class KoreanFoodAgent:
    """한국 음식 에이전트 클래스 (MemorySaver로 자동 히스토리 관리)"""

    def __init__(
        self,
        provider: Optional[str] = None,
        model_name: Optional[str] = None
    ):
        """
        Args:
            provider: 모델 제공자 (openai, gemini)
            model_name: 사용할 모델 이름
        """
        self.provider = provider or settings.model_provider.value
        self.model_name = model_name
        self.checkpointer = MemorySaver()
        self.agent = create_food_agent(provider, model_name, self.checkpointer)
        self.thread_id = "default"

    def new_conversation(self):
        """새 대화를 시작합니다 (새 thread_id 생성)."""
        self.thread_id = str(uuid.uuid4())

    def clear_history(self):
        """대화 히스토리를 초기화합니다 (새 thread_id로 전환)."""
        self.new_conversation()

    def _get_config(self):
        """현재 thread_id로 config 생성."""
        return {"configurable": {"thread_id": self.thread_id}}

    def _prepare_message(self, message: str) -> HumanMessage:
        """메시지를 HumanMessage로 변환 (이미지 포함 가능)."""
        image_paths = extract_image_paths(message)

        if image_paths:
            content = create_multimodal_content(message, image_paths)
            return HumanMessage(content=content)

        return HumanMessage(content=message)

    def chat(self, message: str) -> str:
        """
        사용자 메시지에 응답합니다. (멀티모달 지원, 자동 히스토리 관리)

        Args:
            message: 사용자 입력 메시지 (이미지 경로 포함 가능)

        Returns:
            에이전트 응답
        """
        human_message = self._prepare_message(message)

        result = self.agent.invoke(
            {"messages": [human_message]},
            config=self._get_config()
        )

        messages = result.get("messages", [])
        if messages:
            last_message = messages[-1]
            content = last_message.content
            if isinstance(content, list):
                # 멀티모달 응답에서 텍스트 추출
                for item in content:
                    if isinstance(item, dict) and item.get('type') == 'text':
                        return item.get('text', '')
            return content if isinstance(content, str) else str(content)

        return "응답을 생성하지 못했습니다."

    def stream(self, message: str):
        """
        스트리밍으로 응답합니다. (자동 히스토리 관리)

        Args:
            message: 사용자 입력 메시지

        Yields:
            (message_chunk, metadata) 튜플
        """
        human_message = self._prepare_message(message)

        for chunk in self.agent.stream(
            {"messages": [human_message]},
            config=self._get_config(),
            stream_mode=["messages", "custom"]  # custom 이벤트 활성화
        ):
            yield chunk

    def switch_model(self, provider: str, model_name: Optional[str] = None):
        """
        사용 모델을 전환합니다.

        Args:
            provider: 새 모델 제공자
            model_name: 새 모델 이름
        """
        self.provider = provider
        self.model_name = model_name
        self.agent = create_food_agent(provider, model_name, self.checkpointer)
        self.new_conversation()  # 모델 전환 시 새 대화 시작
        print(f"✅ 모델 전환 완료: {provider} - {model_name or '기본 모델'}")
