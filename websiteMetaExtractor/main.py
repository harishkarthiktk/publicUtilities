import requests
import time
import random
import csv
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from categories import classify_category

INPUT_FILE = "urls.txt"
OUTPUT_FILE = "output.csv"

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
    urls = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line)
    return urls

def get_domain(url):
    return urlparse(url).netloc

def fetch_meta_tags(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    data = {key: None for key in META_PROPERTIES}

    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        for tag_name in META_PROPERTIES:
            meta_tag = soup.find("meta", attrs={"property": tag_name}) \
                        or soup.find("meta", attrs={"name": tag_name})
            if meta_tag and meta_tag.get("content"):
                data[tag_name] = meta_tag["content"].strip()

        data["status"] = "success"
    except requests.RequestException as e:
        data["status"] = f"failure: {e}"

    return data

def main():
    urls = read_urls(INPUT_FILE)
    if not urls:
        print("No valid URLs found in input file.")
        return

    results = []
    last_domain = None

    for url in urls:
        current_domain = get_domain(url)

        if last_domain:
            if current_domain == last_domain:
                time.sleep(random.uniform(1, 3))
            else:
                time.sleep(1)

        print(f"Fetching: {url}")
        meta_data = fetch_meta_tags(url)

        og_title = meta_data.get("og:title")
        og_desc = meta_data.get("og:description")
        meta_data["category"] = classify_category(og_title, og_desc)

        results.append(meta_data)
        last_domain = current_domain

    # Category first, then og:url, then rest of meta tags
    fieldnames = ["category", "og:url"] + [tag for tag in META_PROPERTIES if tag != "og:url"] + ["status"]

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"Done. Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
