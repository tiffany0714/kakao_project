import requests, pandas as pd, json, os
from datetime import datetime, timedelta

def main():
    h_path = 'frontend/data/history.json'
    history = json.load(open(h_path, 'r', encoding='utf-8')) if os.path.exists(h_path) else {}
    
    # 날짜 설정
    today_str = datetime.now().strftime("%Y-%m-%d")
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    last_week_str = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d") # 7일 전 추가

    # 비교용 데이터 추출
    prev_list = history.get(yesterday_str, {})
    week_list = history.get(last_week_str, {})

    # 순위 변화 계산 함수 (이름을 product_code로 통일)
    def get_diff(code, old_data_dict, category_key, current_rank):
        old_list = old_data_dict.get(category_key, [])
        if not old_list: return "-"
        
        # product_code로 비교
        p_item = next((item for item in old_list if str(item.get('product_code')) == code), None)
        if p_item:
            p_rank = int(p_item.get('rank', 999))
            if p_rank != 999:
                change = p_rank - current_rank
                if change > 0: return f"+{change}"
                if change < 0: return f"{change}"
                return "-"
        return "신규"

    # 1. 전략 랭킹 (Strategy Ranking)
    # Target: https://gift.kakao.com/ranking/category/3
    df = pd.read_excel('strategy_items.xlsx')
    c_res = requests.get("https://gift.kakao.com/a/v1/rank/category/3?page=0&size=100").json()
    c_items = c_res.get('contents', [])
    
    seasonal = []
    prev_strat = history.get(prev_day, {}).get('category', []) if prev_day else []
    
for _, row in df.iterrows():
        code = str(row['상품번호'])
        m_idx = next((i for i, item in enumerate(c_items) if str(item.get('productId')) == code), None)
        current_rank = m_idx + 1 if m_idx is not None else 999
        
        # 2번 수정 포인트: 데이터 구조를 app.js와 맞추고 diff 계산 추가
        seasonal.append({
            "season": str(row['계절']),
            "product_code": code, # 'code'에서 'product_code'로 변경
            "name": str(row['상품명']),
            "rank": current_rank,
            "img": c_items[m_idx].get('imageUrl') if m_idx is not None else "",
            "diff": get_diff(code, prev_list, 'category', current_rank),     # 어제 비교
            "week_diff": get_diff(code, week_list, 'category', current_rank) # 지난주 비교
        })

    # 2. 조카선물 랭킹 (Niece Gifts Ranking)
    # Target: https://gift.kakao.com/page/code/life_pregnancy
    # New API found via browser: https://gift.kakao.com/a/content-builder/v2/pages/codes/life_pregnancy?page=1&size=20
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://gift.kakao.com/page/code/life_pregnancy"
    }
    niece = []
    prev_niece = history.get(prev_day, {}).get('niece', []) if prev_day else []
    
    try:
        n_res = requests.get("https://gift.kakao.com/a/content-builder/v2/pages/codes/life_pregnancy?page=1&size=200", headers=headers).json()
        global_idx = 1
        # New structure: components -> contents -> property -> collections -> products
        for comp in n_res.get('components', []):
            if not isinstance(comp, dict): continue
            for content in comp.get('contents', []):
                if not isinstance(content, dict): continue
                if content.get('type') == "PRODUCT_GROUP":
                    prop = content.get('property', {})
                    if not isinstance(prop, dict): continue
                    for coll in prop.get('collections', []):
                        if not isinstance(coll, dict): continue
                        for p in coll.get('products', []):
                            if not isinstance(p, dict): continue
                            brand = p.get('brandName', '') or ''
                            p_name = p.get('productName', '') or ''
                            if "오즈키즈" in brand or "오즈키즈" in p_name:
                                                code = str(p.get('productId'))
                                                current_rank = global_idx
                                                
                                                # 2번 수정 포인트: 변수명 통일 및 지난주 대비 추가
                                                niece.append({
                                                    "product_code": code,
                                                    "name": p_name,
                                                    "rank": current_rank,
                                                    "img": p.get('imageUrl'),
                                                    "diff": get_diff(code, prev_list, 'niece', current_rank),     # 어제 비교
                                                    "week_diff": get_diff(code, week_list, 'niece', current_rank) # 지난주 비교
                                                })
                                            global_idx += 1
                                except Exception as e:
                                    print(f"Error fetching Niece ranking: {e}")


    # Update history
    history[today_str] = {"category": seasonal, "niece": niece}
    # Keep only last 30 days to avoid bloat
    if len(history) > 30:
        sorted_keys = sorted(history.keys())
        for k in sorted_keys[:-30]: del history[k]
        
    os.makedirs('frontend/data', exist_ok=True)
    with open(h_path, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=4, ensure_ascii=False)

    # Update current_data.json
    curr_path = 'frontend/data/current_data.json'
    old = json.load(open(curr_path, 'r', encoding='utf-8')) if os.path.exists(curr_path) else {"events": []}
    
    final = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "events": old.get("events", []),
        "seasonal_ranking": seasonal,
        "niece_ranking": niece
    }
    with open(curr_path, 'w', encoding='utf-8') as f:
        json.dump(final, f, indent=4, ensure_ascii=False)
    
    print(f"Update complete: {today_str}")

if __name__ == "__main__":
    main()