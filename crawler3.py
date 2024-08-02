import asyncio
import logging
import os
import time
import json
import webbrowser
from pyppeteer import launch
from pyppeteer.errors import PageError, TimeoutError

# Initialize logging
logging.basicConfig(level=logging.INFO)
error_logger = logging.getLogger('error_logger')
progress_logger = logging.getLogger('progress_logger')

# Constants
SLEEP_DURATION = 5
MONITOR_DURATION = 120
CHROMIUM_PATH = r'C:\Users\dell\AppData\Local\Chromium\Application\chrome.exe'
SCREENSHOTS_DIR = r'C:\Users\dell\Desktop\Web Security\screenshots'
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

def sanitize_filename(filename: str) -> str:
    # Replace invalid characters with underscores
    return "".join([c if c.isalnum() or c in (' ', '_') else '_' for c in filename])

async def take_screenshot(page, screenshot_path: str):
    try:
        await page.screenshot({'path': screenshot_path, 'fullPage': True})
    except Exception as e:
        error_logger.error(f"Error taking screenshot: {e}")

async def monitor_page_changes(url: str, browser, website_dir: str):
    changes = []
    previous_html, previous_js, previous_network, previous_url = "", "", "", url
    screenshot_count = 0
    start_time = time.time()

    try:
        page = await browser.newPage()
        await page.setViewport({"width": 1920, "height": 1080})

        while time.time() - start_time < MONITOR_DURATION:
            try:
                await page.goto(url)
                await asyncio.sleep(SLEEP_DURATION)

                current_html = await page.content()
                current_js = await page.evaluate('() => Array.from(document.scripts).map(script => script.outerHTML).join("\\n")')
                current_network = await page.evaluate('() => JSON.stringify(window.performance.getEntries())')
                current_url = page.url

                if (current_html != previous_html or current_js != previous_js or
                    current_network != previous_network or current_url != previous_url):
                    
                    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                    change_entry = {
                        "timestamp": timestamp,
                        "url": current_url,
                        "html": current_html,
                        "js": current_js,
                        "network": current_network
                    }
                    changes.append(change_entry)

                    screenshot_path = os.path.join(website_dir, f'{screenshot_count}.png')
                    await take_screenshot(page, screenshot_path)
                    screenshot_count += 1

                    previous_html, previous_js, previous_network, previous_url = current_html, current_js, current_network, current_url

                    progress_logger.info(f"Changes detected and logged for {url} at {timestamp}:\n"
                                         f"URL: {current_url}\n"
                                         f"HTML: {current_html[:100]}...\n"
                                         f"JS: {current_js[:100]}...\n"
                                         f"Network: {current_network[:100]}...")

            except (PageError, TimeoutError) as pe:
                error_logger.error(f"Error navigating to {url}: {pe}")
                break
        await page.close()
    except Exception as e:
        error_logger.error(f"Error monitoring {url}: {e}")
    return {url: changes}

async def monitor_websites_from_file(file_path: str, log_file_path: str):
    browser = await launch(executablePath=CHROMIUM_PATH)
    results = []

    with open(file_path, 'r') as file:
        websites = [line.strip() for line in file if line.strip()]
    
    progress_logger.info(f"Websites to monitor: {websites}")

    for url in websites:
        website_dir = os.path.join(SCREENSHOTS_DIR, sanitize_filename(url.replace("https://", "").replace("http://", "").replace("/", "_")))
        os.makedirs(website_dir, exist_ok=True)
        result = await monitor_page_changes(url, browser, website_dir)
        results.append(result)

    await browser.close()
    log_changes(results, log_file_path)
    open_progress_log(log_file_path)
    progress_logger.info("Website monitoring completed")

def log_changes(results: list, log_file_path: str):
    try:
        with open(log_file_path, 'w') as file:
            json.dump(results, file, indent=4)
        progress_logger.info("Changes logged successfully")
    except Exception as e:
        error_logger.error(f"Error logging changes: {e}")

def open_progress_log(log_file_path: str):
    try:
        webbrowser.open(log_file_path)
    except Exception as e:
        error_logger.error(f"Error opening progress log: {e}")

def main():
    print("Welcome to Web Scraper!")
    print("For progress check --> progress.log")
    print("For any error check --> error.log")
    print("Work in Progress...!")

    file_path = r"C:\Users\dell\Desktop\Web Security\websites.txt"
    log_file_path = r"C:\Users\dell\Desktop\Web Security\website_changes.json"

    try:
        asyncio.run(monitor_websites_from_file(file_path, log_file_path))
    except Exception as e:
        error_logger.error(f"Error in main process: {e}")

    print("Bye bye!")

if __name__ == "__main__":
    main()
