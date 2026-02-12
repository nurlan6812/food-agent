'use client';

import React, { useState, useRef, useImperativeHandle, forwardRef, KeyboardEvent } from 'react';
import { X } from 'lucide-react';
import Image from 'next/image';
import { cn } from '@/lib/utils';

// Figma 사진 첨부 아이콘 (32x32, #F5F7FA 원 + #717171 아이콘)
function PhotoIcon() {
  return (
    <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
      <rect x="0.5" y="0.5" width="31" height="31" rx="15.5" fill="#F5F7FA"/>
      <rect x="0.5" y="0.5" width="31" height="31" rx="15.5" stroke="#F5F7FA"/>
      <g clipPath="url(#clip_photo)">
        <path d="M25.02 9H23V6.98C23 6.44 22.56 6 22.02 6H21.99C21.44 6 21 6.44 21 6.98V9H18.99C18.45 9 18.01 9.44 18 9.98V10.01C18 10.56 18.44 11 18.99 11H21V13.01C21 13.55 21.44 14 21.99 13.99H22.02C22.56 13.99 23 13.55 23 13.01V11H25.02C25.56 11 26 10.56 26 10.02V9.98C26 9.44 25.56 9 25.02 9ZM20 13.01V12H18.99C18.46 12 17.96 11.79 17.58 11.42C17.21 11.04 17 10.54 17 9.98C17 9.62 17.1 9.29 17.27 9H9C7.9 9 7 9.9 7 11V23C7 24.1 7.9 25 9 25H21C22.1 25 23 24.1 23 23V14.72C22.7 14.89 22.36 15 21.98 15C20.89 14.99 20 14.1 20 13.01ZM19.96 23H10C9.59 23 9.35 22.53 9.6 22.2L11.58 19.57C11.79 19.29 12.2 19.31 12.4 19.59L14 22L16.61 18.52C16.81 18.26 17.2 18.25 17.4 18.51L20.35 22.19C20.61 22.52 20.38 23 19.96 23Z" fill="#717171"/>
      </g>
      <defs>
        <clipPath id="clip_photo"><rect width="24" height="24" fill="white" transform="translate(4 4)"/></clipPath>
      </defs>
    </svg>
  );
}

// Figma 전송 아이콘 (32x32, #F5F7FA 원 + black 화살표)
function SendIcon() {
  return (
    <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
      <rect width="32" height="32" rx="16" fill="#F5F7FA"/>
      <g clipPath="url(#clip_send)">
        <path fillRule="evenodd" clipRule="evenodd" d="M18.4457 13.0543L13.1657 16.7202L7.64297 14.8791C7.25748 14.7503 6.99777 14.3886 6.99999 13.9823C7.00224 13.576 7.26492 13.2165 7.65191 13.0922L21.7715 8.54521C22.1071 8.43732 22.4755 8.52586 22.7248 8.77518C22.9741 9.0245 23.0627 9.39287 22.9548 9.72851L18.4078 23.8481C18.2835 24.2351 17.924 24.4978 17.5177 24.5C17.1114 24.5022 16.7497 24.2425 16.6209 23.857L14.7709 18.3076L18.4457 13.0543Z" fill="black"/>
      </g>
      <defs>
        <clipPath id="clip_send"><rect width="16" height="16" fill="white" transform="translate(7 8.5)"/></clipPath>
      </defs>
    </svg>
  );
}

interface ChatInputProps {
  onSend: (message: string, images: File[]) => void;
  disabled?: boolean;
}

export interface ChatInputHandle {
  openImagePicker: () => void;
}

export const ChatInput = forwardRef<ChatInputHandle, ChatInputProps>(
  function ChatInput({ onSend, disabled = false }, ref) {
    const [message, setMessage] = useState('');
    const [selectedImages, setSelectedImages] = useState<File[]>([]);
    const [imagePreviews, setImagePreviews] = useState<string[]>([]);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    useImperativeHandle(ref, () => ({
      openImagePicker: () => {
        fileInputRef.current?.click();
      },
    }));

    const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = Array.from(e.target.files || []);
      if (files.length === 0) return;

      setSelectedImages((prev) => [...prev, ...files]);

      files.forEach((file) => {
        const reader = new FileReader();
        reader.onloadend = () => {
          setImagePreviews((prev) => [...prev, reader.result as string]);
        };
        reader.readAsDataURL(file);
      });

      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    };

    const removeImage = (index: number) => {
      setSelectedImages((prev) => prev.filter((_, i) => i !== index));
      setImagePreviews((prev) => prev.filter((_, i) => i !== index));
    };

    const handleSend = () => {
      if ((!message.trim() && selectedImages.length === 0) || disabled) return;

      onSend(message.trim(), selectedImages);
      setMessage('');
      setSelectedImages([]);
      setImagePreviews([]);

      setTimeout(() => {
        textareaRef.current?.focus();
      }, 0);
    };

    const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    };

    return (
      <div className="bg-white rounded-t-[32px] shadow-[0px_-8px_16px_rgba(171,190,209,0.4)] safe-bottom">
        <div className="max-w-4xl mx-auto px-4 pt-4 pb-3">
          {/* 이미지 프리뷰 */}
          {imagePreviews.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-3">
              {imagePreviews.map((preview, index) => (
                <div
                  key={index}
                  className="relative w-16 h-16 rounded-xl overflow-hidden bg-[#F5F7FA] group"
                >
                  <Image
                    src={preview || '/placeholder.svg'}
                    alt={`선택된 이미지 ${index + 1}`}
                    fill
                    className="object-cover"
                    sizes="64px"
                  />
                  <button
                    onClick={() => removeImage(index)}
                    className="absolute top-0.5 right-0.5 bg-black/50 text-white rounded-full p-0.5 opacity-0 group-hover:opacity-100 transition-opacity"
                    aria-label="이미지 제거"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* 입력 영역 */}
          <div className="flex items-center gap-4">
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              multiple
              onChange={handleImageSelect}
              className="hidden"
            />

            {/* 사진 버튼 - Figma 원본 */}
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={disabled}
              className="flex-shrink-0 disabled:opacity-40"
              aria-label="이미지 선택"
            >
              <PhotoIcon />
            </button>

            {/* 텍스트 입력 */}
            <div className="flex-1">
              <textarea
                ref={textareaRef}
                value={message}
                onChange={(e) => {
                  setMessage(e.target.value);
                  e.target.style.height = 'auto';
                  e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
                }}
                onKeyDown={handleKeyDown}
                placeholder="메시지를 입력하세요..."
                disabled={disabled}
                className={cn(
                  'w-full bg-[#F5F7FA] rounded-[40px] px-4 py-2 text-sm text-[#212121] placeholder-[#89939E]',
                  'resize-none outline-none min-h-[36px] max-h-[120px]',
                  'disabled:opacity-40'
                )}
                rows={1}
              />
            </div>

            {/* 전송 버튼 - Figma 원본 */}
            <button
              onClick={handleSend}
              disabled={disabled || (!message.trim() && selectedImages.length === 0)}
              className="flex-shrink-0 disabled:opacity-40"
              aria-label="전송"
            >
              <SendIcon />
            </button>
          </div>
        </div>
      </div>
    );
  }
);
