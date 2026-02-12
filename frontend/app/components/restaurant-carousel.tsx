'use client';

import { useRef } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import type { RestaurantCardInfo } from '@/lib/types';

interface RestaurantCarouselProps {
  restaurants: RestaurantCardInfo[];
}

function KakaoMapIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
      <path d="M12 2C7.03 2 3 5.13 3 9C3 11.61 4.89 13.88 7.63 15.07L6.8 18.35C6.73 18.61 7.03 18.82 7.26 18.67L11.15 16.11C11.43 16.14 11.71 16.15 12 16.15C16.97 16.15 21 13.02 21 9.15C21 5.28 16.97 2 12 2Z" fill="#3C1E1E"/>
    </svg>
  );
}

export function RestaurantCarousel({ restaurants }: RestaurantCarouselProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  const scroll = (direction: 'left' | 'right') => {
    if (!scrollRef.current) return;
    const amount = 260;
    scrollRef.current.scrollBy({
      left: direction === 'left' ? -amount : amount,
      behavior: 'smooth',
    });
  };

  return (
    <div className="relative w-full">
      {/* 좌우 스크롤 버튼 */}
      {restaurants.length > 2 && (
        <>
          <button
            onClick={() => scroll('left')}
            className="absolute left-1 top-1/2 -translate-y-1/2 z-10 w-8 h-8 rounded-full bg-white/90 shadow-md flex items-center justify-center text-[#89939E] hover:text-[#4D4D4D] transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            onClick={() => scroll('right')}
            className="absolute right-1 top-1/2 -translate-y-1/2 z-10 w-8 h-8 rounded-full bg-white/90 shadow-md flex items-center justify-center text-[#89939E] hover:text-[#4D4D4D] transition-colors"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </>
      )}

      {/* 카드 스크롤 영역 */}
      <div
        ref={scrollRef}
        className="flex gap-3 overflow-x-auto scrollbar-hide scroll-smooth pb-2"
        style={{ scrollSnapType: 'x mandatory' }}
      >
        {restaurants.map((restaurant, idx) => (
          <div
            key={idx}
            className="flex-shrink-0 w-[243px] bg-white rounded-3xl shadow-sm overflow-hidden border border-[#F0F0F0] flex flex-col"
            style={{ scrollSnapAlign: 'start' }}
          >
            {/* 음식 이미지 */}
            {restaurant.imageUrl && (
              <div className="w-full h-[160px] bg-[#F8F8F8] overflow-hidden">
                <img
                  src={restaurant.imageUrl}
                  alt={restaurant.name}
                  className="w-full h-full object-cover"
                  loading="lazy"
                />
              </div>
            )}

            {/* 카드 내용 */}
            <div className="px-4 pt-4 pb-4 flex-1 flex flex-col">
              {/* 번호 + 이름 */}
              <div className="flex items-start gap-2.5 mb-2">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-[#E02020] text-white text-xs font-bold flex items-center justify-center">
                  {idx + 1}
                </span>
                <h4 className="text-base font-bold text-[#212121] leading-tight">{restaurant.name}</h4>
              </div>

              {/* 카테고리 */}
              {restaurant.category && (
                <span className="text-xs text-[#89939E] mb-2">{restaurant.category}</span>
              )}

              {/* AI가 작성한 설명 */}
              {restaurant.description && (
                <p className="text-sm text-[#4D4D4D] leading-relaxed mb-2">
                  {restaurant.description}
                </p>
              )}

              {/* 주소 */}
              {restaurant.address && (
                <p className="text-xs text-[#717171] mb-0.5 flex items-start gap-1">
                  <span className="flex-shrink-0">📍</span>
                  <span>{restaurant.address}</span>
                </p>
              )}

              {/* 전화번호 */}
              {restaurant.phone && (
                <p className="text-xs text-[#717171] mb-3 flex items-center gap-1">
                  <span className="flex-shrink-0">📞</span>
                  <span>{restaurant.phone}</span>
                </p>
              )}

              {/* 스페이서 */}
              <div className="flex-1" />

              {/* 카카오맵 버튼 */}
              {restaurant.kakaoUrl && (
                <a
                  href={restaurant.kakaoUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-center gap-1.5 w-full py-2.5 bg-[#FAE100] hover:bg-[#F0D800] text-[#3C1E1E] rounded-lg text-sm font-medium transition-colors"
                >
                  <KakaoMapIcon />
                  카카오맵에서 보기
                </a>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
