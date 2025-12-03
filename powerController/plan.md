# Windows Power Plan Manager (Python GUI)

## 1. Overview

A desktop application written in **Python**, with a **Tkinter GUI**, that allows users to:
- View and select Windows Power Plans.
- Change the active power plan.
- (Later phases) Modify detailed power settings (sleep timers, display timeouts, etc.).
- Provide a clean, fast alternative to `powercfg.cpl`.

The application uses the **built-in `powercfg.exe` command-line utility** as its backend, executing commands and parsing their output.

---

## 2. Technical Stack

| Component | Technology | Purpose |
|------------|-------------|----------|
| Programming Language | Python 3.10+ | Core logic and scripting |
| GUI Framework | Tkinter (standard library) | Simple, native GUI |
| Subprocess Handling | `subprocess` module | Execute and capture output from `powercfg` |
| OS Compatibility | Windows 10 / 11 | Tested environment |
| Privilege Level | Standard user | Admin only required for specific advanced changes |
| Packaging | `pyinstaller` (optional) | Bundle app into standalone `.exe` |

---

## 3. Functional Specifications

### 3.1 Core Features (Phase 1: MVP)

| Feature | Description | Command / Implementation |
|----------|--------------|--------------------------|
| **List available power plans** | Retrieve all installed power plans and mark the active one. | `powercfg /list` |
| **Set active power plan** | Switch to a selected power plan via GUI. | `powercfg /setactive <GUID>` |
| **Get current active plan** | Identify which plan is currently active. | `powercfg /getactivescheme` |
| **Display command output** | Show command results or logs inside the GUI. | Use `Text` widget or `Label` |

---

### 3.2 Extended Features (Phase 2)

| Feature | Description | Command / Implementation |
|----------|--------------|--------------------------|
| **Modify power settings** | Change parameters like display/sleep timeout, lid close action, etc. | `powercfg /change <setting> <value>` or `/setacvalueindex` |
| **Query detailed settings** | Retrieve subsettings for a plan. | `powercfg /query <GUID>` |
| **Export / Import power plans** | Backup or restore plans. | `powercfg /export` / `powercfg /import` |
| **Rename / Delete plans** | Manage custom plans. | `powercfg /changename` / `/delete` |
| **Reset to defaults** | Restore all settings to default. | `powercfg /restoredefaultschemes` |

---

### 3.3 Future Features (Phase 3)

| Feature | Description |
|----------|-------------|
| Profile presets (Balanced, Gaming, Work, Battery Saver) |
| Scheduled power plan switching (based on time or battery level) |
| Integration with Windows Notifications for plan changes |
| Logging and analytics (time spent on each plan) |
| Cross-version support (Windows Server editions) |

---

## 4. GUI Design Specification

### 4.1 Layout (Phase 1)
**Main Window**
- **Title:** “Windows Power Plan Manager”
- **Components:**
  - Dropdown or Listbox: Display all available plans.
  - Label: Show currently active plan.
  - Button: “Set as Active Plan”.
  - Button: “Refresh List”.
  - Text Area: Output / Log display.

**Example Layout (Tkinter):**
```

+---------------------------------------------------------+
|  [Active Plan: Balanced]                                |
|                                                         |
|  Available Power Plans:                                 |
|  [ Balanced (*) ]                                       |
|  [ High performance ]                                   |
|  [ Power saver ]                                        |
|                                                         |

| [Set Active]  [Refresh List]                                 |
| ------------------------------------------------------------ |
| Output / Log:                                                |
| > Power Scheme GUID: ...                                     |
| > Active Scheme: Balanced                                    |
| +----------------------------------------------------------+ |

````

### 4.2 Layout (Future)
- Add tabbed interface (`ttk.Notebook`) for:
  - “Plans”
  - “Settings”
  - “Profiles”
  - “Logs”

---

## 5. Backend Design

### 5.1 Command Execution Layer
**Module:** `powercfg_wrapper.py`

**Functions:**
```python
def list_power_plans() -> str
def get_active_plan() -> str
def set_active_plan(guid: str) -> None
def change_setting(setting: str, value: str) -> None
def query_settings(guid: str) -> str
````

**Implementation Notes:**

* Use `subprocess.run(["powercfg", "/list"], capture_output=True, text=True)`
* Handle errors with `try/except` and display them in the GUI log.

### 5.2 Parsing Layer

* Parse GUIDs and plan names from plain text using regex:

  ```python
  import re
  plans = re.findall(r"Power Scheme GUID:\s*([\w-]+)\s+\(([^)]+)\)(\s*\*)?", output)
  ```
* Return list of tuples: `(guid, name, is_active)`

---

## 6. GUI Logic Layer

**Main Module:** `main.py`

**Responsibilities:**

* Initialize Tkinter window.
* Load and refresh power plans.
* Handle user input (select plan, click buttons).
* Call backend wrapper functions.
* Update UI state dynamically (active plan indicator).

---

## 7. Error Handling & Logging

* Capture stderr from subprocess and display friendly messages.
* Example:

  ```python
  result = subprocess.run(..., capture_output=True, text=True)
  if result.returncode != 0:
      raise Exception(result.stderr)
  ```
* Optional: write command history to a local `app.log`.

---

## 8. Security & Permissions

* Most `powercfg` commands run under user context.
* Advanced settings (e.g. `/setacvalueindex`) might require admin privileges.
* Detect insufficient permissions and alert the user gracefully.

---

## 9. Packaging & Deployment

| Step             | Tool                                  | Output                         |
| ---------------- | ------------------------------------- | ------------------------------ |
| Freeze app       | `pyinstaller --onefile main.py`       | `PowerPlanManager.exe`         |
| Include manifest | Request execution level: `asInvoker`  | Avoid UAC prompt unless needed |
| Distribution     | Zip or installer (.msi or Inno Setup) | Simple deployment              |

---

## 10. Roadmap Summary

| Phase       | Description                | Deliverable             |
| ----------- | -------------------------- | ----------------------- |
| **Phase 1** | List & switch power plans  | Functional GUI (MVP)    |
| **Phase 2** | Manage individual settings | Extended settings panel |
| **Phase 3** | Presets, scheduling, logs  | Full-featured GUI tool  |

---

## 11. References

* Microsoft Docs: [`powercfg` command-line options](https://learn.microsoft.com/en-us/windows-hardware/design/device-experiences/powercfg-command-line-options)
* Tkinter official reference: [https://docs.python.org/3/library/tkinter.html](https://docs.python.org/3/library/tkinter.html)
* Python `subprocess` documentation: [https://docs.python.org/3/library/subprocess.html](https://docs.python.org/3/library/subprocess.html)

---

## 12. Notes

* Use **Tkinter** for simplicity and native feel.
* Keep the backend modular — easily replaceable with a Rust or C++ backend later.
* Avoid direct registry edits; always use `powercfg` interface for stability.
* Ensure the GUI is responsive — use threading for long-running commands.

