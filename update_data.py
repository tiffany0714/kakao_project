import requests
import json
import os
from datetime import datetime, timedelta

# [핵심 1] 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, "frontend", "data", "current_data.json")

# 1. 카카오 쇼핑 실시간 랭킹 진짜로 긁어오기
def get_kakao_realtime_ranking():
    try:
        # 카카오 쇼핑 랭킹 API 호출
        url = "https://shoppinghow.kakao.com/siso/p/api/best/main.json?v=2"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        raw_data = response.json()
        # itemList에서 상위 20개 추출
        items = raw_data.get('itemList', [])[:20]
        
        rankings = []
        for i, item in enumerate(items):
            rankings.append({
                "rank": i + 1,
                "name": item.get('productName', '상품명 없음'),
                # 이미지 주소가 //로 시작하는 경우 https: 추가
                "img": item.get('imageUrl', '').replace('//', 'https://') if item.get('imageUrl') else "",
                "product_code": item.get('productId', '---'),
                "diff_yesterday": 0, # API 데이터에 따라 추가 가능
                "diff_last_week": 0
            })
        return rankings
    except Exception as e:
        print(f"❌ 랭킹 수집 에러: {e}")
        return []

# 2. 조카 선물 랭킹 (예시로 랭킹 상위권 데이터 활용)
def get_nephew_gift_ranking(real_rankings):
    # 실제로는 특정 키워드(장난감 등)로 검색한 결과를 넣을 수 있습니다.
    # 우선은 수집된 랭킹 중 5개를 샘플로 넣습니다.
    return real_rankings[:5]

if __name__ == "__main__":
    # 🕒 한국 시간(KST) 계산
    seoul_time = datetime.utcnow() + timedelta(hours=9)
    formatted_time = seoul_time.isoformat()

    # 폴더 생성
    os.makedirs(os.path.dirname(FILE_PATH), exist_ok=True)

    # 기본 데이터 구조
    data = {
        "last_updated": formatted_time,
        "events": [],
        "ranking": [],
        "niece_ranking": []
    }
    
    # [핵심 2] 기존 이벤트 데이터 유지
    try:
        if os.path.exists(FILE_PATH):
            with open(FILE_PATH, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
                data["events"] = existing_data.get("events", [])
    except Exception as e:
        print(f"기존 데이터 로드 실패: {e}")

    # [핵심 3] 진짜 데이터 수집 및 할당
    print("🚀 카카오 실시간 랭킹 수집 시작...")
    real_rankings = get_kakao_realtime_ranking()
    data["ranking"] = real_rankings
    data["niece_ranking"] = get_nephew_gift_ranking(real_rankings)

    # 최종 파일 저장
    try:
        with open(FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"✅ 업데이트 성공! 수집된 상품: {len(data['ranking'])}개")
    except Exception as e:
        print(f"❌ 저장 에러: {e}")