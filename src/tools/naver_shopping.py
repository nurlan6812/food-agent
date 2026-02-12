"""네이버 쇼핑 상품 검색 도구"""

import re
import json
from langchain_core.tools import tool
from langgraph.config import get_stream_writer

from ..services.naver_shopping import get_naver_shopping


@tool
def search_recipe_ingredients(ingredients: str) -> str:
    """
    레시피 재료들을 한번에 검색하여 각 재료별 구매 상품 1개씩을 찾습니다.
    search_recipe_online으로 레시피를 받은 후, 재료 목록을 이 도구에 전달하세요.

    Args:
        ingredients: 쉼표로 구분된 재료 목록 (예: "고추장,두부,돼지고기,대파,김치")

    Returns:
        재료별 상품 정보 (이름, 가격, 이미지, 구매 링크)
    """
    writer = get_stream_writer()
    writer({"tool": "search_recipe_ingredients", "status": "재료 상품 검색 중..."})

    ingredient_list = [i.strip() for i in ingredients.split(",") if i.strip()]
    if not ingredient_list:
        return "재료 목록이 비어있습니다."

    naver = get_naver_shopping()
    results = naver.search_multiple(ingredient_list, limit_per=1, sort="sim")

    output = []
    products_data = []

    for ingredient in ingredient_list:
        items = results.get(ingredient, [])
        if not items:
            output.append(f"- {ingredient}: 검색 결과 없음")
            continue

        item = items[0]
        name = re.sub(r'<[^>]+>', '', item.get("title", ""))
        price = int(item.get("lprice", 0))
        image = item.get("image", "")
        url = item.get("link", "")
        mall = item.get("mallName", "")
        brand = item.get("brand", "")

        output.append(f"- {ingredient}: \"{name}\" ({price:,}원) → {url}")

        products_data.append({
            "name": name,
            "price": price,
            "imageUrl": image,
            "productUrl": url,
            "mall": mall,
            "brand": brand,
            "ingredient": ingredient,
        })

    text_output = "\n".join(output)

    if products_data:
        text_output = f"[PRODUCTS_JSON:{json.dumps(products_data, ensure_ascii=False)}]\n\n재료별 상품:\n{text_output}"

    return text_output


@tool
def search_naver_products(query: str, sort: str = "sim") -> str:
    """
    음식 재료, 조리도구, 식품, 간식, 건강식품 등 구매 가능한 상품을 찾을 때 이 도구를 사용하세요.
    사용자가 특정 제품/재료/식품에 관심을 보이거나, 레시피 재료를 구매하고 싶어하거나,
    음식 관련 상품을 추천받고 싶어할 때 호출하세요.

    Args:
        query: 검색 키워드 (예: "김치 담그기 세트", "트러플 오일", "에어프라이어")
        sort: 정렬 기준. "asc"=가격낮은순(기본값), "dsc"=가격높은순, "sim"=정확도순, "date"=최신순

    Returns:
        네이버 쇼핑 상품 정보 (이름, 가격, 이미지, 구매 링크)
    """
    writer = get_stream_writer()
    writer({"tool": "search_naver_products", "status": "네이버 쇼핑 검색 중..."})

    if sort not in ("asc", "dsc", "sim", "date"):
        sort = "asc"

    naver = get_naver_shopping()
    products = naver.search_products(query, limit=20, sort=sort)

    if not products:
        return f"'{query}' 상품 검색 결과가 없습니다."

    output = []
    products_data = []

    for i, product in enumerate(products[:20], 1):
        # HTML 태그 제거 (네이버 API는 <b> 태그 포함)
        name = re.sub(r'<[^>]+>', '', product.get("title", ""))
        price = int(product.get("lprice", 0))
        image = product.get("image", "")
        url = product.get("link", "")
        mall = product.get("mallName", "")
        brand = product.get("brand", "")
        category = product.get("category1", "")
        if product.get("category2"):
            category += f" > {product['category2']}"

        output.append(f"[{i}] {name}")
        output.append(f"   가격: {price:,}원")
        if mall:
            output.append(f"   판매처: {mall}")
        if brand:
            output.append(f"   브랜드: {brand}")
        output.append(f"   링크: {url}")
        output.append("")

        products_data.append({
            "name": name,
            "price": price,
            "imageUrl": image,
            "productUrl": url,
            "mall": mall,
            "brand": brand,
            "category": category,
        })

    if products_data:
        output.insert(0, f"[PRODUCTS_JSON:{json.dumps(products_data, ensure_ascii=False)}]")

    return "\n".join(output)
