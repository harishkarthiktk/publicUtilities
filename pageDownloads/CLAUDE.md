# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**pageDownloads** is a multi-purpose web scraping utility suite for downloading and processing web content:

1. **Page Downloaders** - Convert web pages to Markdown files for local knowledge bases
2. **MHTML Link Extractor** - Extract specific links from MHTML archive files
3. **Meta Tag Scraper** - Extract Open Graph, Twitter Card, and SEO metadata from URLs

The project includes an asynchronous (Playwright) implementation for batch processing.

## Architecture

### Core Modules

- **`page_downloader.py`** - Asynchronous page downloader using Playwright
  - Better for batch processing (handles multiple URLs via async/await)
  - Supports Markdown link format `- [title](url)` or plain URLs
  - Converts with markdownify and BeautifulSoup
  - Includes source URL metadata in output
  - Outputs to `outputs/async/`

- **`link_extractor.py`** - MHTML archive link extraction
  - Parses MHTML email-format files (binary archives with embedded HTML)
  - Uses email.message_from_binary_file for MIME parsing
  - Filters links by domain/path (currently filters for `/deluge/help`)
  - Outputs unique links to text file

- **`pagedownloads/meta_extractor/`** - Meta tag scraper module
  - Fetches meta properties (Open Graph, Twitter Card, SEO, article tags)
  - Groups requests by domain with smart delay logic (1-3s same domain, 1s domain switch)
  - Outputs CSV with extracted metadata and HTTP status
  - Integrates with `classifier.py` for content classification

- **`pagedownloads/meta_extractor/classifier.py`** - Content classifier
  - Uses spaCy for NLP (auto-downloads `en_core_web_sm` if missing)
  - Lemmatizes text and matches against predefined category keywords
  - Returns category or "uncategorised"

## Development Commands

### Setup
```bash
pip install -r requirements.txt
playwright install  # Required for page_downloader.py only
```

### Running Main Tools

**Asynchronous page downloader (batch Markdown links):**
```bash
python page_downloader.py -f data/sample_input.txt -o outputs/async
```

**Extract links from MHTML files:**
```bash
python link_extractor.py -f ./mhtml_folder -o links.txt
```

### Key Dependencies

- **Playwright** (page_downloader.py) - Async browser automation
- **markdownify / BeautifulSoup4** - HTML-to-Markdown conversion
- **spaCy** (meta_extractor/classifier.py) - NLP classification
- **tqdm** - Progress bars for batch operations

## Configuration & Data Flow

### Input/Output Defaults
- `page_downloader.py`: reads from data files (e.g., `data/sample_input.txt`), outputs to `outputs/async/`
- `link_extractor.py`: reads from current directory, outputs to `links.txt`

### Logging
- Scripts write logs to `logs/logs.txt` (appends)
- File operations use UTF-8 encoding throughout
- Configuration in `config.yaml` controls logging level and format

### Filename Sanitization
Both downloaders sanitize filenames by removing invalid chars `<>:"/\|?*`, replacing spaces with underscores, truncating to 200 chars, and removing trailing dots/underscores.

## Important Notes

- **Web Scraping Disclaimer** - Respect site T&Cs, robots.txt, rate limits. Scripts comply via delays and proper user-agents.
- **MHTML Link Filtering** - Currently hardcoded to filter `/deluge/help` links; modify `link_extractor.py` to change filter criteria.
- **Playwright Binary Installation** - `playwright install` must be run before using `page_downloader.py`
- **spaCy Model** - `pagedownloads/meta_extractor/classifier.py` auto-downloads the spaCy model on first run if missing.
- **Browser Dependencies** - Playwright downloads its own browser binaries.
- **Project Structure** - Sample input files are in `data/` directory; downloaded content goes to `outputs/async/`
