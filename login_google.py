import asyncio
from playwright.async_api import async_playwright
import os

async def login():
    url = "https://docs.google.com/forms/d/1jbIi_iNAhAIRWvB3v_d3rGi2kYvlRFoKom2fr5Dg_g4/viewform?edit_requested=true"
    async with async_playwright() as p:
        # Launch non-headless browser so the user can see and interact with it
        browser = await p.chromium.launch(headless=False, args=['--window-size=1000,800'])
        context = await browser.new_context(viewport={'width': 1000, 'height': 800})
        page = await context.new_page()
        
        print(f"Navigating to {url}")
        print("Please log in to Google in the newly opened browser window (Timeout: 3 mins)")
        await page.goto(url)
        
        try:
            # Wait for the heading of the form to appear (indicating successful access to the form)
            await page.wait_for_selector('div[role="heading"]', timeout=180000)
            print("Login successful! Saving session state...")
            
            # Save storage state
            os.makedirs("backend", exist_ok=True)
            state_path = "backend/auth_state.json"
            await context.storage_state(path=state_path)
            print(f"Session saved to: {state_path}")
            
        except Exception as e:
            print(f"Timeout or error: {e}")
            print("Did not detect form page within 3 minutes.")
            
        finally:
            await browser.close()
            print("Closing browser.")

if __name__ == "__main__":
    asyncio.run(login())
