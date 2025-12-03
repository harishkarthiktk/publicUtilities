# power-plan-management Specification

## Purpose
TBD - created by archiving change add-power-plan-manager-mvp. Update Purpose after archive.
## Requirements
### Requirement: List Available Power Plans
The application SHALL retrieve and display all installed power plans, including GUIDs, names, and indicate the active one, using `powercfg /list`.

#### Scenario: Successful List Retrieval
- **WHEN** the user clicks "Refresh List"
- **THEN** the GUI Listbox populates with plans (e.g., "Balanced (*)" for active), and output Text shows raw command results.

#### Scenario: No Plans Available
- **WHEN** no power plans are installed
- **THEN** GUI shows an empty list and logs "No power plans found."

### Requirement: Get Current Active Plan
The application SHALL identify and display the currently active power plan using `powercfg /getactivescheme`.

#### Scenario: Active Plan Display
- **WHEN** the app starts or refreshes
- **THEN** the active plan Label updates (e.g., "[Active Plan: Balanced]") and matches the marked item in the list.

### Requirement: Set Active Power Plan
The application SHALL switch to a user-selected power plan using `powercfg /setactive <GUID>` and confirm the change.

#### Scenario: Successful Switch
- **WHEN** the user selects a plan and clicks "Set Active"
- **THEN** the active plan updates in the GUI, output shows success (e.g., "Power scheme updated"), and a refresh confirms the change.

#### Scenario: Switch Failure (e.g., Invalid GUID)
- **WHEN** an invalid GUID is used
- **THEN** GUI displays error in Text (e.g., from stderr) and active plan remains unchanged.

### Requirement: Display Command Output
The application SHALL show `powercfg` command results and errors in a dedicated GUI Text area for transparency and debugging.

#### Scenario: Output Logging
- **WHEN** any command runs
- **THEN** stdout/stderr appears in Text (e.g., "Power Scheme GUID: ..."), prefixed with timestamp or command name.

