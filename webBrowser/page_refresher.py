#!/usr/bin/env python3
"""
Page Refresher - Monitor web pages and detect changes
Reads YAML configs, opens tabs in a shared Chromium context, monitors for selector changes
"""

import asyncio
import sys
import os
import random
from pathlib import Path
from datetime import datetime
import logging
import signal
import json
from typing import Optional, Dict, List, Any

import yaml
from playwright.async_api import async_playwright, Page, BrowserContext, Browser


class PageRefresherConfig:
    """Parse and validate a YAML config file"""

    def __init__(self, config_dict: Dict[str, Any], config_name: str):
        self.url: str = config_dict.get("url")
        if not self.url:
            raise ValueError(f"{config_name}: 'url' is required")

        self.interval: int = config_dict.get("interval", 180)
        self.jitter: float = config_dict.get("jitter", 0)  # percent, e.g. 20 = ±20%
        self.selectors: List[str] = config_dict.get("selectors", [])
        self.label: str = config_dict.get("label", config_name)

        default_log = f"logs/{config_name}.txt"
        self.log_path: str = config_dict.get("log", default_log)


class TabLogger:
    """Logging for a single tab"""

    def __init__(self, log_path: str, label: str):
        self.log_path = Path(log_path)
        self.label = label
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, message: str):
        """Write to log file and stdout"""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted = f"[{ts}] [{self.label}] {message}"

        # Write to file
        with open(self.log_path, "a") as f:
            f.write(formatted + "\n")

        # Print to stdout
        print(formatted)


class PageRefresher:
    """Main app - manages browser, tabs, and monitoring loops"""

    def __init__(self, configs: List[PageRefresherConfig], headless: bool = False):
        self.configs = configs
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.pages: Dict[str, Page] = {}
        self.loggers: Dict[str, TabLogger] = {}
        self.session_path = Path("sessions/session.json")
        self.session_save_counter = 0
        self.session_save_interval = 5
        self.shutdown_event = asyncio.Event()

    def is_session_valid(self) -> bool:
        """Validate session file structure and integrity"""
        if not self.session_path.exists():
            return False

        try:
            with open(self.session_path, "r") as f:
                data = json.load(f)

            # Check for expected session structure
            if not isinstance(data, dict):
                return False

            # Playwright sessions should have cookies and/or origins
            has_cookies = "cookies" in data and isinstance(data["cookies"], list)
            has_origins = "origins" in data and isinstance(data["origins"], list)

            return has_cookies or has_origins
        except Exception:
            return False

    async def load_session(self) -> Optional[Dict]:
        """Load saved session if it exists and is valid"""
        if not self.session_path.exists():
            return None

        if not self.is_session_valid():
            print(f"\n[!] Session file appears to be corrupted or invalid")
            response = input("[?] Refresh session? (y/n): ").strip().lower()
            if response == "y":
                self.session_path.unlink()
                print("[*] Session cleared. You will need to log in again.")
                return None
            else:
                print("[!] Attempting to use possibly invalid session (may cause crashes)...")
                # Still try to load it if user insists

        try:
            with open(self.session_path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load session: {e}")
        return None

    async def save_session(self):
        """Save current session state"""
        if not self.context:
            return
        try:
            self.session_path.parent.mkdir(parents=True, exist_ok=True)
            state = await self.context.storage_state(path=str(self.session_path))
            self.session_save_counter = 0
        except Exception as e:
            print(f"Warning: Failed to save session: {e}")

    async def init_browser(self):
        """Initialize Playwright browser and context"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=self.headless)

        # Load session if available
        session = await self.load_session()

        # Create context with optional session
        context_kwargs = {
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        }
        if session:
            context_kwargs["storage_state"] = session

        self.context = await self.browser.new_context(**context_kwargs)

    async def navigate_all(self) -> List[str]:
        """Navigate all tabs to their URLs and wait for networkidle
        Returns list of labels that need auth (URL != target URL)
        """
        auth_required = []

        for config in self.configs:
            logger = TabLogger(config.log_path, config.label)
            self.loggers[config.label] = logger

            page = await self.context.new_page()
            self.pages[config.label] = page

            logger.log(f"Navigating to {config.url}")
            await page.goto(config.url, wait_until="networkidle")

            # Check if redirected (auth required)
            if page.url != config.url:
                auth_required.append(config.label)
                logger.log(f"Auth redirect detected: {page.url}")

        return auth_required

    async def wait_for_auth(self, auth_required: List[str]):
        """Wait for manual login"""
        if not auth_required:
            return

        labels = ", ".join(auth_required)
        print(f"\n[!] Auth required for: {labels}")
        print("[!] Log in in the browser, then press Enter to continue monitoring.\n")

        # Non-blocking wait for user input
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, input)

        # Re-navigate auth tabs to their target URLs
        for label in auth_required:
            config = next(c for c in self.configs if c.label == label)
            page = self.pages[label]
            logger = self.loggers[label]

            logger.log(f"Re-navigating after auth to {config.url}")
            await page.goto(config.url, wait_until="networkidle")

    async def monitor_tab(self, config: PageRefresherConfig):
        """Monitor a single tab: reload on interval, check selectors for changes"""
        page = self.pages[config.label]
        logger = self.loggers[config.label]
        previous = {}

        while not self.shutdown_event.is_set():
            try:
                await page.reload(wait_until="networkidle")
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.log(f"Reloaded")

                # Check selectors for changes
                for selector in config.selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        values = [await el.inner_text() for el in elements]

                        if selector not in previous or values != previous[selector]:
                            old = previous.get(selector, "None")
                            logger.log(f"CHANGE {selector}: {old} -> {values}")
                            print(f"[CHANGE] [{config.label}] {selector}")

                        previous[selector] = values
                    except Exception as e:
                        logger.log(f"Error checking selector {selector}: {e}")

                # Periodic session save
                self.session_save_counter += 1
                if self.session_save_counter >= self.session_save_interval:
                    await self.save_session()

                # Sleep until next refresh with optional jitter
                if config.jitter > 0:
                    delta = config.interval * (config.jitter / 100)
                    sleep_time = config.interval + random.uniform(-delta, delta)
                    sleep_time = max(sleep_time, 1)  # guard against <=0
                else:
                    sleep_time = config.interval
                logger.log(f"Next refresh in {sleep_time:.1f}s")
                await asyncio.sleep(sleep_time)

            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.log(f"Error during monitoring: {e}")
                await asyncio.sleep(5)

    async def shutdown(self):
        """Graceful shutdown"""
        print("\n[*] Shutting down...")
        self.shutdown_event.set()

        if self.context:
            await self.save_session()
            await self.context.close()

        if self.browser:
            await self.browser.close()

        print("[*] Done")
        sys.exit(0)

    async def run(self):
        """Main run loop"""
        try:
            # Set up signal handlers now that event loop exists
            loop = asyncio.get_running_loop()

            def handle_signal():
                asyncio.create_task(self.shutdown())

            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, handle_signal)

            await self.init_browser()

            # Navigate all tabs
            auth_required = await self.navigate_all()

            # Handle auth if needed
            await self.wait_for_auth(auth_required)

            # Start monitoring all tabs concurrently
            tasks = [
                self.monitor_tab(config)
                for config in self.configs
            ]

            print("[*] Monitoring started. Press Ctrl+C to stop.\n")

            await asyncio.gather(*tasks)

        except KeyboardInterrupt:
            await self.shutdown()
        except Exception as e:
            print(f"Fatal error: {e}")
            await self.shutdown()


def load_configs(config_sources: List[str]) -> List[PageRefresherConfig]:
    """Load configs from files or directory"""
    configs = []

    for source in config_sources:
        source_path = Path(source)

        if source_path.is_dir():
            # Load all *.yaml from directory
            yaml_files = sorted(source_path.glob("*.yaml"))
            if not yaml_files:
                print(f"Warning: No .yaml files found in {source}")
            for yaml_file in yaml_files:
                config_dict = load_yaml_file(yaml_file)
                config_name = yaml_file.stem
                configs.append(PageRefresherConfig(config_dict, config_name))

        elif source_path.is_file():
            # Load single file
            config_dict = load_yaml_file(source_path)
            config_name = source_path.stem
            configs.append(PageRefresherConfig(config_dict, config_name))

        else:
            print(f"Error: {source} not found")
            sys.exit(1)

    if not configs:
        print("Error: No configs loaded")
        sys.exit(1)

    return configs


def load_yaml_file(path: Path) -> Dict[str, Any]:
    """Load and parse YAML file"""
    try:
        with open(path, "r") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Error loading {path}: {e}")
        sys.exit(1)


def main():
    """CLI entry point"""
    headless = "--headless" in sys.argv
    if headless:
        sys.argv.remove("--headless")

    refresh_session = "--refresh" in sys.argv
    if refresh_session:
        sys.argv.remove("--refresh")
        session_path = Path("sessions/session.json")
        if session_path.exists():
            session_path.unlink()
            print("[*] Session cleared")
        sys.exit(0)

    # Determine config sources
    config_sources = sys.argv[1:] if len(sys.argv) > 1 else ["configs"]

    # Verify config sources exist
    for source in config_sources:
        if not Path(source).exists():
            print(f"Error: {source} not found")
            sys.exit(1)

    # Load configs
    configs = load_configs(config_sources)

    print(f"[*] Loaded {len(configs)} config(s)")
    for config in configs:
        print(f"  - {config.label}: {config.url} (interval: {config.interval}s)")

    # Verify session exists in headless mode
    session_path = Path("sessions/session.json")
    if headless and not session_path.exists():
        print("Error: Session expired. Re-run without --headless to log in again.")
        sys.exit(1)

    print()

    # Run
    refresher = PageRefresher(configs, headless=headless)
    try:
        asyncio.run(refresher.run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
