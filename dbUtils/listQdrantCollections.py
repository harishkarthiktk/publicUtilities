#!/usr/bin/env python3
"""
List all collections from a Qdrant vector database instance, including their sizes and sample contents.

This script connects to a Qdrant server via its REST API, lists all collections,
retrieves the number of points (vectors) in each, and optionally shows sample points
with their payloads for a gist of contents. It assumes no authentication
is required (suitable for local/development setups). For production, consider
adding API key support.

Usage:
    python listQdrantCollections.py [--url http://localhost:6333] [--verbose] [--samples 3]
"""
import argparse
import logging
from typing import List, Dict, Any
import requests
from requests.exceptions import RequestException, HTTPError


class QdrantListError(Exception):
    """Custom exception for Qdrant listing operations."""


def get_collections(session: requests.Session, base_url: str) -> List[str]:
    """Fetch and return a list of collection names from the Qdrant server.

    Args:
        session: Reusable HTTP session.
        base_url: Base URL of the Qdrant server.

    Returns:
        List of collection names.

    Raises:
        QdrantListError: If the API request fails or response is invalid.
    """
    url = f"{base_url}/collections"
    logger = logging.getLogger(__name__)
    logger.debug(f"GET request to {url}")

    try:
        response = session.get(url)
        response.raise_for_status()  # Raises HTTPError for bad status codes
        data = response.json()
        if "result" not in data or "collections" not in data["result"]:
            raise QdrantListError("Invalid response structure from collections API")
        collections = [coll["name"] for coll in data["result"]["collections"]]
        logger.debug(f"Retrieved collections: {collections}")
        return collections
    except HTTPError as e:
        if response.status_code == 404:
            logger.info("No collections endpoint found; assuming empty DB")
            return []
        raise QdrantListError(f"HTTP error fetching collections: {e}")
    except (RequestException, ValueError) as e:
        raise QdrantListError(f"Failed to fetch collections: {e}")


def get_collection_info(session: requests.Session, base_url: str, name: str) -> int:
    """Fetch the number of points (vectors) in a specific collection.

    Args:
        session: Reusable HTTP session.
        base_url: Base URL of the Qdrant server.
        name: Name of the collection.

    Returns:
        Number of points in the collection (0 if unavailable).

    Raises:
        QdrantListError: If the request fails critically.
    """
    url = f"{base_url}/collections/{name}"
    logger = logging.getLogger(__name__)
    logger.debug(f"GET request to {url} for info")

    try:
        response = session.get(url)
        response.raise_for_status()
        data = response.json()
        if "result" not in data:
            raise QdrantListError(f"Invalid response structure for collection {name}")
        vectors_count = data["result"].get("vectors_count", 0)
        logger.debug(f"Collection {name} has {vectors_count} points")
        return vectors_count
    except HTTPError as e:
        logger.warning(f"HTTP error fetching info for {name}: {e} (status: {response.status_code})")
        return 0
    except (RequestException, ValueError) as e:
        raise QdrantListError(f"Failed to fetch info for {name}: {e}")


def get_collection_samples(session: requests.Session, base_url: str, name: str, limit: int = 3) -> List[Dict[str, Any]]:
    """Fetch sample points from a collection to get a gist of its contents.

    Args:
        session: Reusable HTTP session.
        base_url: Base URL of the Qdrant server.
        name: Name of the collection.
        limit: Maximum number of sample points to fetch.

    Returns:
        List of dictionaries with 'id' and 'payload' for each sample.

    Raises:
        QdrantListError: If the request fails critically.
    """
    url = f"{base_url}/collections/{name}/points/scroll?limit={limit}&with_payload=true"
    logger = logging.getLogger(__name__)
    logger.debug(f"GET request to {url} for samples")

    try:
        response = session.get(url)
        response.raise_for_status()
        data = response.json()
        if "result" not in data or "points" not in data["result"]:
            raise QdrantListError(f"Invalid response structure for samples in {name}")
        samples = []
        for point in data["result"]["points"]:
            sample = {
                "id": point.get("id"),
                "payload": point.get("payload", {})
            }
            samples.append(sample)
        logger.debug(f"Fetched {len(samples)} samples for {name}")
        return samples
    except HTTPError as e:
        logger.warning(f"HTTP error fetching samples for {name}: {e} (status: {response.status_code})")
        return []
    except (RequestException, ValueError) as e:
        raise QdrantListError(f"Failed to fetch samples for {name}: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="List Qdrant collections with sizes and optional samples.")
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
        "--samples", "-s",
        type=int,
        default=0,
        help="Number of sample points to show per collection (default: 0, no samples)"
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
    logger.info("Starting Qdrant collections list operation")

    session = requests.Session()
    try:
        collections = get_collections(session, args.url)
        if not collections:
            logger.info("No collections found.")
            return

        logger.info(f"Found {len(collections)} collections:")
        total_points = 0
        for name in collections:
            size = get_collection_info(session, args.url, name)
            logger.info(f"  {name}: {size} points")
            total_points += size

            if args.samples > 0:
                samples = get_collection_samples(session, args.url, name, args.samples)
                if samples:
                    logger.info(f"    Sample contents for {name}:")
                    for sample in samples:
                        logger.info(f"      ID: {sample['id']}")
                        logger.info(f"      Payload: {sample['payload']}")
                else:
                    logger.info(f"    No samples available for {name}")

        logger.info(f"Total points across all collections: {total_points}")
    except QdrantListError as e:
        logger.error(f"Qdrant operation failed: {e}")
        raise SystemExit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise SystemExit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()