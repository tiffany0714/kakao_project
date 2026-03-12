import json
from datetime import datetime

# 데이터 업데이트 로직
def update_json():
    file_path = "frontend/data/current_data.json"
    
    # 기존 파일 읽기
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}

    # 시간 및 데이터 갱신 (예시)
    data["last_updated"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    
    # 파일 저장
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print("Update Complete!")

if __name__ == "__main__":
    update_json()