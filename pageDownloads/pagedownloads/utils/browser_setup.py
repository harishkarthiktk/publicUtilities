import subprocess
import sys
import shutil
from typing import Literal
from .logger import setup_logger

logger = setup_logger(__name__)


def check_chrome_available() -> bool:
    """Check if Chrome/Chromium is installed."""
    chrome_names = ['google-chrome', 'chrome', 'chromium', 'chromium-browser']
    for name in chrome_names:
        if shutil.which(name):
            return True
    return False


def check_playwright_browsers() -> bool:
    """Check if Playwright browsers are installed."""
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'playwright', 'install', '--dry-run'],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False


def prompt_install_chrome() -> bool:
    """Prompt user to install Chrome webdriver."""
    logger.warning("Chrome/Chromium browser not found.")
    logger.info("Chrome is required for Selenium-based page downloading.")
    logger.info("Please install Chrome from: https://www.google.com/chrome/")

    response = input("Would you like to install chromedriver using webdriver-manager? (y/n): ")

    if response.lower() == 'y':
        try:
            logger.info("Installing webdriver-manager...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'webdriver-manager'],
                         check=True)
            logger.info("webdriver-manager installed successfully.")
            logger.info("Note: Please modify main.py to use webdriver-manager for ChromeDriver.")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install webdriver-manager: {e}")
            return False

    return False


def prompt_install_playwright() -> bool:
    """Prompt user to install Playwright browsers."""
    logger.warning("Playwright browsers not found.")
    logger.info("Playwright requires browser binaries for operation.")

    response = input("Would you like to install Playwright browsers now? (y/n): ")

    if response.lower() == 'y':
        try:
            logger.info("Installing Playwright browsers (this may take a few minutes)...")
            subprocess.run([sys.executable, '-m', 'playwright', 'install'], check=True)
            logger.info("Playwright browsers installed successfully.")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install Playwright browsers: {e}")
            return False

    return False


def ensure_browser_available(browser_type: Literal['selenium', 'playwright']) -> bool:
    """
    Ensure required browser is available, prompt to install if missing.

    Args:
        browser_type: 'selenium' or 'playwright'

    Returns:
        True if browser available or successfully installed, False otherwise
    """
    if browser_type == 'selenium':
        if check_chrome_available():
            return True
        return prompt_install_chrome()

    elif browser_type == 'playwright':
        if check_playwright_browsers():
            return True
        return prompt_install_playwright()

    return False
