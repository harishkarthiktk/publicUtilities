# pageDownloads

Web scraping utility suite for downloading and processing web content.

## Tools

- **sync_page_downloader.py** - Synchronous page downloader (Selenium) for single/batch URL processing
- **async_page_downloader.py** - Asynchronous page downloader (Playwright) for batch Markdown files
- **link_extractor.py** - Extract links from MHTML archive files
- **metadata_fetcher.py** - Extract Open Graph, Twitter Card, and SEO metadata from URLs

## Workflows

**Simple Download**
```
URL/URLs → sync_page_downloader.py → Markdown files
```
Quick single-page or small batch downloads.

**Batch Download**
```
Markdown list (- [title](url)) → async_page_downloader.py → Markdown files
```
Efficient parallel downloading of multiple pages.

**MHTML Exploration → Download**
```
MHTML file → link_extractor.py → links.txt → async_page_downloader.py → Downloaded pages
```
Explore saved websites and download linked pages.

**Content Discovery → Analysis → Download**
```
URLs → metadata_fetcher.py → CSV (titles, descriptions, categories)
→ [filter/curate] → markdown list
→ async_page_downloader.py → local knowledge base
```
Research and curate content before downloading.

## Installation

```bash
pip install -r requirements.txt
playwright install  # Required for async_page_downloader.py only
```

## Usage

### Page Downloader (Synchronous)

```bash
python sync_page_downloader.py -f urls.txt -o outputs -t
python sync_page_downloader.py -u https://example.com -o outputs
```

Options: `-f FILE`, `-u URL`, `-o OUTPUT_FOLDER`, `-t` (use page title as filename)

### Async Downloader (Batch)

```bash
python async_page_downloader.py -f links.md -o asyncio_output
```

Supports Markdown format: `- [title](url)` or plain URLs (one per line)

### Link Extractor

```bash
python link_extractor.py -f ./mhtml_folder -o links.txt
```

Extracts links from MHTML archive files with optional filtering.

### Metadata Fetcher

```bash
python metadata_fetcher.py -f urls.txt -o output.csv
```

Reads `urls.txt`, outputs metadata to `output.csv`.

## Configuration

All settings in `config.yaml`:
- Selenium/Playwright options (timeouts, headless mode, concurrency)
- Output folders and defaults
- Logging level and format
- Rate limiting and HTTP headers
- Meta properties to extract
- Content classification categories

CLI arguments override config.yaml values.

## Output

- Downloaded pages saved as Markdown (.md files)
- Metadata exported as CSV
- Logs written to `logs/logs.txt` (configurable)
- Filenames sanitized automatically
