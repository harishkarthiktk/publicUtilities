# Meta Tag Scraper

A Python script that reads a list of URLs from a text file, fetches each page, and extracts useful `<meta>` tag content (Open Graph, Twitter Card, SEO tags) into a CSV file.  
It supports delays between requests to avoid hammering the same domain.

## Features
- Reads URLs from a `.txt` file (one per line, ignores lines starting with `#`)
- Groups requests by domain to apply smart delays:
  - 1–3 seconds between requests to the **same domain**
  - 1 second when switching to a **different domain**
- Extracts common meta tags:
  - **Open Graph**: `og:title`, `og:description`, `og:image`, `og:url`, `og:type`, `og:site_name`
  - **Twitter Card**: `twitter:title`, `twitter:description`, `twitter:image`, `twitter:card`
  - **SEO tags**: `description`, `keywords`, `author`
  - **Article tags**: `article:published_time`, `article:author`, `profile:username`
- Saves results to `output.csv` with:
  - `url`
  - Columns for each meta tag (blank if missing)
  - `status` column (`success` / `failure:<reason>`)

## Requirements
- Python 3.7+
- `requests`
- `beautifulsoup4`

Install dependencies:
```bash
pip install requests beautifulsoup4
````

## Usage
1. Create a `urls.txt` file:

```
# Example URLs
https://www.instagram.com/p/POSTCODE1/
https://twitter.com/someuser/status/12345
https://example.com/article
```

2. Run the script:

```bash
python meta_scraper.py
```

3. Output will be saved as `output.csv`.

## Output Example

| url                                                                        | og\:title                | og\:description     | og\:image                        | ... | status  |
| -------------------------------------------------------------------------- | ------------------------ | ------------------- | -------------------------------- | --- | ------- |
| [https://www.instagram.com/p/XYZ123/](https://www.instagram.com/p/XYZ123/) | "@username on Instagram" | "Cool caption here" | [https://...jpg](https://...jpg) | ... | success |

## Notes

* Script only works for publicly accessible pages.
* Some sites may block automated requests; the script includes delays to help avoid rate-limiting.
* Missing meta tags will result in blank CSV cells for that column.