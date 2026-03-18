
import asyncio
from playwright.async_api import async_playwright
import json

async def test_ranking_scrape():
    url = "https://gift.kakao.com/ranking/category/3"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        print(f"Opening {url}...")
        await page.goto(url)
        await page.wait_for_timeout(5000)
        
        # Click category tab if needed
        await page.evaluate('''() => {
            const tabs = Array.from(document.querySelectorAll('button, a, span'));
            const targetTab = tabs.find(el => el.innerText.trim() === '베이비·키즈패션');
            if (targetTab) targetTab.click();
        }''')
        await page.wait_for_timeout(3000)
        
        items_count = await page.evaluate('''() => {
            const items = document.querySelectorAll('li, [class*="item"]');
            return items.length;
        }''')
        print(f"Found {items_count} potential items with broad selector.")
        
        # Check first item text
        first_item_text = await page.evaluate('''() => {
            const items = document.querySelectorAll('li, [class*="item"]');
            return items[0] ? items[0].innerText.substring(0, 500) : "NONE";
        }''')
        print(f"First item text (first 500 chars):\n{first_item_text}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_ranking_scrape())
