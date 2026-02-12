"""한국 음식 에이전트 도구 모듈"""

from .image import search_food_by_image
from .restaurant import search_restaurant_info, get_restaurant_reviews
from .recipe import search_recipe_online
from .nutrition import get_nutrition_info
from .coupang import search_coupang_products
from .naver_shopping import search_naver_products, search_recipe_ingredients
from .web_search import web_search

# 모든 도구 목록 (쿠팡 API 키 받으면 search_coupang_products로 교체)
ALL_TOOLS = [
    search_food_by_image,      # 이미지 → 음식 인식
    search_restaurant_info,    # 식당 검색
    search_recipe_online,      # 레시피 검색
    get_restaurant_reviews,    # 후기 크롤링
    get_nutrition_info,        # 영양정보 검색
    search_naver_products,     # 네이버 쇼핑 상품 검색
    search_recipe_ingredients, # 레시피 재료 일괄 상품 검색
    web_search,                # 범용 웹검색 (폴백)
]

__all__ = [
    "search_food_by_image",
    "search_restaurant_info",
    "search_recipe_online",
    "get_restaurant_reviews",
    "get_nutrition_info",
    "search_coupang_products",
    "search_naver_products",
    "search_recipe_ingredients",
    "web_search",
    "ALL_TOOLS",
]
