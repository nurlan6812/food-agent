"""이미지 검색 도구 - Serper.dev + Playwright 카카오맵 연동

1. 이미지 → Serper Google Lens → 식당명 추출
2. 식당명 → 카카오맵 API → place_id 획득
3. place_id → Playwright 카카오맵 크롤링 → 메뉴/가격 전체 추출
"""

import os
import re
import base64
import asyncio

# 환경 변수 로드 (모듈 임포트 시 자동 로드)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from collections import Counter
from langchain_core.tools import tool

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

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class SerperImageSearcher:
    """Serper.dev를 활용한 이미지 검색기

    Google Lens + 텍스트 검색 지원
    로컬 파일도 지원 (임시 업로드)
    SerpAPI 대비 15배 저렴, 무료 2,500회/월
    """

    def __init__(self, api_key: Optional[str] = None):
        self.serper_key = api_key or os.getenv("SERPER_API_KEY")
        self.serpapi_key = os.getenv("SERPAPI_KEY")
        self.api_key = self.serper_key  # 텍스트 검색용
        self.lens_url = "https://google.serper.dev/lens"
        self.search_url = "https://google.serper.dev/search"
        self.serpapi_url = "https://serpapi.com/search"

    def _apply_exif_orientation(self, file_path: str) -> str:
        """
        EXIF orientation을 적용한 이미지를 임시 파일로 저장

        Args:
            file_path: 원본 이미지 경로

        Returns:
            회전 적용된 이미지 경로 (임시 파일 또는 원본)
        """
        try:
            from PIL import Image, ExifTags

            img = Image.open(file_path)

            # EXIF orientation 찾기
            orientation_key = None
            for key in ExifTags.TAGS.keys():
                if ExifTags.TAGS[key] == 'Orientation':
                    orientation_key = key
                    break

            exif = img._getexif()
            if exif and orientation_key and orientation_key in exif:
                orientation = exif[orientation_key]

                # 회전 필요한 경우만 처리
                if orientation == 3:
                    img = img.rotate(180, expand=True)
                elif orientation == 6:
                    img = img.rotate(270, expand=True)
                elif orientation == 8:
                    img = img.rotate(90, expand=True)
                else:
                    return file_path  # 회전 불필요

                # 캐시 무효화: 픽셀 하나 수정 (호스팅 서비스 캐시 방지)
                import random
                pixels = img.load()
                x, y = img.width - 1, img.height - 1
                r, g, b = pixels[x, y][:3] if len(pixels[x, y]) >= 3 else (pixels[x, y], pixels[x, y], pixels[x, y])
                pixels[x, y] = (r, g, (b + random.randint(1, 5)) % 256)

                # 임시 파일로 저장
                import tempfile
                temp_file = tempfile.NamedTemporaryFile(suffix='.jpeg', delete=False)
                img.save(temp_file.name, format='JPEG', quality=90)
                print(f"📐 EXIF 회전 적용됨 (orientation={orientation})")
                return temp_file.name

        except Exception as e:
            print(f"  - EXIF 처리 실패: {e}")

        return file_path

    def upload_image(self, file_path: str) -> Optional[str]:
        """
        로컬 이미지를 임시 호스팅 서비스에 업로드

        Args:
            file_path: 로컬 이미지 파일 경로

        Returns:
            업로드된 이미지의 공개 URL (실패시 None)
        """
        if not os.path.exists(file_path):
            return None

        # EXIF orientation 적용
        file_path = self._apply_exif_orientation(file_path)

        # 여러 서비스 순차 시도 (litterbox 우선 - 캐시 없음)
        upload_services = [
            self._upload_to_litterbox,
            self._upload_to_imgbb,
            self._upload_to_freeimage,
        ]

        for upload_func in upload_services:
            try:
                url = upload_func(file_path)
                if url:
                    return url
            except Exception as e:
                print(f"  - {upload_func.__name__} 실패: {e}")
                continue

        return None

    def _upload_to_imgbb(self, file_path: str) -> Optional[str]:
        """imgbb.com에 업로드 (무료, 빠름)"""
        with open(file_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode()

        # 공개 API 엔드포인트 (API 키 없이 사용)
        response = requests.post(
            'https://api.imgbb.com/1/upload',
            data={
                'key': 'da2d77ea2fc52e04d4e62a6d3906f48f',  # 공개 데모 키
                'image': image_data,
                'expiration': 600,  # 10분 후 만료
            },
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data['data']['url']
        return None

    def _upload_to_freeimage(self, file_path: str) -> Optional[str]:
        """freeimage.host에 업로드"""
        with open(file_path, 'rb') as f:
            response = requests.post(
                'https://freeimage.host/api/1/upload',
                data={'key': '6d207e02198a847aa98d0a2a901485a5'},  # 공개 API 키
                files={'source': f},
                timeout=30
            )

        if response.status_code == 200:
            data = response.json()
            if data.get('status_code') == 200:
                return data['image']['url']
        return None

    def _upload_to_litterbox(self, file_path: str) -> Optional[str]:
        """litterbox.catbox.moe에 업로드 (임시 파일용)"""
        with open(file_path, 'rb') as f:
            response = requests.post(
                'https://litterbox.catbox.moe/resources/internals/api.php',
                data={'reqtype': 'fileupload', 'time': '1h'},
                files={'fileToUpload': f},
                timeout=60
            )

        if response.status_code == 200:
            url = response.text.strip()
            if url.startswith('http'):
                return url
        return None

    def is_local_file(self, path: str) -> bool:
        """경로가 로컬 파일인지 확인"""
        return os.path.exists(path) or (
            not path.startswith('http://') and
            not path.startswith('https://') and
            Path(path).suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        )

    def get_image_url(self, image_source: str) -> Optional[str]:
        """
        이미지 소스(URL 또는 로컬 경로)에서 공개 URL 획득

        Args:
            image_source: 이미지 URL 또는 로컬 파일 경로

        Returns:
            공개 접근 가능한 이미지 URL
        """
        # 이미 URL인 경우
        if image_source.startswith('http://') or image_source.startswith('https://'):
            return image_source

        # 로컬 파일인 경우 업로드
        if os.path.exists(image_source):
            print(f"📤 로컬 파일 업로드 중: {image_source}")
            uploaded_url = self.upload_image(image_source)
            if uploaded_url:
                print(f"✅ 업로드 완료: {uploaded_url}")
                return uploaded_url
            else:
                print("❌ 업로드 실패")

        return None

    def search_with_lens(self, image_url: str) -> Dict[str, Any]:
        """
        Google Lens로 이미지 검색 (SerpAPI 우선, Serper 폴백)

        Args:
            image_url: 검색할 이미지의 공개 URL

        Returns:
            검색 결과 딕셔너리
        """
        if not REQUESTS_AVAILABLE:
            return {"error": "requests 라이브러리가 설치되지 않았습니다."}

        # 1. SerpAPI 시도 (우선)
        if self.serpapi_key:
            try:
                params = {
                    "engine": "google_lens",
                    "url": image_url,
                    "api_key": self.serpapi_key,
                    "hl": "ko",
                    "country": "kr"
                }
                response = requests.get(self.serpapi_url, params=params, timeout=30)
                response.raise_for_status()
                result = response.json()

                # SerpAPI 형식 변환
                visual_matches = result.get("visual_matches", [])
                if visual_matches:
                    return {
                        "visual_matches": visual_matches,
                        "text": result.get("text_results", []),
                        "knowledge_graph": result.get("knowledge_graph", {})
                    }
            except Exception as e:
                print(f"SerpAPI 실패, Serper로 폴백: {e}")

        # 2. Serper 폴백
        if not self.serper_key:
            return {"error": "API 키가 설정되지 않았습니다. SERPAPI_KEY 또는 SERPER_API_KEY를 .env에 추가해주세요."}

        headers = {
            "X-API-KEY": self.serper_key,
            "Content-Type": "application/json"
        }
        data = {
            "url": image_url,
            "gl": "kr",
            "hl": "ko"
        }

        try:
            response = requests.post(self.lens_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()

            return {
                "visual_matches": result.get("organic", []),
                "text": [],
                "knowledge_graph": {}
            }
        except requests.Timeout:
            return {"error": "API 요청 시간 초과 (30초)"}
        except requests.RequestException as e:
            return {"error": f"API 요청 실패: {str(e)}"}

    def search_reverse_image(self, image_url: str) -> Dict[str, Any]:
        """
        Serper는 reverse image를 lens로 통합 제공
        lens 결과 반환
        """
        return self.search_with_lens(image_url)

    def search_with_combined(self, image_url: str) -> Dict[str, Any]:
        """
        여러 검색 방법을 조합하여 최상의 결과 반환

        순서: Google Lens → Reverse Image → (결과 병합)
        """
        results = {
            "lens": None,
            "reverse": None,
            "combined": True
        }

        # 1. Google Lens 시도
        lens_result = self.search_with_lens(image_url)
        if "error" not in lens_result:
            results["lens"] = lens_result

        # 2. Reverse Image 시도
        reverse_result = self.search_reverse_image(image_url)
        if "error" not in reverse_result:
            results["reverse"] = reverse_result

        # 3. 결과 병합
        if results["lens"] or results["reverse"]:
            return self._merge_results(results["lens"], results["reverse"])

        return {"error": "Google Lens와 Reverse Image 모두 결과를 찾지 못했습니다."}

    def fetch_page_content(self, url: str) -> Optional[str]:
        """
        검색 결과 링크의 실제 페이지 내용을 가져옴
        네이버 블로그는 모바일 버전으로 변환하여 접근
        """
        import re

        # 네이버 블로그 -> 모바일 버전으로 변환
        if 'blog.naver.com' in url:
            url = url.replace('blog.naver.com', 'm.blog.naver.com')

        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return None

            # HTML에서 텍스트 추출
            text = response.text
            text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', ' ', text)
            text = ' '.join(text.split())

            return text[:5000]  # 앞부분만
        except:
            return None

    def extract_menu_from_page(self, page_text: str) -> List[str]:
        """
        페이지 텍스트에서 메뉴명 후보 추출
        """
        import re

        # 가격 패턴 주변의 메뉴명 찾기
        menu_with_price = re.findall(r'([가-힣a-zA-Z\s]{2,20})\s*[\d,]+원', page_text)

        # "~라는 음식", "~를 주문" 등의 패턴
        menu_patterns = [
            r'([가-힣]{2,15})(?:라는|라고 하는)\s*(?:음식|메뉴)',
            r'([가-힣]{2,15})(?:를|을)\s*(?:주문|시켰|먹었)',
            r'주문[:\s]*([가-힣]{2,15})',
        ]

        menus = list(menu_with_price)
        for pattern in menu_patterns:
            matches = re.findall(pattern, page_text)
            menus.extend(matches)

        # 중복 제거 및 정리
        cleaned = []
        for m in menus:
            m = m.strip()
            if len(m) >= 2 and m not in cleaned:
                # 일반 단어 제외
                if m not in ['맛있는', '정말', '진짜', '오늘', '여기', '이번', '다음']:
                    cleaned.append(m)

        return cleaned[:10]

    def search_text(self, query: str) -> Dict[str, Any]:
        """
        Serper 텍스트 검색으로 추가 정보 획득
        """
        if not self.api_key:
            return {"error": "SERPER_API_KEY가 설정되지 않았습니다."}

        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        data = {
            "q": query,
            "gl": "kr",
            "hl": "ko"
        }

        try:
            response = requests.post(self.search_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()

            # Serper 형식을 기존 형식으로 변환
            return {
                "organic_results": result.get("organic", []),
                "answer_box": result.get("answerBox", {})
            }
        except requests.RequestException as e:
            return {"error": f"API 요청 실패: {str(e)}"}

    def get_menu_price_info(self, brand: str, menu: str) -> Optional[Dict[str, Any]]:
        """
        브랜드와 메뉴명으로 가격/메타 정보 검색
        """
        import re

        query = f"{brand} {menu} 가격 메뉴"
        result = self.search_text(query)

        if "error" in result:
            return None

        info = {
            "prices": [],
            "menu_items": [],
            "calories": None,
            "description": None
        }

        # Organic Results에서 가격 정보 추출
        organic = result.get("organic_results", [])
        for item in organic[:5]:
            snippet = item.get("snippet", "")
            title = item.get("title", "")
            text = f"{title} {snippet}"

            # 가격 패턴
            price_matches = re.findall(r'(\d{1,2}[,.]?\d{3})\s*원', text)
            for price in price_matches:
                price_str = f"{price}원"
                if price_str not in info["prices"]:
                    info["prices"].append(price_str)

            # 칼로리 패턴
            cal_match = re.search(r'(\d+)\s*(?:kcal|칼로리)', text, re.I)
            if cal_match and not info["calories"]:
                info["calories"] = f"{cal_match.group(1)}kcal"

        # Answer Box가 있으면 활용
        answer_box = result.get("answer_box", {})
        if answer_box:
            info["description"] = answer_box.get("snippet") or answer_box.get("answer")

        return info if info["prices"] or info["calories"] else None

    def _merge_results(self, lens: Optional[Dict], reverse: Optional[Dict]) -> Dict[str, Any]:
        """두 검색 결과를 병합"""
        merged = {
            "knowledge_graph": {},
            "visual_matches": [],
            "text": [],
            "related_searches": [],
            "image_results": []
        }

        if lens:
            merged["knowledge_graph"] = lens.get("knowledge_graph", {})
            merged["visual_matches"] = lens.get("visual_matches", [])
            merged["text"] = lens.get("text", [])
            merged["related_searches"] = lens.get("related_searches", [])

        if reverse:
            # Reverse Image 결과 추가
            merged["image_results"] = reverse.get("image_results", [])
            if not merged["knowledge_graph"]:
                merged["knowledge_graph"] = reverse.get("knowledge_graph", {})

        return merged

    def extract_food_info(self, lens_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Google Lens 결과에서 음식 정보 추출

        Returns:
            {
                "identified": str,        # 인식된 음식명
                "brand": str,             # 브랜드/가게명
                "menu_name": str,         # 정확한 메뉴명
                "price": str,             # 가격 정보
                "description": str,       # 설명
                "related_results": list,  # 관련 검색 결과
                "text_in_image": list,    # 이미지 내 텍스트
                "keywords": list,         # 관련 키워드
            }
        """
        if "error" in lens_result:
            return {"error": lens_result["error"]}

        extracted = {
            "identified": None,
            "brand": None,
            "menu_name": None,
            "price": None,
            "description": None,
            "related_results": [],
            "text_in_image": [],
            "keywords": [],
            "sources": [],
            "raw_titles": []  # 메뉴명 추출용
        }

        # 1. Knowledge Graph (가장 정확한 정보)
        kg = lens_result.get("knowledge_graph", {})
        if kg:
            extracted["identified"] = kg.get("title")
            extracted["description"] = kg.get("description")

        # 2. Visual Matches (유사 이미지 매칭)
        visual_matches = lens_result.get("visual_matches", [])
        for match in visual_matches[:10]:
            title = match.get("title", "")
            extracted["related_results"].append({
                "title": title,
                "source": match.get("source", ""),
                "link": match.get("link", ""),
                "snippet": match.get("snippet", "")
            })
            if title:
                extracted["raw_titles"].append(title)
            if match.get("source"):
                extracted["sources"].append(match.get("source"))

        # 3. Image Results (Reverse Image에서)
        image_results = lens_result.get("image_results", [])
        for img in image_results[:5]:
            title = img.get("title", "")
            extracted["related_results"].append({
                "title": title,
                "source": img.get("source", ""),
                "link": img.get("link", ""),
                "snippet": img.get("snippet", "")
            })
            if title:
                extracted["raw_titles"].append(title)

        # 4. 이미지 내 텍스트
        text_results = lens_result.get("text", [])
        for text_item in text_results[:5]:
            if text_item.get("text"):
                extracted["text_in_image"].append(text_item["text"])

        # 5. 관련 검색어
        related_searches = lens_result.get("related_searches", [])
        for search in related_searches[:5]:
            if search.get("query"):
                extracted["keywords"].append(search["query"])

        # 6. 브랜드/메뉴명/가격 추출
        self._extract_detailed_info(extracted)

        return extracted

    def _extract_detailed_info(self, extracted: Dict[str, Any]):
        """
        검색 결과에서 가격 정보만 추출
        브랜드/메뉴 분석은 LLM에게 맡김
        """
        import re

        all_text = " ".join(extracted["raw_titles"] + extracted["text_in_image"] + extracted["keywords"])

        # 가격 추출 (숫자+원 패턴)
        price_matches = re.findall(r'(\d{1,3}[,.]?\d{3})\s*원', all_text)
        if price_matches:
            # 중복 제거
            unique_prices = list(dict.fromkeys(price_matches))
            extracted["price"] = ", ".join([f"{p}원" for p in unique_prices[:3]])

    def format_result(self, extracted: Dict[str, Any]) -> str:
        """추출된 정보를 읽기 좋은 형식으로 포맷 (LLM 해석용)"""
        if "error" in extracted:
            return f"❌ 오류: {extracted['error']}"

        parts = []

        # Knowledge Graph 인식 결과
        if extracted.get("identified"):
            parts.append(f"📌 Google 인식: {extracted['identified']}")

        if extracted.get("description"):
            parts.append(f"📝 설명: {extracted['description']}")

        # 관련 검색 결과 (핵심 정보 - LLM이 해석)
        if extracted.get("related_results"):
            parts.append("\n🔍 검색 결과 (브랜드/메뉴 정보 포함):")
            for i, result in enumerate(extracted["related_results"][:7], 1):
                title = result.get("title", "")
                source = result.get("source", "")
                if title:
                    line = f"  {i}. {title}"
                    if source:
                        line += f" [{source}]"
                    parts.append(line)

        # 이미지 내 텍스트 (간판, 메뉴판 등)
        if extracted.get("text_in_image"):
            texts = ", ".join(extracted["text_in_image"])
            parts.append(f"\n📄 이미지 텍스트: {texts}")

        # 관련 키워드
        if extracted.get("keywords"):
            keywords = ", ".join(extracted["keywords"][:5])
            parts.append(f"\n🏷️ 키워드: {keywords}")

        # 가격 정보 (있으면)
        if extracted.get("price"):
            parts.append(f"\n💰 검색된 가격: {extracted['price']}")

        if parts:
            return "\n".join(parts)

        return "이미지에서 관련 정보를 찾지 못했습니다."


class KakaoLocalAPI:
    """카카오 로컬 API를 활용한 식당 정보 검색"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("KAKAO_API_KEY")
        self.base_url = "https://dapi.kakao.com/v2/local/search/keyword.json"

    def search_restaurant(self, query: str) -> Optional[Dict[str, Any]]:
        """
        식당명으로 카카오 로컬 검색
        """
        if not self.api_key:
            return None

        headers = {"Authorization": f"KakaoAK {self.api_key}"}
        params = {
            "query": query,
            "category_group_code": "FD6",  # 음식점
            "size": 5
        }

        try:
            response = requests.get(self.base_url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None

    def get_place_id_from_url(self, place_url: str) -> Optional[str]:
        """place_url에서 place_id 추출"""
        match = re.search(r'/(\d+)$', place_url)
        return match.group(1) if match else None

    def get_menu_from_place(self, place_id: str) -> List[Dict[str, str]]:
        """
        카카오맵 place에서 메뉴 정보 가져오기
        내부 API 엔드포인트 활용
        """
        menus = []

        # 카카오맵 내부 API 엔드포인트들 시도
        endpoints = [
            f"https://place.map.kakao.com/main/v/{place_id}",
            f"https://place.map.kakao.com/m/main/v/{place_id}",
        ]

        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
            "Accept": "application/json",
        }

        for endpoint in endpoints:
            try:
                response = requests.get(endpoint, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()

                    # menuInfo 찾기 (JSON 구조에서)
                    menu_info = self._find_menu_in_json(data)
                    if menu_info:
                        return menu_info
            except:
                continue

        # JSON API 실패시 HTML 페이지에서 추출 시도
        return self._scrape_menu_from_page(place_id)

    def _find_menu_in_json(self, data: Dict, depth: int = 0) -> List[Dict[str, str]]:
        """JSON 데이터에서 메뉴 정보 재귀 탐색"""
        if depth > 10:
            return []

        menus = []

        if isinstance(data, dict):
            # menuInfo 키가 있으면 파싱
            if "menuInfo" in data:
                menu_list = data["menuInfo"]
                if isinstance(menu_list, list):
                    for item in menu_list:
                        if isinstance(item, dict):
                            name = item.get("menu") or item.get("name") or item.get("menuName", "")
                            price = item.get("price") or item.get("menuPrice", "")
                            if name:
                                menus.append({"name": str(name), "price": str(price)})
                return menus

            # menu 키
            if "menu" in data and isinstance(data["menu"], list):
                for item in data["menu"]:
                    if isinstance(item, dict):
                        name = item.get("name") or item.get("menu", "")
                        price = item.get("price", "")
                        if name:
                            menus.append({"name": str(name), "price": str(price)})
                return menus

            # 재귀 탐색
            for key, value in data.items():
                result = self._find_menu_in_json(value, depth + 1)
                if result:
                    return result

        elif isinstance(data, list):
            for item in data:
                result = self._find_menu_in_json(item, depth + 1)
                if result:
                    return result

        return menus

    def _scrape_menu_from_page(self, place_id: str) -> List[Dict[str, str]]:
        """HTML 페이지에서 메뉴 추출 (폴백)"""
        menus = []

        try:
            url = f"https://place.map.kakao.com/{place_id}"
            headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code != 200:
                return menus

            text = response.text

            # JSON 임베딩 데이터에서 메뉴 찾기
            json_patterns = [
                r'"menuInfo"\s*:\s*(\[[^\]]*\])',
                r'"menu"\s*:\s*(\[[^\]]*\])',
            ]

            for pattern in json_patterns:
                match = re.search(pattern, text, re.DOTALL)
                if match:
                    try:
                        import json
                        menu_data = json.loads(match.group(1))
                        for item in menu_data:
                            if isinstance(item, dict):
                                name = item.get("menu") or item.get("name", "")
                                price = item.get("price", "")
                                if name:
                                    menus.append({"name": name, "price": price})
                        if menus:
                            return menus
                    except:
                        pass

        except:
            pass

        return menus

    def search_menu_via_serper(self, query: str) -> str:
        """
        Serper.dev로 식당/메뉴 정보 가져오기 (빠른 버전)
        검색 결과 스니펫에서 메뉴/가격 정보만 추출 (블로그 크롤링 제거)
        """
        api_key = os.getenv("SERPER_API_KEY") or os.getenv("SERPAPI_KEY")
        if not api_key:
            return ""

        # LLM이 생성한 쿼리를 그대로 사용
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }
        data = {
            "q": query,
            "gl": "kr",
            "hl": "ko"
        }

        try:
            response = requests.post("https://google.serper.dev/search", headers=headers, json=data, timeout=10)
            if response.status_code != 200:
                return ""

            result = response.json()
            output = []

            # 검색 결과 스니펫에서 메뉴/가격 정보 추출
            for item in result.get("organic", [])[:5]:
                title = item.get("title", "")
                snippet = item.get("snippet", "")

                if snippet:
                    output.append(f"{title}: {snippet}")

            return "\n".join(output)
        except:
            return ""

    def get_menu_via_playwright(self, place_id: str) -> str:
        """
        Playwright로 카카오맵에서 메뉴 텍스트 크롤링
        LLM이 직접 해석하도록 텍스트 반환
        """
        if not PLAYWRIGHT_AVAILABLE:
            return ""

        async def _fetch_menu():
            menu_text = ""
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(
                        headless=True,
                        args=['--no-sandbox', '--disable-dev-shm-usage']
                    )
                    page = await browser.new_page()

                    url = f'https://place.map.kakao.com/{place_id}'
                    await page.goto(url, wait_until='networkidle', timeout=15000)

                    # 메뉴 탭 클릭
                    try:
                        menu_tab = await page.query_selector('a[href*="menuInfo"]')
                        if menu_tab:
                            await menu_tab.click()
                            await page.wait_for_timeout(2000)
                    except:
                        pass

                    # 스크롤
                    for _ in range(5):
                        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                        await page.wait_for_timeout(400)

                    # 가격 요소의 조부모에서 메뉴 추출
                    price_elements = await page.query_selector_all('//*[contains(text(), "원")]')
                    menu_lines = []
                    seen = set()

                    for price_el in price_elements:
                        try:
                            # 조부모 요소 (메뉴명+가격 포함)
                            grandparent = await price_el.evaluate_handle('el => el.parentElement?.parentElement')
                            if grandparent:
                                text = await grandparent.inner_text()
                                text = ' '.join(text.split())
                                # 유효한 메뉴 항목인지 확인
                                if ('원' in text and
                                    len(text) > 5 and
                                    len(text) < 80 and
                                    text not in seen and
                                    '블로그' not in text):
                                    seen.add(text)
                                    menu_lines.append(text)
                        except:
                            pass

                    menu_text = '\n'.join(menu_lines[:60])  # 최대 60개
                    await browser.close()

            except Exception as e:
                print(f"Playwright 크롤링 실패: {e}")

            return menu_text

        # 동기 실행
        try:
            return asyncio.run(_fetch_menu())
        except:
            try:
                import nest_asyncio
                nest_asyncio.apply()
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(_fetch_menu())
            except:
                return ""

    def get_reviews_via_playwright(self, place_id: str, max_reviews: int = 15) -> str:
        """
        Playwright로 카카오맵에서 후기 크롤링
        평점, 태그별 평가, 개별 후기를 구조화하여 반환
        """
        if not PLAYWRIGHT_AVAILABLE:
            return ""

        async def _fetch_reviews():
            result = {
                "rating": None,
                "review_count": 0,
                "tags": {},
                "reviews": []
            }

            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(
                        headless=True,
                        args=['--no-sandbox', '--disable-dev-shm-usage']
                    )
                    page = await browser.new_page()

                    url = f'https://place.map.kakao.com/{place_id}'
                    await page.goto(url, wait_until='networkidle', timeout=15000)

                    # 후기 탭 클릭
                    all_elements = await page.query_selector_all('a, button, span')
                    tab_clicked = False

                    for el in all_elements:
                        try:
                            text = await el.inner_text()
                            text = text.strip()
                            if '후기' in text and ('개' in text or '건' in text) and len(text) < 30:
                                await el.click()
                                await page.wait_for_timeout(2000)
                                tab_clicked = True
                                break
                        except:
                            continue

                    # 후기 탭이 없으면 블로그 리뷰로 폴백
                    is_blog_fallback = False
                    if not tab_clicked:
                        blog_tab = await page.query_selector('a[href*="blog"]')
                        if blog_tab:
                            await blog_tab.click()
                            await page.wait_for_timeout(2000)
                            is_blog_fallback = True
                        else:
                            await browser.close()
                            return "매장주 요청으로 후기가 제공되지 않는 장소입니다."

                    # 스크롤하여 후기 로드
                    for _ in range(5):
                        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                        await page.wait_for_timeout(400)

                    # 페이지 텍스트 파싱
                    body_text = await page.inner_text('body')
                    lines = [l.strip() for l in body_text.split('\n') if l.strip()]

                    # 평점과 후기 수 추출
                    for i, line in enumerate(lines):
                        if line == '별점' and i + 1 < len(lines):
                            try:
                                result["rating"] = float(lines[i + 1])
                            except:
                                pass
                        if '후기' in line and i + 1 < len(lines):
                            try:
                                count = int(lines[i + 1].replace(',', ''))
                                if count > result["review_count"]:
                                    result["review_count"] = count
                            except:
                                pass

                    # 태그별 평가 추출 (맛 245명, 가성비 137명 등)
                    tag_names = ['맛', '가성비', '친절', '분위기', '주차', '청결', '양']
                    for i, line in enumerate(lines):
                        if line in tag_names and i + 1 < len(lines):
                            next_line = lines[i + 1]
                            if '명' in next_line:
                                try:
                                    count = int(next_line.replace('명', '').replace(',', ''))
                                    result["tags"][line] = count
                                except:
                                    pass

                    # 개별 후기 추출
                    reviews = []
                    seen = set()
                    review_keywords = ['맛있', '좋', '추천', '또', '최고', '아쉬', '별로', '짜',
                                      '친절', '불친절', '웨이팅', '기다', '양이', '가성비',
                                      '재방문', '단골', '인정', '대박', '실망', '만족', '냄새']

                    for line in lines:
                        if 15 < len(line) < 300 and line not in seen:
                            if line.startswith('http') or '원' in line[:8]:
                                continue
                            if any(skip in line for skip in ['더보기', '접기', '신고', '공유', '저장', '로그인', '바로가기']):
                                continue
                            if any(kw in line for kw in review_keywords):
                                seen.add(line)
                                reviews.append(line)
                                if len(reviews) >= max_reviews:
                                    break

                    result["reviews"] = reviews
                    result["is_blog"] = is_blog_fallback
                    await browser.close()

            except Exception as e:
                print(f"후기 크롤링 실패: {e}")
                return f"후기 크롤링 실패: {e}"

            # 결과 포맷팅
            output = []

            if result["rating"]:
                output.append(f"⭐ 평점: {result['rating']}점")
            if result["review_count"]:
                output.append(f"📝 후기: {result['review_count']}개")

            if result["tags"]:
                output.append("")
                output.append("[태그별 평가]")
                for tag, count in sorted(result["tags"].items(), key=lambda x: -x[1]):
                    output.append(f"  • {tag}: {count}명")

            if result["reviews"]:
                output.append("")
                output.append(f"[최근 후기 {len(result['reviews'])}개]")
                for r in result["reviews"]:
                    output.append(f"  • {r}")

            return '\n'.join(output) if output else "후기를 찾을 수 없습니다."

        # 동기 실행
        try:
            return asyncio.run(_fetch_reviews())
        except:
            try:
                import nest_asyncio
                nest_asyncio.apply()
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(_fetch_reviews())
            except:
                return ""

    def _crawl_blog_menu(self, blog_url: str) -> str:
        """
        블로그에서 메뉴/가격 정보 크롤링
        네이버 블로그, 티스토리 지원 (폴백용)
        """
        try:
            # 네이버 블로그 모바일 버전으로 변환
            if "blog.naver.com" in blog_url and "m.blog" not in blog_url:
                blog_url = blog_url.replace("blog.naver.com", "m.blog.naver.com")

            headers = {
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
                "Accept-Encoding": "gzip, deflate",
            }

            resp = requests.get(blog_url, headers=headers, timeout=10)
            if resp.status_code != 200:
                return ""

            text = resp.text

            # 여러 가격 패턴 시도
            patterns = [
                r'([가-힣]+(?:\s*[가-힣]+)*)\s*[:\-\s]*([\d,]+)\s*원',  # 메뉴: 가격원
                r'([가-힣]{2,12})\s+([\d]{1,2}[,.]?\d{3})\s*원?',  # 메뉴 가격
                r'([가-힣]{2,12}감자튀김|[가-힣]{2,12}볶음밥|[가-힣]{2,12}토핑)\s*([\d,]+)',  # 특정 메뉴 패턴
            ]

            menu_items = []
            seen = set()
            exclude = ['평균', '이용', '최소', '배달', '주문', '결제', '합계', '총', '할인', '인분', '가격', '원가']

            for pattern in patterns:
                prices = re.findall(pattern, text)
                for name, price in prices:
                    name = name.strip()
                    # 가격 정리 (콤마, 점 처리)
                    price = price.replace(',', '').replace('.', '')
                    if (len(name) >= 2 and
                        name not in seen and
                        not any(ex in name for ex in exclude) and
                        price.isdigit() and int(price) >= 1000):  # 1000원 이상만
                        seen.add(name)
                        price_formatted = f"{int(price):,}"
                        menu_items.append(f"  - {name}: {price_formatted}원")

            return "\n".join(menu_items[:15]) if menu_items else ""
        except:
            return ""

    def get_place_detail(self, place_url: str) -> Dict[str, Any]:
        """
        카카오맵 place_url에서 상세 정보 크롤링
        """
        info = {
            "name": None,
            "address": None,
            "phone": None,
            "menus": [],
            "hours": None
        }

        try:
            headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)"}
            response = requests.get(place_url, headers=headers, timeout=10)

            if response.status_code != 200:
                return info

            text = response.text

            # 메뉴 정보 추출 (JSON-LD 또는 HTML에서)
            # 카카오맵 페이지 구조에 맞게 파싱
            menu_pattern = r'"menuInfo":\s*\[(.*?)\]'
            menu_match = re.search(menu_pattern, text, re.DOTALL)
            if menu_match:
                menu_text = menu_match.group(1)
                # 메뉴명과 가격 추출
                items = re.findall(r'"menu":\s*"([^"]+)".*?"price":\s*"([^"]*)"', menu_text)
                for name, price in items:
                    info["menus"].append({"name": name, "price": price})

            # 메뉴 정보가 없으면 일반 텍스트에서 추출
            if not info["menus"]:
                # HTML 태그 제거
                clean_text = re.sub(r'<[^>]+>', ' ', text)
                clean_text = ' '.join(clean_text.split())

                # 가격 패턴으로 메뉴 찾기
                price_menus = re.findall(r'([가-힣]{2,15})\s*([\d,]+)\s*원', clean_text)
                for name, price in price_menus[:10]:
                    if name not in ['메뉴', '가격', '영업', '정보']:
                        info["menus"].append({"name": name, "price": f"{price}원"})

        except Exception as e:
            pass

        return info

    def extract_restaurant_name(self, titles: List[str]) -> Optional[str]:
        """
        검색 결과 제목들에서 식당명 추출
        - 여러 제목에서 공통으로 나오는 이름 우선
        """
        all_text = " ".join(titles)
        candidates = []

        # 1. 음식 종류가 포함된 식당명 (가장 신뢰도 높음)
        food_keywords = ['순대', '국밥', '우동', '교자', '떡볶이', '치킨', '피자', '칼국수', '냉면', '설렁탕', '곰탕', '삼겹살', '갈비']
        for kw in food_keywords:
            # "XXX순대", "XXX국밥" 등 패턴
            pattern = rf'([가-힣]{{2,10}}{kw}[가-힣]{{0,5}})'
            matches = re.findall(pattern, all_text)
            for m in matches:
                # 지점명만 있는 경우 제외
                if not re.match(r'^(본점|직영점|.+점)$', m):
                    candidates.append(m)

        # 2. 제목 시작 부분 (대괄호 뒤)
        for title in titles:
            bracket_match = re.search(r'\]\s*([가-힣a-zA-Z0-9]{3,15})', title)
            if bracket_match:
                name = bracket_match.group(1)
                if not re.match(r'^(본점|직영점|.+점)$', name):
                    candidates.append(name)

        # 3. "식당명 + 지점" 패턴에서 식당명만 추출
        branch_pattern = r'([가-힣]{2,10})\s*(?:본점|직영점|[가-힣]+점)'
        branch_matches = re.findall(branch_pattern, all_text)
        candidates.extend(branch_matches)

        # 일반 단어 제외
        exclude = ['맛집', '후기', '리뷰', '방문', '추천', '웨이팅', '우리집', '시청역',
                   '서울', '부산', '대전', '인천', '삼성동', '강남역', '메뉴', '가격',
                   '생방송', '오늘', '저녁', '명가', '유명', '바삭하니', '맛있겠다',
                   '본점', '직영점', '시청직영점']

        filtered = [c for c in candidates if c not in exclude and len(c) >= 3]

        if not filtered:
            return None

        # 빈도수 계산
        counter = Counter(filtered)

        # 여러 번 등장하는 것 우선
        for name, count in counter.most_common(10):
            if count >= 2:
                return name

        # 음식 키워드 포함된 것 우선
        for name, count in counter.most_common(5):
            if any(kw in name for kw in food_keywords):
                # 조사 제거
                name = re.sub(r'[을를이가의에서]$', '', name)
                return name

        result = counter.most_common(1)[0][0]
        # 조사 제거
        result = re.sub(r'[을를이가의에서]$', '', result)
        return result


# 전역 검색기 인스턴스
_searcher: Optional[SerperImageSearcher] = None
_kakao: Optional[KakaoLocalAPI] = None


def get_searcher() -> SerperImageSearcher:
    """검색기 싱글톤 인스턴스 반환"""
    global _searcher
    if _searcher is None:
        _searcher = SerperImageSearcher()
    return _searcher


def get_kakao() -> KakaoLocalAPI:
    """카카오 API 싱글톤 인스턴스 반환"""
    global _kakao
    if _kakao is None:
        _kakao = KakaoLocalAPI()
    return _kakao


def extract_blog_content(url: str) -> Dict[str, Any]:
    """
    블로그 페이지에서 음식 관련 본문 텍스트 추출
    특정 메뉴명을 하드코딩하지 않고 범용적으로 추출
    """
    result = {"url": url, "content": ""}

    try:
        # 네이버 블로그 모바일 버전으로 변환
        if 'blog.naver.com' in url and 'm.blog' not in url:
            url = url.replace('blog.naver.com', 'm.blog.naver.com')

        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return result

        text = response.text

        # HTML 태그 제거
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = ' '.join(text.split())

        # 음식/주문 관련 문장 추출 (범용 키워드)
        food_keywords = ['주문', '시켰', '먹었', '메뉴', '맛있', '바삭', '쫄깃', '토핑', '소스', '가격', '원']
        sentences = re.split(r'[.!?。]', text)

        relevant_sentences = []
        for sentence in sentences:
            if any(kw in sentence for kw in food_keywords):
                if 20 < len(sentence) < 200:  # 너무 짧거나 긴 문장 제외
                    relevant_sentences.append(sentence.strip())

        result["content"] = ' '.join(relevant_sentences[:10])  # 최대 10문장

    except Exception as e:
        pass

    return result


@tool
def search_food_by_image(image_source: str) -> str:
    """
    새로운 음식 이미지가 있을 때만 사용하세요.
    이미지 URL 또는 로컬 파일 경로를 받아 Google Lens로 검색합니다.

    주의: 이전 대화에서 이미 인식한 음식에 대해서는 이 도구를 다시 호출하지 마세요.
    후속 질문(식당 정보, 메뉴 가격 등)은 다른 도구를 사용하세요.

    Args:
        image_source: 이미지 URL 또는 로컬 파일 경로 (필수)

    Returns:
        Google 이미지 검색 결과 + 블로그 본문
    """
    # 이미지 경로 유효성 검사
    if not image_source or not image_source.strip():
        return "[이미지 없음] 이 도구는 새 이미지가 있을 때만 사용하세요. 이전 대화에서 파악한 정보를 활용해주세요."

    image_source = image_source.strip()

    # URL이 아니고 파일도 아닌 경우 (텍스트만 전달된 경우)
    if not image_source.startswith(('http://', 'https://', '/')):
        return "[이미지 없음] 유효한 이미지 경로가 아닙니다. 이전 대화에서 파악한 정보를 활용해주세요."

    # 로컬 파일인 경우 존재 여부 확인
    if not image_source.startswith(('http://', 'https://')) and not os.path.exists(image_source):
        return f"[이미지 없음] 파일을 찾을 수 없습니다: {image_source}. 이전 대화에서 파악한 정보를 활용해주세요."

    searcher = get_searcher()

    image_url = searcher.get_image_url(image_source)
    if not image_url:
        return f"이미지를 업로드할 수 없습니다: {image_source}"

    result = searcher.search_with_combined(image_url)

    if "error" in result:
        return f"검색 실패: {result['error']}"

    output = []
    blog_links = []

    # 검색 결과 (상위 10개) - title + link + thumbnail
    visual = result.get("visual_matches", [])
    thumbnails = []  # 썸네일 URL 수집

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

            # 썸네일 수집 (상위 3개)
            if thumbnail and len(thumbnails) < 3:
                thumbnails.append(thumbnail)

            # 블로그 링크 수집
            if link and ('blog.naver.com' in link or 'tistory.com' in link):
                blog_links.append(link)

    # 썸네일 이미지 URL 추가
    if thumbnails:
        output.append("\n[검색 결과 이미지]")
        for url in thumbnails:
            output.append(f"[IMAGE:{url}]")

    # 블로그 본문 추출 (상위 3개)
    if blog_links:
        output.append("\n[블로그 본문 (메뉴 판단 참고용)]")
        for i, link in enumerate(blog_links[:3], 1):
            blog_data = extract_blog_content(link)
            if blog_data["content"]:
                output.append(f"\n--- 블로그 {i} ---")
                output.append(blog_data["content"][:1000])  # 최대 1000자

    # 이미지 내 텍스트
    texts = result.get("text", [])
    if texts:
        text_list = [t.get("text", "") for t in texts[:5] if t.get("text")]
        if text_list:
            output.append(f"\n[이미지 텍스트] {', '.join(text_list)}")

    output.append("\n[판단 요청]")
    output.append("1. 원본 이미지를 기반으로 검색 결과 제목, 블로그 본문을 참고하세요.")
    output.append("2. 음식 이름만 물어보면: '~로 보입니다' + 식당이 보이면 '혹시 OO에서 드셨나요?'")
    output.append("3. 식당/메뉴명까지 물어보면: 가능성 있는 식당 2~3곳을 후보로 나열하세요.")
    output.append("4. 하나로 단정짓지 말고 '~일 수도 있고, ~일 수도 있습니다' 형태로 답변하세요.")

    return "\n".join(output) if output else "검색 결과 없음"


@tool
def search_restaurant_info(query: str) -> str:
    """
    식당을 검색합니다. 식당명, 지역+음식, 지역+맛집 등 다양한 검색어를 지원합니다.

    Args:
        query: 검색어 (식당명, 지역+음식, 지역+맛집 등)

    Returns:
        식당 정보 (이름, 주소, 전화번호, 카테고리, 메뉴)
    """
    kakao = get_kakao()

    result = kakao.search_restaurant(query)

    output = []
    place_id = None

    # 카카오맵 검색 결과
    if result and result.get("documents"):
        first_place = result["documents"][0]
        place_url = first_place.get("place_url", "")
        place_id = kakao.get_place_id_from_url(place_url) if place_url else None

        # 여러 식당 좌표 수집
        coords_list = []

        for i, place in enumerate(result["documents"][:3], 1):
            output.append(f"[{i}] {place.get('place_name', '')}")
            output.append(f"   주소: {place.get('road_address_name', '') or place.get('address_name', '')}")
            output.append(f"   전화: {place.get('phone', '')}")
            output.append(f"   카테고리: {place.get('category_name', '')}")
            # 카카오맵 링크 추가
            p_url = place.get('place_url', '')
            if p_url:
                output.append(f"   🗺️ 지도: {p_url}")
            output.append("")

            # 좌표 및 정보 수집
            x = place.get('x', '')  # longitude
            y = place.get('y', '')  # latitude
            name = place.get('place_name', '')
            address = place.get('road_address_name', '') or place.get('address_name', '')
            phone = place.get('phone', '')
            category = place.get('category_name', '').split(' > ')[-1] if place.get('category_name') else ''
            place_url = place.get('place_url', '')
            if x and y:
                # | 로 필드 구분 (이름|주소|전화|카테고리|카카오맵URL)
                info = f"{name}|{address}|{phone}|{category}|{place_url}"
                coords_list.append(f"{y},{x},{info}")

        # 여러 식당 좌표를 MAP 태그에 포함 (세미콜론으로 구분)
        if coords_list:
            coords_str = ";".join(coords_list)
            output.insert(0, f"[MAP:{coords_str}]")

    # Playwright로 메뉴 텍스트 크롤링 (LLM이 해석)
    menu_text = ""
    if place_id and PLAYWRIGHT_AVAILABLE:
        menu_text = kakao.get_menu_via_playwright(place_id)

    if menu_text:
        output.append("[메뉴판]")
        output.append(menu_text)
    else:
        # 폴백: Serper 검색
        menu_info = kakao.search_menu_via_serper(query)
        if menu_info:
            output.append("[메뉴 검색 결과]")
            output.append(menu_info)

    if not output:
        return f"'{query}' 검색 결과 없음"

    return "\n".join(output)


@tool
def search_recipe_online(query: str) -> str:
    """
    인터넷에서 레시피를 검색합니다. LLM이 사용자 질문에 맞게 검색 쿼리를 생성합니다.

    Args:
        query: 검색 쿼리 (예: "김치찌개 레시피", "백종원 된장찌개", "초간단 계란찜 만드는법")

    Returns:
        레시피 정보 (재료, 조리 순서) - 최대 3개 레시피
    """
    searcher = get_searcher()

    # LLM이 생성한 쿼리로 검색
    search_result = searcher.search_text(query)

    if "error" in search_result:
        return f"검색 실패: {search_result['error']}"

    organic = search_result.get("organic_results", [])

    if not organic:
        return f"'{query}' 검색 결과가 없습니다."

    # 상위 3개 결과 크롤링
    output = [f"[검색: {query}]"]
    for i, item in enumerate(organic[:3], 1):
        link = item.get("link", "")
        recipe_data = _crawl_recipe_fast(link)
        output.append(f"\n=== 레시피 {i} ===\n{recipe_data}")

    return "\n".join(output)


def _crawl_recipe_fast(url: str) -> str:
    """requests로 빠른 레시피 크롤링 (Playwright 없이)"""
    if not BS4_AVAILABLE:
        return f"BeautifulSoup 라이브러리가 필요합니다. pip install beautifulsoup4"

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = 'utf-8'

        if resp.status_code != 200:
            return f"페이지 로드 실패: {url}"

        soup = BeautifulSoup(resp.text, 'html.parser')

        # 만개의레시피 - 필요한 정보만 선택적 추출
        if '10000recipe.com' in url:
            output = []

            # 제목
            title_el = soup.select_one('.view2_summary h3, .view2_summary_tit')
            if title_el:
                output.append(f"[{title_el.get_text(strip=True)}]")

            output.append(f"출처: {url}")

            # 설명
            desc_el = soup.select_one('.view2_summary_in')
            if desc_el:
                output.append(f"\n{desc_el.get_text(strip=True)}")

            # 인분/시간/난이도
            info_els = soup.select('.view2_summary_info span')
            if info_els:
                info_text = ' | '.join([el.get_text(strip=True) for el in info_els])
                output.append(f"({info_text})")

            # 재료
            ingredients = []
            for li in soup.select('.ready_ingre3 li'):
                text = li.get_text(strip=True).replace('구매', '').strip()
                if text:
                    ingredients.append(text)
            if ingredients:
                output.append("\n[재료]")
                for ing in ingredients[:20]:
                    output.append(f"  - {ing}")

            # 조리 순서
            steps = []
            for step in soup.select('.view_step_cont'):
                text = step.get_text(strip=True)
                if text:
                    steps.append(text)
            if steps:
                output.append("\n[조리 순서]")
                for i, step in enumerate(steps[:15], 1):
                    if len(step) > 200:
                        step = step[:200] + "..."
                    output.append(f"  {i}. {step}")

            # AI 리뷰 요약
            ai_ratio = soup.select_one('.reply_ai_t2')
            ai_summary = soup.select_one('.reply_ai_sum')
            if ai_ratio or ai_summary:
                output.append("\n[AI 리뷰 요약]")
                if ai_ratio:
                    output.append(f"  {ai_ratio.get_text(strip=True)}")
                if ai_summary:
                    output.append(f"  {ai_summary.get_text(strip=True)[:300]}")

            # 후기 5개
            reviews = soup.select('.reply_list')[:5]
            if reviews:
                output.append("\n[후기]")
                for r in reviews:
                    text = r.get_text(strip=True)[:150]
                    if text:
                        output.append(f"  - {text}")

            return "\n".join(output)

        # 네이버 블로그 / 티스토리 / 기타 - 본문 텍스트 그대로 추출
        else:
            # 네이버 블로그는 모바일 버전 사용
            if 'blog.naver.com' in url:
                url = url.replace('blog.naver.com', 'm.blog.naver.com')
                resp = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(resp.text, 'html.parser')
                content = soup.select_one('.se-main-container, #postViewArea, .post-view')
            else:
                content = soup.select_one('article, .post-content, .entry-content, main, .content')
                if not content:
                    content = soup.body

            if content:
                text = content.get_text(separator='\n')
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                # 본문 텍스트 (최대 3500자)
                body_text = '\n'.join(lines)[:3500]
                return f"[레시피]\n출처: {url}\n\n{body_text}"

    except Exception as e:
        return f"크롤링 실패: {str(e)}\nURL: {url}"

    return f"레시피 내용을 추출하지 못했습니다.\nURL: {url}"


@tool
def get_restaurant_reviews(restaurant_name: str) -> str:
    """
    식당의 후기를 카카오맵에서 가져와 요약합니다.
    사용자가 "후기 어때", "리뷰 알려줘", "평가 어때" 등을 물어볼 때 사용합니다.

    Args:
        restaurant_name: 식당 이름 (예: "요미우돈교자 강남점")

    Returns:
        식당 후기 목록 및 요약
    """
    if not PLAYWRIGHT_AVAILABLE:
        return "Playwright가 설치되지 않아 후기를 가져올 수 없습니다."

    kakao = get_kakao()

    # 1. 식당 검색
    result = kakao.search_restaurant(restaurant_name)

    if not result or not result.get("documents"):
        return f"'{restaurant_name}' 식당을 찾을 수 없습니다."

    # 첫 번째 결과 사용
    place = result["documents"][0]
    place_name = place.get("place_name", "")
    place_url = place.get("place_url", "")
    address = place.get("address_name", "")

    # 2. place_id 추출
    place_id = kakao.get_place_id_from_url(place_url)

    if not place_id:
        return f"'{restaurant_name}' 후기 페이지를 찾을 수 없습니다."

    # 3. 후기 크롤링
    reviews_text = kakao.get_reviews_via_playwright(place_id, max_reviews=15)

    # 4. 결과 포맷팅
    output = []
    output.append(f"[{place_name} 후기]")
    output.append(f"📍 주소: {address}")
    output.append(f"🔗 카카오맵: {place_url}")
    output.append("")

    if reviews_text:
        output.append("📝 방문자 후기:")
        output.append(reviews_text)
        output.append("")
        output.append("[요약 요청] 위 후기들을 분석해서 장점, 단점, 추천 메뉴 등을 요약해주세요.")
    else:
        output.append("후기를 찾을 수 없습니다. 아직 등록된 후기가 없거나 크롤링에 실패했습니다.")

    return "\n".join(output)


@tool
def get_nutrition_info(query: str) -> str:
    """
    음식의 영양정보를 검색합니다. LLM이 사용자 질문에 맞게 검색 쿼리를 생성합니다.

    Args:
        query: 검색 쿼리 (예: "김치찌개 칼로리", "맘스터치 싸이버거 단백질", "스타벅스 아메리카노 1잔 열량")

    Returns:
        영양정보 검색 결과 (본문 크롤링 포함)
    """
    searcher = get_searcher()

    # LLM이 생성한 쿼리로 검색
    search_result = searcher.search_text(query)

    if "error" in search_result:
        return f"검색 실패: {search_result['error']}"

    organic = search_result.get("organic_results", [])

    if not organic:
        return f"'{query}' 검색 결과가 없습니다."

    output = [f"[검색: {query}]"]

    # 상위 3개 페이지 본문 크롤링
    for item in organic[:3]:
        title = item.get("title", "")
        link = item.get("link", "")

        content = _crawl_nutrition_page(link)

        if content:
            output.append(f"\n=== {title} ===")
            output.append(f"출처: {link}")
            output.append(content)

    return "\n".join(output)


def _crawl_nutrition_page(url: str) -> str:
    """영양정보 페이지 본문 크롤링"""
    if not BS4_AVAILABLE:
        return ""

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        # 네이버 블로그 모바일 변환
        if 'blog.naver.com' in url and 'm.blog' not in url:
            url = url.replace('blog.naver.com', 'm.blog.naver.com')

        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = 'utf-8'

        if resp.status_code != 200:
            return ""

        soup = BeautifulSoup(resp.text, 'html.parser')

        # script/style만 제거
        for tag in soup(['script', 'style']):
            tag.decompose()

        if soup.body:
            text = soup.body.get_text(separator='\n')
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            return '\n'.join(lines)[:2000]

    except Exception:
        return ""

    return ""


