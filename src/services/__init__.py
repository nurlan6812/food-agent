"""외부 API 서비스 클라이언트"""

from .serper import SerperImageSearcher, get_searcher
from .kakao import KakaoLocalAPI, get_kakao
from .summarizer import LocalSummarizer, get_summarizer
from .coupang import CoupangPartnersAPI, get_coupang
from .naver_shopping import NaverShoppingAPI, get_naver_shopping

__all__ = [
    "SerperImageSearcher",
    "KakaoLocalAPI",
    "LocalSummarizer",
    "CoupangPartnersAPI",
    "NaverShoppingAPI",
    "get_searcher",
    "get_kakao",
    "get_summarizer",
    "get_coupang",
    "get_naver_shopping",
]
