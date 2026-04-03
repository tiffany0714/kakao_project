import json

with open('frontend/data/history.json', 'r', encoding='utf-8') as f:
    history = json.load(f)

print("History.json 상세 구조:")
print("=" * 60)

for date in sorted(history.keys()):
    data = history[date]
    print(f"\n{date}:")
    print(f"  Keys: {list(data.keys())}")
    if 'category' in data:
        cat_data = data['category']
        print(f"  category: {len(cat_data)} items")
        if cat_data:
            print(f"    First: {cat_data[0]}")
    if 'seasonal' in data:
        seasonal_data = data['seasonal']
        print(f"  seasonal: {len(seasonal_data)} items")
        if seasonal_data:
            print(f"    First: {seasonal_data[0]}")
    if 'niece' in data:
        niece_data = data['niece']
        print(f"  niece: {len(niece_data)} items")
        if niece_data:
            print(f"    First: {niece_data[0]}")
