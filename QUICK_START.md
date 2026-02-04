# Korean Food Agent - 빠른 시작 가이드 ⚡

다른 서버에서 5분 안에 실행하기

## 📋 준비물

1. **API 키들** (미리 발급 받으세요)
   - [Google AI (Gemini)](https://aistudio.google.com/app/apikey)
   - [Serper.dev](https://serper.dev/)
   - [카카오 Developers](https://developers.kakao.com/)
   - [Supabase](https://supabase.com/)

2. **시스템 요구사항**
   - Python 3.9+
   - Node.js 18+
   - Git

## 🚀 설치 (3분)

```bash
# 1. 클론
git clone <repository-url>
cd food_agent

# 2. 자동 설치
chmod +x setup.sh
./setup.sh

# 가상환경 생성 물어보면: y 입력
# 이후 자동 설치됨
```

## ⚙️ 설정 (1분)

```bash
# .env 파일 열기
nano .env

# 아래 5개만 입력 (나머지는 기본값)
GOOGLE_API_KEY=실제-키-입력
SERPER_API_KEY=실제-키-입력
KAKAO_API_KEY=실제-키-입력
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=실제-키-입력

# 저장: Ctrl+O, Enter, Ctrl+X
```

## 🗄️ Supabase 설정 (1분)

1. Supabase Dashboard 접속
2. SQL Editor 클릭
3. `docs/supabase_schema.sql` 내용 복사
4. 붙여넣기 후 실행 (Run)

## ▶️ 실행

```bash
# 서버 시작
./run_all.sh

# 브라우저에서
http://localhost:3000
```

끝! 🎉

---

## 🔧 문제 해결

### 에러: "playwright 브라우저 없음"
```bash
playwright install chromium
playwright install-deps  # Linux만
```

### 에러: "환경변수 없음"
```bash
# .env 파일이 있는지 확인
ls -la .env

# 없으면
cp .env.example .env
nano .env
```

### 에러: "Supabase 연결 실패"
- Supabase에서 `docs/supabase_schema.sql` 실행했는지 확인
- URL과 Anon Key가 정확한지 확인

---

**더 자세한 내용**: [README.md](README.md) | [배포 가이드](docs/deployment.md)
