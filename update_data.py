import requests
import json
import os
import pandas as pd
from datetime import datetime, timedelta

# [경로 설정]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "frontend", "data")
CURRENT_FILE = os.path.join(DATA_DIR, "current_data.json")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json") # 순위 기록 저장용
STRATEGY_EXCEL = os.path.join(BASE_DIR, "strategy_items.xlsx") # 엑셀 파일 이름

# 1. 카카오 쇼핑 실시간 랭킹 전체 긁어오기 (1위~100위까지 넉넉하게)
def get_kakao_full_ranking():
    try:
        url = "https://shoppinghow.kakao.com/siso/p/api/best/main.json?v=2"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        items = response.json().get('itemList', [])
        
        # 딕셔너리 형태로 저장 (키: 상품코드, 값: 순위 및 정보)
        return {str(item.get('productId')): {
            "name": item.get('productName'),
            "img": item.get('imageUrl', '').replace('//', 'https://') if item.get('imageUrl') else "",
            "rank": i + 1
        } for i, item in enumerate(items)}
    except Exception as e:
        print(f"❌ 랭킹 수집 에러: {e}")
        return {}

if __name__ == "__main__":
    # 시간 설정
    now = datetime.utcnow() + timedelta(hours=9)
    today_str = now.strftime("%Y-%m-%d")
    yesterday_str = (now - timedelta(days=1)).strftime("%Y-%m-%d")

    os.makedirs(DATA_DIR, exist_ok=True)

    # 1. 카카오 전체 데이터 가져오기
    all_rankings = get_kakao_full_ranking()

    # 2. 히스토리 로드 (어제 순위 확인용)
    history = {}
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)

    # 3. 엑셀 파일(strategy_items.xlsx) 읽기
    seasonal_ranking = []
    try:
        df = pd.read_excel(STRATEGY_EXCEL)
        for _, row in df.iterrows():
            code = str(row['상품번호'])
            season = row['계절']
            my_name = row['상품명']
            
            # 현재 순위 확인
            item_data = all_rankings.get(code)
            current_rank = item_data['rank'] if item_data else "순위권 밖"
            img_url = item_data['img'] if item_data else ""
            
            # 등락 계산 (어제 기록이 있을 때만)
            diff = 0
            yesterday_rank = history.get(yesterday_str, {}).get(code)
            if isinstance(current_rank, int) and yesterday_rank:
                diff = yesterday_rank - current_rank # 어제 10위 - 오늘 8위 = +2

            seasonal_ranking.append({
                "season": season,
                "name": my_name,
                "code": code,
                "img": img_url,
                "rank": current_rank,
                "diff": diff
            })
    except Exception as e:
        print(f"⚠️ 엑셀 읽기 실패 또는 파일 없음: {e}")

    # 4. 결과 통합 저장
    data = {
        "last_updated": now.isoformat(),
        "seasonal_ranking": seasonal_ranking,
        "total_ranking": list(all_rankings.values())[:20] # 전체 랭킹 상위 20개
    }

    with open(CURRENT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    # 5. 오늘 순위 히스토리에 기록 (내일을 위해)
    history[today_str] = {code: info['rank'] for code, info in all_rankings.items()}
    # 너무 오래된 기록은 삭제 (최근 30일치만 유지)
    if len(history) > 30:
        oldest_date = min(history.keys())
        del history[oldest_date]
        
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)

    print(f"✅ 업데이트 완료! 추적 상품 수: {len(seasonal_ranking)}개")