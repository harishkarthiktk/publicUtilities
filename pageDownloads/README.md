# pageDownloads

## Purpose
This tool downloads and saves webpages as Markdown files for local knowledge base augmentation. It supports both synchronous (Selenium-based) and asynchronous (Playwright-based) versions for processing single or multiple URLs. The async version is better for batch processing Markdown files with links, while the sync version handles plain URL lists flexibly.

Note: While straightforward browser "Save As" works for single pages, this automates batch downloading—though it may take longer to set up!

## Installation
1. Clone or navigate to this directory.
2. Install dependencies:
   - For `main.py` (sync): `pip install -r requirements.txt` (includes selenium, html2text, tqdm).
   - For `main_asyncio.py` (async): `pip install -r requirements.txt` (includes playwright, markdownify, beautifulsoup4, tqdm). Then run `playwright install` for browser binaries.
3. Ensure Chrome is installed for Selenium (or use webdriver-manager if added).

## Usage

### Synchronous Version (main.py)
Processes plain text files with URLs (one per line) or a single URL. Uses Selenium for rendering dynamic content.

Options:
```
  -h, --help            show this help message and exit
  -f FILE, --file FILE  Path to a text file with URLs, one per line.
  -u URL, --url URL     A single URL to process.
  -o OUTPUT_FOLDER, --output-folder OUTPUT_FOLDER
                        Folder to save the output files (default: outputs).
  -t, --title           Use webpage title for output filename instead of URL-derived.
```

Example:
```
python main.py -f urls.txt -o my_downloads -t
```
- Outputs: `.md` files in `outputs/` (or specified folder), with logging to `logs.txt`.
- Filename: URL-based by default (e.g., `https_example_com_page.md`); title-based if `-t` used.

### Asynchronous Version (main_asyncio.py)
Processes Markdown files with links in format `- [title](url)` or plain URLs (one per line, URL as title fallback). Uses Playwright for efficient async loading.

Options:
```
  -h, --help            show this help message and exit
  -f FILE, --input-file FILE
                        Path to input Markdown file (required, default: ./input.md).
  -o OUTPUT_FOLDER, --output-folder OUTPUT_FOLDER
                        Folder to save the output files (default: ./asyncio_output).
```

Example:
```
python main_asyncio.py -f links.md -o batch_downloads
```
- Outputs: `.md` files in `./asyncio_output/` (or specified), each prefixed with `# Title` and `*Source: URL*`.
- Filename: Sanitized page title from `<title>` tag.
- Progress: tqdm bar for sequential processing.

Sample input for async (`testdata.md`):
```
- [Example Page](https://example.com)
https://another-site.com
```

## Output Format
All versions save rendered page content as Markdown (.md files):
- Extracts body content, converts HTML to MD.
- Sanitizes filenames to avoid filesystem issues.
- Includes source URL in async version for traceability.

## Disclaimer
Web scraping and downloading may breach targeted websites' T&Cs. This tool is for personal, ethical use only. Respect robots.txt, rate limits, and user-agent policies. Liability rests with the user.

---
