# Supabase 음식 이미지 데이터 수집 시스템 구현 계획

> **작성일**: 2025-01-30
> **수정일**: 2025-01-30 (v2 - 에이전트 도구 방식으로 변경)
> **목적**: 사용자 대화 기반 음식 이미지 데이터셋 구축

---

## 핵심 변경사항 (v2)

**새로운 방식 - 에이전트가 이미지 비교 후 저장**:

```
이미지 업로드 + "이거 뭐야?"
   ↓
search_food_by_image 호출
   ├── Google Lens 검색
   └── 반환: 검색 결과 + 썸네일 URL 3개
   ↓
에이전트 (원본 + 썸네일 비교):
   ├── "검색 결과에 똑같은 이미지 있네" → 저장 안함
   └── "검색 결과에 같은 이미지 없음" → save_food_image 호출 (verified: false)
   ↓
에이전트: "비빔밥으로 보여요. 어디서 드셨어요?"
   ↓
사용자: "응 명동 본가에서"
   ↓
에이전트:
   ├── update_food_image 호출 (verified: true + 정보 업데이트)
   └── "아 본가 불고기 맛있죠!" 응답
```

**핵심:**
- 에이전트가 원본 vs 썸네일 시각 비교로 새 이미지 판단
- 새 이미지 → save_food_image (verified: false)
- 사용자 확인 → update_food_image (verified: true)
- 확인 안해도 → verified: false로 남아있음 (검증 필요 표시)

---

## 1. 요구사항 분석

### 1.1 핵심 목표
- 인터넷에 없는 새로운 음식 이미지 수집
- AI 대화를 통한 자연스러운 라벨링 (음식명, 식당명)
- **에이전트가 대화 중 판단하여 저장** (별도 검증 호출 없음)

### 1.2 이미지 유형 분류

| 유형 | 설명 | 식당 정보 | 예시 |
|------|------|----------|------|
| `restaurant` | 식당에서 촬영 | 있음 | "강남 OO식당에서 먹은 비빔밥" |
| `home_cooked` | 집에서 직접 조리 | 없음 | "집에서 만든 제육볶음" |
| `delivery` | 배달 음식 | 있을 수 있음 | "배민으로 시킨 치킨" |
| `unknown` | 미확인 | 미확인 | 출처 불명 |

---

## 2. 데이터베이스 스키마

### 2.1 ERD (간소화)
```
┌─────────────────────┐
│    food_images      │
├─────────────────────┤
│ id (PK)             │
│ image_url           │
│ food_name           │
│ food_category       │
│ food_source_type    │
│ restaurant_name     │
│ location            │
│ verified            │
│ created_at          │
└─────────────────────┘
```

**테이블 1개로 충분** - sessions, conversations 불필요

### 2.2 테이블 정의 (간소화)

```sql
-- =====================================================
-- 음식 이미지 테이블 (핵심, 이것만 있으면 됨)
-- =====================================================
CREATE TABLE food_images (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- 이미지 정보
  image_url TEXT NOT NULL,               -- 원본 이미지 URL 또는 Storage URL

  -- 음식 정보
  food_name TEXT NOT NULL,               -- 음식명 (비빔밥, 김치찌개 등)
  food_category TEXT,                    -- 카테고리 (한식, 중식, 일식 등)

  -- 음식 출처 유형
  food_source_type TEXT DEFAULT 'unknown'
    CHECK (food_source_type IN ('restaurant', 'home_cooked', 'delivery', 'unknown')),

  -- 식당 정보 (food_source_type = 'restaurant' or 'delivery')
  restaurant_name TEXT,                  -- 식당명
  location TEXT,                         -- 위치/지역 (강남, 명동 등)

  -- 검증 상태 (에이전트가 호출 = 검증됨)
  verified BOOLEAN DEFAULT TRUE,

  -- 메타데이터
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- 인덱스 생성
-- =====================================================
CREATE INDEX idx_food_images_food_name ON food_images(food_name);
CREATE INDEX idx_food_images_source_type ON food_images(food_source_type);
CREATE INDEX idx_food_images_created ON food_images(created_at DESC);
```

**간소화 이유:**
- `sessions`, `conversations`, `verification_history` 테이블 제거
- 에이전트가 호출 = 검증됨 → 복잡한 verification 필드 불필요
- v2에서 필요하면 추가 (YAGNI 원칙)

### 2.3 Supabase Storage 버킷

```
food-images/
├── {session_id}/
│   ├── {image_id}_original.jpg    # 원본 이미지
│   ├── {image_id}_thumb.jpg       # 썸네일 (200x200)
│   └── {image_id}_medium.jpg      # 중간 크기 (800x800)
```

---

## 3. 구현 순서

### Phase 1: 기본 인프라 (0.5일)
- [ ] Supabase 프로젝트 설정
- [ ] 테이블 생성 (마이그레이션) - 스키마 간소화
- [ ] Storage 버킷 생성
- [ ] RLS (Row Level Security) 정책 설정

### Phase 2: 도구 구현 (1일) ⭐ 핵심
- [ ] `src/tools/image_search.py` 수정
  - [ ] 썸네일 URL을 명확히 반환 (에이전트가 비교용)
  - [ ] 반환 형식: 검색 결과 + `[THUMBNAILS: url1, url2, url3]`
- [ ] `src/tools/save_food_image.py` - 새 도구 생성
  - [ ] 새 이미지 저장 (verified: false)
  - [ ] image_id 반환
- [ ] `src/tools/update_food_image.py` - 새 도구 생성
  - [ ] image_id로 정보 업데이트
  - [ ] verified: true 설정
- [ ] `src/tools/__init__.py` - ALL_TOOLS에 추가
- [ ] 시스템 프롬프트 수정

### Phase 3: 백엔드 모듈 (0.5일)
- [ ] `src/db/` 모듈 생성
  - [ ] `client.py` - Supabase 클라이언트
  - [ ] `models.py` - Pydantic 모델

### Phase 4: 테스트 + API (1일)
- [ ] 도구 호출 테스트
- [ ] 데이터 조회 API (선택)
- [ ] 통계 API (선택)

---

## 4. 상세 구현 설계

### 4.1 디렉토리 구조 (간소화)
```
src/
├── agent.py                     # 시스템 프롬프트 수정
├── config.py
├── tools/
│   ├── __init__.py              # ALL_TOOLS에 도구 추가
│   ├── image_search.py          # 수정: 썸네일 URL 반환
│   ├── save_food_image.py       # NEW: 새 이미지 저장
│   └── update_food_image.py     # NEW: 검증 정보 업데이트
└── db/                          # NEW
    ├── __init__.py
    ├── client.py                # Supabase 클라이언트
    └── models.py                # Pydantic 모델 (간소화)
```

### 4.2 Pydantic 모델 (간소화)

```python
# src/db/models.py
from pydantic import BaseModel
from typing import Optional
from enum import Enum

class FoodSourceType(str, Enum):
    RESTAURANT = "restaurant"
    HOME_COOKED = "home_cooked"
    DELIVERY = "delivery"
    UNKNOWN = "unknown"

class FoodImage(BaseModel):
    id: Optional[str] = None
    image_url: str
    food_name: str
    food_category: Optional[str] = None
    food_source_type: FoodSourceType = FoodSourceType.UNKNOWN
    restaurant_name: Optional[str] = None
    location: Optional[str] = None
    verified: bool = True  # 에이전트가 호출 = 검증됨
```

**간소화:** ConversationMessage, VerificationType 등 제거

### 4.3 image_search.py 수정 (썸네일 명확히 반환)

```python
# src/tools/image_search.py 수정

# 기존 코드에서 썸네일 반환 부분 강화
@tool
def search_food_by_image(image_source: str) -> str:
    # ... 기존 로직 ...

    # 썸네일 수집 (상위 5개)
    thumbnails = []
    for v in visual[:5]:
        thumbnail = v.get("thumbnail", "")
        if thumbnail:
            thumbnails.append(thumbnail)

    # 결과에 썸네일 URL 명시적 추가 (에이전트가 비교용)
    if thumbnails:
        output.append("\n[비교용 썸네일 이미지]")
        output.append(f"[THUMBNAILS:{','.join(thumbnails)}]")
        output.append("위 썸네일들과 원본 이미지를 비교해서 똑같은 이미지가 있는지 확인하세요.")

    return "\n".join(output)
```

**핵심:** 썸네일 URL을 `[THUMBNAILS:...]` 태그로 반환 → 에이전트가 원본과 비교

### 4.4 save_food_image 도구 구현 ⭐ 새로 추가

```python
# src/tools/save_food_image.py

import asyncio
from langchain_core.tools import tool
from typing import Optional
from ..db.client import get_supabase_client

async def _save_to_supabase(
    image_url: str,
    food_name: str,
    source_type: Optional[str],
    restaurant_name: Optional[str],
    location: Optional[str]
) -> str:
    """DB 저장 (백그라운드) - image_id 반환"""
    try:
        supabase = get_supabase_client()
        result = await supabase.table("food_images").insert({
            "image_url": image_url,
            "food_name": food_name,
            "food_source_type": source_type or "unknown",
            "restaurant_name": restaurant_name,
            "location": location,
            "verified": False,  # 아직 검증 안됨
        }).execute()
        return result.data[0]["id"]
    except Exception as e:
        print(f"DB 저장 실패: {e}")
        return None


@tool
def save_food_image(
    image_url: str,
    food_name: str,
    source_type: Optional[str] = None,
    restaurant_name: Optional[str] = None,
    location: Optional[str] = None
) -> str:
    """
    웹에 없는 새 이미지를 데이터베이스에 저장합니다.

    search_food_by_image 결과의 썸네일과 원본 이미지를 비교해서,
    똑같은 이미지가 없으면 (= 새 이미지) 이 도구를 호출하세요.

    Args:
        image_url: 업로드된 이미지 URL
        food_name: 음식 이름 (AI 추론값도 OK)
        source_type: "restaurant", "home_cooked", "delivery" (모르면 생략)
        restaurant_name: 식당 이름 (알면)
        location: 위치/지역 (알면)

    Returns:
        저장된 image_id (update_food_image에서 사용)
    """
    # 동기 실행 (asyncio.run 사용)
    try:
        image_id = asyncio.run(_save_to_supabase(
            image_url=image_url,
            food_name=food_name,
            source_type=source_type,
            restaurant_name=restaurant_name,
            location=location
        ))
        return f"저장 완료. image_id: {image_id}"
    except:
        # 이미 이벤트 루프가 있는 경우
        import nest_asyncio
        nest_asyncio.apply()
        loop = asyncio.get_event_loop()
        image_id = loop.run_until_complete(_save_to_supabase(
            image_url=image_url,
            food_name=food_name,
            source_type=source_type,
            restaurant_name=restaurant_name,
            location=location
        ))
        return f"저장 완료. image_id: {image_id}"
```

### 4.5 update_food_image 도구 구현

```python
# src/tools/update_food_image.py

import asyncio
from langchain_core.tools import tool
from typing import Optional
from ..db.client import get_supabase_client

async def _update_in_supabase(
    image_id: str,
    food_name: str,
    source_type: str,
    restaurant_name: Optional[str],
    location: Optional[str]
):
    """DB 업데이트 (백그라운드)"""
    try:
        supabase = get_supabase_client()
        await supabase.table("food_images").update({
            "food_name": food_name,
            "food_source_type": source_type,
            "restaurant_name": restaurant_name,
            "location": location,
            "verified": True,  # 사용자 확인됨!
        }).eq("id", image_id).execute()
    except Exception as e:
        print(f"DB 업데이트 실패: {e}")


@tool
def update_food_image(
    image_id: str,
    food_name: str,
    source_type: str,
    restaurant_name: Optional[str] = None,
    location: Optional[str] = None
) -> str:
    """
    사용자가 확인해준 음식 정보로 DB를 업데이트합니다.

    사용자가 음식 이름, 식당 정보 등을 확인/수정해줬을 때 호출하세요.

    Args:
        image_id: search_food_by_image에서 반환된 이미지 ID
        food_name: 확인된 음식 이름
        source_type: "restaurant", "home_cooked", "delivery" 중 하나
        restaurant_name: 식당 이름 (식당인 경우)
        location: 위치/지역

    Returns:
        업데이트 결과 메시지
    """
    asyncio.create_task(_update_in_supabase(
        image_id=image_id,
        food_name=food_name,
        source_type=source_type,
        restaurant_name=restaurant_name,
        location=location
    ))

    return "정보 업데이트 완료"
```

**핵심 포인트:**
- `search_food_by_image`: 새 이미지면 바로 저장 (verified: false)
- `update_food_image`: 사용자 확인되면 업데이트 (verified: true)
- 둘 다 fire-and-forget → 응답 지연 없음

### 4.6 시스템 프롬프트 수정

```python
# src/agent.py 에 추가

SYSTEM_PROMPT = """당신은 한국 음식 전문가 AI 어시스턴트입니다.

## 기존 내용 유지...

## 새 이미지 저장 (중요!)
1. search_food_by_image 호출 후, [THUMBNAILS:...] 의 이미지들과 원본 이미지를 비교
2. 비교 기준:
   - "아예 똑같은 이미지" 또는 "원본을 자른/크롭한 이미지" → 웹에 있는 이미지
   - "비슷해 보이는 다른 음식 사진" → 새 이미지 (다른 사람이 찍은 비슷한 음식)
3. 웹에 없는 새 이미지면:
   - save_food_image 호출 (food_name은 AI 추론값으로)
   - 반환된 image_id 기억
4. 똑같거나 자른 이미지가 있으면 → 저장 안함

## 검증 정보 업데이트
- 사용자가 음식/식당 정보를 확인해주면 update_food_image 호출
- 예: "맞아 명동 본가에서 먹었어" → update_food_image(verified: true)
- 예: "응 집에서 만든 비빔밥이야" → update_food_image(source_type: home_cooked)
- image_id는 save_food_image에서 받은 값 사용
- 사용자가 확인 안해도 괜찮음 (이미 저장됨, 나중에 검증)
"""
```

### 4.7 tools/__init__.py 수정

```python
# src/tools/__init__.py

from .image_search import search_food_by_image
from .restaurant import search_restaurant_info, get_restaurant_reviews
from .recipe_search import search_recipe_online
from .nutrition import get_nutrition_info
from .save_food_image import save_food_image  # NEW
from .update_food_image import update_food_image  # NEW

ALL_TOOLS = [
    search_food_by_image,  # 수정됨: 썸네일 URL 반환
    search_restaurant_info,
    get_restaurant_reviews,
    search_recipe_online,
    get_nutrition_info,
    save_food_image,  # NEW: 새 이미지 저장
    update_food_image,  # NEW: 검증 정보 업데이트
]
```

### 4.8 데이터 흐름

```
사용자: "이 음식 뭐야?" + 이미지
   ↓
에이전트: search_food_by_image 호출
   └── 반환: 검색 결과 + [THUMBNAILS: url1, url2, url3]
   ↓
에이전트: 원본 이미지 vs 썸네일 비교
   ├── 똑같은 이미지 있음 → 저장 안함
   └── 똑같은 이미지 없음 → save_food_image 호출
       └── 반환: image_id: "xxx"
   ↓
에이전트: "불고기로 보여요. 어디서 드셨어요?"
   ↓
사용자: "응 명동 본가에서"
   ↓
에이전트:
   ├── update_food_image 호출 (image_id: "xxx", verified: true, 식당 정보)
   └── "아 본가 불고기 맛있죠!" 응답
   ↓
(DB: verified: true, restaurant_name: "본가", location: "명동")
```

**사용자가 확인 안하는 경우:**
```
사용자: "이 음식 뭐야?" + 이미지
   ↓
에이전트: search_food_by_image + 비교 + save_food_image (verified: false)
   ↓
에이전트: "불고기로 보여요!"
   ↓
사용자: "고마워" (다른 대화로 넘어감)
   ↓
(DB: verified: false로 남아있음 → 나중에 수동 검증 필요)
```

**웹에 있는 이미지인 경우:**
```
사용자: "이 음식 뭐야?" + 이미지
   ↓
에이전트: search_food_by_image
   ↓
에이전트: 원본 vs 썸네일 비교 → "똑같거나 자른 이미지 있음!"
   ↓
에이전트: "불고기로 보여요!" (저장 안함)
```

**비슷한 음식 사진만 있는 경우 (새 이미지):**
```
사용자: "이 음식 뭐야?" + 이미지
   ↓
에이전트: search_food_by_image
   ↓
에이전트: 원본 vs 썸네일 비교 → "비슷한 음식 사진은 있지만 똑같은 이미지는 없음"
   ↓
에이전트: save_food_image 호출 → image_id 받음
   ↓
에이전트: "불고기로 보여요!"
```

### 4.7 API (선택, 나중에 추가)

```python
# api/main.py - 기존 /chat 엔드포인트 수정 없음!
# save_food_image 도구가 알아서 DB 저장

# 나중에 필요하면 추가:
@app.get("/data/images")
async def list_images(limit: int = 20):
    """수집된 이미지 목록 조회"""
    supabase = get_supabase_client()
    result = await supabase.table("food_images").select("*").limit(limit).execute()
    return result.data

@app.get("/data/stats")
async def get_stats():
    """수집 통계"""
    # 나중에 구현
    pass
```

**v1에서는 API 추가 안 함** - 도구만 동작하면 됨

---

## 5. 저장/업데이트 기준

### 5.1 새 이미지 판단 (에이전트가 시각 비교)

| 상황 | save_food_image 호출 |
|------|---------------------|
| 썸네일에 아예 똑같은 이미지 있음 | X (웹에 있음) |
| 썸네일에 원본을 자른/크롭한 이미지 있음 | X (웹에 있음) |
| 썸네일에 비슷한 음식 사진만 있음 (다른 사진) | O (새 이미지) |
| 썸네일이 비어있음 (검색 결과 없음) | O (새 이미지) |

**핵심:** "똑같거나 자른 이미지"만 웹에 있는 것. 비슷하게 생긴 다른 음식 사진은 새 이미지!

### 5.2 검증 업데이트 (update_food_image)

| 상황 | update_food_image 호출 |
|------|------------------------|
| 사용자가 "맞아", "응" 등으로 확인 | O |
| 사용자가 직접 정보 제공 ("명동 본가에서") | O |
| 사용자가 수정 ("아니야 김치찌개야") | O |
| 사용자가 확인 안하고 대화 끝남 | X (verified: false 유지) |

**핵심:**
- 에이전트가 원본 vs 썸네일 비교해서 새 이미지 판단
- 새 이미지 → save_food_image (verified: false)
- 사용자 확인 → update_food_image (verified: true)
- 확인 안해도 → 저장은 됨 (나중에 수동 검증)

---

## 7. 일정 (총 2~3일)

| 일차 | 작업 | 산출물 |
|------|------|--------|
| 1일차 | Supabase 설정 + save_food_image 도구 | 테이블, Storage, 도구 |
| 2일차 | 시스템 프롬프트 수정 + 테스트 | 통합 테스트 완료 |
| (3일차) | 버그 수정 + 조회 API (선택) | 완료 |

**단축 이유:**
- 별도 검증 모듈 불필요 → 에이전트가 직접 판단
- 복잡한 대화 추적 불필요 → 도구 파라미터로 전달
- repository, verifier 클래스 불필요 → 도구 하나로 끝

---

## 8. 참고: .env 추가 설정

```env
# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # 백엔드용
```
