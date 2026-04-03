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

    print("Selecting '베이비·키즈패션' category...")
    try:
        await page.evaluate('''() => {
            const tabs = Array.from(document.querySelectorAll('button, a, span'));
            const targetTab = tabs.find(el => el.innerText.trim() === '베이비·키즈패션');
            if (targetTab) targetTab.click();
        }''')
        await page.wait_for_timeout(3000)
    except Exception as e:
        print(f"Error clicking tab: {e}")

    print("Performing deep scroll...")
    for i in range(25):
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(1000)
        if i % 10 == 0:
            print(f"Scrolling... ({i}/25)")

    try:
        diag = await page.evaluate('''() => {
            const allLinks = Array.from(document.querySelectorAll('a[href*="/product/"]'));
            const seenCodes = new Set();
            const uniqueLinks = [];
            allLinks.forEach(a => {
                const m = a.href.match(/product\\/(\\d+)/);
                const code = m ? m[1] : '';
                if (code && !seenCodes.has(code)) {
                    seenCodes.add(code);
                    uniqueLinks.push(code);
                }
            });
            // 오즈키즈 상품 인덱스 찾기
            const ozCodes = ['11387692', '11446625', '12093091', '11239447', '12070123'];
            const ozIndices = ozCodes.map(c => ({ code: c, idx: uniqueLinks.indexOf(c) })).filter(x => x.idx >= 0);
            return {
                total_links: allLinks.length,
                unique_links: uniqueLinks.length,
                first_10: uniqueLinks.slice(0, 10),
                oz_indices: ozIndices
            };
        }''')
        print("DEBUG ranking unique links:", diag)
    except Exception as e:
        print("DEBUG diag error:", e)

    ozkids_products = await page.evaluate(r'''() => {
        const results = [];
        const allLinks = Array.from(document.querySelectorAll('a[href*="/product/"]'));
        const seenCodes = new Set();

        allLinks.forEach(a => {
            const m = a.href.match(/product\/(\d+)/);
            const code = m ? m[1] : '';
            if (!code || seenCodes.has(code)) return;

            const li = a.closest('li') || a.closest('gc-link') || a.parentElement;
            const txt = (li && li.innerText) || a.innerText || '';

            if (txt.includes('오즈키즈') || txt.toUpperCase().includes('OZKIDS')) {
                seenCodes.add(code);

                // 순위 숫자를 li 안에서 직접 찾기
                let rank = null;

                // 방법 1: 순위 전용 엘리먼트
                const rankEl = li && li.querySelector('.num_rank, .num_badge, .badge_rank, [class*="rank_num"], [class*="ranknum"]');
                if (rankEl) {
                    const t = rankEl.innerText.trim();
                    if (/^\d+$/.test(t)) rank = parseInt(t);
                }

                // 방법 2: li 텍스트에서 맨 앞 숫자 추출
                if (!rank) {
                    const lines = txt.split('\n').map(l => l.trim()).filter(l => l);
                    for (const line of lines) {
                        if (/^\d+$/.test(line) && parseInt(line) < 600) {
                            rank = parseInt(line);
                            break;
                        }
                    }
                }

                // 방법 3: 부모 요소에서 순위 찾기
                if (!rank) {
                    let parent = li && li.parentElement;
                    for (let i = 0; i < 3 && parent; i++) {
                        const rankEl2 = parent.querySelector('.num_rank, .num_badge, [class*="rank"]');
                        if (rankEl2) {
                            const t = rankEl2.innerText.trim();
                            if (/^\d+$/.test(t)) { rank = parseInt(t); break; }
                        }
                        parent = parent.parentElement;
                    }
                }

                const imgEl = li ? li.querySelector('img') : null;
                const img = imgEl ? (imgEl.src || imgEl.getAttribute('data-src') || '') : '';

                const titleEl = li && li.querySelector('strong, [class*="tit"], [class*="name"]');
                let name = titleEl ? titleEl.innerText.trim() : '';
                if (!name) {
                    const lines = txt.split('\n').map(l => l.trim()).filter(l => l.length > 3);
                    name = lines.find(l => !l.match(/^\d+$/) && !l.includes('원') && l.includes('오즈키즈')) || '';
                }

                name = name.replace(/^\[오즈키즈\]\s*/, '').replace(/^오즈키즈\s*/, '').trim();
                name = `[오즈키즈] ${name}`;

                results.push({ rank: rank || 999, name, img, product_code: code });
            }
        });

        return results;
    }''')

    seen = set()
    unique_products = []
    for p in ozkids_products:
        key = p['product_code'] or p['name']
        if key not in seen:
            seen.add(key)
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
            if (targetTab) targetTab.click();
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

    try:
        diag2 = await page.evaluate('''() => {
            const allLinks = Array.from(document.querySelectorAll('a[href*="/product/"]'));
            const seenCodes = new Set();
            const uniqueLinks = [];
            allLinks.forEach(a => {
                const m = a.href.match(/product\\/(\d+)/);
                const code = m ? m[1] : '';
                if (code && !seenCodes.has(code)) {
                    seenCodes.add(code);
                    uniqueLinks.push(code);
                }
            });
            return {
                total_links: allLinks.length,
                unique_links: uniqueLinks.length,
                first_10: uniqueLinks.slice(0, 10)
            };
        }''')
        print("DEBUG niece unique links:", diag2)
    except Exception as e:
        print("DEBUG diag error (niece):", e)

    # 상단 고정 섹션 상품 수 파악
    fixed_count = await page.evaluate(r'''() => {
        // 산모를 위한 선물 + 아이를 위한 선물 섹션 링크 수집
        const fixedCodes = new Set();
        const allText = document.body.innerText;
        const sections = document.querySelectorAll('[class*="component"], [class*="section"], [class*="collection"]');
        sections.forEach(sec => {
            const txt = sec.innerText || '';
            if (txt.includes('산모를 위한') || txt.includes('아이를 위한')) {
                sec.querySelectorAll('a[href*="/product/"]').forEach(a => {
                    const m = a.href.match(/product\/(\d+)/);
                    if (m) fixedCodes.add(m[1]);
                });
            }
        });
        return fixedCodes.size;
    }''')
    print(f"DEBUG 상단 고정 섹션 상품 수: {fixed_count}")

    ozkids_products = await page.evaluate(r'''() => {
        const results = [];

        // 상단 고정 섹션 상품 코드 수집
        const fixedCodes = new Set();
        const sections = document.querySelectorAll('[class*="component"], [class*="section"], [class*="collection"]');
        sections.forEach(sec => {
            const txt = sec.innerText || '';
            if (txt.includes('산모를 위한') || txt.includes('아이를 위한')) {
                sec.querySelectorAll('a[href*="/product/"]').forEach(a => {
                    const m = a.href.match(/product\/(\d+)/);
                    if (m) fixedCodes.add(m[1]);
                });
            }
        });

        const allLinks = Array.from(document.querySelectorAll('a[href*="/product/"]'));
        const seenCodes = new Set();
        const filteredLinks = [];

        allLinks.forEach(a => {
            const m = a.href.match(/product\/(\d+)/);
            const code = m ? m[1] : '';
            if (!code || seenCodes.has(code) || fixedCodes.has(code)) return;
            seenCodes.add(code);
            filteredLinks.push({ href: a.href, code, el: a });
        });

        filteredLinks.forEach(({ href, code, el }, idx) => {
            const li = el.closest('li') || el.closest('gc-link') || el.parentElement;
            const txt = (li && li.innerText) || el.innerText || '';

            if (txt.includes('오즈키즈') || txt.toUpperCase().includes('OZKIDS')) {
                const imgEl = li ? li.querySelector('img') : null;
                const img = imgEl ? (imgEl.src || imgEl.getAttribute('data-src') || '') : '';

                const titleEl = li && li.querySelector('strong, [class*="tit"], [class*="name"]');
                let name = titleEl ? titleEl.innerText.trim() : '';
                if (!name) {
                    const lines = txt.split('\n').map(l => l.trim()).filter(l => l.length > 3);
                    name = lines.find(l => !l.match(/^\d+$/) && !l.includes('원') && l.includes('오즈키즈')) || '';
                }

                name = name.replace(/^\[오즈키즈\]\s*/, '').replace(/^오즈키즈\s*/, '').trim();
                name = `[오즈키즈] ${name}`;

                const rank = idx + 1;
                results.push({ rank, name, img, product_code: code });
            }
        });

        return results;
    }''')

    seen = set()
    unique_products = []
    for p in ozkids_products:
        key = p['product_code'] or p['name']
        if key not in seen:
            seen.add(key)
            unique_products.append(p)

    print(f"Found {len(unique_products)} OzKids products in Niece/Nephew tab: {[p['name'] for p in unique_products[:3]]}")
    return unique_products


async def main():
    google_form_url = "https://docs.google.com/forms/d/1jbIi_iNAhAIRWvB3v_d3rGi2kYvlRFoKom2fr5Dg_g4/viewform?edit_requested=true"
    kakao_ranking_url = "https://gift.kakao.com/ranking/category/3"
    kakao_niece_url = "https://gift.kakao.com/page/code/life_pregnancy?banner_id=1385&campaign_code=null"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        backend_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(backend_dir)
        output_dir = os.path.join(project_root, "frontend", "data")
        os.makedirs(output_dir, exist_ok=True)

        output_file = os.path.join(output_dir, "current_data.json")
        history_file = os.path.join(output_dir, "history_data.json")

        context = await browser.new_context()
        page = await context.new_page()

        existing_data = {}
        if os.path.exists(output_file):
            try:
                with open(output_file, "r", encoding='utf-8') as f:
                    existing_data = json.load(f)
            except:
                pass

        seasonal_ranking = []
        niece_ranking = []
        new_events = []

        try:
            seasonal_ranking = await scrape_kakao_ranking(page, kakao_ranking_url)
            niece_ranking = await scrape_niece_ranking(page, kakao_niece_url)
            new_events = await scrape_google_form(page, google_form_url)
        except Exception as e:
            print(f"데이터 수집 중 에러: {e}")

        try:
            import pandas as pd
            excel_path = os.path.join(project_root, 'strategy_items.xlsx')
            season_map = {}

            if os.path.exists(excel_path):
                df = pd.read_excel(excel_path)
                for _, row in df.iterrows():
                    code = str(row.get('상품번호', '')).strip()
                    name = str(row.get('상품명', '')).strip()
                    season = str(row.get('계절', '기타')).strip()
                    if code and code != 'nan': season_map[code] = season
                    if name and name != 'nan': season_map[name] = season

            def apply_season(item_list):
                for p in item_list:
                    p_code = str(p.get('product_code', '')).strip()
                    p_name = str(p.get('name', '')).strip()

                    clean_name = p_name.replace('[오즈키즈]', '')
                    for target in ['"', '"', '"', '조카선물여아', '조카선물', '어린이선물']:
                        clean_name = clean_name.replace(target, '')
                    clean_name = clean_name.strip()

                    if p_code in season_map:
                        p['season'] = season_map[p_code]
                    elif clean_name in season_map:
                        p['season'] = season_map[clean_name]
                    elif p_name in season_map:
                        p['season'] = season_map[p_name]
                    else:
                        matched = False
                        for ex_name, ex_season in season_map.items():
                            if len(ex_name) > 5 and (ex_name in clean_name or clean_name in ex_name):
                                p['season'] = ex_season
                                matched = True
                                break
                        if not matched:
                            p['season'] = '기타'

            apply_season(seasonal_ranking)
            apply_season(niece_ranking)

        except Exception as e:
            print(f"계절 매칭 중 에러: {e}")
            for p in (seasonal_ranking + niece_ranking):
                p['season'] = '기타'

        today_str = (datetime.datetime.now() + datetime.timedelta(hours=9)).strftime("%Y-%m-%d")
        history = existing_data.get("history", [])

        today_record = {
            "date": today_str,
            "seasonal_ranking": seasonal_ranking,
            "niece_ranking": niece_ranking
        }
        history = [r for r in history if r.get('date') != today_str]
        history.append(today_record)

        final_data = {
            "last_updated": (datetime.datetime.now() + datetime.timedelta(hours=9)).isoformat(),
            "events": existing_data.get("events", []),
            "seasonal_ranking": seasonal_ranking,
            "niece_ranking": niece_ranking,
            "history": history[-30:]
        }

        try:
            with open(output_file, "w", encoding='utf-8') as f:
                json.dump(final_data, f, ensure_ascii=False, indent=2)
            with open(history_file, "w", encoding='utf-8') as f:
                json.dump(final_data["history"], f, ensure_ascii=False, indent=2)
            print(f"업데이트 완료: {today_str}")
        except Exception as e:
            print(f"파일 저장 중 에러: {e}")
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())