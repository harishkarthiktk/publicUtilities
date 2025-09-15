import asyncio
import os
import re
import argparse
import markdownify
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

def extract_links_from_md(md_file):
    """
    Parses the markdown file, extracting (title, url) tuples.
    """
    with open(md_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    links = []
    for line in lines:
        match = re.match(r'- \[(.*?)\]\((.*?)\)', line.strip())
        if match:
            links.append((match.group(1), match.group(2)))
    return links

def sanitize_filename(name):
    """Sanitize for safe filesystem usage."""
    return re.sub(r'[\\/*?:"<>|]', "", name)

async def save_webpage_as_markdown(title, url, browser, output_dir):
    """
    Loads the webpage, extracts rendered content, saves it as Markdown.
    """
    try:
        page = await browser.new_page()
        await page.goto(url, timeout=60000)
        html = await page.content()
        soup = BeautifulSoup(html, 'html.parser')
        # Extract page title
        title_tag = soup.find('title')
        file_title = sanitize_filename(title_tag.text.strip() if title_tag else title)
        # Extract main content; can be improved for site-specifics
        main_content = soup.body or soup
        markdown_content = markdownify.markdownify(str(main_content), heading_style="ATX")
        file_path = os.path.join(output_dir, f"{file_title}.md")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f'# {file_title}\n\n')
            f.write(f'*Source: {url}*\n\n')
            f.write(markdown_content)
        print(f'Saved: {file_title}.md')
        await page.close()
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")

async def main(input_file, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    links = extract_links_from_md(input_file)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        for title, url in links:
            await save_webpage_as_markdown(title, url, browser, output_dir)
        await browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download web pages from a Markdown file with URLs and save as markdown.")
    parser.add_argument('-i', '--input-file', help='Input markdown file path (default: ./input.md)', required=True)
    parser.add_argument('-o', '--output-folder', default='./asyncio_output', help='Output folder path (default: ./asyncio_output)')
    args = parser.parse_args()

    asyncio.run(main(args.input_file, args.output_folder))
