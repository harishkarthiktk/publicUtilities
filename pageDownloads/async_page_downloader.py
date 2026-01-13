import argparse
import asyncio
import os
import re

import markdownify
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from tqdm import tqdm
from pagedownloads.utils import config, setup_logger, ensure_browser_available

logger = setup_logger(__name__)


def extract_links_from_md(md_file):
    """
    Parses the markdown file, extracting (title, url) tuples.
    Supports both Markdown link format '- [title](url)' and plain URLs (one per line).
    For plain URLs, uses the URL as the fallback title.
    """
    links = []
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # First, try to parse as Markdown links
        md_links = []
        for line in lines:
            match = re.match(r'- \[(.*?)\]\((.*?)\)', line.strip())
            if match:
                md_links.append((match.group(1), match.group(2)))

        if md_links:
            links = md_links
            logger.info(f"Parsed {len(md_links)} Markdown links from {md_file}")
        else:
            # Fallback: treat non-empty lines as plain URLs, using URL as title
            plain_links = []
            for line in lines:
                url = line.strip()
                if url and not url.startswith('#'):  # Ignore comments or headers
                    plain_links.append((url, url))  # Use URL as title fallback
            links = plain_links
            if plain_links:
                logger.info(f"Parsed {len(plain_links)} plain URLs from {md_file} (using URL as title fallback)")
            else:
                logger.warning(f"No valid URLs found in {md_file}")
    except Exception as e:
        logger.error(f"Error reading input file {md_file}: {e}")

    return links

def sanitize_filename(name):
    """Sanitize for safe filesystem usage."""
    # Enhanced sanitization similar to main.py
    invalid_chars = r'<>:"/\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    name = name.replace(' ', '_')
    if len(name) > 200:
        name = name[:200]
    name = name.rstrip('.')
    name = name.rstrip('_')
    return re.sub(r'[\\/*?:"<>|]', "", name)  # Additional cleanup

async def save_webpage_as_markdown(title, url, browser, output_dir):
    """
    Loads the webpage, extracts rendered content, saves it as Markdown.
    """
    page = None
    try:
        logger.debug(f"Creating new page for {url}...")
        page = await browser.new_page()
        logger.debug(f"Navigating to {url}...")
        timeout = config.get('main_asyncio', 'playwright.timeout', 60000)
        await page.goto(url, timeout=timeout)
        logger.debug(f"Waiting for content...")
        html = await page.content()
        logger.debug(f"Content retrieved, parsing HTML...")
        soup = BeautifulSoup(html, 'html.parser')
        # Extract page title
        title_tag = soup.find('title')
        file_title = sanitize_filename(title_tag.text.strip() if title_tag else title)
        logger.debug(f"Using title: {file_title}")
        # Extract main content; can be improved for site-specifics
        main_content = soup.body or soup
        logger.debug(f"Converting to Markdown...")
        heading_style = config.get('main_asyncio', 'markdown.heading_style', 'ATX')
        markdown_content = markdownify.markdownify(str(main_content), heading_style=heading_style)
        file_path = os.path.join(output_dir, f"{file_title}.md")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f'# {file_title}\n\n')
            include_source = config.get('main_asyncio', 'markdown.include_source_url', True)
            if include_source:
                f.write(f'*Source: {url}*\n\n')
            f.write(markdown_content)
        logger.info(f'Saved: {file_title}.md')
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
    finally:
        if page is not None:
            try:
                await page.close()
                logger.debug(f"Page closed for {url}")
            except Exception as e:
                logger.debug(f"Error closing page for {url}: {e}")

async def main(input_file, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    links = extract_links_from_md(input_file)

    if not links:
        logger.warning(f"No links to process from {input_file}. Exiting.")
        return

    logger.info(f"Starting to process {len(links)} links...")

    # Check browser availability
    if not ensure_browser_available('playwright'):
        logger.error("Playwright browsers not available and installation declined.")
        return

    try:
        async with async_playwright() as p:
            logger.info("Launching browser...")
            headless = config.get('main_asyncio', 'playwright.headless', True)
            browser = await p.chromium.launch(headless=headless)
            logger.info("Browser launched successfully.")

            # Process with concurrency limit
            concurrency_limit = config.get('main_asyncio', 'playwright.concurrency_limit', 5)
            semaphore = asyncio.Semaphore(concurrency_limit)

            async def process_with_semaphore(title, url):
                async with semaphore:
                    logger.info(f"Processing: {url}")
                    await save_webpage_as_markdown(title, url, browser, output_dir)

            # Create tasks for all links
            tasks = [process_with_semaphore(title, url) for title, url in links]

            # Process with progress tracking
            logger.info(f"Processing {len(tasks)} pages with concurrency limit of {concurrency_limit}...")
            await asyncio.gather(*tasks, return_exceptions=True)

            logger.info("Closing browser...")
            await browser.close()
            logger.info("Browser closed. All downloads complete.")
    except Exception as e:
        logger.error(f"Error in main async execution: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download web pages from a Markdown file with URLs and save as markdown.")
    parser.add_argument('-f', '--input-file', help='Input markdown file path', required=True)
    parser.add_argument('-o', '--output-folder', default=config.get('main_asyncio', 'output.default_folder', './asyncio_output'), help='Output folder path')
    args = parser.parse_args()

    asyncio.run(main(args.input_file, args.output_folder))
