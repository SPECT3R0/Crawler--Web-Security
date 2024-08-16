The project is part of SE Ad Blocker

---

# Web Crawler and Monitoring Tool

## Overview

This Python-based tool leverages Playwright for dynamic web scraping and monitoring. It is designed to automate interactions with web pages, simulate random clicks, and capture changes that occur as a result of those interactions. The tool supports multi-threaded execution to handle multiple URLs simultaneously, optimizing performance and reducing processing time.

## Features

- **Dynamic Web Interaction**: Simulates random clicks on web pages, with the number of clicks randomly determined between 5 and 10 for each URL.
- **Change Detection**: Monitors and logs changes in HTML, JavaScript, and CSS after each click, capturing content snippets and taking screenshots.
- **Redirection Handling**: Detects and handles both new tabs and redirections, taking appropriate screenshots and logging changes.
- **Multi-Threading Support**: Utilizes Python's `concurrent.futures` to run multiple instances concurrently, making it suitable for large-scale monitoring tasks.
- **Screenshot Management**: Creates separate folders for each URL to store screenshots, organized by timestamp.
- **Error Handling**: Includes robust error handling and logging to capture and report any issues encountered during execution.

## How It Works

1. **Setup**: Ensure Playwright is installed and the necessary browser binaries are available.
2. **Configuration**: Modify the `websites.txt` file to include the list of URLs you wish to monitor.
3. **Execution**: Run the script. It will navigate to each URL, simulate random clicks, and monitor changes dynamically.
4. **Results**: Changes are logged in a `changes.json` file, and screenshots are saved in separate folders for each URL.

## Installation

To get started, clone this repository and install the required dependencies:

```bash
git clone https://github.com/tkflash/Crawler--Web-Security.git
cd Crawler--Web-Security
pip install -r requirements.txt
```

## Usage

1. **Update the `websites.txt` file** with the URLs you want to monitor.
2. **Run the script**:

```bash
python Crawler.py
```

3. **Review the results** in the `changes.json` file and the screenshot directories.

## Requirements

- Python 3.8 or later
- Playwright
- Asyncio
- Logging

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---
