# Page Refresher

Monitor web pages for changes and track selector values over time. Opens multiple tabs in a single browser window, handles authentication, and logs all activity.

## Features

- **Multi-tab monitoring** - Open multiple pages in one browser session
- **Session persistence** - Auto-save browser state (cookies, localStorage) for seamless re-runs
- **Auth handling** - Pause for manual login with automatic session recovery
- **Change detection** - Monitor CSS selectors for text value changes
- **Async monitoring** - Concurrent page refreshes at different intervals
- **Jitter support** - Optional per-tab refresh interval randomization (±N%) to avoid bot detection
- **Detailed logging** - Per-tab log files + console output with timestamps
- **Headless mode** - Run in background with `nohup` for scheduled monitoring
- **YAML configs** - Simple config files for each monitored page

## Installation

Requires Python 3.7+ and dependencies from `~/.venv_gen`:

```bash
# Activate the shared virtual environment
source ~/.venv_gen/bin/activate

# Verify dependencies are installed
python -c "import yaml; import playwright; print('OK')"
```

Dependencies (already in `~/.venv_gen`):
- `playwright` - Browser automation
- `pyyaml` - YAML config parsing

## Quick Start

### 1. Create a Config

Create a YAML file in `configs/` for each page you want to monitor:

```bash
mkdir -p configs
cat > configs/mypage.yaml << 'EOF'
url: https://example.com/page
interval: 180
selectors:
  - ".price"
  - ".status"
label: "My Page"
EOF
```

### 2. First Run (Headed Mode - with Browser UI)

```bash
source ~/.venv_gen/bin/activate
python page_refresher.py configs/mypage.yaml
```

- Browser opens automatically
- Log in if prompted (page will pause)
- Session saved to `sessions/session.json` on exit
- Monitoring logs go to `logs/mypage.txt`

Press **Ctrl+C** to stop and save session.

### 3. Background Run (Headless Mode)

After initial login, run in the background:

```bash
nohup python page_refresher.py --headless > nohup.out 2>&1 &
```

- Uses saved session (no browser UI)
- Exits if session expired or invalid
- Logs to files, output to `nohup.out`
- Rerun in headed mode to log in again

## Configuration

Each YAML config defines one monitored tab:

```yaml
# Required
url: https://example.com/product/123

# Optional
interval: 180              # seconds between refreshes (default: 180)
jitter: 20                 # ±percent randomization of interval to avoid bot detection (default: 0, no jitter)
selectors:                 # CSS selectors to monitor for text changes
  - ".price"
  - ".in-stock"
log: logs/product.txt      # log file path (default: logs/<config-name>.txt)
label: "Product 123"       # display label (default: filename)
```

### Configuration Details

- **url**: Target page URL (required). Must be navigable and return HTTP 200.
- **interval**: Seconds between page reloads. Default 180 (3 minutes). Min 1 second.
- **jitter**: Optional percentage randomization of interval to prevent bot detection. Default 0 (no jitter). Example: `jitter: 20` means actual sleep time varies by ±20% each cycle (144-216s for 180s interval). Minimum sleep time never goes below 1 second.
- **selectors**: List of CSS selectors to monitor. Logs text content changes. Optional.
- **log**: Output log file path. Created automatically. Default: `logs/<config-stem>.txt`
- **label**: Human-readable name for console output. Default: config filename without `.yaml`

## CLI Usage

### Load all configs from `configs/` directory

```bash
python page_refresher.py
```

### Load specific config files

```bash
python page_refresher.py configs/a.yaml configs/b.yaml
```

### Load all from custom directory

```bash
python page_refresher.py custom_configs/
```

### Headless mode (requires valid session)

```bash
python page_refresher.py --headless
# or with explicit configs:
python page_refresher.py configs/a.yaml --headless
```

Exits with error if `sessions/session.json` is missing or expired:
```
Error: Session expired. Re-run without --headless to log in again.
```

## How It Works

### Startup

1. Parse YAML configs from specified sources
2. Launch Chromium browser (headed or headless)
3. Load saved session if available (`sessions/session.json`)
4. Navigate all tabs, wait for network idle
5. Detect auth redirects (current URL != target URL)

### Auth Flow

If any tab is redirected to auth:

```
[!] Auth required for: Config1, Config2
[!] Log in in the browser, then press Enter to continue monitoring.
```

- User logs in manually in the browser
- Press Enter when done
- Script re-navigates tabs to target URLs

### Monitoring Loop

For each tab, concurrently:

1. Reload page (wait for network idle)
2. Log reload timestamp
3. Check each selector:
   - Extract text content
   - Compare to previous values
   - Log changes if different
4. Sleep until next interval
5. Save session every 5 reloads (safety net)

### Shutdown

On **Ctrl+C** or **SIGTERM**:

1. Stop all monitoring tasks
2. Save session to `sessions/session.json`
3. Close browser cleanly
4. Exit gracefully

## Logging

### Log Format

```
[2025-03-27 14:30:45] [Label] Reloaded
[2025-03-27 14:30:50] [Label] CHANGE .price: ['$10.00'] -> ['$9.99']
[2025-03-27 14:30:51] [Label] Error checking selector .missing: No elements found
```

### Log Files

- **Per-tab logs** - Appended to `logs/<config-name>.txt` (or custom path)
- **Console output** - All events printed to stdout with timestamps
- **Session file** - `sessions/session.json` (Playwright storage state format)

### Example Log Output

```
$ cat logs/mypage.txt
[2025-03-27 14:30:20] [My Page] Navigating to https://example.com/page
[2025-03-27 14:30:25] [My Page] Reloaded
[2025-03-27 14:31:25] [My Page] Reloaded
[2025-03-27 14:31:30] [My Page] CHANGE .price: ['$10.00'] -> ['$9.99']
```

## Session Management

### Session File

- **Location**: `sessions/session.json`
- **Format**: Playwright `storage_state` (cookies + localStorage)
- **Shared**: Single session file for all tabs (shared BrowserContext)
- **Created**: On first run with Ctrl+C or graceful shutdown
- **Loaded**: Automatically on startup if exists

### Session Persistence

- Saves periodically during monitoring (every 5 reloads per tab)
- Saves on exit (Ctrl+C) or shutdown signal (SIGTERM)
- Required for `--headless` mode
- Survives browser crashes (periodic saves act as safety net)
- Format: Playwright `storage_state` (includes cookies, localStorage, sessionStorage)

### Refreshing Session

To log in again or force session refresh:

```bash
# Method 1: Delete and re-run
rm sessions/session.json
python page_refresher.py configs/mypage.yaml

# Method 2: Use --refresh flag (clears session, exits immediately)
python page_refresher.py --refresh
python page_refresher.py configs/mypage.yaml
```

When session is invalid or expired, you'll be prompted:
```
[!] Session file appears to be corrupted or invalid
[?] Refresh session? (y/n):
```

Choose `y` to clear the session and log in fresh, or `n` to attempt using the possibly-invalid session.

## Examples

### Monitor Product Price

```yaml
# configs/product.yaml
url: https://store.example.com/item/12345
interval: 300
jitter: 15                 # ±15% randomization (255-345s actual interval)
selectors:
  - ".product-price"
  - ".stock-status"
label: "Widget Price"
```

Run:
```bash
python page_refresher.py configs/product.yaml
```

Watch for price changes in `logs/product.txt`. Each refresh will have a randomized delay within ±15% to avoid detection as a bot.

Example log output with jitter:
```
[2025-03-27 14:30:20] [Widget Price] Navigating to https://store.example.com/item/12345
[2025-03-27 14:30:25] [Widget Price] Reloaded
[2025-03-27 14:30:25] [Widget Price] Next refresh in 287.3s
[2025-03-27 14:34:52] [Widget Price] Reloaded
[2025-03-27 14:34:53] [Widget Price] Next refresh in 318.7s
```

### Monitor Multiple Pages

```bash
# Create configs
cat > configs/price.yaml << 'EOF'
url: https://store.example.com/item
interval: 600
selectors: [".price"]
EOF

cat > configs/status.yaml << 'EOF'
url: https://api-status.example.com
interval: 300
selectors: [".status-indicator"]
EOF

# Run both
python page_refresher.py
```

Logs:
- `logs/price.txt` - updates every 10 minutes
- `logs/status.txt` - updates every 5 minutes

### Background Monitoring

```bash
# First run - log in
python page_refresher.py configs/important.yaml

# Background run - uses saved session
nohup python page_refresher.py --headless > nohup.out 2>&1 &

# Check progress
tail -f nohup.out
tail -f logs/important.txt
```

## Troubleshooting

### "No .yaml files found in configs"

Create at least one config:

```bash
mkdir -p configs
echo "url: https://example.com" > configs/test.yaml
```

### Auth Loop - Can't Log In

- Ensure browser window is visible (headed mode)
- Try logging in manually, then press Enter
- Check for 2FA or additional steps required
- Session may be cached; delete and retry:
  ```bash
  rm sessions/session.json
  python page_refresher.py configs/mypage.yaml
  ```

### "Session expired. Re-run without --headless"

Headless mode requires a valid session:

```bash
# First: log in with browser
python page_refresher.py configs/mypage.yaml

# Then: run headless
python page_refresher.py --headless
```

### Selectors Not Matching

- Verify selector with browser DevTools
- Test selector in browser console: `document.querySelectorAll(".price")`
- CSS syntax must be valid (`.class`, `#id`, `[attr]`, etc.)
- Logs show "Error checking selector" if element not found

### Browser Crashes / Unexpected Exit

- Periodic saves recover most state (every 5 reloads)
- Check `nohup.out` or console for error messages
- Verify `sessions/session.json` exists and is valid JSON:
  ```bash
  python -m json.tool sessions/session.json > /dev/null && echo "OK"
  ```

## Performance Notes

- Each page reload waits for network idle (can be 5-30s depending on page)
- Multiple tabs run concurrently - total time ≈ slowest single tab
- Selector checking is fast (< 100ms per tab)
- Memory usage: ~100-200MB per tab (Chromium overhead)
- Session file: 5-50KB typically

## Requirements

- Python 3.7+
- Chromium (installed by Playwright)
- `playwright` package (async browser automation)
- `pyyaml` package (YAML config parsing)
- ~500MB disk for browser + logs

## Files and Directories

```
webBrowser/
  page_refresher.py           # Main script
  README.md                   # This file
  configs/                    # Config directory (create)
    example.yaml              # Example config (reference only)
    *.yaml                    # Your configs
  logs/                       # Log output (auto-created)
    <config-name>.txt
  sessions/                   # Session storage (auto-created)
    session.json
```

## License

MIT. Use freely for personal or commercial projects.
