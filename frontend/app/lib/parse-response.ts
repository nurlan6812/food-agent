/**
 * AI 응답을 파싱하여 세그먼트별로 분리하고
 * 식당 카드 데이터와 후속 질문 제안을 추출합니다.
 */

export interface RestaurantCardData {
  name: string;
  category?: string;
  rating?: string;
  address?: string;
  phone?: string;
  description?: string;
  imageUrl?: string;
  kakaoUrl?: string;
}

export interface ResponseSegment {
  type: 'text' | 'restaurants';
  content?: string;          // type === 'text'일 때 마크다운 내용
  restaurants?: RestaurantCardData[]; // type === 'restaurants'일 때 식당 목록
}

/**
 * 마크다운 텍스트에서 식당 데이터를 추출합니다.
 * 패턴: ### 1. **식당명** / 주소, 전화번호, 평점 등
 */
function extractRestaurants(text: string): RestaurantCardData[] {
  const restaurants: RestaurantCardData[] = [];

  // 패턴 1: ### N. **식당명** 또는 **N. 식당명**
  const blockPattern = /(?:#{1,3}\s*)?(?:\d+[\.\)]\s*)?(?:\*\*(.+?)\*\*)([\s\S]*?)(?=(?:#{1,3}\s*)?(?:\d+[\.\)]\s*)?(?:\*\*)|$)/g;
  let match;

  while ((match = blockPattern.exec(text)) !== null) {
    const name = match[1].trim();
    const details = match[2] || '';

    // 식당 관련 키워드가 있는지 확인
    const hasRestaurantKeywords = /(?:주소|위치|📍|전화|📞|평점|⭐|별점|카카오맵|place\.map|리뷰|메뉴|영업|종류|카테고리)/i.test(details);

    if (!hasRestaurantKeywords) continue;

    const restaurant: RestaurantCardData = { name };

    // 카테고리/종류 추출
    const categoryMatch = details.match(/(?:종류|카테고리|업종)\s*[:：]\s*(.+?)(?:\n|$)/);
    if (categoryMatch) restaurant.category = categoryMatch[1].trim();

    // 주소 추출
    const addressMatch = details.match(/(?:📍|주소|위치)\s*[:：]?\s*(.+?)(?:\n|$)/);
    if (addressMatch) restaurant.address = addressMatch[1].trim().replace(/\*\*/g, '');

    // 전화번호 추출
    const phoneMatch = details.match(/(?:📞|전화|연락처)\s*[:：]?\s*(.+?)(?:\n|$)/);
    if (phoneMatch) restaurant.phone = phoneMatch[1].trim().replace(/\*\*/g, '');

    // 평점 추출
    const ratingMatch = details.match(/(?:⭐|별점|평점|점수)\s*[:：]?\s*([0-9.]+)/);
    if (ratingMatch) restaurant.rating = ratingMatch[1];

    // 카카오맵 URL 추출
    const kakaoMatch = details.match(/https?:\/\/place\.map\.kakao\.com\/\d+/);
    if (kakaoMatch) restaurant.kakaoUrl = kakaoMatch[0];

    // 이미지 URL 추출
    const imgMatch = details.match(/https?:\/\/[^\s)]+\.(?:jpg|jpeg|png|webp|gif)/i);
    if (imgMatch) restaurant.imageUrl = imgMatch[0];

    // 설명 추출 (첫 줄 또는 요약)
    const descLines = details.split('\n').filter(l => l.trim() && !l.match(/(?:📍|📞|⭐|주소|전화|평점|카카오맵|---)/));
    if (descLines.length > 0) {
      restaurant.description = descLines[0].trim().replace(/^[-*]\s*/, '').replace(/\*\*/g, '').substring(0, 100);
    }

    restaurants.push(restaurant);
  }

  return restaurants;
}

/**
 * 마크다운 텍스트에서 후속 질문 제안을 추출합니다.
 * 패턴: 문장 끝이 ~까요?, ~을까요?, ~드릴까요? 등으로 끝나는 질문
 */
export function extractSuggestions(text: string): string[] {
  const suggestions: string[] = [];
  const lines = text.split('\n');

  for (const line of lines) {
    const trimmed = line.trim().replace(/^[-*>\s]+/, '').replace(/\*\*/g, '');
    // 한국어 질문 패턴 (제안형)
    if (trimmed.match(/(?:할까요|드릴까요|볼까요|찾아볼까요|알아볼까요|알려드릴까요|추천해드릴까요|검색해드릴까요|비교해드릴까요)\s*\??\s*$/)) {
      const clean = trimmed.replace(/^\d+[\.\)]\s*/, '').replace(/\?$/, '').trim();
      if (clean.length > 5 && clean.length < 50) {
        suggestions.push(clean);
      }
    }
  }

  return suggestions.slice(0, 3); // 최대 3개
}

/**
 * AI 응답을 세그먼트로 분리합니다.
 * 텍스트 → 식당 카드 → 텍스트 → 제안 순으로 구성
 */
export function parseResponseIntoSegments(content: string): ResponseSegment[] {
  const segments: ResponseSegment[] = [];

  // 식당 데이터 추출 시도
  const restaurants = extractRestaurants(content);

  if (restaurants.length >= 2) {
    // 식당 추천 응답: 인트로 + 카드 + 나머지
    // 인트로 텍스트 추출 (첫 번째 식당 데이터 전까지)
    const firstRestaurantPattern = /(?:#{1,3}\s*)?(?:\d+[\.\)]\s*)?\*\*/;
    const firstMatch = content.match(firstRestaurantPattern);

    if (firstMatch && firstMatch.index && firstMatch.index > 0) {
      const intro = content.substring(0, firstMatch.index).trim();
      if (intro) {
        segments.push({ type: 'text', content: intro });
      }
    }

    // 식당 카드 세그먼트
    segments.push({ type: 'restaurants', restaurants });

    // 식당 데이터 이후의 추가 텍스트 (팁, 참고사항 등)
    // 마지막 식당 정보 이후 텍스트
    const lastRestaurant = restaurants[restaurants.length - 1];
    const lastIdx = content.lastIndexOf(lastRestaurant.name);
    if (lastIdx >= 0) {
      // 마지막 식당 이후의 전체 블록을 찾음
      const remaining = content.substring(lastIdx);
      const afterBlock = remaining.match(/(?:\n\n---\n\n|\n\n(?=(?:>|💡|참고|TIP|※|추가)))([\s\S]+)/);
      if (afterBlock) {
        segments.push({ type: 'text', content: afterBlock[1].trim() });
      }
    }
  } else {
    // 일반 응답: ## 헤딩으로 분리
    const sections = content.split(/(?=^## )/m);

    for (const section of sections) {
      const trimmed = section.trim();
      if (trimmed) {
        segments.push({ type: 'text', content: trimmed });
      }
    }
  }

  // 세그먼트가 없으면 전체를 텍스트로
  if (segments.length === 0) {
    segments.push({ type: 'text', content });
  }

  return segments;
}
