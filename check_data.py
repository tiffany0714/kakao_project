import json

with open('frontend/data/current_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("seasonal_ranking:", len(data.get('seasonal_ranking', [])), "items")
if data.get('seasonal_ranking'):
    for item in data['seasonal_ranking'][:3]:
        print(f"  {item['rank']}. {item['name'][:40]}")
    print(f"  ... (total: {len(data['seasonal_ranking'])} items)")

print("\nniece_ranking:", len(data.get('niece_ranking', [])), "items")
for item in data.get('niece_ranking', []):
    print(f"  {item['rank']}. {item['name']}")
