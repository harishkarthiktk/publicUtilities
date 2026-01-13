# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**pageDownloads** is a multi-purpose web scraping utility suite for downloading and processing web content:

1. **Page Downloaders** - Convert web pages to Markdown files for local knowledge bases
2. **MHTML Link Extractor** - Extract specific links from MHTML archive files
3. **Meta Tag Scraper** - Extract Open Graph, Twitter Card, and SEO metadata from URLs

The project includes both synchronous (Selenium) and asynchronous (Playwright) implementations for different use cases.

## Architecture

### Core Modules

- **`main.py`** - Synchronous page downloader using Selenium
  - Renders dynamic content via headless Chrome
  - Supports batch processing from URL lists or single URL input
  - Uses html2text for HTML-to-Markdown conversion
  - Outputs filename based on URL or page title

- **`main_asyncio.py`** - Asynchronous page downloader using Playwright
  - Better for batch processing (handles multiple URLs via async/await)
  - Supports Markdown link format `- [title](url)` or plain URLs
  - Converts with markdownify and BeautifulSoup
  - Includes source URL metadata in output

- **`process_mhtml.py`** - MHTML archive link extraction
  - Parses MHTML email-format files (binary archives with embedded HTML)
  - Uses email.message_from_binary_file for MIME parsing
  - Filters links by domain/path (currently filters for `/deluge/help`)
  - Outputs unique links to text file

- **`websiteMetaExtractor/main.py`** - Meta tag scraper
  - Fetches meta properties (Open Graph, Twitter Card, SEO, article tags)
  - Groups requests by domain with smart delay logic (1-3s same domain, 1s domain switch)
  - Outputs CSV with extracted metadata and HTTP status
  - Integrates with `categories.py` for content classification

- **`websiteMetaExtractor/categories.py`** - Content classifier
  - Uses spaCy for NLP (auto-downloads `en_core_web_sm` if missing)
  - Lemmatizes text and matches against predefined category keywords
  - Returns category or "uncategorised"

## Development Commands

### Setup
```bash
pip install -r requirements.txt
playwright install  # Required for main_asyncio.py only
```

### Running Main Tools

**Synchronous page downloader (single or batch):**
```bash
python main.py -f urls.txt -o outputs -t          # Batch with title-based filenames
python main.py -u https://example.com -o outputs  # Single URL
```

**Asynchronous page downloader (batch Markdown links):**
```bash
python main_asyncio.py -f input.md -o asyncio_output
```

**Extract links from MHTML files:**
```bash
python process_mhtml.py -f ./mhtml_folder -o links.txt
```

**Extract metadata from URLs:**
```bash
cd websiteMetaExtractor
python main.py  # Reads urls.txt, outputs output.csv
```

### Key Dependencies

- **Selenium** (main.py) - Browser automation for dynamic content
- **Playwright** (main_asyncio.py) - Async browser automation
- **html2text / markdownify** - HTML-to-Markdown conversion
- **BeautifulSoup4** - HTML parsing
- **spaCy** (websiteMetaExtractor) - NLP classification
- **tqdm** - Progress bars for batch operations

## Configuration & Data Flow

### Input/Output Defaults
- `main.py`: reads from file/URL, outputs to `outputs/` directory
- `main_asyncio.py`: reads from `input.md`, outputs to `asyncio_output/`
- `process_mhtml.py`: reads from current directory, outputs to `links.txt`
- `websiteMetaExtractor/main.py`: reads from `urls.txt`, outputs to `output.csv`

### Logging
- `main.py` and `process_mhtml.py` write logs to `logs.txt` (appends)
- File operations use UTF-8 encoding throughout

### Filename Sanitization
Both downloaders sanitize filenames by removing invalid chars `<>:"/\|?*`, replacing spaces with underscores, truncating to 200 chars, and removing trailing dots/underscores.

## Important Notes

- **Web Scraping Disclaimer** - Respect site T&Cs, robots.txt, rate limits. Script complies with terms via delays and proper user-agents.
- **MHTML Link Filtering** - Currently hardcoded to filter `/deluge/help` links; modify `process_mhtml.py:102` to change filter criteria.
- **Playwright Binary Installation** - `playwright install` must be run before using `main_asyncio.py`
- **spaCy Model** - `websiteMetaExtractor/categories.py` auto-downloads the spaCy model on first run if missing.
- **Browser Dependencies** - Selenium requires Chrome/Chromium installed; Playwright downloads its own browser binaries.
