## Context
The power controller application is a Python-based GUI tool using tkinter for managing Windows power plans via powercfg commands. Currently, it lists plans, shows active one, and allows switching. This change adds a detail modal for selected plans, requiring UI extension and backend queries for subgroup settings. Stakeholders: end-users needing detailed inspection without external tools. Constraints: Windows-focused, tkinter limitations for advanced UI (no native tabs, need custom implementation).

## Goals / Non-Goals
- Goals: Provide organized, accessible view of plan details; integrate seamlessly with existing list; fetch real-time data via powercfg /query.
- Non-Goals: Full editing of settings (view-only); cross-platform support beyond Windows; advanced animations or themes.

## Decisions
- Decision: Use tkinter Toplevel for modal overlay, positioned centered and semi-transparent background via canvas or frame. Why: Native, no external deps; simple for non-fullscreen.
- Alternatives considered: Custom embedded frame in main window (rejected: disrupts list focus); third-party like customtkinter (rejected: adds dep, overkill for modal).
- Decision: Implement tabs with ttk.Notebook for sections (Display, Monitor, etc.). Why: Built-in, accessible.
- Decision: Extend powercfg_wrapper.py with query functions for subgroups (e.g., /query SCHEME_GUID 7516b95f-f776-4464-8c53-06167... for display). Parse output to key-value for UI population. Why: Matches existing wrapper pattern; handles raw output.
- Alternatives: Direct subprocess in main.py (rejected: violates separation); WMI/COM APIs (rejected: complex, powercfg sufficient).

## Risks / Trade-offs
- Risk: powercfg /query output parsing inconsistencies across Windows versions → Mitigation: Use regex for key-value extraction, fallback to raw display with warnings.
- Risk: Modal blocking main thread → Mitigation: Non-modal Toplevel, but use after() for updates.
- Trade-off: tkinter accessibility limited (no native ARIA) → Use descriptive labels, focus order; note for future web/GTK migration.

## Migration Plan
- No migration needed: Additive feature, no breaking changes to existing specs/code.
- Rollback: Remove modal event bindings and Toplevel code if issues.

## Open Questions
- Confirm single-click vs double-click trigger preference.
- Exact powercfg GUIDs for all subgroups (e.g., battery, USB); may need research via powercfg /q.
- Localization: Hardcode English labels or add i18n?