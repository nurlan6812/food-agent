'use client';

import { useState } from 'react';
import { FeatureCard } from './feature-card';
import { CameraIcon, NoodleIcon, RecipeIcon, NutritionIcon, ReviewIcon } from './icons/feature-icons';
import { ChevronLeft } from 'lucide-react';

interface WelcomeLandingProps {
  onSendMessage: (message: string) => void;
  onOpenImagePicker: () => void;
}

type FeatureKey = 'restaurant' | 'recipe' | 'nutrition' | 'review';

const FEATURE_EXAMPLES: Record<FeatureKey, { title: string; prompts: string[] }> = {
  restaurant: {
    title: '맛집 및 식당 검색',
    prompts: [
      '강남역 근처 혼밥 맛집 추천해줘',
      '홍대 가성비 좋은 한식 맛집',
      '성수동 데이트 레스토랑 추천해줘',
      '을지로 점심 맛집 추천',
      '종로 고깃집 추천해줘',
    ],
  },
  recipe: {
    title: '레시피 검색',
    prompts: [
      '김치찌개 레시피 알려줘',
      '크림파스타 간단하게 만드는 법',
      '집에서 떡볶이 만드는 법',
      '계란볶음밥 레시피 알려줘',
      '달걀이랑 파로 뭐 만들 수 있어',
    ],
  },
  nutrition: {
    title: '영양정보 및 칼로리',
    prompts: [
      '삼겹살 1인분 칼로리 알려줘',
      '비빔밥 칼로리 얼마야',
      '다이어트할 때 먹기 좋은 한식 추천',
      '소주 한 병 칼로리 얼마야',
      '치킨 한 마리 칼로리 알려줘',
    ],
  },
  review: {
    title: '식당 리뷰 요약',
    prompts: [
      '을지로 곱창집 후기 요약해줘',
      '홍대 이자카야 리뷰 정리해줘',
      '성수동 브런치 카페 후기 알려줘',
      '종로 삼계탕 맛집 리뷰 요약',
      '광장시장 빈대떡 후기 정리해줘',
    ],
  },
};

export function WelcomeLanding({ onSendMessage, onOpenImagePicker }: WelcomeLandingProps) {
  const [selectedFeature, setSelectedFeature] = useState<FeatureKey | null>(null);

  if (selectedFeature) {
    const feature = FEATURE_EXAMPLES[selectedFeature];
    return (
      <div className="flex flex-col justify-center px-6 py-4 sm:py-8 max-w-md mx-auto w-full">
        {/* 뒤로가기 */}
        <button
          onClick={() => setSelectedFeature(null)}
          className="flex items-center gap-1 text-[#89939E] text-sm font-medium mb-4 sm:mb-6 hover:text-[#4D4D4D] transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
          돌아가기
        </button>

        {/* 피처 타이틀 */}
        <div className="px-2 mb-4 sm:mb-6">
          <h2 className="text-[#212121] dark:text-white text-xl font-extrabold">
            {feature.title}
          </h2>
          <p className="text-[#89939E] text-sm font-medium mt-1">
            아래 예시를 선택하거나 직접 입력해보세요
          </p>
        </div>

        {/* 예시 프롬프트 칩 */}
        <div className="flex flex-col gap-3">
          {feature.prompts.map((prompt) => (
            <button
              key={prompt}
              onClick={() => onSendMessage(prompt)}
              className="bg-white rounded-[100px] px-5 py-3.5 shadow-sm hover:shadow-md transition-shadow active:scale-[0.98] text-left text-sm font-medium text-[#4D4D4D]"
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col justify-center px-6 py-4 sm:py-8 max-w-md mx-auto w-full">
      {/* 타이틀 */}
      <div className="px-2 mb-4 sm:mb-10">
        <p className="text-[#89939E] text-xl font-medium mb-1">짜릿한 K푸드</p>
        <h2 className="text-[#212121] dark:text-white text-2xl font-extrabold">
          K푸드 무엇이든 물어보세요!
        </h2>
      </div>

      {/* 피처카드 5개 */}
      <div className="w-full flex flex-col gap-2 sm:gap-3">
        <FeatureCard
          icon={<CameraIcon size={32} />}
          label="사진으로 음식점 찾기"
          description="사진을 올리면 어떤 식당의 메뉴인지 찾아줘요"
          onClick={onOpenImagePicker}
        />
        <FeatureCard
          icon={<NoodleIcon size={32} />}
          label="맛집 및 식당 검색"
          description="지역, 가격, 메뉴별 맛집을 찾아줘요"
          onClick={() => setSelectedFeature('restaurant')}
        />
        <FeatureCard
          icon={<RecipeIcon size={32} />}
          label="레시피 검색"
          description="등록한 사진이나, 입력한 메뉴의 조리법을 찾아줘요"
          onClick={() => setSelectedFeature('recipe')}
        />
        <FeatureCard
          icon={<NutritionIcon size={32} />}
          label="영양정보 및 칼로리"
          description="음식의 칼로리나 영양 성분을 알려드려요"
          onClick={() => setSelectedFeature('nutrition')}
        />
        <FeatureCard
          icon={<ReviewIcon size={32} />}
          label="식당 리뷰 요약"
          description="실방문자 후기를 분석해서 핵심만 쏙쏙 알려드려요"
          onClick={() => setSelectedFeature('review')}
        />
      </div>
    </div>
  );
}
