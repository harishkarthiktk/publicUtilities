#!/usr/bin/env python3
"""
Clear all collections from a Qdrant vector database instance.

This script connects to a Qdrant server via its REST API, lists all collections,
optionally confirms with the user, and deletes them. It assumes no authentication
is required (suitable for local/development setups). For production, consider
adding API key support.

Usage:
    python clearQdrantDB.py [--url http://localhost:6333] [--verbose] [--force]
"""

import argparse
import logging
from typing import List
import requests
from requests.exceptions import RequestException, HTTPError


class QdrantClearError(Exception):
    """Custom exception for Qdrant clearing operations."""


def get_collections(session: requests.Session, base_url: str) -> List[str]:
    """Fetch and return a list of collection names from the Qdrant server.

    Args:
        session: Reusable HTTP session.
        base_url: Base URL of the Qdrant server.

    Returns:
        List of collection names.

    Raises:
        QdrantClearError: If the API request fails or response is invalid.
    """
    url = f"{base_url}/collections"
    logger = logging.getLogger(__name__)
    logger.debug(f"GET request to {url}")

    try:
        response = session.get(url)
        response.raise_for_status()  # Raises HTTPError for bad status codes
        data = response.json()
        if "result" not in data or "collections" not in data["result"]:
            raise QdrantClearError("Invalid response structure from collections API")
        collections = [coll["name"] for coll in data["result"]["collections"]]
        logger.debug(f"Retrieved collections: {collections}")
        return collections
    except HTTPError as e:
        if response.status_code == 404:
            logger.info("No collections endpoint found; assuming empty DB")
            return []
        raise QdrantClearError(f"HTTP error fetching collections: {e}")
    except (RequestException, ValueError) as e:
        raise QdrantClearError(f"Failed to fetch collections: {e}")


def delete_collection(session: requests.Session, base_url: str, name: str, max_retries: int = 1) -> bool:
    """Delete a single collection from the Qdrant server.

    Args:
        session: Reusable HTTP session.
        base_url: Base URL of the Qdrant server.
        name: Name of the collection to delete.
        max_retries: Number of retry attempts for transient errors.

    Returns:
        True if deletion succeeded, False otherwise.

    Raises:
        QdrantClearError: If all retries fail.
    """
    url = f"{base_url}/collections/{name}"
    logger = logging.getLogger(__name__)
    logger.debug(f"DELETE request to {url}")

    for attempt in range(max_retries + 1):
        try:
            response = session.delete(url)
            response.raise_for_status()
            logger.debug(f"Successfully deleted {name}: {response.json()}")
            return True
        except HTTPError as e:
            if attempt < max_retries and 500 <= response.status_code < 600:
                logger.warning(f"Transient error deleting {name} (attempt {attempt + 1}): {e}. Retrying...")
                continue
            raise QdrantClearError(f"Failed to delete {name}: {e}")
        except RequestException as e:
            raise QdrantClearError(f"Network error deleting {name}: {e}")

    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Clear all Qdrant collections.")
    parser.add_argument(
        "--url",
        default="http://localhost:6333",
        help="Qdrant base URL (default: http://localhost:6333)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose (DEBUG) logging"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Skip user confirmation before deletion"
    )
    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    logger = logging.getLogger(__name__)
    logger.info("Starting Qdrant collections clear operation")

    session = requests.Session()
    try:
        collections = get_collections(session, args.url)
        if not collections:
            logger.info("No collections found to delete.")
            return

        logger.info(f"Found {len(collections)} collections: {', '.join(collections)}")
        if not args.force:
            confirm = input(f"Delete all {len(collections)} collections? [y/N]: ").strip().lower()
            if confirm != 'y':
                logger.info("Operation aborted by user.")
                return

        deleted_count = 0
        for name in collections:
            logger.info(f"Deleting collection: {name}")
            if delete_collection(session, args.url, name):
                deleted_count += 1
            else:
                logger.error(f"Failed to delete {name}")

        logger.info(f"Operation complete: {deleted_count}/{len(collections)} collections deleted successfully.")
    except QdrantClearError as e:
        logger.error(f"Qdrant operation failed: {e}")
        raise SystemExit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise SystemExit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()