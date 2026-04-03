import requests
import pandas as pd

headers_kakao = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://gift.kakao.com",
    "Content-Type": "application/json"
}

df = pd.read_excel('strategy_items.xlsx')
codes = set()
for x in df['상품번호']:
    if pd.notna(x):
        try:
            codes.add(str(int(x)))
        except:
            codes.add(str(x).strip())

print('Strategy codes sample:', list(codes)[:10])

c_res = requests.post(
    "https://gift.kakao.com/a/rank/v1/gift-rank/ranking-tab/category-tab/search",
    headers=headers_kakao,
    json={"navId": 1, "page": 0, "size": 500, "subNavId": 11100}
).json()

products = c_res.get('products', [])
print('API products count:', len(products))
print('API sample ids:', [p.get('productId') for p in products[:10]])

matched = [p for p in products if str(p.get('productId')) in codes]
print('Matched count:', len(matched))
print('Matched sample:', [p.get('productId') for p in matched[:10]])
