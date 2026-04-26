#!/usr/bin/env python3
"""
Page Refresher - Monitor web pages and detect changes
Reads YAML configs, opens tabs in a shared Chromium context, monitors for selector changes
"""

import asyncio
import sys
import os
import random
import argparse
from pathlib import Path
from datetime import datetime
import logging
import signal
import json
import tempfile
from typing import Optional, Dict, List, Any
from urllib.parse import urlparse

import yaml
from playwright.async_api import async_playwright, Page, BrowserContext, Browser, TimeoutError as PlaywrightTimeoutError


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
        self.shutdown_event = asyncio.Event()
        self.restart_event = asyncio.Event()

    def _is_valid_session_file(self, path: str) -> bool:
        """Validate a Playwright session file at the given path"""
        try:
            with open(path, "r") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return False
            has_cookies = "cookies" in data and isinstance(data["cookies"], list)
            has_origins = "origins" in data and isinstance(data["origins"], list)
            return has_cookies or has_origins
        except Exception:
            return False

    def is_session_valid(self) -> bool:
        """Validate the current session file"""
        if not self.session_path.exists():
            return False
        return self._is_valid_session_file(str(self.session_path))

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
        """Save session atomically; only replace existing file if new data validates."""
        if not self.context:
            return
        tmp_path = None
        try:
            self.session_path.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp_path = tempfile.mkstemp(
                dir=str(self.session_path.parent), suffix=".tmp"
            )
            os.close(fd)
            await self.context.storage_state(path=tmp_path)
            if self._is_valid_session_file(tmp_path):
                os.replace(tmp_path, str(self.session_path))
            else:
                os.unlink(tmp_path)
                print("[!] Session data failed validation - keeping last good session")
        except Exception as e:
            try:
                if tmp_path:
                    os.unlink(tmp_path)
            except OSError:
                pass
            if "closed" not in str(e).lower():
                print(f"Warning: Failed to save session: {e}")

    async def _periodic_save_loop(self):
        """Save session every 5 seconds until shutdown"""
        while not self.shutdown_event.is_set():
            try:
                await asyncio.wait_for(self.shutdown_event.wait(), timeout=5.0)
                break  # shutdown triggered within the 5s window
            except asyncio.TimeoutError:
                await self.save_session()

    async def _cleanup_browser(self):
        """Clean up browser and context resources"""
        if self.context:
            try:
                await self.context.close()
            except Exception:
                pass
            self.context = None
        if self.browser:
            try:
                await self.browser.close()
            except Exception:
                pass
            self.browser = None
        self.pages.clear()

    async def init_browser(self):
        """Initialize Playwright browser and context"""
        try:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=self.headless)
        except Exception as e:
            print(f"Fatal: Failed to launch browser: {e}")
            print("Ensure Playwright browsers are installed: playwright install chromium")
            sys.exit(1)

        # Load session if available
        session = await self.load_session()

        # Create context with optional session
        context_kwargs = {
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        }
        if session:
            context_kwargs["storage_state"] = session

        try:
            self.context = await self.browser.new_context(**context_kwargs)
        except Exception as e:
            print(f"Fatal: Failed to create browser context: {e}")
            await self.browser.close()
            sys.exit(1)

    async def _bind_save_hotkey(self, page: Page, label: str):
        """Bind Ctrl+S on a page to force-save the session"""
        async def handle_save():
            print(f"[*] Save hotkey triggered from [{label}] - saving session...")
            await self.save_session()
            print(f"[*] Session saved.")

        await page.expose_function("__forceSaveSession", lambda: asyncio.ensure_future(handle_save()))
        await page.evaluate("""
            document.addEventListener('keydown', (e) => {
                if (e.ctrlKey && e.key === 's') {
                    e.preventDefault();
                    window.__forceSaveSession();
                }
            });
        """)

    def _is_auth_redirect(self, target_url: str, current_url: str) -> bool:
        """Return True only if current_url looks like an auth/login page, not a legit app redirect."""
        if current_url == target_url:
            return False
        target_host = urlparse(target_url).hostname or ""
        current_host = urlparse(current_url).hostname or ""
        # Same host = legit app redirect (e.g. /company/xxx/index.do)
        return current_host != target_host

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
            try:
                await page.goto(config.url, wait_until="networkidle", timeout=60000)
            except PlaywrightTimeoutError:
                logger.log(f"Timeout navigating to {config.url} - page may still be usable")
            except Exception as e:
                logger.log(f"Error navigating to {config.url}: {e}")
                continue

            await self._bind_save_hotkey(page, config.label)

            # Check if redirected to an auth/login page (not a legit same-host app redirect)
            if self._is_auth_redirect(config.url, page.url):
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
            try:
                await page.goto(config.url, wait_until="networkidle", timeout=60000)
            except PlaywrightTimeoutError:
                logger.log(f"Timeout re-navigating to {config.url} - continuing anyway")
            except Exception as e:
                logger.log(f"Error re-navigating to {config.url}: {e}")

    async def monitor_tab(self, config: PageRefresherConfig):
        """Monitor a single tab: reload on interval, check selectors for changes"""
        page = self.pages[config.label]
        logger = self.loggers[config.label]
        previous = {}
        first_run = True

        while not self.shutdown_event.is_set():
            try:
                if first_run:
                    first_run = False
                else:
                    await page.reload(wait_until="networkidle", timeout=60000)
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
                    except PlaywrightTimeoutError:
                        logger.log(f"Timeout checking selector {selector}")
                    except Exception as e:
                        logger.log(f"Error checking selector {selector}: {e}")

                # Save session after each reload
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
            except PlaywrightTimeoutError:
                logger.log(f"Timeout reloading page - retrying in 30s")
                await asyncio.sleep(30)
            except Exception as e:
                crash_keywords = ("closed", "disconnected", "destroyed", "crashed")
                if any(kw in str(e).lower() for kw in crash_keywords):
                    logger.log(f"Browser crash detected: {e}")
                    self.restart_event.set()
                    return
                logger.log(f"Error during monitoring: {e}")
                await asyncio.sleep(5)

    async def shutdown(self):
        """Graceful shutdown"""
        print("\n[*] Shutting down...")
        self.shutdown_event.set()

    async def run(self):
        """Main run loop with restart support"""
        loop = asyncio.get_running_loop()

        def handle_signal():
            asyncio.create_task(self.shutdown())

        def handle_save():
            print("[*] SIGUSR1 received - force saving session...")
            asyncio.create_task(self.save_session())

        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, handle_signal)
        loop.add_signal_handler(signal.SIGUSR1, handle_save)

        restart_count = 0

        while True:
            self.restart_event.clear()

            await self.init_browser()
            auth_required = await self.navigate_all()

            if auth_required:
                if self.headless:
                    for label in auth_required:
                        self.loggers[label].log("Auth required in headless mode - retrying in 60s")
                    await self._cleanup_browser()
                    await asyncio.sleep(60)
                    continue
                else:
                    await self.wait_for_auth(auth_required)

            monitor_tasks = [
                asyncio.create_task(self.monitor_tab(config), name=f"monitor_{config.label}")
                for config in self.configs
            ]
            monitor_tasks.append(
                asyncio.create_task(self._periodic_save_loop(), name="periodic_save")
            )

            if restart_count == 0:
                print("[*] Monitoring started. Press Ctrl+C to stop.\n")
            else:
                print(f"[*] Monitoring resumed (restart #{restart_count}).\n")

            shutdown_waiter = asyncio.create_task(self.shutdown_event.wait())
            restart_waiter  = asyncio.create_task(self.restart_event.wait())
            all_tasks = set(monitor_tasks) | {shutdown_waiter, restart_waiter}

            done, pending = await asyncio.wait(all_tasks, return_when=asyncio.FIRST_COMPLETED)

            if shutdown_waiter in done or self.shutdown_event.is_set():
                # Save session before canceling tasks and closing browser
                await self.save_session()
                # Now cancel pending monitor tasks
                for t in pending:
                    t.cancel()
                await asyncio.gather(*pending, return_exceptions=True)
                # Clean up browser
                await self._cleanup_browser()
                print("[*] Done")
                sys.exit(0)

            for t in pending:
                t.cancel()
            await asyncio.gather(*pending, return_exceptions=True)

            restart_count += 1
            print(f"[*] Browser crash detected - restarting (attempt {restart_count})...")
            await self._cleanup_browser()
            await asyncio.sleep(5)


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
    parser = argparse.ArgumentParser(
        description="Monitor web pages and detect changes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                      # Load all configs from ./configs directory
  %(prog)s config.yaml          # Load single config file
  %(prog)s configs/ more_configs/  # Load from multiple directories
  %(prog)s --headless config.yaml  # Run in headless mode (requires saved session)
  %(prog)s --refresh            # Clear saved session and exit
        """.strip()
    )

    parser.add_argument(
        "config_sources",
        nargs="*",
        default=["configs"],
        help="Config file(s) or directory(ies) to load (default: configs)"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless mode (requires valid saved session)"
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Clear saved session and exit"
    )

    args = parser.parse_args()

    # Handle --refresh flag
    if args.refresh:
        session_path = Path("sessions/session.json")
        if session_path.exists():
            session_path.unlink()
            print("[*] Session cleared")
        sys.exit(0)

    # Verify config sources exist
    for source in args.config_sources:
        if not Path(source).exists():
            print(f"Error: {source} not found")
            sys.exit(1)

    # Load configs
    configs = load_configs(args.config_sources)

    print(f"[*] Loaded {len(configs)} config(s)")
    for config in configs:
        print(f"  - {config.label}: {config.url} (interval: {config.interval}s)")

    # Verify session exists in headless mode
    session_path = Path("sessions/session.json")
    if args.headless and not session_path.exists():
        print("Error: Session expired. Re-run without --headless to log in again.")
        sys.exit(1)

    print()

    # Run
    refresher = PageRefresher(configs, headless=args.headless)
    try:
        asyncio.run(refresher.run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
