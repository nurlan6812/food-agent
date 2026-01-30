# 한국 음식 AI 에이전트 연구일지

> **작성일**: 2025-01-30
> **프로젝트명**: Korean Food Agent
> **기술 스택**: LangGraph, Gemini 3.0 Flash, FastAPI, Next.js

---

## 1. 프로젝트 개요

### 1.1 목적
사용자가 음식 사진을 업로드하거나 텍스트로 질문하면, AI가 음식을 인식하고 식당 정보, 레시피, 영양정보 등을 제공하는 멀티모달 대화형 에이전트 시스템 구축.

### 1.2 주요 기능
| 기능 | 설명 |
|------|------|
| 음식 이미지 인식 | Google Lens API로 음식/식당 파악 |
| 식당 검색 | 카카오맵 API로 식당 정보 및 메뉴 조회 |
| 레시피 검색 | 만개의레시피 등에서 크롤링 |
| 후기 분석 | 카카오맵 후기 크롤링 및 요약 |
| 영양정보 | 칼로리, 단백질 등 영양성분 검색 |

---

## 2. 시스템 아키텍처

### 2.1 전체 구조
```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│                   (Next.js + Tailwind)                       │
│                    localhost:3000                            │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP/SSE
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                          │
│                      localhost:8000                          │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              KoreanFoodAgent                         │    │
│  │         (LangGraph ReAct Agent)                      │    │
│  │                                                      │    │
│  │  ┌─────────────┐    ┌─────────────────────────────┐ │    │
│  │  │   Gemini    │    │         Tools               │ │    │
│  │  │  3.0 Flash  │───▶│  - search_food_by_image     │ │    │
│  │  │             │    │  - search_restaurant_info   │ │    │
│  │  │  (LLM)      │    │  - search_recipe_online     │ │    │
│  │  └─────────────┘    │  - get_restaurant_reviews   │ │    │
│  │                     │  - get_nutrition_info       │ │    │
│  │  ┌─────────────┐    └─────────────────────────────┘ │    │
│  │  │MemorySaver  │  (대화 히스토리 관리)               │    │
│  │  └─────────────┘                                    │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┬─────────────┐
        ▼             ▼             ▼             ▼
   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
   │ Google  │  │  Kakao  │  │ Serper  │  │Playwright│
   │  Lens   │  │   Map   │  │   API   │  │ (크롤링) │
   │ (SerpAPI)│  │   API   │  │         │  │         │
   └─────────┘  └─────────┘  └─────────┘  └─────────┘
```

### 2.2 디렉토리 구조
```
food_agent/
├── api/
│   └── main.py              # FastAPI 백엔드 (동기/스트리밍 API)
├── src/
│   ├── agent.py             # LangGraph 에이전트 코어
│   ├── config.py            # 설정 관리
│   └── tools/
│       ├── __init__.py      # 도구 익스포트
│       └── image_search.py  # 5개 도구 구현 (1,752줄)
├── frontend/app/            # Next.js 프론트엔드
├── .env                     # API 키 설정
└── run_all.sh               # 백엔드+프론트엔드 실행 스크립트
```

---

## 3. LangGraph 기반 에이전트 구현

### 3.1 에이전트 생성 코드
```python
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

def create_food_agent(provider, model_name, checkpointer):
    llm = get_llm(provider, model_name)

    agent = create_react_agent(
        model=llm,
        tools=ALL_TOOLS,
        prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,  # 대화 히스토리 자동 관리
    )
    return agent
```

### 3.2 ReAct 패턴
LangGraph의 `create_react_agent`는 **ReAct (Reasoning + Acting)** 패턴을 구현:

```
사용자 질문
    │
    ▼
┌─────────────────┐
│   Reasoning     │  ← LLM이 어떤 도구를 사용할지 판단
│   (사고 단계)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Acting       │  ← 선택한 도구 실행
│   (행동 단계)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Observation    │  ← 도구 실행 결과 관찰
│   (관찰 단계)    │
└────────┬────────┘
         │
    ┌────┴────┐
    │ 충분한가? │
    └────┬────┘
     No  │  Yes
    ┌────┘    └────┐
    ▼              ▼
  반복         최종 응답
```

### 3.3 메모리 관리
```python
class KoreanFoodAgent:
    def __init__(self):
        self.checkpointer = MemorySaver()  # 메모리 저장소
        self.thread_id = "default"          # 대화 세션 ID

    def _get_config(self):
        return {"configurable": {"thread_id": self.thread_id}}

    def chat(self, message):
        result = self.agent.invoke(
            {"messages": [human_message]},
            config=self._get_config()  # thread_id로 대화 구분
        )
```

- `MemorySaver`: 대화 히스토리를 메모리에 저장
- `thread_id`: 세션별로 독립적인 대화 컨텍스트 유지
- 새 대화 시작 시 `uuid.uuid4()`로 새 thread_id 생성

---

## 4. 도구(Tools) 상세

### 4.1 도구 목록
| 도구명 | 기능 | 외부 API |
|--------|------|----------|
| `search_food_by_image` | 이미지로 음식/식당 인식 | SerpAPI (Google Lens) |
| `search_restaurant_info` | 식당 검색 및 메뉴 조회 | Kakao Map API + Playwright |
| `search_recipe_online` | 레시피 검색 | Serper API + 크롤링 |
| `get_restaurant_reviews` | 식당 후기 수집 | Playwright (카카오맵 크롤링) |
| `get_nutrition_info` | 영양정보 검색 | Serper API + 크롤링 |

### 4.2 도구별 상세 설명

#### 4.2.1 `search_food_by_image`
```python
@tool
def search_food_by_image(image_source: str) -> str:
    """
    이미지 URL 또는 로컬 파일 경로를 받아 Google Lens로 검색

    처리 흐름:
    1. 로컬 이미지 → 임시 호스팅 서비스 업로드
    2. Google Lens API 호출 (SerpAPI)
    3. 검색 결과 + 블로그 본문 추출
    4. LLM이 해석할 수 있는 형태로 반환
    """
```

**출력 예시:**
```
[검색 결과]
1. 또보겠지 치즈감자 - 강남역 맛집 [네이버 블로그]
2. 또보겠지 시청직영점 치즈감자 후기 [티스토리]
...

[블로그 본문 (메뉴 판단 참고용)]
--- 블로그 1 ---
치즈감자 주문했는데 바삭한 감자튀김 위에 치즈가...

[이미지 텍스트] 또보겠지, 치즈감자
```

#### 4.2.2 `search_restaurant_info`
```python
@tool
def search_restaurant_info(query: str) -> str:
    """
    카카오맵 API로 식당 검색 + Playwright로 메뉴 크롤링

    출력에 포함되는 정보:
    - 식당명, 주소, 전화번호, 카테고리
    - 메뉴판 (Playwright 크롤링)
    - [MAP:좌표] 태그 (프론트엔드 지도 표시용)
    """
```

**MAP 태그 형식:**
```
[MAP:37.494,127.028,식당명|주소|전화|카테고리|카카오맵URL;37.502,127.024,...]
```

#### 4.2.3 `search_recipe_online`
```python
@tool
def search_recipe_online(query: str) -> str:
    """
    Serper API로 레시피 검색 후 상위 3개 페이지 크롤링

    지원 사이트:
    - 만개의레시피 (10000recipe.com) → 구조화된 파싱
    - 네이버 블로그 → 본문 텍스트 추출
    - 티스토리 → 본문 텍스트 추출
    """
```

#### 4.2.4 `get_restaurant_reviews`
```python
@tool
def get_restaurant_reviews(restaurant_name: str) -> str:
    """
    Playwright로 카카오맵에서 후기 크롤링

    추출 정보:
    - 평점, 후기 개수
    - 태그별 평가 (맛, 가성비, 친절 등)
    - 개별 후기 텍스트 (최대 15개)
    """
```

#### 4.2.5 `get_nutrition_info`
```python
@tool
def get_nutrition_info(query: str) -> str:
    """
    영양정보 검색 및 페이지 크롤링

    검색 예: "김치찌개 칼로리", "스타벅스 아메리카노 열량"
    """
```

---

## 5. 워크플로우 동작 예시

### 5.1 시나리오 1: 이미지로 음식 질문

**사용자 입력:**
```
/path/to/food.png 이 음식 뭐야?
```

**워크플로우:**
```
[1] 사용자 메시지 수신
    │
[2] 이미지 경로 감지 → 멀티모달 메시지 생성
    │
[3] LangGraph ReAct 에이전트 실행
    │
    ├─ [Reasoning] "이미지가 있으니 search_food_by_image 도구 사용"
    │
    ├─ [Acting] search_food_by_image("/path/to/food.png") 호출
    │     │
    │     ├─ 이미지 업로드 (litterbox/imgbb)
    │     ├─ Google Lens API 호출
    │     └─ 검색 결과 + 블로그 본문 반환
    │
    ├─ [Observation] 검색 결과 분석
    │     "또보겠지 치즈감자로 보임"
    │
    └─ [Response] 최종 응답 생성
          "치즈감자로 보입니다! 🍟 혹시 '또보겠지'에서 드셨나요?"
```

### 5.2 시나리오 2: 맛집 추천

**사용자 입력:**
```
강남역 근처 맛집 3곳 추천해줘
```

**워크플로우:**
```
[1] LangGraph ReAct 에이전트 실행
    │
    ├─ [Reasoning] "맛집 검색이니 search_restaurant_info 사용"
    │
    ├─ [Acting] search_restaurant_info("강남역 맛집") 호출
    │     │
    │     ├─ Kakao Map API 검색
    │     ├─ 상위 3개 식당 정보 수집
    │     ├─ Playwright로 메뉴 크롤링
    │     └─ MAP 태그 생성
    │
    ├─ [Observation] 3개 식당 정보 수신
    │
    └─ [Response] 응답 생성
          "강남역 맛집 3곳 추천드려요! 😋
           1. 삼성각 (중식) - 삼선짬뽕 유명
           2. 하이디라오 강남점 (샤브샤브)
           3. 이자카야심 (일본식주점)

           [MAP:37.494,127.028,삼성각|...; ...]"
```

### 5.3 시나리오 3: 멀티턴 대화

```
[Turn 1]
사용자: /path/to/image.png 이 음식 뭐야?
에이전트: 비빔밥으로 보입니다! 🍚

[Turn 2]  ← 이전 컨텍스트 활용 (MemorySaver)
사용자: 레시피 알려줘
에이전트: [search_recipe_online("비빔밥 레시피") 호출]
          비빔밥 레시피입니다! ...

[Turn 3]
사용자: 칼로리는?
에이전트: [get_nutrition_info("비빔밥 칼로리") 호출]
          비빔밥 1인분 약 550kcal입니다.
```

---

## 6. 시스템 프롬프트

```python
SYSTEM_PROMPT = """당신은 한국 음식 전문가 AI 어시스턴트입니다.

## 핵심 원칙
- 사용자 질문에 맞는 도구를 선택해서 호출하세요
- 추측하지 말고 도구 결과를 기반으로 답변하세요
- 도구 결과를 그대로 전달하지 말고, 핵심만 구조화해서 답변하세요
- 한국어로 자연스럽게 대화하고 이모지를 적절히 사용하세요

## 도구 사용
- search_food_by_image: 현재 메시지에 새 이미지가 있을 때만 사용
- 이전 대화에서 이미 이미지 검색을 했다면 그 결과를 활용하세요
- 후속 질문은 search_restaurant_info 등 다른 도구 사용

## 이미지 분석 응답
- 음식 이름만 물으면: "~음식으로 보입니다" + 식당이 보이면 "혹시 OO에서 드셨나요?"
- 확실하지 않으면 "~일 수도 있고, ~일 수도 있어요" 형태로 답변

## 응답 형식
- [IMAGE:url]: 음식 사진이 도움될 때 응답 앞에 포함
- [MAP:...]: 위치/맛집 질문일 때 도구 결과의 태그를 수정 없이 그대로 복사
- 중요: 응답에서 언급한 식당 개수와 [MAP:] 태그의 식당 개수가 반드시 일치해야 함
"""
```

---

## 7. API 엔드포인트

### 7.1 동기 채팅
```
POST /chat
Content-Type: application/json

{
  "message": "강남역 맛집 추천해줘",
  "session_id": "optional-session-id",
  "images": [
    {"data": "base64...", "mime_type": "image/jpeg"}
  ]
}

Response:
{
  "response": "강남역 맛집 3곳 추천드려요!...",
  "session_id": "uuid",
  "map_url": "37.494,127.028,...",
  "images": ["https://..."]
}
```

### 7.2 스트리밍 채팅
```
POST /chat/stream
Content-Type: application/json

Response: text/event-stream
data: {"type": "session", "session_id": "uuid"}
data: {"type": "tool", "tool": "search_restaurant_info", "status": "start"}
data: {"type": "tool", "tool": "search_restaurant_info", "status": "done"}
data: {"type": "text", "content": "강남역"}
data: {"type": "text", "content": " 맛집"}
...
data: {"type": "done", "map_url": "...", "images": [...]}
```

---

## 8. 기술 스택 요약

| 레이어 | 기술 |
|--------|------|
| LLM | Gemini 3.0 Flash (`gemini-3-flash-preview`) |
| 에이전트 프레임워크 | LangGraph (`create_react_agent`) |
| 메모리 | LangGraph `MemorySaver` |
| 백엔드 | FastAPI + Uvicorn |
| 프론트엔드 | Next.js 16 + Tailwind CSS |
| 외부 API | SerpAPI (Google Lens), Kakao Map API, Serper API |
| 크롤링 | Playwright (Headless Chrome) |

---

## 9. 성능 및 제한사항

### 9.1 응답 시간
| 작업 | 평균 시간 |
|------|----------|
| 텍스트 질문 (도구 1개) | 3-5초 |
| 이미지 분석 | 5-8초 |
| 식당 검색 + 메뉴 크롤링 | 5-10초 |
| 후기 크롤링 | 8-15초 |

### 9.2 알려진 제한
- Gemini API 과부하 시 503 에러 발생 가능
- Playwright 크롤링은 네트워크 상태에 의존
- 이미지 업로드 서비스 제한 (1시간 만료)

---

## 10. 향후 개선 방향

1. **캐싱 도입**: Redis로 식당 정보/메뉴 캐싱
2. **비동기 처리**: 도구 병렬 실행으로 응답 속도 개선
3. **Groq 연동**: 초저지연 추론을 위한 옵션 추가
4. **벡터 DB**: 이전 검색 결과 저장 및 재활용

---

## 참고 자료

- [LangGraph 공식 문서](https://langchain-ai.github.io/langgraph/)
- [Gemini API 문서](https://ai.google.dev/docs)
- [Kakao Map API](https://developers.kakao.com/docs/latest/ko/local/dev-guide)
