"""
Extract links from MHTML files.

This script processes MHTML files in a specified folder, extracts HTML content,
parses it using BeautifulSoup, and collects links matching configured patterns.
Links are written to an output file. Includes error handling and logging.

Usage:
    python process_mhtml.py -f <folder> -o <output> [--include-patterns PATTERN ...] [--exclude-patterns PATTERN ...]

Arguments:
    -f, --folder: Folder containing .mhtml files (default: current directory)
    -o, --output: Output file for links (default: links.txt)
    --include-patterns: Patterns to match in hrefs (overrides config.yaml)
    --exclude-patterns: Patterns to exclude from hrefs (overrides config.yaml)

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
import os
import sys
from email import policy

from bs4 import BeautifulSoup
from pagedownloads.utils import config, setup_logger

logger = setup_logger(__name__)


def extract_links_from_mhtml_files(folder, include_patterns, exclude_patterns):
    """
    Extract links from all MHTML files in a folder.

    Args:
        folder: Folder containing MHTML files
        include_patterns: List of patterns to match in hrefs (empty = all)
        exclude_patterns: List of patterns to exclude from hrefs

    Returns:
        Set of unique links
    """
    links = set()
    extract_all = len(include_patterns) == 0

    try:
        mhtml_files = []
        for pattern in ['*.mhtml', '*.MHTML']:
            mhtml_files.extend(glob.glob(os.path.join(folder, pattern)))
        mhtml_files = list(set(mhtml_files))

        if not mhtml_files:
            logger.warning(f"No MHTML files found in {folder}")
        else:
            logger.info(f"Found {len(mhtml_files)} MHTML files in {folder}")

    except OSError as e:
        logger.error(f"Error accessing folder {folder}: {e}")
        return links
    except Exception as e:
        logger.error(f"Unexpected error discovering MHTML files: {e}")
        return links

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
                        if href:
                            # Check include patterns
                            if extract_all or any(pattern in href for pattern in include_patterns):
                                # Check exclude patterns
                                if not any(pattern in href for pattern in exclude_patterns):
                                    links.add(href)
                    logger.info(f"Successfully extracted links from {mhtml_file}")
                except Exception as e:
                    logger.error(f"BeautifulSoup parsing error in {mhtml_file}: {e}")
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

    return links


def write_links_to_file(links, output_file):
    """
    Write unique links to output file.

    Args:
        links: Set of links to write
        output_file: Path to output file

    Returns:
        True if successful, False otherwise
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for link in sorted(links):
                f.write(link + '\n')
        logger.info(f"Successfully wrote {len(links)} unique links to {output_file}")
        return True
    except PermissionError:
        logger.error(f"Permission denied writing to {output_file}")
        return False
    except IOError as e:
        logger.error(f"IO error writing to {output_file}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error writing output: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Extract links from MHTML files')
    parser.add_argument(
        '-f',
        '--folder',
        default=config.get('process_mhtml', 'output.default_folder', '.'),
        help='Folder with MHTML files'
    )
    parser.add_argument(
        '-o',
        '--output',
        default=config.get('process_mhtml', 'output.default_file', 'links.txt'),
        help='Output links file'
    )
    parser.add_argument(
        '--include-patterns',
        nargs='*',
        help='Patterns to match in hrefs (overrides config.yaml)'
    )
    parser.add_argument(
        '--exclude-patterns',
        nargs='*',
        help='Patterns to exclude from hrefs (overrides config.yaml)'
    )
    args = parser.parse_args()

    # Load filter patterns from CLI or config
    if args.include_patterns is not None:
        include_patterns = args.include_patterns
    else:
        include_patterns = config.get('process_mhtml', 'filters.include_patterns', [])

    if args.exclude_patterns is not None:
        exclude_patterns = args.exclude_patterns
    else:
        exclude_patterns = config.get('process_mhtml', 'filters.exclude_patterns', [])

    logger.info(f"Include patterns: {include_patterns if include_patterns else 'all links'}")
    logger.info(f"Exclude patterns: {exclude_patterns if exclude_patterns else 'none'}")

    # Extract links
    links = extract_links_from_mhtml_files(args.folder, include_patterns, exclude_patterns)

    if not links:
        logger.warning("No links extracted from MHTML files")
        return

    # Write to output
    success = write_links_to_file(links, args.output)
    if success:
        logger.info(f"Extracted {len(links)} unique links to {args.output}")


if __name__ == "__main__":
    main()
