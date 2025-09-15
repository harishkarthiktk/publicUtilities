import requests
import csv
import concurrent.futures
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from categories import classify_category

INPUT_FILE = "urls.txt"
OUTPUT_FILE = "output.csv"
MAX_WORKERS = 10  # Number of concurrent threads

META_PROPERTIES = [
    # Open Graph
    "og:title", "og:description", "og:image", "og:url",
    "og:type", "og:site_name",

    # Twitter Card
    "twitter:title", "twitter:description", "twitter:image", "twitter:card",

    # SEO / Misc
    "description", "keywords", "author",

    # Article-specific
    "article:published_time", "article:author", "profile:username"
]

def read_urls(file_path):
    """Reads a file and returns a list of non-empty, non-comment lines."""
    urls = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line)
    return urls

def fetch_meta_tags(url):
    """
    Fetches a URL and extracts its meta tags.
    Returns a dictionary with the extracted data and a status.
    """
    headers = {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"}
    data = {key: None for key in META_PROPERTIES}
    data["url"] = url  # Include original URL for context

    try:
        # Using a timeout is crucial for concurrent requests
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        soup = BeautifulSoup(r.text, "html.parser")

        for tag_name in META_PROPERTIES:
            # Find meta tag by 'property' (Open Graph) or 'name' (Twitter, SEO)
            meta_tag = soup.find("meta", attrs={"property": tag_name}) or \
                       soup.find("meta", attrs={"name": tag_name})
            
            if meta_tag and meta_tag.get("content"):
                data[tag_name] = meta_tag["content"].strip()

        # If 'og:url' is missing, use the original URL as a fallback
        if not data.get("og:url"):
            data["og:url"] = url

        data["status"] = "success"
    except requests.RequestException as e:
        # Catch any request-related error (timeout, connection error, etc.)
        data["status"] = f"failure: {e}"
    except Exception as e:
        # Catch other potential errors during processing
        data["status"] = f"failure: unexpected error - {e}"

    return data

def main():
    """
    Main function to read URLs, fetch meta tags concurrently, and save to CSV.
    """
    urls = read_urls(INPUT_FILE)
    if not urls:
        print(f"No valid URLs found in {INPUT_FILE}.")
        return

    results = []
    # Using ThreadPoolExecutor to perform network I/O concurrently
    # 'max_workers' controls how many URLs are fetched at the same time
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # map() runs 'fetch_meta_tags' for each url in the list.
        # It returns results in the same order the tasks were submitted.
        future_to_url = {executor.submit(fetch_meta_tags, url): url for url in urls}
        
        print(f"Fetching {len(urls)} URLs with up to {MAX_WORKERS} concurrent workers...")

        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                meta_data = future.result()
                
                # Classify category based on title and description
                og_title = meta_data.get("og:title")
                og_desc = meta_data.get("og:description")
                meta_data["category"] = classify_category(og_title, og_desc)
                
                results.append(meta_data)
                print(f"[{meta_data['status'].upper()}] Fetched: {url}")

            except Exception as exc:
                print(f"An error occurred while processing {url}: {exc}")
                # Optionally log this to a separate error file
                results.append({"url": url, "status": f"failure: {exc}", "category": "unknown"})


    if not results:
        print("No results were generated.")
        return

    # Define the order of columns for the CSV file
    # Start with key identifiers, then the category, then the rest
    fieldnames = ["category", "og:url"] + [tag for tag in META_PROPERTIES if tag != "og:url"] + ["status"]
    
    # Remove duplicates that might arise from the original URL being added
    fieldnames = list(dict.fromkeys(fieldnames)) 

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        # Use DictWriter to handle missing data gracefully
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(results)

    print(f"\nDone. {len(results)} results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
