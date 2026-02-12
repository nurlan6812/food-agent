'use client';

import { useRef } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import type { ProductCardInfo } from '@/lib/types';

interface ProductCarouselProps {
  products: ProductCardInfo[];
}

function formatPrice(price?: number): string {
  if (!price) return '';
  return price.toLocaleString('ko-KR') + '원';
}

export function ProductCarousel({ products }: ProductCarouselProps) {
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
      {products.length > 2 && (
        <>
          <button
            onClick={() => scroll('left')}
            className="absolute -left-2 top-1/2 -translate-y-1/2 z-10 w-8 h-8 rounded-full bg-white shadow-md flex items-center justify-center text-[#89939E] hover:text-[#4D4D4D] transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            onClick={() => scroll('right')}
            className="absolute -right-2 top-1/2 -translate-y-1/2 z-10 w-8 h-8 rounded-full bg-white shadow-md flex items-center justify-center text-[#89939E] hover:text-[#4D4D4D] transition-colors"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </>
      )}

      <div
        ref={scrollRef}
        className="flex gap-3 overflow-x-auto scrollbar-hide scroll-smooth pb-2 -mx-1 px-1"
        style={{ scrollSnapType: 'x mandatory' }}
      >
        {products.map((product, idx) => (
          <div
            key={idx}
            className="flex-shrink-0 w-[243px] bg-white rounded-3xl shadow-sm overflow-hidden border border-[#F0F0F0] flex flex-col"
            style={{ scrollSnapAlign: 'start' }}
          >
            {/* 상품 이미지 */}
            {product.imageUrl && (
              <div className="w-full h-[222px] bg-[#F8F8F8] overflow-hidden">
                <img
                  src={product.imageUrl}
                  alt={product.name}
                  className="w-full h-full object-contain"
                  loading="lazy"
                />
              </div>
            )}

            {/* 상품 정보 */}
            <div className="px-4 pt-4 pb-6 flex-1 flex flex-col gap-4">
              <h4 className="text-base font-bold text-[#212121] line-clamp-2 leading-tight">
                {product.name}
              </h4>

              {/* AI 설명 */}
              {product.description && (
                <p className="text-sm text-[#717171] leading-snug">
                  {product.description}
                </p>
              )}

              {/* 가격 + 판매처 */}
              {(product.price != null && product.price > 0 || product.mall) && (
                <div className="text-sm">
                  {product.price != null && product.price > 0 && (
                    <span className="font-medium text-[#212121]">{formatPrice(product.price)}</span>
                  )}
                  {product.mall && (
                    <span className="ml-1.5 text-[#717171]">· {product.mall}</span>
                  )}
                  <p className="text-xs text-[#B0B0B0] mt-0.5">최저가 기준 · 배송비 별도</p>
                </div>
              )}

              {/* 스페이서 */}
              <div className="flex-1" />

              {/* 구매 버튼 */}
              {product.productUrl && (
                <a
                  href={product.productUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block w-full text-center py-2.5 bg-[#212121] hover:bg-[#333333] text-white rounded-lg text-sm font-bold transition-colors"
                >
                  지금 구매하기
                </a>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* 출처 고지 */}
      <p className="text-[10px] text-[#B0B0B0] mt-1 px-1">
        네이버 쇼핑 검색 결과입니다.
      </p>
    </div>
  );
}
