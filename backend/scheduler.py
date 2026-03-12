import time
import subprocess
import os
import sys

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
SCRAPER_SCRIPT = os.path.join(BACKEND_DIR, "scraper.py")
MANAGER_SCRIPT = os.path.join(BACKEND_DIR, "data_manager.py")

def run_update():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting update cycle...")
    
    # 1. Run the scraper
    print("Running scraper...")
    result = subprocess.run([sys.executable, SCRAPER_SCRIPT], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Scraper error: {result.stderr}")
    else:
        print(result.stdout)
    
    # 2. Run the data manager for history and changes
    print("Running data manager...")
    result = subprocess.run([sys.executable, MANAGER_SCRIPT], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Data manager error: {result.stderr}")
    else:
        print(result.stdout)
        
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Update cycle complete.")

def main():
    # Run once immediately
    run_update()
    
    # Then every hour
    while True:
        time.sleep(3600)
        run_update()

if __name__ == "__main__":
    main()
