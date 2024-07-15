import asyncio
import logging
import os
import random
import time
import webbrowser
import json
from typing import Dict, Any
from pyppeteer import launch
from pyppeteer.errors import PageError, TimeoutError

# Initialize logging
logging.basicConfig(level=logging.INFO)
error_logger = logging.getLogger('error_logger')
progress_logger = logging.getLogger('progress_logger')

# Constants
SLEEP_DURATION = 5
MONITOR_DURATION = 120
chromium_path = r'C:\Users\dell\AppData\Local\Chromium\Application\chrome.exe'
screenshots_dir = r'C:\Users\dell\Desktop\Web Security\screenshots'
os.makedirs(screenshots_dir, exist_ok=True)

async def monitor_with_puppeteer(url: str, browser):
    changes = []
    start_time = time.time()
    screenshot_count = 0

    previous_html = ""
    previous_js = ""
    previous_network = ""

    # Create a subfolder for the website
    website_dir = os.path.join(screenshots_dir, url.replace("https://", "").replace("http://", "").replace("/", "_"))
    os.makedirs(website_dir, exist_ok=True)

    try:
        page = await browser.newPage()
        await page.setViewport({"width": 1920, "height": 1080})
        while time.time() - start_time < MONITOR_DURATION:
            try:
                await page.goto(url)

                # Simulate targeted clicks on specific elements
                await simulate_targeted_clicks(page)

                # Wait for page to settle after actions
                await asyncio.sleep(SLEEP_DURATION)

                current_html = await page.content()
                current_js = await page.evaluate('document.scripts[0].outerHTML')
                current_network = await page.evaluate('() => JSON.stringify(window.performance.getEntries())')

                if current_html != previous_html or current_js != previous_js or current_network != previous_network:
                    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                    change_entry = {
                        "timestamp": timestamp,
                        "html": current_html,
                        "js": current_js,
                        "network": current_network
                    }
                    changes.append(change_entry)

                    screenshot_path = os.path.join(website_dir, f'{screenshot_count}.png')
                    await page.screenshot({'path': screenshot_path, 'fullPage': True})
                    screenshot_count += 1

                    previous_html = current_html
                    previous_js = current_js
                    previous_network = current_network

                    progress_logger.info(f"Changes detected and logged for {url} at {timestamp}")

            except (PageError, TimeoutError) as pe:
                error_logger.error(f"Error navigating to {url}: {pe}")

    except Exception as e:
        error_logger.error(f"Error monitoring {url}: {e}")

    finally:
        if page:
            await page.close()

    return {url: changes}

async def simulate_targeted_clicks(page):
    try:
        elements = await page.querySelectorAll('input, a, button, img')
        if elements:
            element = random.choice(elements)
            await element.click()
            await asyncio.sleep(2)  # Wait a bit after click
    except Exception as e:
        error_logger.error(f"Error simulating clicks: {e}")

async def monitor_websites_from_file(file_path: str, log_file_path: str):
    browser = None
    try:
        with open(file_path, 'r') as file:
            websites = [line.strip() for line in file if line.strip()]

        progress_logger.info(f"Websites to monitor: {websites}")

        browser = await launch(executablePath=chromium_path)

        tasks = []
        for url in websites:
            task = asyncio.create_task(monitor_with_puppeteer(url, browser))
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # Log changes to a file
        log_changes({url: changes for result in results for url, changes in result.items()}, log_file_path)
        progress_logger.info("Website monitoring completed")

        open_progress_log(log_file_path)

    except Exception as e:
        error_logger.error(f"Error in monitor_websites_from_file: {e}")

    finally:
        if browser:
            await browser.close()

def log_changes(website_changes: Dict[str, Any], log_file_path: str):
    try:
        with open(log_file_path, 'w') as file:
            json.dump(website_changes, file, indent=4)
        progress_logger.info("Changes logged successfully")
    except Exception as e:
        error_logger.error(f"Error logging changes: {e}")

def open_progress_log(log_file_path: str):
    try:
        webbrowser.open(log_file_path)
    except Exception as e:
        error_logger.error(f"Error opening progress log: {e}")

if __name__ == "__main__":
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
