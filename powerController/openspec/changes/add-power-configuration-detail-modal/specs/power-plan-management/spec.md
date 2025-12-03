## ADDED Requirements

### Requirement: Power Configuration Detail Modal
The application SHALL display a non-fullscreen modal pane overlaying the main window when a user single-clicks (or double-clicks, if configured) on a power configuration entry in the main list, providing comprehensive details without disrupting the workflow.

#### Scenario: Modal Opens on Selection
- **WHEN** the user single-clicks a power plan entry in the Listbox
- **THEN** the modal pane appears centered, semi-transparent background, with the selected plan's details loaded, and the main interface remains interactive underneath.

#### Scenario: Modal Closes Properly
- **WHEN** the user presses ESC, clicks the close button, or clicks outside the pane
- **THEN** the modal closes immediately, returning focus to the main list without state changes.

### Requirement: Modal Header Display
The modal SHALL include a header section with the power configuration name, description, and a power-related icon (e.g., battery symbol).

#### Scenario: Header Renders Correctly
- **WHEN** the modal opens for a selected plan
- **THEN** the header shows the plan name (e.g., "Balanced"), any available description, and an icon, positioned at the top with a clear title bar.

### Requirement: Organized Content Sections
The modal SHALL organize content into readable sections using tabs or accordions: Display Settings, Monitor Settings, Power Management Details, and Additional Settings, populated with relevant configuration values.

#### Scenario: Sections Display Plan Details
- **WHEN** the modal loads a plan's data
- **THEN** the Display tab shows brightness levels, timeouts, etc.; Monitor tab shows multi-monitor policies; Power Management shows CPU/GPU limits, timers; Additional shows network/audio/peripheral settings; content is scrollable if exceeding viewport.

### Requirement: Real-Time Data Fetching and Validation
The application SHALL fetch real-time power settings from system APIs (e.g., powercfg /query for Windows) for the selected plan's GUID, validate against hardware capabilities, and display warnings for incompatible or unsupported configurations.

#### Scenario: Data Loads with Validation
- **WHEN** the modal opens
- **THEN** settings are queried and displayed (e.g., "Brightness (Active): 80%"); if a setting is invalid (e.g., unsupported refresh rate), a warning label appears (e.g., "Hardware does not support 144Hz").

### Requirement: Responsive and Accessible Design
The modal SHALL be responsive, resizable, support screen readers via descriptive labels, high-contrast mode, keyboard navigation (e.g., Tab for sections, arrows for tabs), and localization for all labels and text.

#### Scenario: Accessibility Features Work
- **WHEN** the modal is navigated via keyboard or screen reader
- **THEN** all elements have focusable states, ARIA-equivalent labels (e.g., via tkinter text), and content adapts to high-contrast themes; labels support localization strings.

### Requirement: Integration with Existing Interface
The modal SHALL integrate seamlessly with the existing power plan list, updating dynamically if the active plan changes while open, and log all query outputs to the main Text area for transparency.

#### Scenario: Dynamic Updates and Logging
- **WHEN** the active plan is switched while modal is open
- **THEN** the modal refreshes to show the new plan's details if selected, and command outputs (e.g., powercfg /query results) appear in the main output Text prefixed with timestamps.