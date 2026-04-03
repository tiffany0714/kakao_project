import json
import pandas as pd

# Load current data
with open('frontend/data/current_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Load strategy items
df = pd.read_excel('strategy_items.xlsx')
strategy_codes = set(str(code) for code in df['상품번호'].astype(str).tolist())

print("=" * 60)
print("Strategy Items 상품코드 (첫 10개):")
print(list(strategy_codes)[:10])

print("\n" + "=" * 60)
print("Niece Ranking에서 찾은 상품코드들:")
for item in data.get('niece_ranking', [])[:5]:
    code = item.get('product_code')
    name = item.get('name', '')
    print(f"  Code: {code} | {name[:50]}")

print("\n" + "=" * 60)
print("Strategy Ranking 분석:")
seasonal = data.get('seasonal_ranking', [])
rank_999_count = sum(1 for s in seasonal if s.get('rank') == 999)
rank_found_count = sum(1 for s in seasonal if s.get('rank') != 999)

print(f"  Total: {len(seasonal)}")
print(f"  Found (rank != 999): {rank_found_count}")
print(f"  Not found (rank = 999): {rank_999_count}")

# Check if product codes are being stored
print("\n" + "=" * 60)
print("Product codes in seasonal ranking (first 5):")
for s in seasonal[:5]:
    print(f"  {s['product_code']} -> rank {s['rank']}: {s['name'][:40]}")
