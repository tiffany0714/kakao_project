import requests
import json
from datetime import datetime, timedelta

# 1. 카카오 쇼핑 실시간 랭킹 수집 함수
def get_kakao_realtime_ranking():
    # 실제 카카오 쇼핑 API나 웹 구조에 맞춘 수집 로직 (예시 구조)
    # 현재는 사이트가 멈추지 않도록 업데이트된 데이터 형식만 유지합니다.
    return [
        {"rank": 1, "name": "실시간 인기 상품 1위", "price": "19,800원"},
        {"rank": 2, "name": "실시간 인기 상품 2위", "price": "34,500원"},
        {"rank": 3, "name": "실시간 인기 상품 3위", "price": "12,900원"}
    ]

# 2. 조카 선물 (추천) 랭킹 수집 함수
def get_nephew_gift_ranking():
    return [
        {"rank": 1, "name": "조카가 좋아하는 장난감", "price": "45,000원"},
        {"rank": 2, "name": "아이들 인기 간식 세트", "price": "21,000원"},
        {"rank": 3, "name": "귀여운 아동용 가방", "price": "28,900원"}
    ]

if __name__ == "__main__":
    # 🕒 한국 시간(KST) 계산: UTC + 9시간
    seoul_time = datetime.utcnow() + timedelta(hours=9)
    formatted_time = seoul_time.strftime("%Y-%m-%d %H:%M:%S")

    # 최종 저장할 데이터 구조
    data = {
        "last_updated": formatted_time,
        "rankings": {
            "realtime": get_kakao_realtime_ranking(),
            "nephew": get_nephew_gift_ranking()
        }
    }

    # 파일 저장 (경로: frontend/data/current_data.json)
    file_path = "frontend/data/current_data.json"
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"✅ 업데이트 성공! 시간: {formatted_time}")
    except FileNotFoundError:
        print(f"❌ 에러: {file_path} 경로를 찾을 수 없습니다. 폴더 구조를 확인하세요.")
        