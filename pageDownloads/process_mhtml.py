"""
Extract links from MHTML files.

This script processes MHTML files in a specified folder, extracts HTML content,
parses it using BeautifulSoup, and collects unique links containing
'/deluge/help'. Links are written to an output file. Includes error handling
and logging to 'logs.txt'.

Usage:
    python crawl_mhtml.py [-f <folder>] [-o <output>]

Arguments:
    -f, --folder: Folder containing .mhtml files (default: current directory)
    -o, --output: Output file for links (default: links.txt)

Requirements:
    - Python 3.6+
    - beautifulsoup4 (pip install beautifulsoup4)

Error Handling:
    - Catches file I/O, parsing, and permission errors.
    - Logs info, warnings, and errors to 'logs.txt'.

OS Compatibility:
    - Cross-platform (Windows, macOS, Linux) using os.path.join.
    - Handles case variations in file extensions (.mhtml/.MHTML).
"""

import argparse
import email
import glob
import logging
import os
import sys
from email import policy

from bs4 import BeautifulSoup

# Setup logging to logs.txt
logging.basicConfig(
    filename='logs.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='a'  # Append to logs.txt if it exists
)
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(description='Extract links from MHTML files')
parser.add_argument(
    '-f',
    '--folder',
    default='.',
    help='Folder with mhtml files'
)
parser.add_argument(
    '-o',
    '--output',
    default='links.txt',
    help='Output links file'
)
args = parser.parse_args()

links = set()

try:
    mhtml_files = []
    for pattern in ['*.mhtml', '*.MHTML']:
        mhtml_files.extend(glob.glob(os.path.join(args.folder, pattern)))
    mhtml_files = list(set(mhtml_files))  # Remove duplicates if any
    if not mhtml_files:
        logger.warning(f"No MHTML files found in {args.folder}")
    else:
        logger.info(f"Found {len(mhtml_files)} MHTML files in {args.folder}")
except OSError as e:
    logger.error(f"Error accessing folder {args.folder}: {e}")
    sys.exit(1)
except Exception as e:
    logger.error(f"Unexpected error discovering MHTML files: {e}")
    sys.exit(1)

for mhtml_file in mhtml_files:
    try:
        logger.info(f"Processing {mhtml_file}")
        with open(mhtml_file, 'rb') as f:
            msg = email.message_from_binary_file(f, policy=policy.default)

        html_content = None
        try:
            for part in msg.walk():
                if part.get_content_type() == 'text/html':
                    html_content = part.get_content()
                    break
        except email.Error as e:
            logger.error(f"Email parsing error in {mhtml_file}: {e}")
            continue

        if html_content:
            try:
                soup = BeautifulSoup(html_content, 'html.parser')
                for a in soup.find_all('a'):
                    href = a.get('href')
                    if href and '/deluge/help' in href:
                        links.add(href)
                logger.info(f"Successfully extracted links from {mhtml_file}")
            except Exception as e:
                logger.error(
                    "BeautifulSoup parsing error in %s: %s",
                    mhtml_file,
                    e
                )
        else:
            logger.warning(f"No HTML content found in {mhtml_file}")

    except FileNotFoundError:
        logger.error(f"File not found: {mhtml_file}")
    except PermissionError:
        logger.error(f"Permission denied accessing {mhtml_file}")
    except IOError as e:
        logger.error(f"IO error reading {mhtml_file}: {e}")
    except email.Error as e:
        logger.error(f"Email message error in {mhtml_file}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error processing {mhtml_file}: {e}")

try:
    with open(args.output, 'w', encoding='utf-8') as f:
        for link in sorted(links):
            f.write(link + '\n')
    logger.info(
        "Successfully wrote %d unique links to %s",
        len(links),
        args.output
    )
    print(f"Extracted {len(links)} unique links to {args.output}")
except PermissionError:
    logger.error(f"Permission denied writing to {args.output}")
    sys.exit(1)
except IOError as e:
    logger.error(f"IO error writing to {args.output}: {e}")
    sys.exit(1)
except Exception as e:
    logger.error(f"Unexpected error writing output: {e}")
    sys.exit(1)
