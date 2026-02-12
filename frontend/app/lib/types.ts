export interface RestaurantCardInfo {
  name: string;
  address?: string;
  phone?: string;
  category?: string;
  kakaoUrl?: string;
  description?: string;
  imageUrl?: string;
}

export interface ProductCardInfo {
  name: string;
  price?: number;
  imageUrl?: string;
  productUrl?: string;
  description?: string;
  mall?: string;
  brand?: string;
  category?: string;
  isRocket?: boolean;
  isFreeShipping?: boolean;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  images?: string[];
  restaurants?: RestaurantCardInfo[];
  products?: ProductCardInfo[];
  mapUrl?: string;
  suggestions?: string[];
  toolsUsed?: string[];
  timestamp: Date;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
}

export interface ChatResponse {
  response: string;
  session_id: string;
  map_url?: string;
  images?: string[];
}
