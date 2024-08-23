import asyncio
import logging
import os
import json
import random
import re
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import aiofiles

print("Hello!")
print("Welcome to Web Crawler!")
print("By: tkFlash!")

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger().addHandler(console)

error_logger = logging.getLogger('error_logger')

# Base directory for screenshots
BASE_SCREENSHOTS_DIR = 'screenshots'
os.makedirs(BASE_SCREENSHOTS_DIR, exist_ok=True)

# JSON file for storing all changes
CHANGES_JSON_FILE = 'changes.json'
changes_data = []

# Semaphore to limit the number of concurrent tasks
semaphore = asyncio.Semaphore(5)  # Adjust as needed

def sanitize_filename(filename):
    """Sanitizes a string to be a valid filename by removing or replacing invalid characters."""
    return re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', filename)

async def take_screenshot(page, screenshot_path: str):
    """Takes a screenshot of the current page with a longer timeout."""
    try:
        await page.screenshot(path=screenshot_path, full_page=True, timeout=60000)
        logging.info(f"Screenshot saved: {screenshot_path}")
    except PlaywrightTimeoutError:
        error_logger.error("Failed to take screenshot: Timeout exceeded while waiting for fonts or other resources to load.")
    except Exception as e:
        error_logger.error(f"Failed to take screenshot: {e}")

async def monitor_changes(page, click_description):
    """Monitors and logs changes on the page after a click."""
    changes = {}
    try:
        html_content = await page.content()
        js_content = await page.evaluate('Array.from(document.scripts).map(s => s.outerHTML).join("\\n")')
        css_content = await page.evaluate('Array.from(document.styleSheets).map(s => s.ownerNode.outerHTML).join("\\n")')
        current_url = page.url

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        changes = {
            "timestamp": now,
            "click_description": click_description,
            "url": current_url,
            "html_snippet": html_content[:200],
            "js_snippet": js_content[:200],
            "css_snippet": css_content[:200]
        }
        logging.info("Changes detected and logged.")
    except Exception as e:
        error_logger.error(f"Error while monitoring changes: {e}")
    
    return changes

async def handle_redirection_or_new_tab(page, element_text, screenshots_dir):
    """Handles possible redirection or new tabs after a click."""
    initial_url = page.url
    try:
        await page.wait_for_timeout(5000)

        pages = [page]
        for context_page in page.context.pages:
            if context_page.url != initial_url and context_page not in pages:
                pages.append(context_page)

        for p in pages:
            if p.url != initial_url:
                if p != page:
                    logging.info(f"New tab detected: {p.url}")
                    await p.wait_for_load_state()
                    redirected_changes = await monitor_changes(p, f"New tab after click: {element_text}")
                    changes_data.append(redirected_changes)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    redirected_screenshot_path = f"{screenshots_dir}/{timestamp}_new_tab_screenshot.png"
                    await take_screenshot(p, redirected_screenshot_path)
                    await p.close()
                else:
                    logging.info(f"Redirection detected: {p.url}")
                    redirected_changes = await monitor_changes(p, f"Redirection after click: {element_text}")
                    changes_data.append(redirected_changes)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    redirected_screenshot_path = f"{screenshots_dir}/{timestamp}_redirected_screenshot.png"
                    await take_screenshot(p, redirected_screenshot_path)
                    await p.go_back()

    except asyncio.TimeoutError:
        logging.info("No redirection or new tab detected within the timeout period.")
    except Exception as e:
        error_logger.error(f"Error handling redirection or new tab: {e}")

async def simulate_clicks(page, screenshots_dir):
    """Simulates random clicks on a webpage and monitors for changes."""
    num_clicks = random.randint(5, 10)
    logging.info(f"Will perform {num_clicks} clicks on this webpage.")

    try:
        for i in range(num_clicks):
            clickable_elements = await page.query_selector_all('a, button, input[type="button"], input[type="submit"], [onclick]')
            
            if not clickable_elements:
                logging.info("No clickable elements found on this page.")
                return

            element = random.choice(clickable_elements)

            if await element.is_visible() and await element.is_enabled():
                element_text = await page.evaluate('(element) => element.innerText || element.outerHTML', element)
                logging.info(f"Clicking on element: {element_text}")
                await element.click()

                await handle_redirection_or_new_tab(page, element_text, screenshots_dir)

                click_description = f"Clicked on element: {element_text}"
                changes = await monitor_changes(page, click_description)
                changes_data.append(changes)

                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                screenshot_path = f"{screenshots_dir}/{timestamp}_click_{i+1}.png"
                await take_screenshot(page, screenshot_path)

                await page.wait_for_timeout(2000)

    except Exception as e:
        error_logger.error(f"Error during click simulation: {e}")

async def monitor_website(browser, url: str):
    """Monitors a single website by navigating to it and simulating clicks."""
    async with semaphore:
        page = await browser.new_page()

        # Sanitize the URL to create a valid directory name
        sanitized_url = sanitize_filename(url)
        screenshots_dir = os.path.join(BASE_SCREENSHOTS_DIR, sanitized_url)
        os.makedirs(screenshots_dir, exist_ok=True)

        try:
            logging.info(f"Navigating to {url}...")
            await page.goto(url, timeout=30000)
            logging.info(f"Successfully navigated to {url}")

            await simulate_clicks(page, screenshots_dir)

        except Exception as e:
            error_logger.error(f"Error during website monitoring: {e}")
        finally:
            await page.close()
async def main():
    """Main function to handle multiple website monitoring concurrently."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, slow_mo=50, timeout=30000)

        with open('websites.txt', 'r') as file:
            websites = [line.strip() for line in file.readlines()]

        # Processing websites in batches
        batch_size = 5  # Adjust as needed
        for i in range(0, len(websites), batch_size):
            batch = websites[i:i + batch_size]
            tasks = [monitor_website(browser, website) for website in batch]
            await asyncio.gather(*tasks)

            # After each batch, write the collected changes to the JSON file
            logging.info(f"Writing changes for batch {i // batch_size + 1} to {CHANGES_JSON_FILE}")
            async with aiofiles.open(CHANGES_JSON_FILE, 'w') as f:
                await f.write(json.dumps(changes_data, indent=4))
            logging.info(f"Changes for batch {i // batch_size + 1} have been logged in {CHANGES_JSON_FILE}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

