import argparse
import asyncio
import os
import re

import markdownify
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from tqdm import tqdm


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
            print(f"Parsed {len(md_links)} Markdown links from {md_file}")
        else:
            # Fallback: treat non-empty lines as plain URLs, using URL as title
            plain_links = []
            for line in lines:
                url = line.strip()
                if url and not url.startswith('#'):  # Ignore comments or headers
                    plain_links.append((url, url))  # Use URL as title fallback
            links = plain_links
            if plain_links:
                print(f"Parsed {len(plain_links)} plain URLs from {md_file} (using URL as title fallback)")
            else:
                print(f"No valid URLs found in {md_file}")
    except Exception as e:
        print(f"Error reading input file {md_file}: {e}")
    
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
    try:
        print(f"  Creating new page for {url}...")
        page = await browser.new_page()
        print(f"  Navigating to {url}...")
        await page.goto(url, timeout=60000)
        print(f"  Waiting for content...")
        html = await page.content()
        print(f"  Content retrieved, parsing HTML...")
        soup = BeautifulSoup(html, 'html.parser')
        # Extract page title
        title_tag = soup.find('title')
        file_title = sanitize_filename(title_tag.text.strip() if title_tag else title)
        print(f"  Using title: {file_title}")
        # Extract main content; can be improved for site-specifics
        main_content = soup.body or soup
        print(f"  Converting to Markdown...")
        markdown_content = markdownify.markdownify(str(main_content), heading_style="ATX")
        file_path = os.path.join(output_dir, f"{file_title}.md")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f'# {file_title}\n\n')
            f.write(f'*Source: {url}*\n\n')
            f.write(markdown_content)
        print(f'  Saved: {file_title}.md')
        await page.close()
        print(f"  Page closed for {url}")
    except Exception as e:
        tqdm.write(f"Failed to fetch {url}: {e}")
        try:
            await page.close()
        except:
            pass  # Ignore if page not created

async def main(input_file, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    links = extract_links_from_md(input_file)
    
    if not links:
        print(f"No links to process from {input_file}. Exiting.")
        return
    
    print(f"Starting to process {len(links)} links...")
    
    try:
        async with async_playwright() as p:
            print("Launching browser...")
            browser = await p.chromium.launch(headless=True)
            print("Browser launched successfully.")
            
            # Note: Progress tracking is for sequential processing only.
            # For parallelization (e.g., via asyncio.gather), tqdm.asyncio would be required and is out of scope here.
            for title, url in tqdm(links, desc="Processing links"):
                print(f"Processing: {url}")
                await save_webpage_as_markdown(title, url, browser, output_dir)
            
            print("Closing browser...")
            await browser.close()
            print("Browser closed.")
    except Exception as e:
        print(f"Error in main async execution: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download web pages from a Markdown file with URLs and save as markdown.")
    parser.add_argument('-f', '--input-file', help='Input markdown file path (default: ./input.md)', required=True)
    parser.add_argument('-o', '--output-folder', default='./asyncio_output', help='Output folder path (default: ./asyncio_output)')
    args = parser.parse_args()

    asyncio.run(main(args.input_file, args.output_folder))
