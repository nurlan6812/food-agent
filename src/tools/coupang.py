"""쿠팡 파트너스 상품 검색 도구"""

import json
from langchain_core.tools import tool
from langgraph.config import get_stream_writer

from ..services.coupang import get_coupang


@tool
def search_coupang_products(query: str) -> str:
    """
    음식 재료, 조리도구, 식품, 간식, 건강식품 등 구매 가능한 상품을 찾을 때 이 도구를 사용하세요.
    사용자가 특정 제품/재료/식품에 관심을 보이거나, 레시피 재료를 구매하고 싶어하거나,
    음식 관련 상품을 추천받고 싶어할 때 호출하세요.

    Args:
        query: 검색 키워드 (예: "김치 담그기 세트", "트러플 오일", "에어프라이어")

    Returns:
        쿠팡 상품 정보 (이름, 가격, 이미지, 구매 링크)
    """
    writer = get_stream_writer()
    writer({"tool": "search_coupang_products", "status": "쿠팡 상품 검색 중..."})

    coupang = get_coupang()
    products = coupang.search_products(query, limit=5)

    if not products:
        return f"'{query}' 상품 검색 결과가 없습니다."

    output = []
    products_data = []

    for i, product in enumerate(products[:5], 1):
        name = product.get("productName", "")
        price = product.get("productPrice", 0)
        image = product.get("productImage", "")
        url = product.get("productUrl", "")
        is_rocket = product.get("isRocket", False)
        is_free_shipping = product.get("isFreeShipping", False)

        output.append(f"[{i}] {name}")
        output.append(f"   가격: {price:,}원")
        if is_rocket:
            output.append("   🚀 로켓배송")
        if is_free_shipping:
            output.append("   📦 무료배송")
        output.append(f"   링크: {url}")
        output.append("")

        products_data.append({
            "name": name,
            "price": price,
            "imageUrl": image,
            "productUrl": url,
            "isRocket": is_rocket,
            "isFreeShipping": is_free_shipping,
        })

    if products_data:
        output.insert(0, f"[PRODUCTS_JSON:{json.dumps(products_data, ensure_ascii=False)}]")

    return "\n".join(output)
