import os
import argparse
import logging
from urllib.parse import urlparse
import html2text
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from tqdm import tqdm

# Setup logging to file and stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs.txt"),
        logging.StreamHandler()
    ]
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

def save_content_to_file(content, filename, output_folder):
    """Save Markdown content to a file in the specified output folder."""
    os.makedirs(output_folder, exist_ok=True)
    filepath = os.path.join(output_folder, filename)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        logging.info(f"Saved: {filepath}")
    except Exception as e:
        logging.error(f"Failed to write {filepath}: {e}")

def process_url(driver, url, output_folder):
    """Fetch a page, convert to Markdown, and save."""
    try:
        html_content = fetch_page(driver, url)
        if html_content:
            md_content = html2text.html2text(html_content)
            filename = url_to_filename(url)
            save_content_to_file(md_content, filename, output_folder)
        else:
            logging.warning(f"Skipping saving for {url} due to fetch failure.")
    except Exception as e:
        logging.exception(f"Exception while processing {url}: {e}")

def read_urls_from_file(file_path):
    """Read URLs from a text file."""
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
    parser = argparse.ArgumentParser(description='Render pages from URLs and save their content.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-f', '--file', help='Path to a text file with URLs, one per line.')
    group.add_argument('-u', '--url', help='A single URL to process.')
    parser.add_argument('-o', '--output-folder', default='outputs', help='Folder to save the output files.')
    args = parser.parse_args()

    # Prepare list of URLs
    if args.file:
        urls = read_urls_from_file(args.file)
        if not urls:
            logging.error("No URLs found in the file. Exiting.")
            return
        use_tqdm = True
    else:
        urls = [args.url]
        use_tqdm = False

    driver = get_webdriver()
    if not driver:
        logging.error("Could not initialize WebDriver. Exiting.")
        return

    try:
        # Process URLs with or without tqdm
        iterable = tqdm(urls, desc='Processing URLs') if use_tqdm else urls
        for url in iterable:
            logging.info(f"Processing: {url}")
            try:
                process_url(driver, url, args.output_folder)
            except Exception:
                logging.exception(f"Error processing {url}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()