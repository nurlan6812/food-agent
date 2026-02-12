# Korean Food Agent 배포 가이드

다른 서버에서 프로젝트를 실행하는 방법입니다.

## 사전 요구사항

### 시스템 요구사항
- Python 3.10 이상
- Node.js 18 이상
- npm
- Git

### API 키 준비

| API | 발급 URL | 필수 여부 | 비용 |
|-----|----------|-----------|------|
| Google AI (Gemini) | https://aistudio.google.com/app/apikey | 필수 | 무료 (일 할당량) |
| Serper.dev | https://serper.dev/ | 필수 | 무료 2,500회/월 |
| 카카오 REST API | https://developers.kakao.com/ | 필수 | 무료 |
| 네이버 Developers | https://developers.naver.com/ | 선택 | 무료 25,000회/일 |
| 쿠팡 파트너스 | https://partners.coupang.com/ | 선택 | 무료 (커미션 기반) |
| OpenAI | https://platform.openai.com/ | 선택 | 종량제 |

---

## 설치

### 방법 1: 자동 설치 (권장)

```bash
git clone https://github.com/nurlan6812/food-agent.git
cd food-agent

chmod +x setup.sh run_all.sh
./setup.sh

# .env 파일 편집 (API 키 입력)
nano .env

# 서버 시작
./run_all.sh
```

### 방법 2: 수동 설치

```bash
git clone https://github.com/nurlan6812/food-agent.git
cd food-agent

# Python 가상환경 (선택)
python3 -m venv venv
source venv/bin/activate

# Python 패키지 설치
pip install -r requirements.txt

# Playwright 브라우저 설치
playwright install chromium
playwright install-deps  # Linux 시스템 의존성

# 프론트엔드 패키지 설치
cd frontend/app
npm install
cd ../..

# 환경 변수 설정
cp .env.example .env
nano .env
```

---

## 환경 변수

`.env` 파일의 필수/선택 항목:

```env
# === 필수 ===
GOOGLE_API_KEY=your-google-api-key
SERPER_API_KEY=your-serper-api-key
KAKAO_API_KEY=your-kakao-rest-api-key
NEXT_PUBLIC_KAKAO_JS_KEY=your-kakao-js-key

# === 모델 설정 (기본값: Gemini) ===
MODEL_PROVIDER=gemini
GEMINI_MODEL=gemini-2.0-flash

# === 선택: 쇼핑 API ===
NAVER_CLIENT_ID=your-naver-client-id
NAVER_CLIENT_SECRET=your-naver-client-secret
COUPANG_ACCESS_KEY=your-coupang-access-key
COUPANG_SECRET_KEY=your-coupang-secret-key

# === 선택: 대체 LLM ===
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o
```

---

## 실행

### 개발 모드

```bash
# 백엔드 + 프론트엔드 동시 실행
./run_all.sh

# 접속
# - 프론트엔드: http://localhost:3000
# - 백엔드 API: http://localhost:8000
```

### 개별 실행

```bash
# 백엔드만 (핫 리로드)
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# 프론트엔드만
cd frontend/app && npm run dev
```

### 프로덕션 모드

```bash
# 백엔드
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4

# 프론트엔드 빌드 & 실행
cd frontend/app
npm run build
npx next start -p 3000 --hostname 0.0.0.0
```

---

## 문제 해결

### Playwright 브라우저 오류
```bash
playwright install chromium
playwright install-deps  # Linux 의존성 설치
```

### 카카오맵 크롤링 오류
- Playwright headless 모드 이슈일 수 있음
- `src/services/kakao.py`에서 `headless=False`로 변경해서 테스트

### API 키 오류
```bash
# 환경변수 로드 확인
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('GOOGLE_API_KEY'))"
```

### API 상태 확인
```bash
curl http://localhost:8000/
# 응답: {"message": "Korean Food Agent API", "version": "1.0.0"}
```

---

## 보안 설정 (프로덕션)

### 환경 변수 보호
```bash
chmod 600 .env
```

### CORS 설정
`api/main.py`의 CORS 설정 수정:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 업데이트

```bash
git pull origin main
pip install -r requirements.txt --upgrade
cd frontend/app && npm install
playwright install chromium
./run_all.sh
```
