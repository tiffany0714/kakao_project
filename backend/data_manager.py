import json
import os
import datetime
import shutil

DATA_PATH = "C:/Users/User/.gemini/antigravity/scratch/kakao_project/data/current_data.json"
HISTORY_DIR = "C:/Users/User/.gemini/antigravity/scratch/kakao_project/history"

def get_monthly_path():
    now = datetime.datetime.now()
    month_str = now.strftime("%Y-%m")
    path = os.path.join(HISTORY_DIR, month_str)
    os.makedirs(path, exist_ok=True)
    return path

def save_history(data):
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    history_file = os.path.join(get_monthly_path(), f"data_{timestamp}.json")
    
    with open(history_file, "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return history_file

def detect_changes(new_data):
    if not os.path.exists(DATA_PATH):
        return ["Initial data creation"]
    
    with open(DATA_PATH, "r", encoding='utf-8') as f:
        old_data = json.load(f)
    
    changes = []
    
    # Compare events
    old_event_names = {e['name'] for e in old_data.get('events', [])}
    new_event_names = {e['name'] for e in new_data.get('events', [])}
    
    added = new_event_names - old_event_names
    removed = old_event_names - new_event_names
    
    if added: changes.append(f"Added events: {', '.join(added)}")
    if removed: changes.append(f"Removed events: {', '.join(removed)}")
    
    # Check for content changes in existing events
    for new_event in new_data.get('events', []):
        for old_event in old_data.get('events', []):
            if new_event['name'] == old_event['name']:
                if new_event != old_event:
                    changes.append(f"Updated event details: {new_event['name']}")
                break
                
    # Compare ranking
    if new_data.get('ranking', {}).get('rank') != old_data.get('ranking', {}).get('rank'):
        changes.append(f"Ranking changed from {old_data.get('ranking', {}).get('rank')} to {new_data.get('ranking', {}).get('rank')}")
        
    return changes

def run_update_cycle():
    # This function would be called by a scheduler
    # 1. Run scraper (via subprocess or direct import if possible)
    # For now, we assume scraper.py has run and updated current_data.json
    # Or we can trigger it here.
    
    if not os.path.exists(DATA_PATH):
        print("Scraper has not run yet.")
        return

    with open(DATA_PATH, "r", encoding='utf-8') as f:
        current_data = json.load(f)
    
    # Calculate rank changes before saving
    calculate_fluctuations(current_data.get('ranking', []))
    calculate_fluctuations(current_data.get('niece_ranking', []))
    
    changes = detect_changes(current_data)
    
    if changes:
        print(f"Detected changes: {changes}")
        current_data['changes'] = changes
        # Save to history
        save_history(current_data)
        # Update current data with change info
        with open(DATA_PATH, "w", encoding='utf-8') as f:
            json.dump(current_data, f, ensure_ascii=False, indent=2)
    else:
        print("No changes detected.")

if __name__ == "__main__":
    run_update_cycle()
