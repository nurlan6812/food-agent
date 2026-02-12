'use client';

import type { Message } from '@/lib/types';
import { ImageGallery } from './image-gallery';
import { MapEmbed } from './map-embed';
import { RestaurantCarousel } from './restaurant-carousel';
import { ProductCarousel } from './product-carousel';
import { SuggestionChips } from './suggestion-chips';
import { AIAvatar } from './icons/ai-avatar';
import { extractSuggestions } from '@/lib/parse-response';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ChatMessageProps {
  message: Message;
  onSuggestionSelect?: (suggestion: string) => void;
}

export function ChatMessage({ message, onSuggestionSelect }: ChatMessageProps) {
  const isUser = message.role === 'user';

  // 유저 메시지
  if (isUser) {
    return (
      <div className="flex w-full gap-3 px-4 py-3 justify-end">
        <div className="flex flex-col gap-3 max-w-[85%] md:max-w-[70%] items-end">
          {message.content && (
            <div className="bg-white rounded-[24px] rounded-tr-[4px] px-4 py-3 shadow-sm">
              <p className="text-[15px] leading-relaxed whitespace-pre-wrap break-words text-[#212121]">
                {message.content}
              </p>
            </div>
          )}
          {message.images && message.images.length > 0 && (
            <div className="w-full max-w-md">
              <ImageGallery images={message.images} />
            </div>
          )}
          <span className="text-xs text-[#89939E] px-2">
            {message.timestamp.toLocaleTimeString('ko-KR', {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </span>
        </div>
      </div>
    );
  }

  // AI 메시지 - 구조화 데이터 우선
  const hasStructuredRestaurants = message.restaurants && message.restaurants.length > 0;
  const hasStructuredProducts = message.products && message.products.length > 0;
  const hasCardImages = (message.restaurants?.some(r => r.imageUrl)) || (message.products?.some(p => p.imageUrl));
  const isRecipe = message.toolsUsed?.includes('search_recipe_online');
  const hasImages = message.images && message.images.length > 0 && !hasCardImages;

  // 제안: 구조화 데이터 우선, 없으면 텍스트 추출 폴백
  const suggestions = (message.suggestions?.length)
    ? message.suggestions
    : extractSuggestions(message.content);

  // 텍스트 세그먼트: ## 기준 분리
  const textSegments = message.content
    ? message.content.split(/(?=^## )/m).filter(s => s.trim())
    : [];
  if (textSegments.length === 0 && message.content) {
    textSegments.push(message.content);
  }

  return (
    <div className="flex w-full gap-3 px-4 py-3 justify-start">
      {/* AI 아바타 */}
      <div className="flex-shrink-0 mt-1">
        <AIAvatar size={32} />
      </div>

      <div className="flex flex-col gap-3 max-w-[85%] md:max-w-[75%]">
        {/* 1. 레시피 이미지 (응답 상단) */}
        {isRecipe && hasImages && (
          <div className="w-full max-w-md">
            <ImageGallery images={message.images!} />
          </div>
        )}

        {/* 2. 텍스트 세그먼트들 */}
        {textSegments.map((segment, idx) => (
          <div key={idx} className="bg-white rounded-3xl px-4 py-4 shadow-sm">
            <div className="text-[15px] chat-markdown text-[#333333]">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  a: ({ href, children }) => (
                    <a href={href} target="_blank" rel="noopener noreferrer" className="text-[#E02020] font-semibold hover:text-[#C91A1A]">
                      {children}
                    </a>
                  ),
                  table: ({ children }) => (
                    <div className="table-wrapper">
                      <table>{children}</table>
                    </div>
                  ),
                }}
              >
                {segment
                  .replace(/(\d)~(\d)/g, '$1～$2')
                  .replace(/\*\*'([^']+)'\*\*/g, '**$1**')
                  .replace(/\*\*'([^']+)'\*\*/g, '**$1**')
                }
              </ReactMarkdown>
            </div>
          </div>
        ))}

        {/* 2. 구조화 식당 캐러셀 (텍스트 아래 중간 배치) */}
        {hasStructuredRestaurants && (
          <div className="w-full">
            <RestaurantCarousel restaurants={message.restaurants!} />
          </div>
        )}

        {/* 3. 구조화 상품 캐러셀 */}
        {hasStructuredProducts && (
          <div className="w-full">
            <ProductCarousel products={message.products!} />
          </div>
        )}

        {/* 4. 비레시피 이미지 (텍스트/카드 뒤) */}
        {!isRecipe && hasImages && (
          <div className="w-full max-w-md">
            <ImageGallery images={message.images!} />
          </div>
        )}

        {/* 5. 지도 */}
        {message.mapUrl && (
          <div className="w-full">
            <MapEmbed url={message.mapUrl} />
          </div>
        )}

        {/* 6. 후속 질문 제안 칩 */}
        {suggestions.length > 0 && onSuggestionSelect && (
          <SuggestionChips suggestions={suggestions} onSelect={onSuggestionSelect} />
        )}

        {/* 7. 타임스탬프 */}
        <span className="text-xs text-[#89939E] px-2">
          {message.timestamp.toLocaleTimeString('ko-KR', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </span>
      </div>
    </div>
  );
}
