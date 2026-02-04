"""이미지 검색 도구"""

import os
import re
from typing import Dict, Any
from langchain_core.tools import tool
from langgraph.config import get_stream_writer

try:
    import requests
except ImportError:
    pass

from ..services import get_searcher


def extract_blog_content(url: str) -> Dict[str, Any]:
    """블로그 페이지에서 음식 관련 본문 텍스트 추출"""
    result = {"url": url, "content": ""}

    try:
        if 'blog.naver.com' in url and 'm.blog' not in url:
            url = url.replace('blog.naver.com', 'm.blog.naver.com')

        headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return result

        text = response.text
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = ' '.join(text.split())

        food_keywords = ['주문', '시켰', '먹었', '메뉴', '맛있', '바삭', '쫄깃', '토핑', '소스', '가격', '원']
        sentences = re.split(r'[.!?。]', text)

        relevant_sentences = []
        for sentence in sentences:
            if any(kw in sentence for kw in food_keywords):
                if 20 < len(sentence) < 200:
                    relevant_sentences.append(sentence.strip())

        result["content"] = ' '.join(relevant_sentences[:10])
    except:
        pass

    return result


@tool
def search_food_by_image(image_source: str) -> str:
    """
    새로운 음식 이미지가 있을 때만 사용하세요.
    이미지 URL 또는 로컬 파일 경로를 받아 Google Lens로 검색합니다.

    Args:
        image_source: 이미지 URL 또는 로컬 파일 경로 (필수)

    Returns:
        Google 이미지 검색 결과 + 블로그 본문
    """
    # 실시간 스트리밍을 위한 writer 획득
    writer = get_stream_writer()


    if not image_source or not image_source.strip():
        return "[이미지 없음] 이 도구는 새 이미지가 있을 때만 사용하세요."

    image_source = image_source.strip()

    if not image_source.startswith(('http://', 'https://', '/')):
        return "[이미지 없음] 유효한 이미지 경로가 아닙니다."

    if not image_source.startswith(('http://', 'https://')) and not os.path.exists(image_source):
        return f"[이미지 없음] 파일을 찾을 수 없습니다: {image_source}"

    searcher = get_searcher()

    # 🔥 실시간 업데이트: 이미지 업로드 시작
    writer({"tool": "search_food_by_image", "status": "이미지 업로드 중..."})

    image_url = searcher.get_image_url(image_source)
    if not image_url:
        return f"이미지를 업로드할 수 없습니다: {image_source}"


    # 🔥 실시간 업데이트: Google Lens 검색 시작
    writer({"tool": "search_food_by_image", "status": "Google Lens로 검색 중..."})

    result = searcher.search_with_combined(image_url)

    if "error" in result:
        return f"검색 실패: {result['error']}"


    # 🔥 실시간 업데이트: 검색 완료
    writer({"tool": "search_food_by_image", "status": "검색 결과 분석 중..."})

    output = []
    blog_links = []
    thumbnails = []

    visual = result.get("visual_matches", [])
    if visual:
        output.append("[검색 결과]")
        for i, v in enumerate(visual[:10], 1):
            title = v.get("title", "")
            snippet = v.get("snippet", "")
            link = v.get("link", "")
            thumbnail = v.get("thumbnail", "")

            if title:
                line = f"{i}. {title}"
                if snippet:
                    line += f" - {snippet[:100]}"
                output.append(line)

            if thumbnail and len(thumbnails) < 3:
                thumbnails.append(thumbnail)

            if link and ('blog.naver.com' in link or 'tistory.com' in link):
                blog_links.append(link)

    if thumbnails:
        output.append("\n[검색 결과 이미지]")
        for url in thumbnails:
            output.append(f"[IMAGE:{url}]")

    if blog_links:
        output.append("\n[블로그 본문 (메뉴 판단 참고용)]")
        for i, link in enumerate(blog_links[:3], 1):
            blog_data = extract_blog_content(link)
            if blog_data["content"]:
                output.append(f"\n--- 블로그 {i} ---")
                output.append(blog_data["content"][:1000])

    texts = result.get("text", [])
    if texts:
        text_list = [t.get("text", "") for t in texts[:5] if t.get("text")]
        if text_list:
            output.append(f"\n[이미지 텍스트] {', '.join(text_list)}")

    output.append("\n[판단 요청]")
    output.append("1. 원본 이미지를 기반으로 검색 결과 제목, 블로그 본문을 참고하세요.")
    output.append("2. 음식 이름만 물어보면: '~로 보입니다' + 식당이 보이면 '혹시 OO에서 드셨나요?'")
    output.append("3. 식당/메뉴명까지 물어보면: 가능성 있는 식당 2~3곳을 후보로 나열하세요.")

    return "\n".join(output) if output else "검색 결과 없음"
