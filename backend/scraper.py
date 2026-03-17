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
                    scheme += line_str + "<br>"
                    
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
        const items = document.querySelectorAll('li');
        
        items.forEach(li => {
            const brandEl = li.querySelector('.txt_brand');
            const titleEl = li.querySelector('.tit_goods');
            const infoLink = li.querySelector('.link_info');
            
            const brandName = brandEl ? brandEl.innerText : "";
            const titleText = titleEl ? titleEl.innerText : "";
            const fullText = li.innerText;
            
            if (brandName.includes('오즈키즈') || titleText.includes('오즈키즈') || 
                fullText.includes('오즈키즈') || fullText.toUpperCase().includes('OZKIDS')) {
                
                const rankEl = li.querySelector('.num_rank');
                const rank = rankEl ? rankEl.innerText.trim() : "N/A";
                
                const imgEl = li.querySelector('.link_thumb img');
                const img = imgEl ? imgEl.src : "";
                
                let productCode = "";
                if (infoLink && infoLink.href) {
                    const match = infoLink.href.match(/product\/(\d+)/);
                    productCode = match ? match[1] : "";
                }
                
                const finalName = titleText.trim() || (infoLink ? infoLink.innerText.trim().split('\n')[1] : "Unknown");
                
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

    print(f"Found {len(unique_products)} OzKids products.")
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
        const items = document.querySelectorAll('gc-link, li[class*="item"], app-view-item, div[class*="product"]');
        let rankCounter = 1;
        
        items.forEach(li => {
            const brandEl = li.querySelector('.txt_brand, [class*="brand"]');
            const titleEl = li.querySelector('.tit_prd, .tit_goods, strong, [class*="tit"], [class*="name"]');
            const infoLink = li.querySelector('a');
            
            const brandName = brandEl ? brandEl.innerText : "";
            const titleText = titleEl ? titleEl.innerText : "";
            const fullText = li.innerText || "";
            
            // Sometimes gc-link has the href attribute directly
            let href = infoLink ? infoLink.href : "";
            if (!href && li.tagName.toLowerCase() === 'gc-link' && li.hasAttribute('href')) {
                href = li.getAttribute('href');
            }
            
            if (titleText) {
                if (brandName.includes('오즈키즈') || titleText.includes('오즈키즈') || 
                    fullText.includes('오즈키즈') || fullText.toUpperCase().includes('OZKIDS')) {
                    
                    const rankEl = li.querySelector('.num_rank, .num_badge, .badge_rank');
                    const rank = rankEl ? rankEl.innerText.trim() : String(rankCounter);
                    
                    const imgEl = li.querySelector('img');
                    const img = imgEl ? imgEl.src : "";
                    
                    let productCode = "";
                    if (href) {
                        const match = href.match(/product\/(\d+)/);
                        productCode = match ? match[1] : "";
                    }
                    
                    results.push({ rank, name: titleText.trim(), img, product_code: productCode });
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

    print(f"Found {len(unique_products)} OzKids products in Niece/Nephew tab.")
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
        
        data = {"last_updated": datetime.datetime.now().isoformat(), "events": [], "ranking": [], "niece_ranking": []}
        
        try:
            data["ranking"] = await scrape_kakao_ranking(page, kakao_ranking_url)
        except Exception as e:
            print(f"Error ranking: {e}")
            
        try:
            data["niece_ranking"] = await scrape_niece_ranking(page, kakao_niece_url)
        except Exception as e:
            print(f"Error niece ranking: {e}")
            
        try:
            data["events"] = await scrape_google_form(page, google_form_url)
        except Exception as e:
            print(f"Error form: {e}")
            # Load old events fallback
        try:
            # Construct relative path to frontend/data
            project_root = os.path.dirname(backend_dir)
            output_dir = os.path.join(project_root, "frontend", "data")
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, "current_data.json")
            
            # Load existing events if they exist to prevent overwriting with error fallback
            if not data["events"]:
                try:
                    if os.path.exists(output_file):
                        with open(output_file, "r", encoding='utf-8') as f:
                            old_data = json.load(f)
                            data["events"] = old_data.get("events", [])
                except: pass

            with open(output_file, "w", encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Successfully saved data to {output_file}")
        except Exception as e:
            print(f"Error saving: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
