import pandas as pd
import requests

df = pd.read_excel('strategy_items.xlsx')
excel_codes = set(str(int(row['상품번호'])) for _, row in df.iterrows() if pd.notna(row['상품번호']))
print(f"엑셀 상품 수: {len(excel_codes)}")

headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://gift.kakao.com",
    "Content-Type": "application/json"
}

all_items = []
for page in range(30):  # 0~29 페이지 (600개)
    r = requests.post(
        "https://gift.kakao.com/a/rank/v1/gift-rank/ranking-tab/category-tab/search",
        headers=headers,
        json={"navId": 1, "page": page, "size": 20, "subNavId": 11100}
    ).json()
    products = r.get('products', [])
    all_items.extend(products)
    print(f"page {page}: {len(products)}개 (누적 {len(all_items)}개)")
    if r.get('last', True) or not products:
        break

print(f"\n총 {len(all_items)}개 수집")
matched = [p for p in all_items if str(p.get('productId')) in excel_codes]
print(f"매칭된 상품: {len(matched)}개")
for p in matched[:5]:
    idx = next(i for i, x in enumerate(all_items) if x.get('productId') == p.get('productId'))
    print(f"  {idx+1}위: {p.get('name', '')[:40]}")