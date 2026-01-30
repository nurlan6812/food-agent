# 🍜 Korean Food Agent

한국 음식 도메인 특화 AI 에이전트 - LangGraph 기반, GPT-5/Gemini 3 지원

## 주요 기능

- 🔍 **레시피 검색**: 음식명 또는 재료로 레시피 검색
- 🥗 **재료 기반 추천**: 보유 재료로 만들 수 있는 음식 추천
- 📊 **영양 정보**: 칼로리, 단백질 등 영양 성분 조회
- 📅 **식단 계획**: 목표에 맞는 주간 식단 생성
- 👨‍🍳 **조리 가이드**: 단계별 조리법 안내
- 🔄 **재료 대체**: 대체 가능한 재료 추천

## 설치

```bash
# 저장소 클론
cd food_agent

# 가상환경 생성 (권장)
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt
```

## 설정

`.env.example`을 `.env`로 복사하고 API 키를 설정하세요:

```bash
cp .env.example .env
```

```env
# OpenAI API Key (GPT-5 사용시)
OPENAI_API_KEY=your-openai-api-key

# Google AI API Key (Gemini 사용시)
GOOGLE_API_KEY=your-google-api-key

# 기본 모델 제공자 (openai 또는 gemini)
MODEL_PROVIDER=openai
```

## 사용법

### CLI 실행

```bash
python -m src.main
```

### Python 코드에서 사용

```python
from src.agent import KoreanFoodAgent

# 에이전트 생성 (기본 설정 사용)
agent = KoreanFoodAgent()

# 또는 특정 모델 지정
agent = KoreanFoodAgent(provider="openai", model_name="gpt-5.2")

# 대화
response = agent.chat("김치찌개 레시피 알려줘")
print(response)

# 모델 전환
agent.switch_model("gemini", "gemini-3-pro-preview")
```

### 비동기 사용

```python
import asyncio
from src.agent import KoreanFoodAgent

async def main():
    agent = KoreanFoodAgent()
    response = await agent.achat("비빔밥 칼로리가 얼마야?")
    print(response)

asyncio.run(main())
```

## 지원 모델

| 제공자 | 모델 | 설정값 |
|--------|------|--------|
| OpenAI | GPT-5 | `gpt-5` |
| OpenAI | GPT-5.1 | `gpt-5.1` |
| OpenAI | GPT-5.2 | `gpt-5.2` |
| Google | Gemini 3 Flash | `gemini-3-flash-preview` |
| Google | Gemini 3 Pro | `gemini-3-pro-preview` |

## 프로젝트 구조

```
food_agent/
├── src/
│   ├── __init__.py
│   ├── main.py          # CLI 진입점
│   ├── agent.py         # LangGraph 에이전트
│   ├── config.py        # 설정 관리
│   ├── models/          # LLM 모델 관리
│   │   ├── factory.py
│   │   └── ensemble.py  # (향후 앙상블 지원)
│   └── tools/           # 커스텀 도구
│       ├── recipe.py
│       ├── nutrition.py
│       ├── meal_plan.py
│       └── cooking_guide.py
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```

## 질문 예시

```
👤 "김치찌개 레시피 알려줘"
👤 "냉장고에 두부랑 김치 있는데 뭐 만들 수 있어?"
👤 "비빔밥 칼로리가 얼마야?"
👤 "일주일 다이어트 식단 짜줘"
👤 "돼지고기 대신 쓸 수 있는 재료 있어?"
👤 "불고기 만들 때 팁 좀 알려줘"
```

## 라이선스

MIT License
