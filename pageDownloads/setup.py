"""Setup configuration for pageDownloads package."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pagedownloads",
    version="2.0.0",
    author="pageDownloads Contributors",
    description="Web scraping and metadata extraction utilities",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/pageDownloads",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.7",
    install_requires=[
        "attrs>=25.4.0",
        "beautifulsoup4>=4.14.2",
        "certifi>=2025.10.5",
        "greenlet>=3.2.4",
        "h11>=0.16.0",
        "html2text>=2025.4.15",
        "idna>=3.11",
        "markdownify>=1.2.0",
        "playwright>=1.55.0",
        "pyee>=13.0.0",
        "PySocks>=1.7.1",
        "PyYAML>=6.0.1",
        "selenium>=4.38.0",
        "six>=1.17.0",
        "sniffio>=1.3.1",
        "sortedcontainers>=2.4.0",
        "soupsieve>=2.8",
        "tqdm>=4.67.1",
        "trio>=0.32.0",
        "trio-websocket>=0.12.2",
        "typing_extensions>=4.15.0",
        "urllib3>=2.5.0",
        "websocket-client>=1.9.0",
        "wsproto>=1.2.0",
    ],
    extras_require={
        "spacy": ["spacy>=3.0.0"],
        "dev": ["pytest>=7.0", "pytest-cov>=4.0"],
    },
    entry_points={
        "console_scripts": [
            "sync-page-downloader=sync_page_downloader:main",
            "async-page-downloader=async_page_downloader:main",
            "link-extractor=link_extractor:main",
            "metadata-fetcher=metadata_fetcher:main",
        ],
    },
)
