"""네이버 쇼핑 검색 API 클라이언트"""

import requests
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from ..config import settings


class NaverShoppingAPI:
    """네이버 쇼핑 검색 API 클라이언트"""

    ENDPOINT = "https://openapi.naver.com/v1/search/shop.json"

    def __init__(self, client_id: str = "", client_secret: str = ""):
        self.client_id = client_id or settings.naver_client_id
        self.client_secret = client_secret or settings.naver_client_secret

    def search_products(self, keyword: str, limit: int = 5, sort: str = "sim") -> list[dict]:
        """
        네이버 쇼핑 상품 검색

        Args:
            keyword: 검색 키워드
            limit: 결과 수 (최대 100)
            sort: 정렬 기준 (sim=정확도, date=날짜, asc=가격낮은순, dsc=가격높은순)

        Returns:
            상품 리스트
        """
        if not self.client_id or not self.client_secret:
            return []

        try:
            response = requests.get(
                self.ENDPOINT,
                headers={
                    "X-Naver-Client-Id": self.client_id,
                    "X-Naver-Client-Secret": self.client_secret,
                },
                params={
                    "query": keyword,
                    "display": min(limit, 100),
                    "sort": sort,
                },
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("items", [])
        except Exception:
            return []

    def search_multiple(self, keywords: list[str], limit_per: int = 1, sort: str = "sim") -> dict[str, list[dict]]:
        """
        여러 키워드를 병렬로 검색

        Args:
            keywords: 검색 키워드 리스트
            limit_per: 키워드당 결과 수
            sort: 정렬 기준

        Returns:
            {키워드: 상품리스트} 딕셔너리
        """
        def _search(kw: str):
            return kw, self.search_products(kw, limit=limit_per, sort=sort)

        results = {}
        with ThreadPoolExecutor(max_workers=10) as executor:
            for kw, items in executor.map(_search, keywords):
                results[kw] = items
        return results


# 싱글턴
_naver: Optional[NaverShoppingAPI] = None


def get_naver_shopping() -> NaverShoppingAPI:
    global _naver
    if _naver is None:
        _naver = NaverShoppingAPI()
    return _naver
