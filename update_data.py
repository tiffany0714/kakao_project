import requests
import json
from datetime import datetime, timedelta

# 1. 카카오 쇼핑 실시간 랭킹 수집 함수
def get_kakao_realtime_ranking():
    return [
        {"rank": 1, "name": "실시간 인기 상품 1위", "img": "", "product_code": "00001", "diff_yesterday": 2, "diff_last_week": 5},
        {"rank": 2, "name": "실시간 인기 상품 2위", "img": "", "product_code": "00002", "diff_yesterday": -1, "diff_last_week": 0},
        {"rank": 3, "name": "실시간 인기 상품 3위", "img": "", "product_code": "00003", "diff_yesterday": 0, "diff_last_week": -3}
    ]

# 2. 조카 선물 (추천) 랭킹 수집 함수
def get_nephew_gift_ranking():
    return [
        {"rank": 1, "name": "조카가 좋아하는 장난감", "img": "", "product_code": "10001", "diff_yesterday": 10, "diff_last_week": 20},
        {"rank": 2, "name": "아이들 인기 간식 세트", "img": "", "product_code": "10002", "diff_yesterday": 5, "diff_last_week": 10},
        {"rank": 3, "name": "귀여운 아동용 가방", "img": "", "product_code": "10003", "diff_yesterday": -2, "diff_last_week": 5}
    ]

if __name__ == "__main__":
    file_path = "frontend/data/current_data.json"
    # 🕒 한국 시간(KST) 계산: UTC + 9시간
    seoul_time = datetime.utcnow() + timedelta(hours=9)
    formatted_time = seoul_time.strftime("%Y-%m-%d %H:%M:%S")

    # 3. 기존 데이터 로드 (events, ranking 유지 목적)
    data = {
        "last_updated": formatted_time,
        "events": [],
        "ranking": [],
        "niece_ranking": []
    }
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
            data["events"] = existing_data.get("events", [])
            data["ranking"] = existing_data.get("ranking", [])
            data["niece_ranking"] = existing_data.get("niece_ranking", [])
    except (FileNotFoundError, json.JSONDecodeError):
        # 파일이 없으면 더미가 아닌 최소한의 구조만 생성 (필요시 get_kakao_realtime_ranking 호출 가능)
        pass

    # 파일 저장 (경로: frontend/data/current_data.json)
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Update Success! Time: {formatted_time}")
    except Exception as e:
        print(f"Error: {e}")
        