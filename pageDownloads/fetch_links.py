#!/usr/bin/env python
"""
Fetch and extract links from dynamically rendered web pages.

This script fetches a URL using Playwright, waits for JavaScript to finish loading,
then extracts href values (or constructs them from text/hqid) from <a> tags within
elements matching a specified CSS class.

Usage:
    # Extract actual hrefs (if populated by JavaScript)
    python fetch_links.py --url <URL> --css-class <CLASS>

    # Construct URLs from link text (slugified)
    python fetch_links.py --url <URL> --css-class <CLASS> --construct-from text

    # Construct URLs from hqid attribute
    python fetch_links.py --url <URL> --css-class <CLASS> --construct-from hqid --url-pattern "/api/{hqid}"

    # Click-based URL discovery (for React SPAs with hash routing)
    python fetch_links.py --url <URL> --css-class <CLASS> --click

Arguments:
    --url: URL to fetch and render (required)
    --css-class: CSS class name to target for link extraction (required)
    --output: Output file path (default: outputs/links.txt)
    --construct-from: Construct URLs from 'text' (slugified) or 'hqid' attribute (default: None - use actual hrefs)
    --url-pattern: URL pattern for construction (e.g., "/api/{hqid}" or "/docs/{text}"). Required if --construct-from is used.
    --base-url: Base URL to prepend to constructed paths (e.g., "https://help.servicedeskplus.com")
    --click: Enable click-based URL discovery instead of href extraction (for React SPAs with hash routing)

Output:
    Saves unique links to a text file (one per line)

Requirements:
    - Playwright (pip install playwright)
    - BeautifulSoup4 (pip install beautifulsoup4)
    - playwright install (to download browser binaries)
"""

import argparse
import asyncio
import os
import re
import sys

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from pagedownloads.utils import setup_logger, ensure_browser_available, config

logger = setup_logger(__name__)


def slugify(text):
    """Convert text to URL-friendly slug."""
    # Convert to lowercase and replace spaces with hyphens
    slug = text.lower().strip()
    slug = re.sub(r'\s+', '-', slug)
    # Remove non-alphanumeric characters except hyphens
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    # Remove consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    return slug


def construct_url(pattern, text=None, hqid=None):
    """
    Construct URL from pattern and values.

    Args:
        pattern: URL pattern with placeholders (e.g., "/api/{hqid}" or "/docs/{text}")
        text: Link text (will be slugified)
        hqid: hqid attribute value

    Returns:
        Constructed URL or None if pattern is invalid
    """
    try:
        url = pattern
        if '{text}' in url and text:
            url = url.replace('{text}', slugify(text))
        if '{hqid}' in url and hqid:
            url = url.replace('{hqid}', str(hqid))
        return url
    except Exception as e:
        logger.error(f"Error constructing URL from pattern '{pattern}': {e}")
        return None


async def fetch_links_by_clicking(page, css_class):
    """
    Fetch links by clicking each one in the page and capturing the resulting URL.

    Uses Playwright to click links, wait for URL changes, and go back.

    Args:
        page: Playwright page object
        css_class: CSS class to target for link extraction

    Returns:
        Set of unique URLs collected from clicking links
    """
    links = set()

    try:
        # Snapshot all hqids inside the target class
        logger.info(f"Snapshotting hqids from elements with class '{css_class}'...")
        hqids = await page.evaluate(f"""
            () => Array.from(document.querySelectorAll('.{css_class} a[hqid]'))
                    .map(a => a.getAttribute('hqid'))
        """)

        logger.info(f"Found {len(hqids)} link(s) to click")

        original_url = page.url
        logger.info(f"Original URL: {original_url}")

        for idx, hqid in enumerate(hqids, 1):
            try:
                logger.info(f"Clicking link {idx}/{len(hqids)} (hqid={hqid})...")

                # Build selector and click
                selector = f".{css_class} a[hqid='{hqid}']"
                await page.click(selector)

                # Wait for URL to change
                try:
                    await page.wait_for_url(lambda url: url != original_url, timeout=5000)
                    current_url = page.url
                    links.add(current_url)
                    logger.info(f"Captured URL: {current_url}")
                except Exception as e:
                    logger.warning(f"URL didn't change after clicking link {idx} (hqid={hqid}): {e}")

                # Go back
                logger.info(f"Going back to original URL...")
                await page.go_back()
                try:
                    await page.wait_for_url(original_url, timeout=5000)
                except Exception:
                    # Fallback: reload original URL if go_back doesn't land there
                    logger.warning(f"go_back() didn't land on original URL, reloading...")
                    await page.goto(original_url, wait_until="networkidle", timeout=60000)

            except Exception as e:
                logger.error(f"Error processing link {idx} (hqid={hqid}): {e}")
                continue

        logger.info(f"Collected {len(links)} unique URL(s) from clicking")

    except Exception as e:
        logger.error(f"Error in click-based link discovery: {e}")
        raise

    return links


async def fetch_and_extract_links_by_clicking(url, css_class):
    """
    Fetch a URL using Playwright and discover links by clicking them.

    Args:
        url: URL to fetch
        css_class: CSS class name to target for link extraction

    Returns:
        Set of unique link values
    """
    links = set()

    try:
        async with async_playwright() as p:
            logger.info("Launching browser...")
            headless = config.get('page_downloader', 'playwright.headless', True)
            browser = await p.chromium.launch(headless=headless)
            logger.info("Browser launched successfully.")

            try:
                logger.info(f"Creating page and navigating to {url}...")
                page = await browser.new_page()
                timeout = config.get('page_downloader', 'playwright.timeout', 60000)

                # Wait for network idle to ensure JS has finished loading
                await page.goto(url, wait_until="networkidle", timeout=timeout)
                logger.info("Page loaded, beginning click-based link discovery...")

                # Use click-based discovery
                links = await fetch_links_by_clicking(page, css_class)

            finally:
                await browser.close()
                logger.info("Browser closed.")

    except Exception as e:
        logger.error(f"Error fetching or parsing URL: {e}")
        sys.exit(1)

    return links


async def fetch_and_extract_links(url, css_class, construct_from=None, url_pattern=None, base_url=None):
    """
    Fetch a URL using Playwright and extract links from elements with specified class.

    Args:
        url: URL to fetch
        css_class: CSS class name to target for link extraction
        construct_from: 'text' or 'hqid' to construct URLs from those attributes, None to use actual hrefs
        url_pattern: Pattern for URL construction (e.g., "/api/{hqid}")
        base_url: Base URL to prepend to constructed paths

    Returns:
        Set of unique link values
    """
    links = set()

    try:
        async with async_playwright() as p:
            logger.info("Launching browser...")
            headless = config.get('page_downloader', 'playwright.headless', True)
            browser = await p.chromium.launch(headless=headless)
            logger.info("Browser launched successfully.")

            try:
                logger.info(f"Creating page and navigating to {url}...")
                page = await browser.new_page()
                timeout = config.get('page_downloader', 'playwright.timeout', 60000)

                # Wait for network idle to ensure JS has finished loading
                await page.goto(url, wait_until="networkidle", timeout=timeout)
                logger.info("Page loaded, retrieving HTML content...")

                html = await page.content()
                logger.info("HTML content retrieved.")

                # Parse HTML and extract links
                logger.info(f"Parsing HTML and extracting links from elements with class '{css_class}'...")
                soup = BeautifulSoup(html, 'html.parser')

                # Find all elements with the specified class
                elements = soup.find_all(class_=css_class)
                logger.info(f"Found {len(elements)} element(s) with class '{css_class}'")

                # Extract links from <a> tags within those elements
                for element in elements:
                    for a_tag in element.find_all('a'):
                        if construct_from == 'text':
                            # Construct from link text
                            text = a_tag.get_text(strip=True)
                            if text and url_pattern:
                                link = construct_url(url_pattern, text=text)
                                if link:
                                    if base_url:
                                        link = base_url.rstrip('/') + link
                                    links.add(link)
                        elif construct_from == 'hqid':
                            # Construct from hqid attribute
                            hqid = a_tag.get('hqid')
                            if hqid and url_pattern:
                                link = construct_url(url_pattern, hqid=hqid)
                                if link:
                                    if base_url:
                                        link = base_url.rstrip('/') + link
                                    links.add(link)
                        else:
                            # Use actual href
                            href = a_tag.get('href')
                            if href and href != '#':
                                links.add(href)

                logger.info(f"Extracted {len(links)} unique link(s)")

            finally:
                await browser.close()
                logger.info("Browser closed.")

    except Exception as e:
        logger.error(f"Error fetching or parsing URL: {e}")
        sys.exit(1)

    return links


def write_links_to_file(links, output_file):
    """
    Write unique links to output file.

    Args:
        links: Set of links to write
        output_file: Path to output file
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            for link in sorted(links):
                f.write(link + '\n')

        logger.info(f"Successfully wrote {len(links)} unique link(s) to {output_file}")
    except Exception as e:
        logger.error(f"Error writing to output file {output_file}: {e}")
        sys.exit(1)


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Fetch a dynamically rendered webpage and extract links from elements with a specific CSS class."
    )
    parser.add_argument(
        '--url',
        required=True,
        help='URL to fetch and render'
    )
    parser.add_argument(
        '--css-class',
        required=True,
        help='CSS class name to target for link extraction'
    )
    parser.add_argument(
        '--output',
        default='outputs/links.txt',
        help='Output file path (default: outputs/links.txt)'
    )
    parser.add_argument(
        '--construct-from',
        choices=['text', 'hqid'],
        help='Construct URLs from link text (slugified) or hqid attribute. Use with --url-pattern.'
    )
    parser.add_argument(
        '--url-pattern',
        help='URL pattern for construction (e.g., "/api/{hqid}" or "/docs/{text}"). Required if --construct-from is used.'
    )
    parser.add_argument(
        '--base-url',
        help='Base URL to prepend to constructed paths (e.g., "https://help.servicedeskplus.com")'
    )
    parser.add_argument(
        '--click',
        action='store_true',
        help='Enable click-based URL discovery instead of href extraction (for React SPAs with hash routing)'
    )

    args = parser.parse_args()

    # Validate construct-from arguments
    if args.construct_from and not args.url_pattern:
        parser.error("--url-pattern is required when using --construct-from")

    # Validate click flag
    if args.click and args.construct_from:
        parser.error("--click and --construct-from cannot be used together")

    # Check browser availability
    if not ensure_browser_available('playwright'):
        logger.error("Playwright browsers not available.")
        sys.exit(1)

    # Fetch and extract links
    if args.click:
        links = await fetch_and_extract_links_by_clicking(
            args.url,
            args.css_class
        )
    else:
        links = await fetch_and_extract_links(
            args.url,
            args.css_class,
            construct_from=args.construct_from,
            url_pattern=args.url_pattern,
            base_url=args.base_url
        )

    # Write links to output file
    write_links_to_file(links, args.output)


if __name__ == "__main__":
    asyncio.run(main())
