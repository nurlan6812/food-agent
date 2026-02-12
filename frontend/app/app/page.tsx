'use client';

import { useState, useRef, useEffect } from 'react';
import { ChatMessage } from '@/components/chat-message';
import { ChatInput, ChatInputHandle } from '@/components/chat-input';
import { ThemeToggle } from '@/components/theme-toggle';
import { WelcomeLanding } from '@/components/welcome-landing';
import { AIAvatar } from '@/components/icons/ai-avatar';
import { KFoodieLogo } from '@/components/icons/logo';
import { streamChatMessage, clearSession } from '@/lib/api';
import type { Message, RestaurantCardInfo, ProductCardInfo } from '@/lib/types';
// Figma refresh icon (24x24)
function RefreshIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
      <g clipPath="url(#clip_refresh)">
        <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4C7.58 4 4.01 7.58 4.01 12C4.01 16.42 7.58 20 12 20C15.73 20 18.84 17.45 19.73 14H17.65C16.83 16.33 14.61 18 12 18C8.69 18 6 15.31 6 12C6 8.69 8.69 6 12 6C13.66 6 15.14 6.69 16.22 7.78L13 11H20V4L17.65 6.35Z" fill="currentColor"/>
      </g>
      <defs>
        <clipPath id="clip_refresh"><rect width="24" height="24" fill="white"/></clipPath>
      </defs>
    </svg>
  );
}
import { useToast } from '@/hooks/use-toast';
import { Toaster } from '@/components/ui/toaster';

// 도구 이름 한글 매핑
const TOOL_NAMES_KR: Record<string, string> = {
  search_food_by_image: '이미지로 음식 검색',
  search_restaurant_info: '식당 정보 검색',
  search_recipe_online: '레시피 검색',
  get_restaurant_reviews: '후기 검색',
  get_nutrition_info: '영양 정보 검색',
  search_coupang_products: '쿠팡 상품 검색',
  search_naver_products: '네이버 쇼핑 검색',
  search_recipe_ingredients: '재료 상품 검색',
};

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [toolStatus, setToolStatus] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatInputRef = useRef<ChatInputHandle>(null);
  const { toast } = useToast();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, toolStatus]);

  const handleClearChat = () => {
    clearSession();
    setMessages([]);
  };

  const handleSend = async (message: string, images: File[]) => {
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: message,
      images: images.map((img) => URL.createObjectURL(img)),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setToolStatus('');

    try {
      let aiContent = '';
      let mapUrl: string | undefined;
      let aiImages: string[] = [];
      let restaurants: RestaurantCardInfo[] = [];
      let products: ProductCardInfo[] = [];
      let suggestions: string[] = [];
      let toolsUsed: string[] = [];

      for await (const event of streamChatMessage(message, images)) {
        switch (event.type) {
          case 'tool':
            if (event.status === 'start' && event.tool) {
              if (!toolsUsed.includes(event.tool)) {
                toolsUsed.push(event.tool);
              }
              const toolName = TOOL_NAMES_KR[event.tool] || event.tool;
              setToolStatus(`${toolName} 사용중`);
            } else if (event.status === 'done') {
              setToolStatus('');
            }
            break;

          case 'tool_progress':
            if (event.status) {
              setToolStatus(event.status);
            }
            break;

          case 'restaurants':
            if (event.restaurants) {
              restaurants = [...restaurants, ...event.restaurants];
              setMessages((prev) => {
                const existing = prev.find((m) => m.id === 'ai-streaming');
                if (existing) {
                  return prev.map((m) =>
                    m.id === 'ai-streaming' ? { ...m, restaurants } : m
                  );
                }
                return [
                  ...prev,
                  {
                    id: 'ai-streaming',
                    role: 'assistant' as const,
                    content: '',
                    restaurants,
                    timestamp: new Date(),
                  },
                ];
              });
            }
            break;

          case 'products':
            if (event.products) {
              products = [...products, ...event.products];
              // 텍스트가 이미 있으면 바로 반영, 없으면 텍스트 올 때 같이 반영
              setMessages((prev) => {
                const existing = prev.find((m) => m.id === 'ai-streaming');
                if (existing) {
                  return prev.map((m) =>
                    m.id === 'ai-streaming' ? { ...m, products } : m
                  );
                }
                return prev;
              });
            }
            break;

          case 'text':
            if (event.content) {
              setToolStatus('');
              aiContent += event.content;
              setMessages((prev) => {
                const existing = prev.find((m) => m.id === 'ai-streaming');
                if (existing) {
                  return prev.map((m) =>
                    m.id === 'ai-streaming'
                      ? { ...m, content: filterContent(aiContent), restaurants }
                      : m
                  );
                } else {
                  return [
                    ...prev,
                    {
                      id: 'ai-streaming',
                      role: 'assistant' as const,
                      content: filterContent(aiContent),
                      restaurants,
                      timestamp: new Date(),
                    },
                  ];
                }
              });
            }
            break;

          case 'done':
            mapUrl = event.map_url;
            aiImages = event.images || [];
            suggestions = event.suggestions || [];
            setToolStatus('');
            // done 즉시 카드+제안 칩 표시 (텍스트 스트리밍 끝난 직후)
            setMessages((prev) => {
              const existing = prev.find((m) => m.id === 'ai-streaming');
              if (existing) {
                return prev.map((m) =>
                  m.id === 'ai-streaming'
                    ? { ...m, products, suggestions }
                    : m
                );
              }
              return prev;
            });
            break;

          case 'error':
            throw new Error(event.message || '오류가 발생했습니다');
        }
      }

      setMessages((prev) => {
        const filtered = prev.filter((m) => m.id !== 'ai-streaming');
        return [
          ...filtered,
          {
            id: `ai-${Date.now()}`,
            role: 'assistant' as const,
            content: filterContent(aiContent),
            mapUrl,
            images: aiImages,
            restaurants,
            products,
            suggestions,
            toolsUsed,
            timestamp: new Date(),
          },
        ];
      });
    } catch (error) {
      console.error('[Chat] Error:', error);
      toast({
        variant: 'destructive',
        title: '오류가 발생했습니다',
        description: error instanceof Error ? error.message : '메시지 전송에 실패했습니다.',
      });

      setMessages((prev) => prev.filter((m) => m.id !== 'ai-streaming'));

      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: '죄송합니다. 메시지를 처리하는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setToolStatus('');
    }
  };

  const handleFeatureSend = (message: string) => {
    handleSend(message, []);
  };

  const handleOpenImagePicker = () => {
    chatInputRef.current?.openImagePicker();
  };

  const hasMessages = messages.length > 0;

  return (
    <div className="flex flex-col h-[100dvh] bg-background">
      {/* 헤더 */}
      <header className="sticky top-0 z-10 bg-background safe-top">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between">
          <button onClick={handleClearChat} className="flex items-center gap-2 hover:opacity-80 transition-opacity">
            <KFoodieLogo size={36} />
            <h1 className="font-changa text-2xl tracking-tight flex items-center gap-3">
              <span className="text-[#212121] dark:text-white">K-Foodie</span>
              <span className="text-[#E02020]">AI</span>
            </h1>
          </button>
          <div className="flex items-center gap-4">
            <button
              onClick={handleClearChat}
              className="w-6 h-6 flex items-center justify-center text-[#89939E] hover:text-[#4D4D4D] transition-colors"
              aria-label="새 대화"
            >
              <RefreshIcon />
            </button>
            <ThemeToggle />
          </div>
        </div>
      </header>

      {/* 메시지 영역 */}
      <main className="flex-1 overflow-y-auto overscroll-contain">
        <div className="max-w-4xl mx-auto px-2 sm:px-0">
          {!hasMessages ? (
            /* 웰컴 랜딩 */
            <div className="flex items-start sm:items-center justify-center min-h-full py-2 sm:py-0">
              <WelcomeLanding
                onSendMessage={handleFeatureSend}
                onOpenImagePicker={handleOpenImagePicker}
              />
            </div>
          ) : (
            /* 채팅 메시지 */
            <div className="py-4">
              {messages.map((message) => (
                <ChatMessage
                  key={message.id}
                  message={message}
                  onSuggestionSelect={(suggestion) => handleSend(suggestion, [])}
                />
              ))}
              {(isLoading && !messages.some(m => m.id === 'ai-streaming')) && (
                <div className="flex justify-start px-4 py-3">
                  <div className="flex items-center gap-3 bg-white rounded-[24px] px-4 py-4 shadow-sm">
                    <AIAvatar size={24} />
                    <span className="text-sm font-bold text-[#212121]">
                      {toolStatus || 'AI가 응답을 생성하고 있습니다'}
                    </span>
                    <div className="flex gap-1">
                      <div className="w-1.5 h-1.5 rounded-full bg-[#E02020] bouncing-dot" />
                      <div className="w-1.5 h-1.5 rounded-full bg-[#E02020] bouncing-dot" />
                      <div className="w-1.5 h-1.5 rounded-full bg-[#E02020] bouncing-dot" />
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </main>

      {/* 입력 영역 */}
      <ChatInput ref={chatInputRef} onSend={handleSend} disabled={isLoading} />

      <Toaster />
    </div>
  );
}

// 내부 추론 및 태그 필터링
function filterContent(text: string): string {
  text = text.replace(/Plan:.*?(?=\n\n|\Z)/gs, '');
  text = text.replace(/\[IMAGE:[^\]]+\]/g, '');
  text = text.replace(/\[MAP:[^\]]+\]/g, '');
  text = text.replace(/\[검색 결과 이미지\]\s*/g, '');
  text = text.replace(/\[SUGGEST:[^\]]+\]/g, '');
  text = text.replace(/\[RESTAURANTS_JSON:\[.*?\]\]/g, '');
  text = text.replace(/\[PRODUCTS_JSON:\[.*?\]\]/g, '');
  // 스트리밍 중 불완전한 태그도 제거 (아직 닫히지 않은 태그)
  text = text.replace(/\[MAP:.*$/s, '');
  text = text.replace(/\[RESTAURANTS_JSON:.*$/s, '');
  text = text.replace(/\[PRODUCTS_JSON:.*$/s, '');
  text = text.replace(/\[SUGGEST:.*$/s, '');
  text = text.replace(/\[THUMBNAIL:[^\]]+\]/g, '');
  text = text.replace(/\[검색 결과 썸네일\]\s*/g, '');
  return text.trim();
}
