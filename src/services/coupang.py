"""쿠팡 파트너스 API 클라이언트"""

import hmac
import hashlib
import urllib.parse
import requests
from time import gmtime, strftime
from typing import Optional

from ..config import settings


class CoupangPartnersAPI:
    """쿠팡 파트너스 Open API 클라이언트"""

    DOMAIN = "https://api-gateway.coupang.com"

    def __init__(self, access_key: str = "", secret_key: str = ""):
        self.access_key = access_key or settings.coupang_access_key
        self.secret_key = secret_key or settings.coupang_secret_key

    def _generate_hmac(self, method: str, url: str) -> str:
        """HMAC-SHA256 인증 헤더 생성"""
        path, *query = url.split("?")
        datetime_gmt = strftime('%y%m%d', gmtime()) + 'T' + strftime('%H%M%S', gmtime()) + 'Z'
        message = datetime_gmt + method + path + (query[0] if query else "")

        signature = hmac.new(
            bytes(self.secret_key, "utf-8"),
            message.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        return f"CEA algorithm=HmacSHA256, access-key={self.access_key}, signed-date={datetime_gmt}, signature={signature}"

    def search_products(self, keyword: str, limit: int = 5) -> list[dict]:
        """
        상품 검색

        Args:
            keyword: 검색 키워드
            limit: 결과 수 (최대 10)

        Returns:
            상품 리스트
        """
        if not self.access_key or not self.secret_key:
            return []

        limit = min(limit, 10)
        url = (
            f"/v2/providers/affiliate_open_api/apis/openapi/products/search"
            f"?keyword={urllib.parse.quote(keyword)}&limit={limit}"
        )

        auth = self._generate_hmac("GET", url)

        try:
            response = requests.get(
                self.DOMAIN + url,
                headers={
                    "Authorization": auth,
                    "Content-Type": "application/json;charset=UTF-8",
                },
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("data", {}).get("productData", [])
        except Exception:
            return []

    def create_deeplink(self, urls: list[str]) -> list[dict]:
        """
        쿠팡 URL을 파트너스 딥링크로 변환

        Args:
            urls: 쿠팡 상품 URL 리스트

        Returns:
            딥링크 리스트
        """
        if not self.access_key or not self.secret_key:
            return []

        url = "/v2/providers/affiliate_open_api/apis/openapi/v1/deeplink"
        auth = self._generate_hmac("POST", url)

        try:
            response = requests.post(
                self.DOMAIN + url,
                headers={
                    "Authorization": auth,
                    "Content-Type": "application/json;charset=UTF-8",
                },
                json={"coupangUrls": urls},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except Exception:
            return []


# 싱글턴
_coupang: Optional[CoupangPartnersAPI] = None


def get_coupang() -> CoupangPartnersAPI:
    global _coupang
    if _coupang is None:
        _coupang = CoupangPartnersAPI()
    return _coupang
