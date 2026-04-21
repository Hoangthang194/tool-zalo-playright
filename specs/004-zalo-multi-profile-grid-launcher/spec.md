# Feature Specification: Zalo Multi-Profile Grid Launcher

## Status

Implemented.

## Summary

Extend the multi-profile Zalo Chrome manager so operators can select multiple saved Chrome profiles, launch them in one action, and automatically tile the resulting Chrome windows into a fixed `4 columns x 2 rows` grid on the primary monitor. Each grid cell represents one launched profile, ordered by the profile list index.

## Problem Statement

Operators often need several Zalo accounts visible at the same time. Launching profiles one by one and arranging windows manually is slow and error-prone. They need a bulk-launch action that opens multiple saved Chrome profiles and places them into a predictable `4x2` layout automatically.

## Goals

- Allow selecting multiple saved profiles from the GUI.
- Launch multiple saved profiles in one action.
- Arrange launched Chrome windows into a `4x2` grid on the primary monitor.
- Preserve the visible profile order when assigning windows to grid cells.
- Keep launch orchestration and window-management logic outside Tkinter event handlers.

## Non-Goals

- Free-form drag-and-drop window layout editing.
- Multi-monitor placement rules.
- Arbitrary grid sizes in the first version.
- Automatic creation of Chrome profile folders on disk.
- Zalo chat automation after the browser opens.

## Primary Users

### Multi-Account Zalo Operator

Needs to monitor several Zalo sessions side by side without manually moving windows.

### Maintainer

Needs bulk launch, window discovery, and tiling logic to remain testable outside GUI code.

### Reviewer

Needs a clear contract for how selected profiles are launched, limited, ordered, and arranged.

## User Stories

1. As a Zalo operator, I want to select several saved profiles and open them together so I can start a monitoring session faster.
2. As a Zalo operator, I want the opened Chrome windows arranged into a `4x2` grid so each profile has a predictable place on screen.
3. As a Zalo operator, I want the grid order to follow the saved-profile list order so profile positions are stable.
4. As a maintainer, I want bulk launch and window tiling expressed through use cases and ports so Windows-specific APIs do not leak into Tkinter callbacks.

## Functional Requirements

### Multi-Selection

- FR-001: The saved-profile list MUST support selecting multiple saved profiles at once.
- FR-002: The GUI MUST preserve the visible list order when resolving the selected profiles for launch.
- FR-003: The GUI MUST still support selecting a single profile for normal editing and single-profile launch behavior.
- FR-004: When multiple profiles are selected, the GUI MUST make it clear that the selection will be used for grid launch.

### Bulk Launch

- FR-005: The operator MUST be able to launch multiple selected saved profiles in one action.
- FR-006: Each selected profile MUST be launched using its saved Chrome executable path and saved full Chrome profile folder path.
- FR-007: Bulk launch MUST continue using `https://chat.zalo.me` as the fixed target URL.
- FR-008: The bulk-launch action MUST reject an empty selection.
- FR-009: The implementation MUST cap one grid launch action to at most `8` profiles because the grid is fixed at `4x2`.
- FR-010: If more than `8` profiles are selected, the tool MUST launch and tile only the first `8` by list order and MUST report that the remainder were omitted.

### Grid Tiling

- FR-011: The tool MUST arrange detected Chrome windows on the primary monitor using `4 columns x 2 rows`.
- FR-012: The grid MUST use the primary monitor work area so the taskbar is not covered intentionally.
- FR-013: The first selected profile by list order MUST occupy cell `1`, the next profile cell `2`, and so on left-to-right, then top-to-bottom.
- FR-014: If fewer than `8` profiles are launched, the tool MUST fill only the first `N` cells and leave the rest unused.
- FR-015: The tool SHOULD restore minimized Chrome windows before moving them into grid cells.
- FR-016: The tool MUST not require the operator to resize or move Chrome windows manually after a successful grid launch.
- FR-017: Each grid-launched Chrome window SHOULD be started with launch-time `window width`, `window height`, and `window position` that already match its target grid cell as closely as Chrome allows.
- FR-018: The operator SHOULD not see a full-size Chrome window flash briefly before it is resized into the grid layout.

### Detection and Failure Handling

- FR-019: The tool MUST detect newly opened top-level Chrome windows after launch and use those windows for tiling.
- FR-020: If a launched profile window cannot be detected in time, the tool MUST keep launching the remaining selected profiles instead of aborting the whole batch immediately.
- FR-021: If only some launched windows are detected, the tool MUST tile the detected subset and surface a partial-success status.
- FR-022: Validation failures for one selected saved profile MUST prevent the grid-launch action before any Chrome processes are started.

### Architecture and Verification

- FR-023: Bulk launch and window tiling MUST be orchestrated through application use cases and ports, not coded directly in Tkinter event handlers.
- FR-024: Windows-specific window discovery and movement MUST remain inside infrastructure adapters.
- FR-025: The implementation MUST include automated tests for bulk-launch ordering, launch-time window sizing arguments, the `8`-profile cap, and grid geometry calculation.

## Non-Functional Requirements

- NFR-001: The feature MUST remain Windows-first.
- NFR-002: The grid-launch path SHOULD arrange detected windows within `15` seconds for up to `8` selected profiles on a normal workstation.
- NFR-003: The operator SHOULD need only one launch action after profiles have already been configured.
- NFR-004: Single-profile behavior from the previous feature MUST continue to work.

## Acceptance Scenarios

### Scenario 1: Launch Four Profiles Into the First Row and Second Row

- Given the operator has saved at least four valid Chrome profiles
- When the operator selects those four profiles in the GUI
- And the operator launches them together
- Then real Chrome windows open for those profiles
- And the windows are arranged into the first four grid cells in list order

### Scenario 2: Launch Eight Profiles

- Given the operator has eight valid saved profiles
- When the operator selects all eight and launches them
- Then each launched profile occupies one cell in a `4x2` grid
- And the order is left-to-right on row one, then left-to-right on row two

### Scenario 3: More Than Eight Profiles Selected

- Given the operator selects ten saved profiles
- When the operator launches the grid action
- Then only the first eight selected profiles are launched and tiled
- And the GUI reports that two profiles were omitted because the grid limit is eight

### Scenario 4: Partial Window Detection

- Given six selected profiles are launched
- And only five Chrome windows are detected in time
- When tiling runs
- Then the five detected windows are arranged into the first five cells
- And the GUI reports partial success instead of claiming all six were tiled

## Edge Cases

- The operator selects profiles in non-contiguous rows.
- One or more selected profile windows take longer than usual to appear.
- A selected profile is already open before the grid action starts.
- The profile list changes while a bulk launch is already in progress.
- The primary monitor work area is not evenly divisible by `4` or `2`.
- A selected profile launches successfully but its new top-level window is not detected before timeout.

## Success Metrics

- Operators can open multiple Zalo Chrome profiles with one action instead of repeated single launches.
- Manual window-arrangement time drops to near zero for the `4x2` use case.
- The same selected profiles land in the same predictable grid order each run.
- Partial failures are explicit rather than silently leaving the operator unsure which windows were arranged.
