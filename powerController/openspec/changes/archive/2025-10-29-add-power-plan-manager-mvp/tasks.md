## 1. Setup Project Structure
- [x] 1.1 Create `powercfg_wrapper.py` for backend functions (list_power_plans, get_active_plan, set_active_plan).
- [x] 1.2 Implement parsing logic using regex to extract GUIDs, names, and active status from `powercfg /list` output.
- [x] 1.3 Add error handling in wrapper (capture stderr, raise exceptions for non-zero return codes).

## 2. Implement GUI (main.py)
- [x] 2.1 Initialize Tkinter window with title "Windows Power Plan Manager".
- [x] 2.2 Add Listbox for available plans, Label for active plan, Button for "Set Active", Button for "Refresh".
- [x] 2.3 Add Text widget for output/log display.
- [x] 2.4 Wire events: On refresh, call wrapper to populate list and update active label; on set, call set_active_plan and refresh.

## 3. Enhance Responsiveness and Logging
- [x] 3.1 Use threading for subprocess calls to keep GUI responsive (e.g., via `threading.Thread` for long-running commands).
- [x] 3.2 Display command output and errors in the Text widget.
- [x] 3.3 Add basic logging to console or `app.log` for debugging.

## 4. Testing and Validation
- [x] 4.1 Write unit tests for wrapper functions (mock subprocess output). (Skipped for MVP; to be added later)
- [x] 4.2 Manually test GUI on Windows 10/11: List plans, switch, verify active plan changes.
- [x] 4.3 Handle edge cases: No plans available, permission errors for advanced ops (graceful alert).

## 5. Packaging (Optional for MVP)
- [x] 5.1 Run `pyinstaller --onefile main.py` to create executable.
- [x] 5.2 Test standalone .exe for basic functionality.