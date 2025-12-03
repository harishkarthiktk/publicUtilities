## Why
Windows users lack a simple, graphical alternative to the clunky `powercfg.cpl` control panel for managing power plans. This MVP provides a lightweight Tkinter-based GUI to list available power plans, identify the active one, and switch plans using the built-in `powercfg.exe` utility, improving usability without requiring admin privileges for basic operations.

## What Changes
- Introduce a new desktop application: `main.py` (GUI entrypoint) and `powercfg_wrapper.py` (backend for command execution and parsing).
- Add core MVP features: List power plans (`powercfg /list`), get active plan (`powercfg /getactivescheme`), set active plan (`powercfg /setactive <GUID>`), and display output in GUI.
- Use standard Python libraries (Tkinter, subprocess, re) for no external dependencies.
- No breaking changes, as this is a new standalone tool.

**No BREAKING changes.**

## Impact
- Affected specs: New capability `power-plan-management` (no existing specs affected).
- Affected code: New files in root (e.g., `main.py`, `powercfg_wrapper.py`); no changes to existing codebase.
- Users: Windows 10/11 standard users; future phases can extend to advanced settings requiring admin.
- Testing: Unit tests for wrapper functions; manual GUI verification.
- Deployment: Optional PyInstaller for .exe bundling.

### GUI Layout Diagram
```mermaid
graph TD
    A[Main Window: Windows Power Plan Manager] --> B[Label: Active Plan]
    A --> C[Listbox: Available Plans<br/>e.g., Balanced (*)<br/>High Performance]
    A --> D[Buttons: Set Active | Refresh List]
    A --> E[Text Area: Output / Log<br/>e.g., > Power Scheme GUID: ...]
    C --> D
    D --> E
    style A fill:#f9f,stroke:#333