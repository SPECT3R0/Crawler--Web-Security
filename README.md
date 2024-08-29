The project is part of SE Ad Blocker

# Web Crawler for Website Monitoring

Welcome to the **Web Crawler for Website Monitoring**! This tool is designed to simulate random user interactions with a website, detect changes in the HTML, CSS, and JavaScript, and capture screenshots of the site before and after these interactions. The primary purpose of this tool is to monitor websites for potential social engineering ads or other malicious activities by identifying dynamic changes in content and structure.

## Features

- **Simulate Random Clicks**: Randomly clicks on elements such as links, buttons, and inputs to mimic user behavior.
- **Monitor Changes**: Detects changes in HTML, CSS, and JavaScript after each interaction.
- **Redirection and New Tab Handling**: Handles scenarios where a click leads to a redirection or opens a new tab.
- **Screenshots**: Captures screenshots of the webpage before and after each interaction for visual reference.
- **Logs Changes**: Records detected changes in a structured JSON format.
- **Concurrent Task Execution**: Uses asyncio to handle multiple websites concurrently.

## Installation

### Prerequisites

- Python 3.7+
- Playwright

### Setup

1. **Clone the repository**:
    ```bash
    git clone https://github.com/tkflash/Crawler--Web-Security.git
    cd Crawler--Web-Security
    ```

2. **Install the required dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Install Playwright browsers**:
    ```bash
    playwright install
    ```

## Usage

1. **Prepare a list of websites**: Create a file named `websites.txt` in the same directory as the script, containing the URLs of websites you want to monitor, one per line.

2. **Run the script**:
    ```bash
    python Crawler.py
    ```

3. **View Results**: The crawler will create a directory named `screenshots` in the project root, where it stores screenshots and JSON files for each monitored website.

### Example

To see the script in action, check out the [Crawler.py](https://github.com/tkflash/Crawler--Web-Security/blob/main/Crawler.py) file on GitHub.

## Configuration

You can adjust the script's configuration to change the number of concurrent tasks or the timeout periods. For instance, the semaphore limit is currently set to `2`, which means only two websites will be processed concurrently. Adjust the `semaphore` value in the script to change this behavior.

```python
semaphore = asyncio.Semaphore(2)  # Adjust as needed


## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---
