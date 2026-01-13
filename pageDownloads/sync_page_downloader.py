import os
import argparse
import html2text
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from tqdm import tqdm
from pagedownloads.utils import config, setup_logger, ensure_browser_available

logger = setup_logger(__name__)


def get_webdriver():
    """Initialize headless Selenium WebDriver."""
    if not ensure_browser_available('selenium'):
        logger.error("Chrome/Chromium not available and installation declined.")
        return None

    options = Options()
    if config.get('main', 'selenium.headless', True):
        options.add_argument("--headless")
    if config.get('main', 'selenium.disable_gpu', True):
        options.add_argument("--disable-gpu")
    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        logger.error(f"Error initializing WebDriver: {e}")
        return None


def fetch_page(driver, url):
    """Load a webpage and return its source HTML."""
    try:
        driver.get(url)
        wait_time = config.get('main', 'selenium.wait_time', 2)
        time.sleep(wait_time)
        return driver.page_source
    except Exception as e:
        logger.error(f"Error loading {url}: {e}")
        return None


def url_to_filename(url):
    """Convert a URL into a safe filename."""
    filename = (url.replace('://', '_')
                .replace('/', '_')
                .replace(':', '')
                .replace('?', '_')
                .replace('&', '_')
                .replace('=', '_'))
    return f"{filename}.md"


def sanitize_filename(title):
    """Sanitize a title to a safe filename base."""
    invalid_chars = r'<>:"/\|?*'
    for char in invalid_chars:
        title = title.replace(char, '_')
    title = title.replace(' ', '_')
    if len(title) > 200:
        title = title[:200]
    # Remove trailing dots or underscores if any
    title = title.rstrip('.')
    title = title.rstrip('_')
    return title


def save_content_to_file(content, filename, output_folder):
    """Save Markdown content to a file in the specified output folder."""
    os.makedirs(output_folder, exist_ok=True)
    filepath = os.path.join(output_folder, filename)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Saved: {filepath}")
    except Exception as e:
        logger.error(f"Failed to write {filepath}: {e}")


def process_url(driver, url, output_folder, use_title=False):
    """Fetch a page, convert to Markdown, and save."""
    try:
        html_content = fetch_page(driver, url)
        if html_content:
            md_content = html2text.html2text(html_content)
            if use_title:
                title = driver.title.strip()
                if title:
                    filename = sanitize_filename(title) + '.md'
                    logger.info(
                        f"Using title-based filename "
                        f"for {url}: {filename}"
                    )
                else:
                    filename = url_to_filename(url)
                    logger.warning(
                        f"Empty title for {url}, "
                        f"falling back to URL-based filename"
                    )
            else:
                filename = url_to_filename(url)
            save_content_to_file(md_content, filename, output_folder)
        else:
            logger.warning(f"Skipping saving for {url} due to fetch failure.")
    except Exception as e:
        logger.exception(f"Exception while processing {url}: {e}")


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
        logger.error(f"Error reading URL file {file_path}: {e}")
        return []


def main():
    parser = argparse.ArgumentParser(
        description='Render pages from URLs and save their content.'
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '-f',
        '--file',
        help='Path to a text file with URLs, one per line.'
    )
    group.add_argument(
        '-u',
        '--url',
        help='A single URL to process.'
    )
    parser.add_argument(
        '-o',
        '--output-folder',
        default=config.get('main', 'output.default_folder', 'outputs'),
        help='Folder to save the output files.'
    )
    parser.add_argument(
        '-t',
        '--title',
        action='store_true',
        help='Use webpage title for output filename instead of URL.'
    )
    args = parser.parse_args()

    # Prepare list of URLs
    if args.file:
        urls = read_urls_from_file(args.file)
        if not urls:
            logger.error("No URLs found in the file. Exiting.")
            return
        use_tqdm = True
    else:
        urls = [args.url]
        use_tqdm = False

    driver = get_webdriver()
    if not driver:
        logger.error("Could not initialize WebDriver. Exiting.")
        return

    try:
        # Process URLs with or without tqdm
        iterable = tqdm(urls, desc='Processing URLs') if use_tqdm else urls
        for url in iterable:
            logger.info(f"Processing: {url}")
            try:
                process_url(driver, url, args.output_folder, args.title)
            except Exception:
                logger.exception(f"Error processing {url}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
