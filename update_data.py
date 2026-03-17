import requests
import json
import os
from datetime import datetime, timedelta

# [핵심 1] 경로 절대값 고정 (어디서 실행해도 frontend/data 폴더를 찾아감)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, "frontend", "data", "current_data.json")

# 1. 카카오 쇼핑 실시간 랭킹 수집 (실제 데이터 수집 로직으로 대체 가능)
def get_kakao_realtime_ranking():
    # 현재는 예시 데이터지만, 나중에 크롤링 코드를 여기 넣으면 됩니다.
    return [
        {"rank": 1, "name": "실시간 인기 상품 1위", "img": "", "product_code": "00001", "diff_yesterday": 2, "diff_last_week": 5},
        {"rank": 2, "name": "실시간 인기 상품 2위", "img": "", "product_code": "00002", "diff_yesterday": -1, "diff_last_week": 0},
        {"rank": 3, "name": "실시간 인기 상품 3위", "img": "", "product_code": "00003", "diff_yesterday": 0, "diff_last_week": -3}
    ]

# 2. 조카 선물 (추천) 랭킹 수집
def get_nephew_gift_ranking():
    return [
        {"rank": 1, "name": "조카가 좋아하는 장난감", "img": "", "product_code": "10001", "diff_yesterday": 10, "diff_last_week": 20},
        {"rank": 2, "name": "아이들 인기 간식 세트", "img": "", "product_code": "10002", "diff_yesterday": 5, "diff_last_week": 10},
        {"rank": 3, "name": "귀여운 아동용 가방", "img": "", "product_code": "10003", "diff_yesterday": -2, "diff_last_week": 5}
    ]

if __name__ == "__main__":
    # 🕒 한국 시간(KST) 계산
    seoul_time = datetime.utcnow() + timedelta(hours=9)
    formatted_time = seoul_time.isoformat() # 웹사이트 호환을 위해 ISO 형식 사용

    # 폴더가 없으면 생성
    os.makedirs(os.path.dirname(FILE_PATH), exist_ok=True)

    # 기본 구조 설정
    data = {
        "last_updated": formatted_time,
        "events": [],
        "ranking": [],
        "niece_ranking": []
    }
    
    # [핵심 2] 기존 데이터 로드 (구글 폼으로 받은 events를 유지하기 위함)
    try:
        if os.path.exists(FILE_PATH):
            with open(FILE_PATH, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
                data["events"] = existing_data.get("events", [])
    except Exception as e:
        print(f"기존 데이터 로드 실패: {e}")

    # [핵심 3] 수집한 랭킹 데이터를 변수에 할당 (이게 빠져있었음!)
    data["ranking"] = get_kakao_realtime_ranking()
    data["niece_ranking"] = get_nephew_gift_ranking()

    # 최종 파일 저장
    try:
        with open(FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"✅ 업데이트 성공! 시간: {formatted_time}")
        print(f"📍 저장 위치: {FILE_PATH}")
    except Exception as e:
        print(f"❌ 저장 에러: {e}")