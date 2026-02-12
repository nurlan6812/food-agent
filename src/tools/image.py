"""이미지 검색 도구 (Gemini 비전 분석 통합)"""

import os
import re
from pathlib import Path
from typing import Dict, Any
from langchain_core.tools import tool
from langgraph.config import get_stream_writer

try:
    import requests
except ImportError:
    pass

from ..config import settings, ModelProvider
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


def _get_mime_type(path_or_url: str) -> str:
    """파일 경로 또는 URL에서 MIME 타입 추출"""
    ext = Path(path_or_url.split('?')[0]).suffix.lower()
    return {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".gif": "image/gif",
        ".webp": "image/webp",
    }.get(ext, "image/jpeg")


def _analyze_with_gemini(image_source: str, image_url: str, search_results: str) -> str:
    """Gemini API로 이미지 + Google Lens 검색 결과를 종합 분석
    (vLLM/Qwen 등 이미지를 직접 볼 수 없는 모델용)

    Args:
        image_source: 원본 이미지 소스 (로컬 경로 또는 URL)
        image_url: 업로드된 공개 이미지 URL
        search_results: Google Lens 검색 결과 텍스트
    """
    api_key = settings.google_api_key
    if not api_key:
        return f"[Gemini API 키 미설정 - 원본 검색 결과]\n{search_results}"

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-3-flash-preview')

        # 이미지 준비 (로컬 파일이면 직접 읽기, URL이면 다운로드)
        if os.path.exists(image_source):
            with open(image_source, 'rb') as f:
                image_data = f.read()
            mime_type = _get_mime_type(image_source)
        else:
            resp = requests.get(image_url, timeout=15)
            resp.raise_for_status()
            image_data = resp.content
            mime_type = resp.headers.get('Content-Type', 'image/jpeg').split(';')[0]

        image_part = {"mime_type": mime_type, "data": image_data}

        prompt = f"""당신은 음식 이미지 분석 전문가입니다.
이미지를 보고 Google Lens 검색 결과와 비교하여, 어느 식당의 어떤 메뉴인지 후보를 분석해주세요.

[검색 결과]
{search_results}

분석 방법:
1. 검색 결과에 여러 식당/메뉴가 있으면 가능성 순으로 후보를 모두 제시하세요
2. 블로그 후기에서 해당 메뉴의 맛 평가, 추천 포인트, 관련 음식 정보가 있으면 포함

작성 규칙:
- URL은 포함하지 마세요
- 검색 결과에 없는 내용을 추측하지 마세요
- 보기 좋게 이모지와 볼드체를 활용해 포맷팅"""

        response = model.generate_content([image_part, prompt])
        return response.text

    except Exception as e:
        return f"[Gemini 분석 실패: {e}]\n{search_results}"


def _is_gemini_agent() -> bool:
    """현재 에이전트가 Gemini 모델인지 확인"""
    return settings.model_provider in (ModelProvider.GEMINI, "gemini")


@tool
def search_food_by_image(image_source: str) -> str:
    """
    새로운 음식 이미지가 있을 때만 사용하세요.
    이미지 URL 또는 로컬 파일 경로를 받아 Google Lens로 검색합니다.

    Args:
        image_source: 이미지 URL 또는 로컬 파일 경로 (필수)

    Returns:
        Google Lens 검색 결과 (음식 이름, 식당, 메뉴, 썸네일 등)
    """
    writer = get_stream_writer()

    if not image_source or not image_source.strip():
        return "[이미지 없음] 이 도구는 새 이미지가 있을 때만 사용하세요."

    image_source = image_source.strip()

    if not image_source.startswith(('http://', 'https://', '/')):
        return "[이미지 없음] 유효한 이미지 경로가 아닙니다."

    if not image_source.startswith(('http://', 'https://')) and not os.path.exists(image_source):
        return f"[이미지 없음] 파일을 찾을 수 없습니다: {image_source}"

    searcher = get_searcher()

    # 1. 이미지 업로드
    writer({"tool": "search_food_by_image", "status": "이미지 분석 중..."})
    image_url = searcher.get_image_url(image_source)
    if not image_url:
        return f"이미지를 업로드할 수 없습니다: {image_source}"

    # 2. Google Lens 검색
    result = searcher.search_with_combined(image_url)

    if "error" in result:
        return f"검색 실패: {result['error']}"

    # 3. 검색 결과를 텍스트로 정리
    raw_parts = []
    blog_links = []
    thumbnails_with_titles = []  # (url, title) 쌍으로 저장

    visual = result.get("visual_matches", [])
    all_thumbnails = []  # (thumbnail_url, 검색결과번호, 우선순위) 수집

    if visual:
        raw_parts.append("[Google Lens 검색 결과]")
        for i, v in enumerate(visual[:10], 1):
            title = v.get("title", "")
            snippet = v.get("snippet", "")
            link = v.get("link", "")
            thumbnail = v.get("thumbnail", "") or v.get("thumbnailUrl", "")

            line_parts = []
            if title:
                line_parts.append(title)
            if snippet:
                line_parts.append(snippet[:100])
            if line_parts:
                raw_parts.append(f"{i}. {' - '.join(line_parts)}")

            is_blog = link and ('blog.naver.com' in link or 'tistory.com' in link)
            is_korean = any(kw in (title + snippet) for kw in ['맛집', '메뉴', '후기', '리뷰', '식당', '피자', '치킨', '고기', '국수', '카페'])

            if thumbnail:
                # 블로그 > 한국어 음식 키워드 > 기타 순 우선순위
                priority = 0 if is_blog else (1 if is_korean else 2)
                all_thumbnails.append((thumbnail, str(i), priority))

            if is_blog:
                blog_links.append(link)

        # 우선순위 정렬 후 상위 5개 선택
        all_thumbnails.sort(key=lambda x: x[2])
        thumbnails_with_titles = [(url, num) for url, num, _ in all_thumbnails[:5]]

    if blog_links:
        raw_parts.append("\n[블로그 본문]")
        for i, link in enumerate(blog_links[:3], 1):
            blog_data = extract_blog_content(link)
            if blog_data["content"]:
                raw_parts.append(f"--- 블로그 {i} ---")
                raw_parts.append(blog_data["content"][:1000])

    texts = result.get("text", [])
    if texts:
        text_list = [t.get("text", "") for t in texts[:5] if t.get("text")]
        if text_list:
            raw_parts.append(f"\n[이미지 내 텍스트] {', '.join(text_list)}")

    search_text = "\n".join(raw_parts)

    # 4. 모델에 따라 분기
    if _is_gemini_agent():
        # Gemini 에이전트: 이미지를 직접 볼 수 있으므로 검색 결과만 전달
        output = search_text
    else:
        # vLLM/Qwen 등: 이미지를 볼 수 없으므로 Gemini API로 별도 분석
        writer({"tool": "search_food_by_image", "status": "결과 정리 중..."})
        output = _analyze_with_gemini(image_source, image_url, search_text)

    # 5. 썸네일 URL을 검색결과 번호와 함께 추가
    # AI가 위의 검색결과 목록(제목/snippet/블로그 본문)을 보고 식당 매칭
    if thumbnails_with_titles:
        output += "\n\n[검색 결과 썸네일 - 위 검색결과 번호에 대응]"
        for url, num in thumbnails_with_titles:
            output += f"\n[THUMBNAIL:{url}|#{num}]"

    return output if output else "검색 결과 없음"
