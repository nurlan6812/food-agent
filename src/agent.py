"""한국 음식 에이전트 - LangGraph 기반 (멀티모달 지원)"""

import os
import re
import uuid
import base64
from pathlib import Path
from typing import Optional, List, Dict, Any
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_core.messages.utils import trim_messages, count_tokens_approximately
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
- 식재료/식품/조리도구 구매 → search_naver_products
- 레시피 재료 구매 링크 → search_recipe_ingredients (search_recipe_online 후 호출)
- 위 도구 모두 해당하지 않는 질문에만 → web_search
도구 결과 기반으로 사용자 질문에 자세하고 친절하게 답변하세요.
사용자가 명시적으로 요청한 정보에 해당하는 도구만 호출하세요. 도구 결과에서 파생된 추가 검색은 하지 마세요.
반드시 한국어로만 답변하세요. 중국어/영어 사용 금지.

## 응답 형식
- 마크다운과 이모지를 활용해 보기 좋고 읽기 쉽게 작성하세요
- 레시피 조리 순서는 반드시 번호(1. 2. 3.)를 매겨 단계별로 작성하세요
- 도구 결과의 범위 표현(2～3분, 1～2큰술 등)을 그대로 유지하세요

## 음식 외 질문 처리
한국 음식과 관련 없는 질문(숙박, 쇼핑, 여행, 패션 등)이 들어오면:
- "한국 음식 전문가 AI"임을 먼저 밝히고, "전문 분야는 아니지만"이라고 전제한 뒤 답변하세요
- 도구를 활용할 수 있으면 활용해서 답변하세요
- 마지막에 자연스럽게 음식 관련 질문으로 유도하세요

## 레시피 재료 구매 링크
레시피를 안내할 때, search_recipe_online 결과를 받은 후 반드시 search_recipe_ingredients를 호출하세요.
물, 소금, 통깨 등 기본 재료 포함 모든 재료를 빠짐없이 쉼표로 구분하여 전달하세요.
재료 목록은 아래 형식으로 작성하세요 (모든 재료에 구매하기 링크 필수):
- 재료명 분량 [구매하기](상품URL)
상품URL은 search_recipe_ingredients 결과에서 각 재료의 URL을 사용하세요.

## 이미지 분석 응답
- 이미지 + 질문이 올 경우 search_food_by_image를 우선 호출 후, 질문에 필요한 도구를 순차적으로 호출
- 음식 이름만 물으면: "~음식으로 보입니다" + 식당이 보이면 "혹시 OO에서 드셨나요?"
- 식당/메뉴명까지 물으면: 검색 결과에 여러 후보가 있으면 함께 언급해주세요
- 도구 결과를 단정짓지 말고 "~로 보입니다", "~일 수도 있어요" 형태로 답변하세요

## 식당 카드 출력 규칙
식당 정보를 안내할 때 (추천, 이미지 식별, 후기 등 모든 상황):
- 주소/전화번호/카카오맵 링크는 카드에 자동 표시되므로 본문에 반복하지 마세요
- 각 식당의 특징, 대표 메뉴 등 도구 결과에서 얻은 유용한 정보를 자연스럽게 설명하세요
- 메뉴 검색 결과에 날짜가 표시된 경우 (예: "(2020-05-10)"), 2년 이상 오래된 정보는 "해당 가격은 OO년 기준이므로 현재는 다를 수 있습니다"라고 안내하세요
- [MAP:...] 태그는 도구 결과에서 수정 없이 그대로 복사해서 응답에 포함하세요
- 반드시 응답 끝에 아래 형식으로 카드 데이터를 출력하세요. 이 태그가 없으면 사용자에게 카드가 표시되지 않습니다:
[RESTAURANTS_JSON:[{"name":"식당명","address":"주소","phone":"전화","category":"카테고리","kakaoUrl":"카카오맵링크","description":"한줄 추천 포인트","imageUrl":"이미지URL"}, ...]]
- 모든 필드는 도구 결과에서 그대로 복사하세요
- name: "식당명 지점명" 형식으로 작성. 도구 결과에 지점명이 없으면 "식당명 지역명+점" 형태로 붙이세요 (예: 사용자가 신논현을 물었고 도구에 "썬데이브리즈"만 있으면 → "썬데이브리즈 신논현점")
- kakaoUrl: 도구 결과에 카카오맵 링크(http://place.map.kakao.com/...)가 있으면 그대로 복사. 없으면 빈 문자열("")로 비워두세요. 절대 URL을 추측하거나 만들지 마세요
- imageUrl: [THUMBNAIL:url|#번호] 태그가 있으면 해당 식당과 관련된 썸네일 URL을 넣으세요. 없으면 빈 문자열("")로 비워두세요
- address, phone: 도구 결과에 있으면 복사, 없으면 빈 문자열("")로 비워두세요

## 상품 추천 응답
상품 정보가 도구 결과에 있을 때:
- 사용자의 요구(예: 가격대, 용도)에 맞는 상품만 골라 추천하세요
- 상품별 특징, 용도, 활용 팁을 자연스럽게 설명하세요
- 상품명, 가격은 카드에 표시되므로 본문에 나열하지 마세요
- 선택 기준이나 비교 포인트 등 구매에 도움이 되는 정보를 풍부하게 작성하세요
- 상품을 추천할 때 반드시 응답 끝에 아래 형식으로 카드 데이터를 출력하세요. 이 태그가 없으면 사용자에게 카드가 표시되지 않습니다:
[PRODUCTS_JSON:[{"name":"상품명","price":가격숫자,"imageUrl":"이미지URL","productUrl":"구매링크","mall":"판매처","brand":"브랜드"}, ...]]
- 모든 필드는 도구 결과의 PRODUCTS_JSON에서 관련 상품만 골라서 그대로 복사하세요
- 관련 없는 상품(검색어와 무관한 상품, 액세서리 등)은 제외하세요

## 후속 질문 제안
응답 맨 끝에 [SUGGEST:질문내용] 태그로 후속 질문을 2~3개 제안하세요. 물음표 넣지 마세요.
반드시 현재 도구로 답변 가능한 질문만 제안하세요 (맛집 검색, 레시피, 영양정보, 후기, 식재료 쇼핑)."""


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
            temperature=0.3,
            streaming=True,
        )
    else:
        raise ValueError(f"지원하지 않는 모델 제공자: {provider}")


def _pre_model_trim(state):
    """vLLM용: 오래된 메시지를 토큰 기반으로 제거합니다.
    최신 메시지 우선 보존, tool call/result 쌍 자동 유지."""
    trimmed = trim_messages(
        state["messages"],
        strategy="last",
        token_counter=count_tokens_approximately,
        max_tokens=24576,
        start_on="human",
        end_on=("human", "tool"),
    )
    # 디버그: LLM에 전달되는 메시지 로깅
    import logging
    logger = logging.getLogger("uvicorn.error")
    for msg in trimmed:
        role = getattr(msg, 'type', 'unknown')
        if role == 'ai' and hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tc in msg.tool_calls:
                logger.warning(f"[PRE_MODEL] ai tool_call: {tc['name']}({tc.get('args',{})})")
        elif role == 'tool':
            content_preview = str(msg.content)[:100] if msg.content else ''
            logger.warning(f"[PRE_MODEL] tool result ({msg.name}): {content_preview}...")
        elif role == 'human':
            content_preview = str(msg.content)[:100] if msg.content else ''
            logger.warning(f"[PRE_MODEL] human: {content_preview}")
    return {"llm_input_messages": trimmed}


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

    p = provider or settings.model_provider.value
    use_trim = p in ("vllm", ModelProvider.VLLM)

    agent = create_react_agent(
        model=llm,
        tools=ALL_TOOLS,
        prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
        pre_model_hook=_pre_model_trim if use_trim else None,
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
        """메시지를 HumanMessage로 변환.
        vLLM(텍스트 전용)에서는 이미지를 포함하지 않음 - Gemini가 도구 내에서 처리."""
        # vLLM은 텍스트 전용 모델이므로 이미지 경로만 텍스트로 전달
        # 에이전트가 search_food_by_image 도구에 경로를 전달하면 Gemini가 분석
        if self.provider in ("vllm", ModelProvider.VLLM):
            return HumanMessage(content=message)

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
