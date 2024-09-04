import asyncio
import logging
import os
import json
import random
import time
import re
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import aiofiles

print("Hello!")
print("Welcome to Web Crawler!")
print("By: tkFlash!")

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Stream handler for console output
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Adding the console handler to the logger
logger.addHandler(console_handler)

# Error logger for file output
error_logger = logging.getLogger('error_logger')
file_handler = logging.FileHandler('errors.log')
file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(formatter)
error_logger.addHandler(file_handler)

# Base directory for screenshots
BASE_SCREENSHOTS_DIR = 'screenshots'
os.makedirs(BASE_SCREENSHOTS_DIR, exist_ok=True)

# File to log inaccessible URLs
INACCESSIBLE_URLS_FILE = 'inaccessible_urls.txt'
# File to log monitored URLs
MONITORED_URLS_FILE = 'monitored_websites.txt'

# Semaphore to limit the number of concurrent tasks
SEMAPHORE_LIMIT = 10  # Adjust based on system resources
semaphore = asyncio.Semaphore(SEMAPHORE_LIMIT)

def sanitize_filename(filename):
    """Sanitizes a string to be a valid filename by removing or replacing invalid characters."""
    return re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', filename)

async def take_screenshot(page, screenshot_path: str):
    """Takes a screenshot of the current page with a longer timeout."""
    try:
        await page.screenshot(path=screenshot_path, full_page=True, timeout=60000)
        logger.info(f"Screenshot saved: {screenshot_path}")
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
        # Increase the timeout for waiting on redirections or new tabs
        await page.wait_for_timeout(10000)  # Wait for up to 10 seconds

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

    start_time = time.time()  # Track the start time
    click_duration = 120  # Time in seconds for which clicks will be performed
    total_wait_duration = 120  # Total duration in seconds to wait after clicks

    try:
        for i in range(num_clicks):
            if time.time() - start_time > click_duration:
                break  # Stop clicking if the time exceeds the allowed click duration

            clickable_elements = await page.query_selector_all('a, button, input[type="button"], input[type="submit"], [onclick]')
            
            logging.info(f"Found {len(clickable_elements)} clickable elements on the page.")

            if not clickable_elements:
                logging.info("No clickable elements found on this page. Ending click simulation.")
                break

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

                await page.wait_for_timeout(2000)  # Reduced wait time to 2 seconds

            else:
                logging.info(f"Element not visible or not enabled: {await page.evaluate('(element) => element.outerHTML', element)}")

        # Wait for the rest of the total wait duration if clicks were done in less time
        elapsed_time = time.time() - start_time
        remaining_time = total_wait_duration - elapsed_time
        if remaining_time > 0:
            logging.info(f"Waiting for the remaining {remaining_time:.2f} seconds.")
            await page.wait_for_timeout(int(remaining_time * 1000))  # Convert seconds to milliseconds

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
            # Check if the URL has already been monitored
            if await is_already_monitored(url):
                logging.info(f"URL {url} has already been monitored. Skipping.")
                return

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

            # Save the changes to a JSON file
            json_filename = os.path.join(screenshots_dir, "changes.json")
            async with aiofiles.open(json_filename, 'w') as json_file:
                await json_file.write(json.dumps(changes_list, indent=4))

            logging.info(f"Finished monitoring {url}. Results saved to {screenshots_dir}")

            # Log the monitored URL
            await log_monitored_url(url)

        except Exception as e:
            error_logger.error(f"Error while monitoring {url}: {e}")

        finally:
            await page.close()

async def is_already_monitored(url):
    """Checks if the URL has already been monitored by checking the monitored_websites.txt file."""
    try:
        async with aiofiles.open(MONITORED_URLS_FILE, 'r') as file:
            async for line in file:
                if url in line:
                    return True
    except FileNotFoundError:
        # If the file does not exist, assume no URLs have been monitored yet
        return False
    return False

async def log_monitored_url(url):
    """Logs the URL to monitored_websites.txt after successful monitoring."""
    async with aiofiles.open(MONITORED_URLS_FILE, 'a') as file:
        await file.write(url + '\n')

async def monitor_websites(urls):
    """Monitors multiple websites concurrently."""
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        try:
            tasks = [monitor_website(browser, url) for url in urls]
            await asyncio.gather(*tasks)
        finally:
            await browser.close()

def load_urls(filename):
    """Loads URLs from a text file."""
    with open(filename, 'r') as file:
        urls = [line.strip() for line in file.readlines()]
    return urls

if __name__ == "__main__":
    start_time = time.time()

    # Load the list of URLs
    urls = load_urls('websites.txt')
    random.shuffle(urls)

    asyncio.run(monitor_websites(urls))

    elapsed_time = time.time() - start_time
    logging.info(f"Completed monitoring of all websites. Total time taken: {elapsed_time:.2f} seconds.")
