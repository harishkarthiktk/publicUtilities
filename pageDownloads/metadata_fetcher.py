import argparse
import csv
import random
import sys
import time
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from pagedownloads.utils import config, setup_logger
from pagedownloads.meta_extractor import classify_category

logger = setup_logger(__name__)

def read_urls(file_path):
    urls = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    urls.append(line)
    except FileNotFoundError:
        logger.error(f"Input file not found: {file_path}")
    except Exception as e:
        logger.error(f"Error reading input file: {e}")
    return urls

def get_domain(url):
    return urlparse(url).netloc

def fetch_meta_tags(url, user_agent, timeout, meta_properties):
    headers = {"User-Agent": user_agent}
    data = {key: None for key in meta_properties}

    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        for tag_name in meta_properties:
            meta_tag = soup.find("meta", attrs={"property": tag_name}) \
                        or soup.find("meta", attrs={"name": tag_name})
            if meta_tag and meta_tag.get("content"):
                data[tag_name] = meta_tag["content"].strip()

        data["status"] = "success"
    except requests.RequestException as e:
        data["status"] = f"failure: {e}"

    return data

def main():
    parser = argparse.ArgumentParser(description='Extract meta tags from URLs')
    parser.add_argument(
        '-f',
        '--input-file',
        default=config.get('meta_extractor', 'input.default_file', 'urls.txt'),
        help='Input file with URLs'
    )
    parser.add_argument(
        '-o',
        '--output-file',
        default=config.get('meta_extractor', 'output.default_file', 'output.csv'),
        help='Output CSV file'
    )
    args = parser.parse_args()

    # Load configuration
    user_agent = config.get('meta_extractor', 'http.user_agent', 'Mozilla/5.0')
    timeout = config.get('meta_extractor', 'http.timeout', 10)
    meta_properties = config.get('meta_extractor', 'meta_properties', [])

    # Load rate limiting config
    same_domain_min = config.get('meta_extractor', 'rate_limiting.same_domain_delay_min', 1)
    same_domain_max = config.get('meta_extractor', 'rate_limiting.same_domain_delay_max', 3)
    domain_switch = config.get('meta_extractor', 'rate_limiting.domain_switch_delay', 1)

    urls = read_urls(args.input_file)
    if not urls:
        logger.warning("No valid URLs found in input file.")
        return

    results = []
    last_domain = None

    for url in urls:
        current_domain = get_domain(url)

        if last_domain:
            if current_domain == last_domain:
                delay = random.uniform(same_domain_min, same_domain_max)
                time.sleep(delay)
            else:
                time.sleep(domain_switch)

        logger.info(f"Fetching: {url}")
        meta_data = fetch_meta_tags(url, user_agent, timeout, meta_properties)

        og_title = meta_data.get("og:title")
        og_desc = meta_data.get("og:description")
        meta_data["category"] = classify_category(og_title, og_desc)

        results.append(meta_data)
        last_domain = current_domain

    # Category first, then og:url, then rest of meta tags
    fieldnames = ["category", "og:url"] + [tag for tag in meta_properties if tag != "og:url"] + ["status"]

    try:
        with open(args.output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        logger.info(f"Done. Results saved to {args.output_file}")
    except Exception as e:
        logger.error(f"Failed to write output file: {e}")

if __name__ == "__main__":
    main()
