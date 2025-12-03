## Why
The current power plan management interface lists available plans but lacks a detailed view for users to inspect comprehensive settings of a selected plan. This modal pane will enhance usability by providing an in-depth, organized display of power configuration details without leaving the main interface, improving workflow and user understanding of power settings.

## What Changes
- Add a non-fullscreen modal pane that opens on single-click (or double-click if specified) of a power configuration entry in the main list.
- Implement sections for Display Settings, Monitor Settings, Power Management Details, and Additional Settings, pulling data from system APIs.
- Include header with name, description, icon; support closing via ESC, button, or outside click.
- Ensure responsive design with tabs/accordions, accessibility (ARIA, high-contrast, keyboard nav), and validation against hardware.
- **No breaking changes** to existing list, get active, or set active functionalities.

## Impact
- Affected specs: power-plan-management (adding new requirements for detail view)
- Affected code: main.py (GUI updates for modal trigger and display), powercfg_wrapper.py (extend to fetch detailed settings via additional powercfg queries or APIs)