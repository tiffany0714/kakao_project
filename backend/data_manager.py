import json
import os
import datetime

# Use relative paths for portability
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "frontend", "data", "current_data.json")
HISTORY_FILE = os.path.join(BASE_DIR, "history", "rank_history.json")

def load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

import re

def calculate_diff(current_rank_str, historical_rank_str):
    try:
        # Extract only digits from strings like "단독\n순위 : 1"
        c_match = re.search(r'(\d+)', str(current_rank_str))
        h_match = re.search(r'(\d+)', str(historical_rank_str))
        
        if c_match and h_match:
            current = int(c_match.group(1))
            historical = int(h_match.group(1))
            return historical - current 
        return 0
    except:
        return 0

def update_history_and_calc_diffs(current_data):
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    history = load_json(HISTORY_FILE)
    
    if "seasonal_ranking" not in history: history["seasonal_ranking"] = {}
    if "niece_ranking" not in history: history["niece_ranking"] = {}
    
    # Store today's rankings in history
    for tab in ["seasonal_ranking", "niece_ranking"]:
        hist_tab = history[tab]
        hist_tab[today_str] = {}
        for item in current_data.get(tab, []):
            product_id = item.get("product_code") or item.get("name")
            if product_id:
                hist_tab[today_str][product_id] = item.get("rank")

        # Sort dates to find T-1 and T-7
        sorted_dates = sorted(hist_tab.keys(), reverse=True)
        yesterday_idx = 1 if len(sorted_dates) > 1 else None
        last_week_idx = None
        
        # Find exactly 7 days ago if possible, or closest
        today_date = datetime.datetime.strptime(today_str, "%Y-%m-%d")
        y_date = (today_date - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        w_date = (today_date - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
        
        # Add diff info to current items
        for item in current_data.get(tab, []):
            product_id = item.get("product_code") or item.get("name")
            
            # Yesterday
            y_rank = hist_tab.get(y_date, {}).get(product_id)
            if y_rank:
                item["diff_yesterday"] = calculate_diff(item.get("rank"), y_rank)
            else:
                item["diff_yesterday"] = 0
                
            # Last week
            w_rank = hist_tab.get(w_date, {}).get(product_id)
            if w_rank:
                item["diff_last_week"] = calculate_diff(item.get("rank"), w_rank)
            else:
                item["diff_last_week"] = 0

    # Cleanup history (keep last 30 days to avoid bloating)
    # sorted_dates = sorted(history["ranking"].keys())
    # if len(sorted_dates) > 30:
    #     for d in sorted_dates[:-30]:
    #         del history["ranking"][d]
    #         if d in history["niece_ranking"]: del history["niece_ranking"][d]

    save_json(HISTORY_FILE, history)

def run_update_cycle():
    if not os.path.exists(DATA_PATH):
        print(f"Data file not found: {DATA_PATH}")
        return

    current_data = load_json(DATA_PATH)
    
    # Update fluctuations
    update_history_and_calc_diffs(current_data)
    
    # Track changes log (optional but nice)
    # (Existing detect_changes logic can be added here if needed)
    
    current_data["last_updated"] = datetime.datetime.now().isoformat()
    
    save_json(DATA_PATH, current_data)
    print("Fluctuation data updated successfully.")

if __name__ == "__main__":
    run_update_cycle()
