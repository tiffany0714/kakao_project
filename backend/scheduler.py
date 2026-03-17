import time
import subprocess
import os
import sys
from datetime import datetime, timedelta

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
SCRAPER_SCRIPT = os.path.join(BACKEND_DIR, "scraper.py")
MANAGER_SCRIPT = os.path.join(BACKEND_DIR, "data_manager.py")

def run_update():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting update cycle...")
    
    # 1. Run the scraper
    print("Running scraper...")
    result = subprocess.run([sys.executable, SCRAPER_SCRIPT], capture_output=True, text=True, encoding='utf-8')
    if result.returncode != 0:
        print(f"Scraper error: {result.stderr}")
    else:
        print(result.stdout)
    
    # 2. Run the data manager for history and changes
    print("Running data manager...")
    result = subprocess.run([sys.executable, MANAGER_SCRIPT], capture_output=True, text=True, encoding='utf-8')
    if result.returncode != 0:
        print(f"Data manager error: {result.stderr}")
    else:
        print(result.stdout)
        
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Update cycle complete.")

def main():
    print("OzKids Ranking Scheduler started.")
    print("This script will run every day at 12:00 PM (KST).")
    
    while True:
        now = datetime.now()
        # Target time: 12:00:00 (KST - assuming local system is on KST)
        target = now.replace(hour=12, minute=0, second=0, microsecond=0)
        
        if now >= target:
            target += timedelta(days=1)
            
        wait_seconds = (target - now).total_seconds()
        print(f"Next update in {wait_seconds/3600:.2f} hours (at {target})")
        
        # Check every 60 seconds if it's time
        time.sleep(min(wait_seconds, 60))
        
        if datetime.now() >= target:
            run_update()

if __name__ == "__main__":
    main()
