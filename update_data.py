import requests
import pandas as pd
import json
import os
from datetime import datetime

# 1. 구글 폼 응답 수집 (CSV 내보내기 링크 활용)
def get_google_form_events():
    # 구글 시트 '웹에 게시' -> CSV 링크를 여기에 넣어야 합니다.
    # 우선 형식만 맞춰두겠습니다.
    sheet_url = "https://docs.google.com/spreadsheets/d/1jbIi_iNAhAIRWvB3v_d3rGi2kYvlRFoKom2fr5Dg_g4/export?format=csv"
    try:
        df = pd.read_csv(sheet_url)
        events = []
        for _, row in df.iterrows():
            events.append({
                "name": row['행사명'],
                "schedule": row['일정'],
                "deadline": row['마감일'],
                "scheme": row['행사스킴']
            })
        return events
    except:
        return []

# 2. 카테고리 랭킹 수집 (엑셀 상품 기반)
def get_category_ranking():
    url = "https://gift.kakao.com/a/v1/rank/category/3?page=0&size=100"
    res = requests.get(url).json()
    items = res.get('contents', [])
    
    df = pd.read_excel('strategy_items.xlsx')
    results = []
    for _, row in df.iterrows():
        code = str(row['상품번호'])
        match = next((i for i, item in enumerate(items) if str(item.get('productId')) == code), None)
        rank = match + 1 if match is not None else 999
        img = items[match].get('imageUrl') if match is not None else ""
        results.append({"season": row['계절'], "code": code, "name": row['상품명'], "rank": rank, "img": img})
    return results

# 3. 조카선물 탭 순위 (오즈키즈 찾기)
def get_niece_ranking():
    url = "https://gift.kakao.com/a/v1/pages/code/life_pregnancy"
    res = requests.get(url).json()
    
    oz_items = []
    rank_idx = 1
    for section in res.get('sections', []):
        for product in section.get('products', []):
            if "오즈키즈" in product.get('brandName', '') or "오즈키즈" in product.get('productName', ''):
                oz_items.append({
                    "code": str(product.get('productId')),
                    "name": product.get('productName'),
                    "rank": rank_idx
                })
            rank_idx += 1
    return oz_items

# 4. 통합 및 저장
def main():
    events = get_google_form_events()
    curr_cat = get_category_ranking()
    curr_niece = get_niece_ranking()
    
    # 이력(history.json) 로직 생략 (간결화)
    # 현재 데이터 저장
    final_data = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "events": events,
        "seasonal_ranking": curr_cat,
        "niece_ranking": curr_niece
    }
    
    os.makedirs('frontend/data', exist_ok=True)
    with open('frontend/data/current_data.json', 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    main()