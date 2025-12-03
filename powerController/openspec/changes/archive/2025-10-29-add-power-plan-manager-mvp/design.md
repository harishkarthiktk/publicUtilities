## Context
This MVP builds a modular Python app for Windows power plan management. Constraints: Use only standard libraries; ensure non-admin usability; keep GUI simple and responsive. Stakeholders: End-users seeking a better `powercfg.cpl` alternative.

## Goals / Non-Goals
- Goals: Functional MVP for listing/switching plans; modular backend for future extensions (e.g., Phase 2 settings).
- Non-Goals: Advanced settings (Phase 2); cross-platform support; heavy UI theming.

## Decisions
- Decision: Backend wrapper (`powercfg_wrapper.py`) abstracts `subprocess.run` calls and regex parsing (e.g., `re.findall(r"Power Scheme GUID:\s*([\w-]+)\s+\(([^)]+)\)(\s*\*)?", output)`). Why: Encapsulates OS-specific logic; easy to test/mock.
- Alternatives: Direct `powercfg` in GUI (rejected: violates separation of concerns); WMI/COM APIs (rejected: more complex, requires pywin32 dependency).
- Decision: Threading for subprocess (e.g., `queue.Queue` to pass results to GUI). Why: Prevents UI freezing on command execution.
- Alternatives: Asyncio (rejected: overkill for simple app; Tkinter threading is sufficient).
- Decision: Error handling via try/except on subprocess, displaying user-friendly messages in GUI. Why: Graceful degradation (e.g., "Run as admin for advanced features").
- Decision: No external deps; Tkinter for native Windows look.

## Risks / Trade-offs
- Risk: `powercfg` output format changes in future Windows versions → Mitigation: Version-check in wrapper; log raw output.
- Risk: Subprocess security (command injection) → Mitigation: Hardcode args, no user input in commands.
- Trade-off: Threading adds complexity → Benefit: Responsive GUI outweighs for MVP.

## Migration Plan
- N/A (new app); future phases append to wrapper (e.g., add `change_setting` function).

## Open Questions
- Confirm Python version (3.10+ per plan.md)?
- Any specific error messages or icons for GUI alerts?

### Backend Flow Diagram
```mermaid
sequenceDiagram
    participant U as User/GUI
    participant W as powercfg_wrapper.py
    participant P as powercfg.exe
    U->>W: list_power_plans()
    W->>P: subprocess.run(["powercfg", "/list"])
    P-->>W: Output (GUIDs, names)
    W->>W: Parse with regex
    W-->>U: List of (GUID, name, active)
    Note over U,W: Threading for async