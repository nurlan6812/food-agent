"""범용 웹검색 도구 - 다른 도구로 답변할 수 없는 음식 관련 질문용"""

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

from langchain_core.tools import tool
from langgraph.config import get_stream_writer

from ..services import get_searcher


def _crawl_page(url: str, max_chars: int = 2000) -> str:
    """웹페이지 본문 텍스트 크롤링"""
    if not BS4_AVAILABLE or not REQUESTS_AVAILABLE:
        return ""

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

        if 'blog.naver.com' in url and 'm.blog' not in url:
            url = url.replace('blog.naver.com', 'm.blog.naver.com')

        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = 'utf-8'

        if resp.status_code != 200:
            return ""

        soup = BeautifulSoup(resp.text, 'html.parser')

        for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()

        if soup.body:
            text = soup.body.get_text(separator='\n')
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            return '\n'.join(lines)[:max_chars]

    except Exception:
        return ""

    return ""


@tool
def web_search(query: str) -> str:
    """
    다른 전문 도구가 모두 해당하지 않을 때만 사용하세요.
    식당 검색, 레시피, 영양정보, 후기, 쇼핑 질문에는 절대 사용하지 마세요.

    Args:
        query: 검색할 질문

    Returns:
        웹 검색 결과 요약
    """
    writer = get_stream_writer()
    writer({"tool": "web_search", "status": "웹 검색 중..."})

    searcher = get_searcher()
    search_result = searcher.search_text(query)

    if "error" in search_result:
        return f"검색 실패: {search_result['error']}"

    organic = search_result.get("organic_results", [])
    answer_box = search_result.get("answer_box", {})

    if not organic and not answer_box:
        return f"'{query}' 검색 결과가 없습니다."

    output = [f"[웹 검색: {query}]"]

    # answer box가 있으면 우선 포함
    if answer_box:
        snippet = answer_box.get("snippet") or answer_box.get("answer", "")
        if snippet:
            output.append(f"\n[요약]\n{snippet}")

    writer({"tool": "web_search", "status": "검색 결과 분석 중..."})

    # 상위 3개 결과 크롤링
    for i, item in enumerate(organic[:3], 1):
        title = item.get("title", "")
        link = item.get("link", "")
        snippet = item.get("snippet", "")

        content = _crawl_page(link)

        output.append(f"\n=== {i}. {title} ===")
        output.append(f"출처: {link}")
        if content:
            output.append(content)
        elif snippet:
            output.append(snippet)

    return "\n".join(output)
