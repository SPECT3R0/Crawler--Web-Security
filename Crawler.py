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

# File to log inaccessible URLs
INACCESSIBLE_URLS_FILE = 'inaccessible_urls.txt'

# Semaphore to limit the number of concurrent tasks
semaphore = asyncio.Semaphore(2)  # Adjust as needed

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

async def handle_redirection_or_new_tab(page, element_text, screenshots_dir, changes_list):
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
                    changes_list.append(redirected_changes)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    redirected_screenshot_path = f"{screenshots_dir}/{timestamp}_new_tab_screenshot.png"
                    await take_screenshot(p, redirected_screenshot_path)
                    await p.close()
                else:
                    logging.info(f"Redirection detected: {p.url}")
                    redirected_changes = await monitor_changes(p, f"Redirection after click: {element_text}")
                    changes_list.append(redirected_changes)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    redirected_screenshot_path = f"{screenshots_dir}/{timestamp}_redirected_screenshot.png"
                    await take_screenshot(p, redirected_screenshot_path)
                    await p.go_back()

    except asyncio.TimeoutError:
        logging.info("No redirection or new tab detected within the timeout period.")
    except Exception as e:
        error_logger.error(f"Error handling redirection or new tab: {e}")

async def simulate_clicks(page, screenshots_dir, changes_list):
    """Simulates random clicks on a webpage and monitors for changes."""
    num_clicks = random.randint(5, 10)
    logging.info(f"Will attempt to perform up to {num_clicks} clicks on this webpage.")

    try:
        for i in range(num_clicks):
            clickable_elements = await page.query_selector_all('a, button, input[type="button"], input[type="submit"], [onclick]')
            
            logging.info(f"Found {len(clickable_elements)} clickable elements on the page.")

            if not clickable_elements:
                logging.info("No clickable elements found on this page. Ending click simulation.")
                return

            element = random.choice(clickable_elements)

            if await element.is_visible() and await element.is_enabled():
                element_text = await page.evaluate('(element) => element.innerText || element.outerHTML', element)
                logging.info(f"Clicking on element: {element_text} (click {i + 1}/{num_clicks})")
                await element.click()

                await handle_redirection_or_new_tab(page, element_text, screenshots_dir, changes_list)

                click_description = f"Clicked on element: {element_text}"
                changes = await monitor_changes(page, click_description)
                changes_list.append(changes)

                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                screenshot_path = f"{screenshots_dir}/{timestamp}_click_{i+1}.png"
                await take_screenshot(page, screenshot_path)

                await page.wait_for_timeout(2000)

            else:
                logging.info(f"Element not visible or not enabled: {await page.evaluate('(element) => element.outerHTML', element)}")

    except Exception as e:
        error_logger.error(f"Error during click simulation: {e}")

async def is_site_accessible(page, url):
    """Checks if a site is accessible by navigating to it."""
    try:
        await page.goto(url, timeout=30000)
        return True
    except PlaywrightTimeoutError:
        logging.warning(f"Timeout while trying to access {url}. Site may not be accessible.")
        return False
    except Exception as e:
        logging.warning(f"Error while trying to access {url}: {e}")
        return False

async def monitor_website(browser, url: str):
    """Monitors a single website by navigating to it and simulating clicks."""
    async with semaphore:
        page = await browser.new_page()

        changes_list = []  # Store changes for this URL

        try:
            logging.info(f"Checking accessibility of {url}...")
            if not await is_site_accessible(page, url):
                logging.info(f"Site {url} is not accessible. Logging to {INACCESSIBLE_URLS_FILE}.")
                async with aiofiles.open(INACCESSIBLE_URLS_FILE, 'a') as f:
                    await f.write(url + '\n')
                return

            logging.info(f"Successfully navigated to {url}")

            # Only create directories and start monitoring if the site is accessible
            sanitized_url = sanitize_filename(url)
            screenshots_dir = os.path.join(BASE_SCREENSHOTS_DIR, sanitized_url)
            os.makedirs(screenshots_dir, exist_ok=True)

            # Capture initial state
            initial_state = {
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "initial_url": url,
                "initial_html": await page.content(),
                "initial_js": await page.evaluate('Array.from(document.scripts).map(s => s.outerHTML).join("\\n")'),
                "initial_css": await page.evaluate('Array.from(document.styleSheets).map(s => s.ownerNode.outerHTML).join("\\n")')
            }
            changes_list.append(initial_state)  # Save initial state

            await simulate_clicks(page, screenshots_dir, changes_list)

        except Exception as e:
            error_logger.error(f"Error during website monitoring: {e}")
        finally:
            await page.close()

            # Save the changes to a JSON file specific to this URL
            if changes_list:  # Only save if there are changes recorded
                changes_json_path = os.path.join(screenshots_dir, 'changes.json')
                logging.info(f"Writing changes for {url} to {changes_json_path}")
                async with aiofiles.open(changes_json_path, 'w') as f:
                    await f.write(json.dumps(changes_list, indent=4))
                logging.info(f"Changes saved for {url}")


async def main():
    """Main function to monitor multiple websites."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        async with aiofiles.open('websites.txt', 'r') as f:
            urls = [line.strip() for line in await f.readlines() if line.strip()]

        monitor_tasks = [monitor_website(browser, url) for url in urls]
        await asyncio.gather(*monitor_tasks)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
