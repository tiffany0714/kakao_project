import json

with open('frontend/data/current_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=" * 70)
print("SEASONAL RANKING (전략상품 - 카카오 랭킹)")
print("=" * 70)

seasonal = data.get('seasonal_ranking', [])
print(f"Total: {len(seasonal)} items\n")

for item in seasonal:
    rank = item.get('rank', '?')
    season = item.get('season', '미분류')
    name = item.get('name', '')[:50]
    code = item.get('product_code', '')
    print(f"[{rank:3d}] 계절: {season:8s} | 코드: {code} | {name}")

print("\n" + "=" * 70)
print("NIECE RANKING (조카선물 - 카카오 랭킹)")
print("=" * 70)

niece = data.get('niece_ranking', [])
print(f"Total: {len(niece)} items\n")

for item in niece:
    rank = item.get('rank', '?')
    season = item.get('season', '미분류')
    name = item.get('name', '')[:50]
    code = item.get('product_code', '')
    print(f"[{rank:3d}] 계절: {season:8s} | 코드: {code} | {name}")

# 통계
print("\n" + "=" * 70)
print("STATISTICS")
print("=" * 70)

# seasonal 계절별 분류
season_counts = {}
for item in seasonal:
    season = item.get('season', '미분류')
    season_counts[season] = season_counts.get(season, 0) + 1

print(f"\n전략상품 계절별 분포:")
for season, count in sorted(season_counts.items()):
    print(f"  {season}: {count}")

# niece 계절별 분류
season_counts_niece = {}
for item in niece:
    season = item.get('season', '미분류')
    season_counts_niece[season] = season_counts_niece.get(season, 0) + 1

print(f"\n조카선물 계절별 분포:")
for season, count in sorted(season_counts_niece.items()):
    print(f"  {season}: {count}")
