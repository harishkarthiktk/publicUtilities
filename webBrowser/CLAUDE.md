# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start

**Activation:** Use the shared venv from global user config:
```bash
source ~/.venv_gen/bin/activate
```

**Run the main script:**
```bash
python page_refresher.py                    # Load all configs from ./configs
python page_refresher.py configs/mypage.yaml  # Load specific config
python page_refresher.py --headless         # Run headless (requires saved session)
python page_refresher.py --refresh          # Clear session and exit
```

## Project Overview

**Purpose:** Monitor web pages for content changes across multiple tabs. Opens pages in a shared Chromium browser context, periodically reloads them, and tracks CSS selector values over time.

**Key Files:**
- `page_refresher.py` - Main entry point and application logic (~535 lines)
- `configs/` - YAML configuration files (one per monitored page)
- `sessions/session.json` - Persistent browser state (cookies, localStorage)
- `logs/` - Per-tab monitoring output

## Architecture & Code Structure

The codebase uses an async/await pattern with four main components:

### 1. **PageRefresherConfig** (lines 25-40)
Parses and validates YAML config files. Each config must have:
- `url` (required): Target page URL
- `interval` (default 180s): Seconds between page reloads
- `jitter` (default 0): ±percent randomization of interval to avoid bot detection
- `selectors` (default []): CSS selectors to monitor for text changes
- `label` (default: config filename): Display name for logging
- `log` (default: `logs/<config-name>.txt`): Log file path

### 2. **TabLogger** (lines 42-60)
Simple logging utility that writes to file and stdout with timestamps. Called once per tab during initialization.

### 3. **PageRefresher** (lines 63-416)
Core application class managing browser lifecycle, multi-tab context, monitoring loops, and graceful shutdown. Key methods:

- `init_browser()` - Launch Chromium and create BrowserContext with session (if available)
- `navigate_all()` - Open all tabs and detect auth redirects (URL mismatch = auth required)
- `wait_for_auth()` - Pause for manual login, then re-navigate tabs
- `monitor_tab()` - Async loop: reload page, check selectors, sleep until next interval
- `save_session()` - Atomically save Playwright storage_state (cookies + localStorage)
- `_periodic_save_loop()` - Runs in background, saves session every 5 seconds
- `_cleanup_browser()` - Clean up browser and context resources
- `run()` - Main event loop with signal handling (SIGINT, SIGTERM, SIGUSR1) and auto-restart on browser crashes

### 4. **Config Loading & CLI** (lines 419-536)
- `load_configs()` - Loads YAML files from directories or individual files
- `load_yaml_file()` - Parses YAML and handles errors
- `main()` - argparse entry point with three flags: `config_sources`, `--headless`, `--refresh`

## Key Design Patterns

**Async Concurrency:**
- All tabs are monitored concurrently using `asyncio.create_task()` and `asyncio.wait()`
- Each tab's `monitor_tab()` runs independently; total time ≈ slowest single tab

**Session Persistence:**
- Uses Playwright's `storage_state` format (JSON with cookies + origins)
- Atomic save: write to temp file, validate, then replace existing file
- Periodic saves every 5 seconds act as a safety net for crashes
- Session validated on load; user prompted to clear if corrupted

**Auth Detection:**
- Compares target URL hostname with current page hostname
- Same-host redirects are legit app navigation; cross-host = auth required
- On auth redirect, script pauses for manual login, then re-navigates tabs

**Graceful Shutdown & Restart:**
- Catches SIGINT (Ctrl+C) and SIGTERM, triggers `shutdown_event`
- Saves session before closing browser
- Browser crashes trigger `restart_event`; app auto-restarts (with backoff)
- SIGUSR1 forces a session save without shutdown

**Error Handling:**
- Timeouts on page.goto() and page.reload() are caught; monitoring continues
- Selector errors logged but don't break monitoring loop
- Browser crash keywords ("closed", "disconnected", "crashed") trigger restart
- YAML parse errors and missing configs exit early with error messages

## Dependencies

- `playwright` - Async browser automation
- `pyyaml` - YAML config parsing
- Standard library: `asyncio`, `argparse`, `pathlib`, `json`, `signal`, `tempfile`

## Testing / Manual Verification

Create a test config:
```bash
mkdir -p configs
cat > configs/test.yaml << 'EOF'
url: https://example.com
interval: 60
selectors:
  - "h1"
  - ".price"
label: "Test Page"
EOF
```

Run with browser UI:
```bash
python page_refresher.py configs/test.yaml
```

Verify:
- Browser opens with tab navigated to URL
- Selector values logged every 60s to `logs/test.txt`
- Session saved to `sessions/session.json` on exit (Ctrl+C)

## Common Development Tasks

**Add a new configuration option:**
1. Add field to `PageRefresherConfig.__init__()` (line 28+)
2. Document in README.md
3. Use in relevant method (e.g., `monitor_tab()` for monitoring behavior)

**Change monitoring loop behavior:**
- Modify `monitor_tab()` (lines 281-338)
- Be careful with `await asyncio.sleep()` - jitter math is at lines 317-322

**Add new CLI flags:**
- Add `parser.add_argument()` in `main()` (line 478+)
- Handle in logic before `asyncio.run()`

**Debug session issues:**
- Validate session JSON: `python -m json.tool sessions/session.json`
- Clear and force re-login: `python page_refresher.py --refresh`
- Check `_is_valid_session_file()` (lines 77-88) for validation rules

**Monitor browser crashes:**
- Restart logic at lines 408-416; change sleep(5) backoff if needed
- Check crash keywords in `monitor_tab()` line 332
