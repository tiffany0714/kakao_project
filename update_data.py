import requests, pandas as pd, json, os
from datetime import datetime, timedelta

def main():
    h_path = 'frontend/data/history.json'
    history = json.load(open(h_path, 'r', encoding='utf-8')) if os.path.exists(h_path) else {}
    
    # Calculate previous day for diff
    today_str = datetime.now().strftime("%Y-%m-%d")
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Use the most recent available date if yesterday is not available
    prev_dates = sorted([d for d in history.keys() if d < today_str], reverse=True)
    prev_day = prev_dates[0] if prev_dates else None

    # Helper to find rank change
    def get_diff(code, prev_ranking):
        if not prev_ranking: return 0
        prev_item = next((item for item in prev_ranking if str(item.get('code')) == code), None)
        if prev_item:
            return prev_item.get('rank', 999) - current_rank # prev - current: if 10 -> 5, diff is +5 (up)
        return 0

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
        
        # Calculate diff
        diff = 0
        if prev_strat:
            p_item = next((item for item in prev_strat if str(item.get('code')) == code), None)
            if p_item:
                p_rank = p_item.get('rank', 999)
                if p_rank != 999 and current_rank != 999:
                    diff = p_rank - current_rank
        
        seasonal.append({
            "season": str(row['계절']),
            "code": code,
            "name": str(row['상품명']),
            "rank": current_rank,
            "img": c_items[m_idx].get('imageUrl') if m_idx is not None else "",
            "diff": diff
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
                                
                                # Calculate diff
                                diff = 0
                                if prev_niece:
                                    p_item = next((item for item in prev_niece if str(item.get('code')) == code), None)
                                    if p_item:
                                        p_rank = p_item.get('rank', 999)
                                        diff = p_rank - current_rank
                                
                                niece.append({
                                    "code": code,
                                    "name": p_name,
                                    "rank": current_rank,
                                    "img": p.get('imageUrl'),
                                    "diff": diff
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