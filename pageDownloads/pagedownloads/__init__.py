"""
pageDownloads - Web scraping and metadata extraction utilities.

A suite of tools for downloading web pages, extracting metadata, and processing
MHTML archives. Includes both synchronous (Selenium) and asynchronous (Playwright)
implementations for batch processing.

Version: 2.0.0
"""

__version__ = "2.0.0"
__author__ = "pageDownloads Contributors"

# Expose public API at package level
from .utils import config, setup_logger, ensure_browser_available

# lazy import classify_category since it requires optional spacy dependency
def __getattr__(name):
    if name == "classify_category":
        from .meta_extractor import classify_category
        return classify_category
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "config",
    "setup_logger",
    "ensure_browser_available",
    "classify_category",
]
