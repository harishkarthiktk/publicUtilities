import os
import argparse
import logging
from urllib.parse import urlparse
import html2text
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_webdriver():
    """Initialize headless Selenium WebDriver."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        logging.error(f"Error initializing WebDriver: {e}")
        return None

def fetch_page(driver, url):
    """Load a webpage and return its source HTML."""
    try:
        driver.get(url)
        time.sleep(2)  # Wait for dynamic content to load
        return driver.page_source
    except Exception as e:
        logging.error(f"Error loading {url}: {e}")
        return None

def url_to_filename(url):
    """Convert a URL into a safe filename."""
    filename = url.replace('://', '_').replace('/', '_').replace(':', '').replace('?', '_').replace('&', '_').replace('=', '_')
    return f"{filename}.md"

def save_content_to_file(content, filename):
    """Save Markdown content to the specified file."""
    os.makedirs('outputs', exist_ok=True)
    filepath = os.path.join('outputs', filename)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        logging.info(f"Saved: {filepath}")
    except Exception as e:
        logging.error(f"Failed to write {filepath}: {e}")

def process_url(driver, url):
    """Fetch a page, convert to Markdown, and save."""
    html_content = fetch_page(driver, url)
    if html_content:
        md_content = html2text.html2text(html_content)
        filename = url_to_filename(url)
        save_content_to_file(md_content, filename)
    else:
        logging.warning(f"Skipped saving for {url} due to fetch failure.")

def read_urls_from_file(file_path):
    """Read URLs from a specified text file."""
    urls = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    urls.append(line)
        return urls
    except Exception as e:
        logging.error(f"Error reading URL file {file_path}: {e}")
        return []

def main():
    parser = argparse.ArgumentParser(description='Render pages from URLs in a file and save their content.')
    parser.add_argument('-f', '--file', required=True, help='Path to a text file with URLs, one per line.')
    args = parser.parse_args()

    urls = read_urls_from_file(args.file)
    if not urls:
        logging.error("No URLs to process. Exiting.")
        return

    driver = get_webdriver()
    if not driver:
        logging.error("WebDriver initialization failed. Exiting.")
        return

    try:
        for url in urls:
            logging.info(f"Processing: {url}")
            process_url(driver, url)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()