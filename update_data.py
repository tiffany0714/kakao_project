import requests
import pandas as pd
import json
import os
import subprocess
from datetime import datetime, timedelta

def main():
    # 1. 스크래퍼 먼저 실행
    try:
        print("실시간 스크래퍼 실행 중...")
        subprocess.run(["python", os.path.join('backend', 'scraper.py')], check=False)
        print("스크래퍼 완료")
    except Exception as e:
        print("스크래퍼 실행 오류:", e)

    h_path = 'frontend/data/history.json'
    history = json.load(open(h_path, 'r', encoding='utf-8')) if os.path.exists(h_path) else {}

    today_str = datetime.now().strftime("%Y-%m-%d")
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    last_week_str = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    prev_list = history.get(yesterday_str, {})
    week_list = history.get(last_week_str, {})

    def get_diff(code, old_data_dict, category_key, current_rank):
        old_list = old_data_dict.get(category_key, [])
        if not old_list:
            return "-"
        p_item = next((item for item in old_list if str(item.get('product_code')) == code), None)
        if p_item:
            p_rank = int(p_item.get('rank', 999))
            if p_rank != 999:
                change = p_rank - current_rank
                if change > 0: return f"+{change}"
                if change < 0: return f"{change}"
                return "-"
        return "신규"

    headers_kakao = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://gift.kakao.com",
        "Content-Type": "application/json"
    }

    # 2. 전략상품 랭킹
    print("전략상품 랭킹 수집 중...")

    # 카카오 API로 전체 순위 가져오기
    c_items = []
    for page_num in range(25):
        c_res = requests.post(
            "https://gift.kakao.com/a/rank/v1/gift-rank/ranking-tab/category-tab/search",
            headers=headers_kakao,
            json={"navId": 1, "page": page_num, "size": 20, "subNavId": 11100}
        ).json()
        products = c_res.get('products', [])
        if not products:
            break
        c_items.extend(products)
        if c_res.get('last', True):
            break
    print(f"카카오 랭킹 총 {len(c_items)}개 수집")

    # API 순위 맵 (product_code → rank)
    api_rank_map = {str(item.get('productId', '')): idx + 1 for idx, item in enumerate(c_items)}
    api_name_map = {str(item.get('productId', '')): item.get('name', '') for item in c_items}
    api_img_map  = {str(item.get('productId', '')): (item.get('image') or {}).get('imageUrl', '') for item in c_items}

    # 스크래퍼 결과에서 상품 코드 가져오기
    seasonal = []
    cd_path = 'frontend/data/current_data.json'
    if os.path.exists(cd_path):
        try:
            cd = json.load(open(cd_path, 'r', encoding='utf-8'))
            scraped = cd.get('seasonal_ranking', [])
            for s in scraped:
                code = str(s.get('product_code', ''))
                if not code:
                    continue
                # API에서 실제 순위 찾기
                real_rank = api_rank_map.get(code)
                if not real_rank:
                    # API 500위 밖이면 scraper 순위 사용
                    scraper_rank = s.get('rank')
                    if scraper_rank and str(scraper_rank).isdigit():
                        real_rank = int(scraper_rank)
                    else:
                        continue
                seasonal.append({
                    "season": s.get('season', '기타'),
                    "product_code": code,
                    "name": api_name_map.get(code) or s.get('name', ''),
                    "img": api_img_map.get(code) or s.get('img', ''),
                    "rank": real_rank,
                    "diff": get_diff(code, prev_list, 'category', real_rank),
                    "week_diff": get_diff(code, week_list, 'category', real_rank)
                })
            seasonal.sort(key=lambda x: x['rank'])
            print(f"전략상품 {len(seasonal)}개 완료")
        except Exception as e:
            print("전략상품 처리 오류:", e)

    # 3. 조카선물 랭킹
    print("조카선물 랭킹 수집 중...")
    niece = []
    if os.path.exists(cd_path):
        try:
            cd = json.load(open(cd_path, 'r', encoding='utf-8'))
            scraped_niece = cd.get('niece_ranking', [])
            for s in scraped_niece:
                code = str(s.get('product_code', ''))
                rank = s.get('rank')
                if not rank or not str(rank).isdigit():
                    continue
                # 상단 고정 섹션(산모를 위한 선물 10개 + 아이를 위한 선물 8개 = 18개) 제외
                rank = max(1, int(rank) - 20)
                niece.append({
                    "product_code": code,
                    "name": s.get('name', ''),
                    "rank": rank,
                    "img": s.get('img', ''),
                    "season": s.get('season', '기타'),
                    "diff": get_diff(code, prev_list, 'niece', rank),
                    "week_diff": get_diff(code, week_list, 'niece', rank)
                })
            niece.sort(key=lambda x: x['rank'])
            print(f"조카선물 {len(niece)}개 완료")
        except Exception as e:
            print("조카선물 처리 오류:", e)

    # 4. 히스토리 저장
    history[today_str] = {"category": seasonal, "niece": niece}
    if len(history) > 30:
        for k in sorted(history.keys())[:-30]:
            del history[k]

    os.makedirs('frontend/data', exist_ok=True)
    with open(h_path, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=4, ensure_ascii=False)

    # 5. current_data.json 업데이트
    curr_path = 'frontend/data/current_data.json'
    old = json.load(open(curr_path, 'r', encoding='utf-8')) if os.path.exists(curr_path) else {"events": []}

    final = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "events": old.get("events", []),
        "seasonal_ranking": seasonal,
        "niece_ranking": niece
    }
    with open(curr_path, 'w', encoding='utf-8') as f:
        json.dump(final, f, indent=4, ensure_ascii=False)

    print(f"업데이트 완료: {today_str}")

if __name__ == "__main__":
    main()