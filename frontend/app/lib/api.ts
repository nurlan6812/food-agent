import type { ChatResponse } from './types';

// 브라우저에서 실행 시 window.location 기반으로 API URL 결정
function getApiBaseUrl(): string {
  if (typeof window !== 'undefined') {
    // 개발 환경이면 localhost:8000 사용
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      return 'http://localhost:8000';
    }
    // 프로덕션이면 같은 호스트의 /api 사용 또는 환경변수
    return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  }
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
}

const API_BASE_URL = getApiBaseUrl();

// 디버깅용 로그
if (typeof window !== 'undefined') {
  console.log('[API] Base URL:', API_BASE_URL);
}

let currentSessionId: string | null = null;

export async function sendChatMessage(message: string): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
      session_id: currentSessionId,
    }),
  });

  if (!response.ok) {
    throw new Error(`API 요청 실패: ${response.status}`);
  }

  const data = await response.json();
  currentSessionId = data.session_id;
  return data;
}

export interface StreamEvent {
  type: 'session' | 'tool' | 'tool_progress' | 'text' | 'done' | 'error';
  session_id?: string;
  tool?: string;
  status?: string;
  content?: string;
  map_url?: string;
  images?: string[];
  message?: string;
}

// File을 base64로 변환하는 유틸리티 함수
async function fileToBase64(file: File): Promise<{ data: string; mime_type: string }> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      // data:image/jpeg;base64,xxxxx 형식에서 base64 부분만 추출
      const base64 = result.split(',')[1];
      resolve({
        data: base64,
        mime_type: file.type || 'image/jpeg',
      });
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

export async function* streamChatMessage(
  message: string,
  images?: File[]
): AsyncGenerator<StreamEvent, void, unknown> {
  const url = `${API_BASE_URL}/chat/stream`;
  console.log('[API] Fetching:', url, 'with images:', images?.length || 0);

  // 이미지를 base64로 변환
  let imageData: { data: string; mime_type: string }[] = [];
  if (images && images.length > 0) {
    imageData = await Promise.all(images.map(fileToBase64));
  }

  let response: Response;
  try {
    response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        session_id: currentSessionId,
        images: imageData.length > 0 ? imageData : undefined,
      }),
    });
  } catch (err) {
    console.error('[API] Fetch error:', err);
    throw new Error(`서버 연결 실패: ${err instanceof Error ? err.message : '알 수 없는 오류'}`);
  }

  if (!response.ok) {
    throw new Error(`API 요청 실패: ${response.status}`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error('응답 스트림을 읽을 수 없습니다');
  }

  const decoder = new TextDecoder();

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim();
          if (data) {
            try {
              const event: StreamEvent = JSON.parse(data);
              if (event.type === 'session' && event.session_id) {
                currentSessionId = event.session_id;
              }
              yield event;
            } catch {
              // JSON 파싱 실패 무시
            }
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

export function clearSession() {
  currentSessionId = null;
}
