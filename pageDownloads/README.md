# pageDownloads

Web scraping utility suite for downloading and processing web content.

## Tools

- **page_downloader.py** - Asynchronous page downloader (Playwright) for batch Markdown files
- **link_extractor.py** - Extract links from MHTML archive files

## Workflows

**Batch Download**
```
Markdown list (- [title](url)) → page_downloader.py → Markdown files
```
Efficient parallel downloading of multiple pages.

**MHTML Exploration → Download**
```
MHTML file → link_extractor.py → links.txt → page_downloader.py → Downloaded pages
```
Explore saved websites and download linked pages.

## Installation

```bash
pip install -r requirements.txt
playwright install  # Required for page_downloader.py only
```

## Usage

### Async Downloader (Batch)

```bash
python page_downloader.py -f data/sample_input.txt -o outputs/async
```

Supports Markdown format: `- [title](url)` or plain URLs (one per line)

### Link Extractor

```bash
python link_extractor.py -f ./mhtml_folder -o links.txt
```

Extracts links from MHTML archive files with optional filtering.

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
