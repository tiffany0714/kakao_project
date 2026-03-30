import json
import asyncio
from playwright.async_api import async_playwright
import datetime
import os
import re

async def scrape_google_form(page, url):
    print(f"Scraping Google Form: {url}")
    await page.goto(url)
    try:
        await page.wait_for_selector('div[role="heading"]', timeout=30000)
    except:
        pass
    
    text = await page.evaluate("document.body.innerText")
    
    events = []
    blocks = re.split(r'\n\d+\.\s*', '\n' + text)
    
    for block in blocks[1:]:
        lines = block.split('\n')
        name_line = lines[0].strip()
        if not name_line or len(name_line) > 100 or "이메일" in name_line:
            continue
            
        name = name_line
        schedule = ""
        deadline = ""
        scheme = ""
        
        mode = None
        for line in lines[1:]:
            line_str = line.strip()
            if not line_str:
                continue
            
            if "행사 확정 건에 한해" in line_str or "파일을 업로드하고" in line_str or "tiffany@ozkiz.com" in line_str:
                break
                
            if "일정" in line_str and ("☑️" in line_str or "☑" in line_str):
                schedule = line_str.replace("☑️", "").replace("☑", "").replace("일정:", "").replace("일정 :", "").strip()
                if not schedule:
                    mode = "schedule"
                else:
                    mode = "schedule_append"
            elif "제안기간" in line_str and ("☑️" in line_str or "☑" in line_str):
                deadline = line_str.replace("☑️", "").replace("☑", "").replace("제안기간:", "").replace("제안기간 :", "").strip()
                mode = "deadline"
            elif "지원스킴" in line_str and "✅" in line_str:
                mode = "scheme"
            elif line_str.startswith("☑️") or line_str.startswith("☑"):
                mode = "other"
            elif line_str.startswith("✅"):
                mode = "scheme"
            else:
                if mode == "schedule":
                    schedule = line_str
                    mode = "schedule_append"
                elif mode == "schedule_append":
                    schedule += " " + line_str
                elif mode == "deadline":
                    deadline += " " + line_str
                elif mode == "scheme":
                    scheme += line_str + "\n"
                    
        if name and (schedule or deadline or scheme):
            events.append({
                "area": "유아동 / 패션",
                "name": name.strip(),
                "schedule": schedule.strip() or "일정 미정",
                "scheme": scheme.strip().removesuffix("<br>") or "-",
                "deadline": deadline.strip() or "추후 안내"
            })
            
    return events

async def scrape_kakao_ranking(page, url):
    print(f"Scraping Kakao Ranking: {url}")
    await page.goto(url)
    await page.wait_for_timeout(5000)
    
    # Click on the '베이비·키즈패션' tab
    print("Selecting '베이비·키즈패션' category...")
    try:
        await page.evaluate('''() => {
            const tabs = Array.from(document.querySelectorAll('button, a, span'));
            const targetTab = tabs.find(el => el.innerText.trim() === '베이비·키즈패션');
            if (targetTab) {
                targetTab.click();
            }
        }''')
        await page.wait_for_timeout(3000)
    except Exception as e:
        print(f"Error clicking tab: {e}")

    # Deep scroll logic
    print("Performing deep scroll...")
    for i in range(25):
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(1000)
        if i % 10 == 0:
            print(f"Scrolling... ({i}/25)")

    # Granular detection logic with Product Code
    ozkids_products = await page.evaluate(r'''() => {
        const results = [];
        // Refined selector to target actual product cards and avoid containers
        const items = Array.from(document.querySelectorAll('li')).filter(li => {
            const hasBrand = li.querySelector('.txt_brand, [class*="brand"]');
            const hasTitle = li.querySelector('.tit_goods, .tit_prd, .tit_item, [class*="tit"], strong');
            // Ensure it's not a container by checking if it contains other li elements
            return hasBrand && hasTitle && li.querySelectorAll('li').length === 0;
        });
        
        items.forEach(li => {
            const brandEl = li.querySelector('.txt_brand, [class*="brand"]');
            const titleEl = li.querySelector('.tit_goods, .tit_prd, .tit_item, [class*="tit"], strong');
            const infoLink = li.querySelector('a');
            
            const brandName = brandEl ? brandEl.innerText.trim() : "";
            const titleText = titleEl ? titleEl.innerText.trim() : "";
            const fullText = li.innerText || "";
            
            if (brandName.includes('오즈키즈') || titleText.includes('오즈키즈') || 
                fullText.includes('오즈키즈') || fullText.toUpperCase().includes('OZKIDS')) {
                
                const rankEl = li.querySelector('.num_rank, .num_badge, [class*="rank"]');
                const rank = rankEl ? rankEl.innerText.trim() : "N/A";
                
                const imgEl = li.querySelector('img, [style*="background-image"]');
                let img = "";
                if (imgEl) {
                    if (imgEl.tagName.toLowerCase() === 'img') {
                        img = imgEl.src || imgEl.getAttribute('data-src') || imgEl.getAttribute('data-original') || "";
                    } else {
                        const style = imgEl.getAttribute('style') || "";
                        const match = style.match(/url\((['"]?)(.*?)\1\)/);
                        if (match) img = match[2];
                    }
                }
                
                let productCode = "";
                let href = infoLink ? infoLink.href : "";
                if (href) {
                    const match = href.match(/product\/(\d+)/);
                    productCode = match ? match[1] : "";
                }
                
                // Smart name extraction
                let finalName = titleText;
                if (!finalName || finalName === "오즈키즈" || finalName === "OZKIDS") {
                    const lines = fullText.split('\n').map(l => l.trim()).filter(l => l.length > 3 && !l.includes('원') && !l.match(/^\d+$/));
                    const betterName = lines.find(l => l !== "오즈키즈" && l !== brandName);
                    if (betterName) finalName = betterName;
                }
                
                // Unify formatting
                finalName = finalName.replace(/^\[오즈키즈\]\s*/, '').replace(/^오즈키즈\s*/, '').trim();
                finalName = `[오즈키즈] ${finalName}`;
                
                results.push({ rank, name: finalName, img, product_code: productCode });
            }
        });
        return results;
    }''')
    
    # Deduplicate
    seen = set()
    unique_products = []
    for p in ozkids_products:
        p_key = (p['rank'], p['product_code'] or p['name'])
        if p_key not in seen:
            seen.add(p_key)
            unique_products.append(p)

    print(f"Found {len(unique_products)} OzKids products: {[p['name'] for p in unique_products[:3]]}")
    return unique_products

async def scrape_niece_ranking(page, url):
    print(f"Scraping Niece/Nephew Ranking: {url}")
    await page.goto(url)
    await page.wait_for_timeout(5000)
    
    print("Selecting '조카선물' category...")
    try:
        await page.evaluate('''() => {
            const tabs = Array.from(document.querySelectorAll('button, a, span, div.tab_item'));
            const targetTab = tabs.find(el => el.innerText && el.innerText.trim() === '조카선물');
            if (targetTab) {
                targetTab.click();
            }
        }''')
        await page.wait_for_timeout(3000)
    except Exception as e:
        print(f"Error clicking tab: {e}")

    print("Performing deep scroll on Niece/Nephew page...")
    for i in range(25):
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(1000)
        if i % 10 == 0:
            print(f"Scrolling... ({i}/25)")

    ozkids_products = await page.evaluate(r'''() => {
        const results = [];
        // Recommendations use custom element <gc-link>
        // Find all collection blocks on the page
        const collections = document.querySelectorAll('app-view-collection, .wrap_list, [class*="collection"], [class*="component"]');
        let container = document;
        
        // Find the last collection that actually contains products (the infinite scroll main grid)
        for (let i = collections.length - 1; i >= 0; i--) {
            const hasProducts = collections[i].querySelector('gc-link, li[class*="item"], app-view-item');
            if (hasProducts) {
                container = collections[i];
                break;
            }
        }
        
        const items = container.querySelectorAll('gc-link, li[class*="item"], app-view-item, div[class*="product"]');
        let rankCounter = 1;
        
        items.forEach(li => {
            const brandEl = li.querySelector('.txt_brand, [class*="brand"]');
            const titleEl = li.querySelector('.tit_prd, .tit_goods, .tit_item, strong, [class*="tit"], [class*="name"]');
            const infoLink = li.querySelector('a');
            
            const brandName = brandEl ? brandEl.innerText.trim() : "";
            const titleText = titleEl ? titleEl.innerText.trim() : "";
            const fullText = li.innerText || "";
            
            // Sometimes gc-link has the href attribute directly
            let href = infoLink ? infoLink.href : "";
            if (!href && li.tagName.toLowerCase() === 'gc-link' && li.hasAttribute('href')) {
                href = li.getAttribute('href');
            }
            
            let isProductCard = false;
            if (titleText || brandName) isProductCard = true;
            if (href && href.includes('/product/')) isProductCard = true;
            
            if (isProductCard) {
                if (brandName.includes('오즈키즈') || titleText.includes('오즈키즈') || 
                    fullText.includes('오즈키즈') || fullText.toUpperCase().includes('OZKIDS')) {
                    
                    const rankEl = li.querySelector('.num_rank, .num_badge, .badge_rank, [class*="rank"]');
                    let adjustedRank = rankCounter - 95;
                    if (adjustedRank < 1) adjustedRank = Math.max(1, rankCounter);
                    const rank = rankEl ? rankEl.innerText.trim() : String(adjustedRank);
                    
                    const imgEl = li.querySelector('img, [style*="background-image"]');
                    let img = "";
                    if (imgEl) {
                        if (imgEl.tagName.toLowerCase() === 'img') {
                            img = imgEl.src || imgEl.getAttribute('data-src') || imgEl.getAttribute('data-original') || "";
                        } else {
                            const style = imgEl.getAttribute('style') || "";
                            const match = style.match(/url\((['"]?)(.*?)\1\)/);
                            if (match) img = match[2];
                        }
                    }
                    
                    let productCode = "";
                    if (href) {
                        const match = href.match(/product\/(\d+)/);
                        productCode = match ? match[1] : "";
                    }
                    
                    let finalName = titleText || fullText.split('\n')[0].trim();
                    // Clean up prefixes like "조카선물"
                    finalName = finalName.replace(/^["'“”]*(조카선물|어린이선물)[^"”“]*["'“”]*\s*/, '').trim();
                    finalName = finalName.replace(/^\[오즈키즈\]\s*/, '').replace(/^오즈키즈\s*/, '').trim();
                    finalName = `[오즈키즈] ${finalName}`;
                    
                    results.push({ rank, name: finalName, img, product_code: productCode });
                }
                rankCounter++;
            }
        });
        return results;
    }''')
    
    seen = set()
    unique_products = []
    for p in ozkids_products:
        p_key = (p['rank'], p['product_code'] or p['name'])
        if p_key not in seen:
            seen.add(p_key)
            unique_products.append(p)

    print(f"Found {len(unique_products)} OzKids products in Niece/Nephew tab: {[p['name'] for p in unique_products[:3]]}")
    return unique_products

async def main():
    google_form_url = "https://docs.google.com/forms/d/1jbIi_iNAhAIRWvB3v_d3rGi2kYvlRFoKom2fr5Dg_g4/viewform?edit_requested=true"
    kakao_ranking_url = "https://gift.kakao.com/ranking/category/3"
    kakao_niece_url = "https://gift.kakao.com/page/code/life_pregnancy?banner_id=1385&campaign_code=null"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        import os
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        state_path = os.path.join(backend_dir, "auth_state.json")
        if os.path.exists(state_path):
            context = await browser.new_context(storage_state=state_path)
            print(f"Loaded auth state for scraping.")
        else:
            context = await browser.new_context()
            
        page = await context.new_page()
        
        # Load existing data to preserve events if they are already polished
        existing_data = {}
        try:
            backend_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(backend_dir)
            output_file = os.path.join(project_root, "frontend", "data", "current_data.json")
            if os.path.exists(output_file):
                with open(output_file, "r", encoding='utf-8') as f:
                    existing_data = json.load(f)
        except: pass

        import datetime
        # 1. 파일 경로 설정
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_file = os.path.join(project_root, "frontend", "data", "current_data.json")
        history_file = os.path.join(project_root, "frontend", "data", "history_data.json")

        # 2. 기존 데이터 로드 (과거 기록을 보존하기 위함)
        existing_data = {}
        if os.path.exists(output_file):
            try:
                with open(output_file, "r", encoding='utf-8') as f:
                    existing_data = json.load(f)
            except: pass

        # 3. 데이터 저장용 그릇 생성 (초기화)
        data = {
            "last_updated": (datetime.datetime.now() + datetime.timedelta(hours=9)).isoformat(),
            "events": existing_data.get("events", []),
            "seasonal_ranking": [],
            "niece_ranking": [],
            "history": []
        }
        
        try:
            raw_ranking = await scrape_kakao_ranking(page, kakao_ranking_url)
            
            # 1-1. Map seasons from Excel
            import pandas as pd
            import os
            try:
                excel_path = os.path.join(project_root, 'strategy_items.xlsx')
                df = pd.read_excel(excel_path)
                season_map = {}
                for _, row in df.iterrows():
                    code = str(row.get('상품번호', '')).strip()
                    name = str(row.get('상품명', '')).strip()
                    season = str(row.get('계절', '기타')).strip()
                    if code and code != 'nan':
                        season_map[code] = season
                    if name and name != 'nan':
                        season_map[name] = season
                
                # 1-2. Apply seasons to raw ranking
                for p in raw_ranking:
                    p_code = str(p.get('product_code', ''))
                    p_name = str(p.get('name', ''))
                    clean_name = p_name.replace('[오즈키즈]', '').strip()
                    
                    if p_code in season_map:
                        p['season'] = season_map[p_code]
                    elif clean_name in season_map:
                        p['season'] = season_map[clean_name]
                    elif p_name in season_map:
                        p['season'] = season_map[p_name]
                    else:
                        p['season'] = '기타'
            except Exception as e:
                print(f"Error reading strategy_items.xlsx: {e}")
                for p in raw_ranking:
                    p['season'] = '기타'
                    
            data["seasonal_ranking"] = raw_ranking
        except Exception as e:
            print(f"Error ranking: {e}")
            
           
        # 3. Handle Events (Merge new with existing to preserve history/formatting)
        new_events = []
        try:
            new_events = await scrape_google_form(page, google_form_url)
        except Exception as e:
            print(f"Error scraping Google Form: {e}")

        # Merge logic: Keep existing ones (they have manual formatting), add new ones
        existing_events = existing_data.get("events", [])
        existing_event_names = {e["name"] for e in existing_events}
        
        merged_events = list(existing_events)
        for ne in new_events:
            if ne["name"] not in existing_event_names:
                print(f"Adding new event: {ne['name']}")
                merged_events.append(ne)
        
        data["events"] = merged_events
        try:
            # Construct relative path to frontend/data
            project_root = os.path.dirname(backend_dir)
            output_dir = os.path.join(project_root, "frontend", "data")
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, "current_data.json")
            
            # 1. 오늘 날짜 기록 생성
            today_str = (datetime.datetime.now() + datetime.timedelta(hours=9)).strftime("%Y-%m-%d")
            today_record = {
                "date": today_str,
                "seasonal_ranking": data.get("seasonal_ranking", []),
                "niece_ranking": data.get("niece_ranking", [])
            }

            # 2. 히스토리 업데이트 (기존 기록 + 오늘 기록)
            # 기존에 있던 history를 가져와서 오늘 날짜와 겹치는 게 있다면 지우고 새로 추가합니다.
            history = data.get("history", [])
            history = [r for r in history if r.get('date') != today_str]
            history.append(today_record)
            
            # 최근 30일 데이터만 남기고 저장 (용량 관리)
            data["history"] = history[-30:]

            # 3. 최종 파일 저장 (current_data.json)
            with open(output_file, "w", encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            # 4. 별도의 백업용 히스토리 파일도 저장 (선택 사항이지만 안전함)
            history_file = os.path.join(os.path.dirname(output_file), "history_data.json")
            with open(history_file, "w", encoding='utf-8') as f:
                json.dump(data["history"], f, ensure_ascii=False, indent=2)

            print(f"데이터 업데이트 및 히스토리 누적 완료: {today_str}")
            print(f"Successfully saved merged data to {output_file}")
        except Exception as e:
            print(f"Error saving: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
