# Korean Food Agent - 전체 폴더 구조

프로젝트의 실제 폴더 구조입니다.

## 📂 전체 구조

```
food_agent/
├── 📄 루트 파일
│   ├── README.md              # 프로젝트 메인 문서
│   ├── QUICK_START.md         # 5분 빠른 시작 가이드
│   ├── VERIFICATION.md        # 코드 검증 결과
│   ├── STRUCTURE.md           # 이 파일 (전체 구조)
│   ├── requirements.txt       # Python 의존성 (18개)
│   ├── .env.example           # 환경 변수 템플릿
│   ├── setup.sh              # 자동 설치 스크립트
│   ├── run_all.sh            # 서버 실행 스크립트
│   ├── .gitignore            # Git 제외 목록
│   └── pyproject.toml        # Python 프로젝트 설정
│
├── 🔧 api/ - FastAPI 백엔드
│   └── main.py               # FastAPI 서버 (SSE 스트리밍)
│
├── 🤖 src/ - AI 에이전트 코어
│   ├── __init__.py
│   ├── agent.py              # LangGraph ReAct 에이전트
│   ├── config.py             # 설정 관리
│   │
│   ├── db/                   # 데이터베이스
│   │   ├── __init__.py
│   │   └── client.py         # Supabase 클라이언트
│   │
│   ├── services/             # 외부 API 클라이언트
│   │   ├── __init__.py
│   │   ├── serper.py         # Google Lens + 텍스트 검색
│   │   ├── kakao.py          # 카카오맵 API + Playwright
│   │   └── summarizer.py     # (미사용) vLLM 요약기
│   │
│   └── tools/                # LangChain 도구 (7개)
│       ├── __init__.py
│       ├── image.py          # search_food_by_image
│       ├── restaurant.py     # search_restaurant_info, get_restaurant_reviews
│       ├── recipe.py         # search_recipe_online
│       ├── nutrition.py      # get_nutrition_info
│       ├── save_image.py     # save_food_image
│       └── update_image.py   # update_food_image
│
├── 🎨 frontend/app/ - Next.js 프론트엔드
│   ├── app/                  # Next.js 13+ App Router
│   │   ├── page.tsx          # 메인 채팅 페이지
│   │   ├── layout.tsx        # 루트 레이아웃
│   │   └── globals.css       # 글로벌 스타일
│   │
│   ├── components/           # React 컴포넌트
│   │   ├── chat-input.tsx    # 채팅 입력 필드
│   │   ├── chat-message.tsx  # 메시지 버블
│   │   ├── map-embed.tsx     # 카카오맵 임베드
│   │   ├── image-gallery.tsx # 이미지 갤러리
│   │   ├── restaurant-card.tsx # 식당 카드
│   │   ├── theme-toggle.tsx  # 다크모드 토글
│   │   └── ui/               # shadcn/ui 기본 컴포넌트
│   │       ├── button.tsx
│   │       ├── card.tsx
│   │       ├── dialog.tsx
│   │       ├── textarea.tsx
│   │       └── toaster.tsx
│   │
│   ├── hooks/                # React Hooks
│   │   └── use-toast.ts      # Toast 알림 훅
│   │
│   ├── lib/                  # 유틸리티 라이브러리
│   │   ├── api.ts            # 백엔드 API 클라이언트
│   │   ├── types.ts          # TypeScript 타입 정의
│   │   └── utils.ts          # 유틸리티 함수
│   │
│   ├── package.json          # Node.js 의존성
│   ├── tsconfig.json         # TypeScript 설정
│   ├── tailwind.config.ts    # Tailwind CSS 설정
│   ├── next.config.js        # Next.js 설정
│   └── postcss.config.js     # PostCSS 설정
│
├── 📚 docs/ - 문서
│   ├── deployment.md         # 배포 가이드
│   ├── research_note.md      # 상세 기술 문서
│   └── supabase_schema.sql   # DB 스키마
│
└── 🧪 scripts/ - 유틸리티 스크립트
    ├── benchmark_latency.py  # Gemini 레이턴시 측정
    ├── run_vllm.sh          # (미사용) vLLM 실행
    └── setup_vllm.sh        # (미사용) vLLM 설치
```

## 📊 통계

| 카테고리 | 개수 |
|---------|------|
| Python 파일 | 17개 |
| TypeScript/React 파일 | 24개 |
| 문서 파일 | 9개 |
| 설정 파일 | 8개 |
| 스크립트 | 3개 |

## 🎯 핵심 파일

### 백엔드
- `api/main.py` - FastAPI 서버, SSE 스트리밍
- `src/agent.py` - LangGraph 에이전트
- `src/tools/*.py` - 7개 도구

### 프론트엔드
- `frontend/app/app/page.tsx` - 메인 UI
- `frontend/app/components/*.tsx` - 6개 주요 컴포넌트
- `frontend/app/lib/api.ts` - API 클라이언트

### 설정
- `.env.example` - 환경 변수 (10개)
- `requirements.txt` - Python 패키지 (18개)
- `package.json` - Node.js 패키지

### 문서
- `README.md` - 메인 문서
- `docs/deployment.md` - 배포 가이드
- `docs/supabase_schema.sql` - DB 스키마

## ⚠️ 미사용 파일/폴더

다음 항목은 코드에 있지만 현재 API 구성에서는 사용하지 않습니다:

1. **vLLM 관련** (로컬 LLM 요약기)
   - `src/services/summarizer.py`
   - `scripts/run_vllm.sh`
   - `scripts/setup_vllm.sh`

2. **테스트 이미지** (.gitignore 대상)
   - `aa.jpeg`, `aaa.png`, `de.png`, `fd.png`, `s22.png`

이 파일들은 삭제하지 않고 유지하되, 문서에서는 현재 사용 중인 API 기반 구성만 안내합니다.

## 🚀 다음 단계

1. **설치**: `./setup.sh` 실행
2. **환경 설정**: `.env` 파일에 API 키 입력
3. **DB 설정**: `docs/supabase_schema.sql` 실행
4. **실행**: `./run_all.sh`

더 자세한 내용은 `README.md`를 참고하세요.
