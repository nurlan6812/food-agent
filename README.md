# K-Foodie AI

> LangGraph + Gemini 기반 한국 음식 전문 AI 에이전트 (PWA)

음식 이미지 분석, 맛집 검색, 레시피/영양정보 제공, 식당 후기 요약, 식재료 쇼핑까지 지원하는 멀티모달 AI 챗봇입니다.

**Live Demo**: [food.jaekwang.store](https://food.jaekwang.store)

---

## 주요 기능

| 기능 | 설명 | 도구 |
|------|------|------|
| **음식 이미지 인식** | 사진을 올리면 음식명/식당을 파악 | `search_food_by_image` |
| **맛집 검색** | 지역+조건 기반 식당 추천 + 카카오맵 연동 | `search_restaurant_info` |
| **식당 후기 요약** | 카카오맵 방문자 후기 크롤링 및 AI 요약 | `get_restaurant_reviews` |
| **레시피 검색** | 만개의레시피 등에서 레시피 크롤링 | `search_recipe_online` |
| **영양정보** | 칼로리, 단백질 등 영양성분 검색 | `get_nutrition_info` |
| **식재료 쇼핑** | 네이버 쇼핑에서 재료 구매 링크 제공 | `search_naver_products`, `search_recipe_ingredients` |
| **범용 웹검색** | 다른 도구로 답할 수 없는 음식 관련 질문 처리 | `web_search` |

---

## 아키텍처

### 전체 시스템 흐름

```
사용자 (PWA)
    │  텍스트/이미지 입력
    ▼
Next.js 프론트엔드 (port 3000)
    │  SSE 스트리밍
    ▼
FastAPI 백엔드 (port 8000)
    │  LangGraph ReAct Agent
    ▼
Gemini Flash (LLM)
    │  도구 호출 결정
    ▼
┌──────────────────────────────────────┐
│           도구 (Tools)                │
├──────────────────────────────────────┤
│ search_food_by_image  → Serper.dev   │
│ search_restaurant_info → Kakao API   │
│ get_restaurant_reviews → Playwright  │
│ search_recipe_online   → 웹 크롤링   │
│ get_nutrition_info     → 웹 검색     │
│ search_naver_products  → 네이버 API  │
│ web_search             → Serper.dev  │
└──────────────────────────────────────┘
    │
    ▼
백엔드 후처리
  - 식당 카드: AI 응답에서 RESTAURANTS_JSON 추출 → 카카오 재검색(병렬)으로 검증
  - 상품 카드: AI가 관련 상품만 큐레이션
  - 지도: 검증된 좌표로 카카오맵 렌더링
  - 제안 칩: SUGGEST 태그 추출
    │
    ▼
SSE 이벤트 스트림
  → tool (도구 진행 상황)
  → text (AI 응답 텍스트)
  → restaurants (식당 카드 데이터)
  → products (상품 카드 데이터)
  → done (지도 좌표 + 제안 칩)
```

### 식당 검색 파이프라인

```
1. 카카오 로컬 API (FD6 카테고리)
   → 식당 5개 + 주소/전화/좌표/kakaoUrl
   │
2. 메뉴 정보 수집
   ├─ Playwright: 카카오맵 메뉴탭 크롤링 (우선)
   └─ Serper: 구글 검색 폴백 (날짜 포함)
   │
3. AI가 추천 텍스트 + RESTAURANTS_JSON 작성
   │
4. 백엔드 검증 (병렬 처리)
   ├─ 각 식당명으로 카카오 재검색
   ├─ _name_matches()로 이름 매칭 검증
   ├─ 매칭 성공 → 진짜 kakaoUrl/주소/좌표로 덮어씀
   └─ 매칭 실패 → 가짜 URL 제거
```

---

## 기술 스택

### Backend

| 레이어 | 기술 | 설명 |
|--------|------|------|
| LLM | Gemini Flash | 멀티모달 (텍스트+이미지), 스트리밍 |
| LLM (대체) | GPT-4o / Qwen3 (vLLM) | OpenAI 또는 로컬 추론 |
| 에이전트 | LangGraph | ReAct 패턴, 도구 호출 |
| API 서버 | FastAPI | SSE 스트리밍, 세션 관리 |
| 크롤링 | Playwright | 메뉴/후기 동적 크롤링 |
| 검색 | Serper.dev | Google Lens + 웹 검색 |

### Frontend

| 레이어 | 기술 | 설명 |
|--------|------|------|
| 프레임워크 | Next.js 16 (React 19) | App Router, SSR |
| 스타일링 | Tailwind CSS 3.4 | 반응형, 다크모드 |
| UI 컴포넌트 | shadcn/ui + Radix UI | 접근성 지원 |
| 지도 | 카카오맵 JS SDK | 식당 위치 마커 |
| 마크다운 | React-Markdown + GFM | 채팅 메시지 렌더링 |
| PWA | next-pwa | 모바일 앱 설치 가능 |

### 외부 API

| 서비스 | 용도 | 비용 |
|--------|------|------|
| Google AI (Gemini) | 멀티모달 LLM | 무료 티어 제공 |
| Serper.dev | 이미지/웹 검색 | 무료 2,500회/월 |
| Kakao Developers | 식당 검색 + 지도 | 무료 |
| Naver Developers | 쇼핑 상품 검색 | 무료 25,000회/일 |
| Coupang Partners | 제휴 상품 링크 (선택) | 무료 (커미션 기반) |

---

## 프로젝트 구조

```
food-agent/
├── api/
│   └── main.py                    # FastAPI 백엔드 (SSE 스트리밍, 세션 관리, 후처리)
│
├── src/
│   ├── agent.py                   # LangGraph ReAct 에이전트 + 시스템 프롬프트
│   ├── config.py                  # 설정 관리 (ModelProvider, API 키)
│   ├── local_llm.py               # 로컬 LLM 지원 (GLM-4V)
│   │
│   ├── services/                  # 외부 API 클라이언트
│   │   ├── kakao.py               # 카카오 로컬 API + Playwright 메뉴/후기 크롤링
│   │   ├── serper.py              # Google Lens + 웹 검색 (Serper.dev)
│   │   ├── naver_shopping.py      # 네이버 쇼핑 API
│   │   ├── coupang.py             # 쿠팡 파트너스 API (HMAC-SHA256)
│   │   └── summarizer.py          # 후기 요약 (LLM 기반)
│   │
│   └── tools/                     # LangChain 도구
│       ├── image.py               # search_food_by_image (멀티모달)
│       ├── restaurant.py          # search_restaurant_info, get_restaurant_reviews
│       ├── recipe.py              # search_recipe_online
│       ├── nutrition.py           # get_nutrition_info
│       ├── naver_shopping.py      # search_naver_products, search_recipe_ingredients
│       ├── coupang.py             # search_coupang_products
│       └── web_search.py          # web_search (범용 웹검색 폴백)
│
├── frontend/app/
│   ├── app/
│   │   ├── page.tsx               # 메인 채팅 페이지 (SSE 스트리밍 클라이언트)
│   │   ├── layout.tsx             # 루트 레이아웃 (폰트, 카카오맵 SDK)
│   │   └── globals.css            # 글로벌 스타일
│   │
│   ├── components/
│   │   ├── chat-input.tsx         # 텍스트/이미지 입력 (다중 이미지, 압축)
│   │   ├── chat-message.tsx       # AI 메시지 렌더링 (마크다운 + 구조화 데이터)
│   │   ├── welcome-landing.tsx    # 웰컴 화면 (기능 카드 + 예시 프롬프트)
│   │   ├── restaurant-carousel.tsx # 식당 카드 캐러셀 (이미지, 카카오맵 링크)
│   │   ├── restaurant-card.tsx    # 개별 식당 카드
│   │   ├── product-carousel.tsx   # 상품 카드 캐러셀
│   │   ├── map-embed.tsx          # 카카오맵 (다중 마커, 클릭 인터랙션)
│   │   ├── suggestion-chips.tsx   # 후속 질문 제안 칩
│   │   ├── feature-card.tsx       # 기능 소개 카드
│   │   ├── image-gallery.tsx      # 이미지 갤러리 (라이트박스)
│   │   ├── theme-toggle.tsx       # 다크모드 토글
│   │   └── icons/                 # SVG 아이콘 (로고, AI 아바타)
│   │
│   ├── lib/
│   │   ├── api.ts                 # SSE 스트리밍 API 클라이언트
│   │   ├── types.ts               # TypeScript 타입 정의
│   │   ├── parse-response.ts      # 응답 파싱 유틸리티
│   │   └── utils.ts               # 유틸 함수
│   │
│   └── public/
│       ├── manifest.json          # PWA 매니페스트
│       ├── logo-icon.svg          # 앱 로고
│       └── icons/                 # 앱 아이콘 (192x192, 512x512)
│
├── requirements.txt               # Python 의존성
├── .env.example                   # 환경 변수 템플릿
├── setup.sh                       # 자동 설치 스크립트
└── run_all.sh                     # 서버 실행 스크립트
```

---

## SSE 스트리밍 프로토콜

프론트엔드와 백엔드는 Server-Sent Events로 통신합니다.

| 이벤트 타입 | 시점 | 데이터 |
|------------|------|--------|
| `session` | 연결 시 | `{ session_id }` |
| `tool` | 도구 시작/완료 | `{ tool, status: "start"/"done" }` |
| `tool_progress` | 도구 진행 중 | `{ tool, status: "메뉴 검색 중..." }` |
| `text` | AI 응답 스트리밍 | `{ content: "텍스트 조각" }` |
| `restaurants` | 도구 완료 후 | `{ restaurants: [{name, address, phone, category, kakaoUrl, imageUrl}] }` |
| `products` | 도구 완료 후 | `{ products: [{name, price, imageUrl, productUrl, mall}] }` |
| `done` | 최종 | `{ map_url, images, suggestions }` |
| `error` | 오류 시 | `{ message }` |

**스트리밍 UX 순서:**
1. "식당 정보 검색 사용중" 로딩 표시
2. AI 텍스트 점진적 표시
3. 텍스트 완료 → 식당/상품 카드 표시
4. 지도 렌더링 + 제안 칩 표시

---

## 빠른 시작

### 사전 준비

**필수 API 키:**
- [Google AI (Gemini)](https://aistudio.google.com/app/apikey) - 무료
- [Serper.dev](https://serper.dev/) - 무료 2,500회/월
- [카카오 Developers](https://developers.kakao.com/) - REST API 키 + JavaScript 키

**선택 API 키:**
- [네이버 Developers](https://developers.naver.com/) - 쇼핑 검색
- [쿠팡 파트너스](https://partners.coupang.com/) - 제휴 상품

### 1. 설치

```bash
git clone https://github.com/nurlan6812/food-agent.git
cd food-agent
./setup.sh
```

### 2. 환경 변수 설정

```bash
cp .env.example .env
nano .env
```

**필수 항목:**
```env
GOOGLE_API_KEY=your-google-api-key
SERPER_API_KEY=your-serper-api-key
KAKAO_API_KEY=your-kakao-rest-api-key
```

**프론트엔드 카카오맵:**
```env
NEXT_PUBLIC_KAKAO_JS_KEY=your-kakao-js-key
```

**모델 설정 (기본값: Gemini):**
```env
MODEL_PROVIDER=gemini
GEMINI_MODEL=gemini-2.0-flash
```

### 3. 실행

```bash
./run_all.sh
```

- 프론트엔드: http://localhost:3000
- 백엔드 API: http://localhost:8000

---

## 사용 예시

### 웹 인터페이스

1. http://localhost:3000 접속 (또는 모바일에서 PWA 설치)
2. 웰컴 화면에서 기능 선택 또는 직접 입력
3. 실시간 스트리밍 응답 + 식당 카드/지도/제안 칩 확인

### Python API

```python
from src.agent import KoreanFoodAgent

agent = KoreanFoodAgent(provider="gemini")

# 텍스트 질문
response = agent.chat("강남역 혼밥 맛집 추천해줘")

# 이미지 질문
response = agent.chat("/path/to/food.jpg 이 음식 뭐야?")

# 스트리밍
for chunk in agent.stream("김치찌개 레시피 알려줘"):
    print(chunk)
```

### REST API

```bash
# 동기 채팅
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "성수동 브런치 카페 추천"}'

# 스트리밍 채팅 (SSE)
curl -N -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "김치찌개 레시피 알려줘"}'

# 세션 초기화
curl -X POST http://localhost:8000/session/clear?session_id=your-session-id
```

---

## 개발

### 수동 설치

```bash
# Python
pip install -r requirements.txt
playwright install chromium

# 프론트엔드
cd frontend/app
npm install
```

### 개별 실행

```bash
# 백엔드 (핫 리로드)
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# 프론트엔드 (개발 모드)
cd frontend/app && npm run dev
```

### LLM 모델 변경

`.env`에서 `MODEL_PROVIDER`를 변경:

| Provider | 설정 | 용도 |
|----------|------|------|
| `gemini` | `GEMINI_MODEL=gemini-2.0-flash` | 기본 (추천) |
| `openai` | `OPENAI_MODEL=gpt-4o` | OpenAI 사용 시 |
| `vllm` | `VLLM_BASE_URL=http://localhost:8001/v1` | 로컬 GPU 추론 |
| `local` | `LOCAL_MODEL_PATH=/path/to/model` | GLM-4V 로컬 |

---

## 새 서버에서 처음부터 설정

### 1. 시스템 요구사항

- Python 3.10+
- Node.js 18+
- Git

```bash
# Ubuntu/Debian 기준
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nodejs npm git
```

### 2. 프로젝트 클론 및 설치

```bash
git clone https://github.com/nurlan6812/food-agent.git
cd food-agent
chmod +x setup.sh run_all.sh
./setup.sh
```

### 3. API 키 입력

```bash
nano .env
```

최소 필수 3개만 입력하면 동작합니다:
```env
GOOGLE_API_KEY=...       # https://aistudio.google.com/app/apikey
SERPER_API_KEY=...       # https://serper.dev/
KAKAO_API_KEY=...        # https://developers.kakao.com/
NEXT_PUBLIC_KAKAO_JS_KEY=...  # 카카오 JavaScript 키 (지도용)
```

### 4. 실행

```bash
# 개발 모드 (핫 리로드)
./run_all.sh

# 또는 개별 실행
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000  # 백엔드
cd frontend/app && npm run dev  # 프론트엔드
```

- 프론트엔드: http://localhost:3000
- 백엔드 API: http://localhost:8000

### 5. 프로덕션 실행

```bash
# 백엔드
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4

# 프론트엔드 빌드 후 실행
cd frontend/app
npm run build
npx next start -p 3000 --hostname 0.0.0.0
```

### 6. 문제 해결

```bash
# Playwright 브라우저 설치 실패 시
playwright install-deps    # Linux 시스템 의존성
playwright install chromium

# 환경변수 로드 확인
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('GOOGLE_API_KEY'))"

# API 상태 확인
curl http://localhost:8000/
```

---

## Cloudflare Tunnel로 HTTPS 배포

외부에서 접속할 수 있도록 Cloudflare Tunnel을 설정하는 방법입니다. 공유기 포트포워딩 없이 HTTPS를 제공합니다.

### 1. Cloudflare 사전 준비

- [Cloudflare](https://dash.cloudflare.com/) 계정 생성
- 도메인을 Cloudflare DNS에 등록 (네임서버 변경 필요)

### 2. cloudflared 설치

```bash
# Debian/Ubuntu
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb

# 또는 ARM64 (라즈베리파이 등)
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb
sudo dpkg -i cloudflared.deb
```

### 3. Cloudflare 로그인 및 터널 생성

```bash
# 브라우저에서 Cloudflare 로그인 (인증 URL이 출력됨)
cloudflared tunnel login

# 터널 생성
cloudflared tunnel create food-agent

# 터널 ID 확인 (출력된 UUID를 메모)
cloudflared tunnel list
```

### 4. 설정 파일 작성

```bash
mkdir -p ~/.cloudflared
nano ~/.cloudflared/config.yml
```

```yaml
tunnel: your-tunnel-id   # 위에서 메모한 UUID
credentials-file: /home/your-user/.cloudflared/your-tunnel-id.json

ingress:
  # 프론트엔드 (메인 도메인)
  - hostname: food.yourdomain.com
    service: http://localhost:3000

  # 백엔드 API (서브도메인)
  - hostname: api-food.yourdomain.com
    service: http://localhost:8000

  # 나머지 요청은 404
  - service: http_status:404
```

### 5. Cloudflare DNS에 CNAME 등록

```bash
cloudflared tunnel route dns food-agent food.yourdomain.com
cloudflared tunnel route dns food-agent api-food.yourdomain.com
```

### 6. 터널 실행

```bash
# 포그라운드 실행 (테스트용)
cloudflared tunnel --config ~/.cloudflared/config.yml run

# 시스템 서비스로 등록 (서버 재시작 시 자동 실행)
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

### 7. 프론트엔드 API URL 변경

`.env`에서 백엔드 URL을 터널 도메인으로 변경:
```env
NEXT_PUBLIC_API_URL=https://api-food.yourdomain.com
```

프론트엔드 재빌드 후 확인:
```bash
cd frontend/app && npm run build && npx next start -p 3000 --hostname 0.0.0.0
```

### 8. CORS 설정 업데이트

`api/main.py`의 `allow_origins`에 프론트엔드 도메인 추가:
```python
allow_origins=[
    "https://food.yourdomain.com",
    "http://localhost:3000",
]
```

이제 `https://food.yourdomain.com`으로 접속할 수 있습니다.

---

### PWA 모바일 설치

1. 모바일 브라우저에서 사이트 접속
2. "홈 화면에 추가" 선택
3. 앱처럼 사용 가능

---

## 보안

- API 키는 `.env`에서 관리 (Git 제외)
- CORS: 프로덕션 도메인만 허용
- AI kakaoUrl 날조 방지: 카카오 재검색으로 항상 검증
- Serper 검색 결과 날짜 표시: 오래된 가격 정보 안내

---

## Supabase (미연동)

`src/db/`, `src/tools/save_image.py`, `src/tools/update_image.py`, `docs/supabase_schema.sql`에 Supabase 연동 코드가 준비되어 있으나 현재는 사용하지 않습니다. 향후 이미지 저장, 사용자 데이터 등에 활용할 예정입니다.

연동 시 필요한 환경 변수:
```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
```

---

## 외부 참고

- [LangGraph](https://langchain-ai.github.io/langgraph/)
- [Gemini API](https://ai.google.dev/)
- [Serper.dev](https://serper.dev/)
- [카카오 Developers](https://developers.kakao.com/)

## 라이선스

MIT License
