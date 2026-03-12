import asyncio
from playwright.async_api import async_playwright
import os

async def scrape_form():
    url = "https://docs.google.com/forms/d/1jbIi_iNAhAIRWvB3v_d3rGi2kYvlRFoKom2fr5Dg_g4/viewform?edit_requested=true"
    state_path = "backend/auth_state.json"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        if os.path.exists(state_path):
            context = await browser.new_context(storage_state=state_path)
            print(f"Loaded auth state from {state_path}")
        else:
            context = await browser.new_context()
            print("No auth state found.")
            
        page = await context.new_page()
        print(f"Navigating to {url}")
        await page.goto(url)
        
        try:
            await page.wait_for_selector('div[role="heading"]', timeout=15000)
            print("Form loaded successfully.")
            
            # Extract main text
            description_element = await page.query_selector('div[id="i4"] + div')
            form_text = await page.evaluate("document.body.innerText")
            
            with open('form_content_auth.txt', 'w', encoding='utf-8') as f:
                f.write(form_text)
            print("Form content saved to form_content_auth.txt")
            
        except Exception as e:
            print(f"Error accessing form: {e}")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_form())
