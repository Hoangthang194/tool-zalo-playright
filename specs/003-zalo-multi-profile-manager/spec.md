# Feature Specification: Zalo Multi-Profile Chrome Manager

## Status

Implemented baseline feature.

## Summary

Extend the Zalo launcher GUI so operators can manage multiple saved Google Chrome profiles by storing the full Chrome profile folder path for each entry, such as `C:\Users\<user>\AppData\Local\Google\Chrome\User Data\Profile 1`. Launching a saved entry should open `https://chat.zalo.me` in that exact Chrome profile.

## Problem Statement

Operators often manage several Chrome profiles for different Zalo accounts. Re-entering `user_data_dir` and `profile_directory` values manually is inconvenient. They need to save one full profile path per entry and launch that profile directly from the GUI.

## Goals

- Provide a GUI for managing multiple saved Chrome profile entries.
- Allow each saved entry to be added by full Chrome profile path.
- Launch any saved profile directly into `https://chat.zalo.me`.
- Preserve clean architecture boundaries by keeping profile management logic outside GUI event code.
- Keep the happy path fast: select a saved profile and launch it.

## Non-Goals

- Sending Zalo messages automatically.
- Automating chat navigation after the browser opens.
- Bulk launching all saved profiles at once in the baseline version.
- Managing Zalo credentials or bypassing login.

## Primary Users

### Multi-Account Zalo Operator

Uses several Chrome profiles and needs to open the correct Zalo session without retyping profile paths.

### Maintainer

Needs saved-profile management, launch orchestration, and GUI rendering to remain separable so future changes stay testable.

### Reviewer

Needs a clear contract for how full Chrome profile paths are stored, validated, selected, and launched.

## User Stories

1. As a Zalo operator, I want to save multiple Chrome profile paths so I do not need to re-enter them every time I switch accounts.
2. As a Zalo operator, I want each saved profile to have a friendly name so I can launch the right one quickly.
3. As a Zalo operator, I want to edit or remove a saved profile when my Chrome setup changes.
4. As a Zalo operator, I want to add a profile using a path like `...\User Data\Profile 1` and launch that exact profile later with one click.
5. As a maintainer, I want saved-profile CRUD and launch behavior expressed through use cases so GUI changes do not absorb business rules.

## Functional Requirements

### Profile Library Management

- FR-001: The GUI MUST allow the operator to create multiple saved Chrome profile entries.
- FR-002: Each saved profile entry MUST include a user-visible name, Chrome executable path, and full Chrome profile folder path.
- FR-003: The GUI MUST allow the operator to edit an existing saved profile entry.
- FR-004: The GUI MUST allow the operator to delete an existing saved profile entry.
- FR-005: The tool SHOULD allow the operator to duplicate an existing saved profile entry as a starting point for a new one.
- FR-006: The tool MUST persist the saved profile library between launches.
- FR-007: The persistence format MUST support more than one saved profile entry at a time.
- FR-008: The tool SHOULD remember the last selected saved profile independently from the full profile library.

### Profile Validation

- FR-009: The tool MUST validate each saved profile before it can be launched.
- FR-010: Validation MUST include Chrome executable existence and Chrome profile folder existence.
- FR-011: The tool MUST reject an empty friendly name.
- FR-012: The tool MUST reject use of the same exact Chrome profile path across multiple saved entries.
- FR-013: The tool MUST reject selecting the parent `User Data` root when the operator should have selected an actual profile folder such as `Default` or `Profile 1`.
- FR-014: Validation errors MUST be actionable and identify which saved profile entry is invalid.

### Launch Behavior

- FR-015: The GUI MUST display the available saved profiles in a form that supports direct selection and launch.
- FR-016: The operator MUST be able to launch a selected saved profile without manually re-entering its path values.
- FR-017: Launching a saved profile MUST open real Google Chrome with launch arguments derived from the saved profile path.
- FR-018: The launcher MUST derive `user_data_dir` from the saved profile path's parent directory and `profile_directory` from the saved profile path's directory name.
- FR-019: Launching a saved profile MUST open `https://chat.zalo.me`.
- FR-020: The launcher SHOULD request a new Chrome window when launching a saved profile.
- FR-021: The tool MUST prevent duplicate concurrent launch requests for the same selection while a launch is already in progress.
- FR-022: The tool MUST surface launch failures without removing the saved profile entry automatically.
- FR-031: On Windows, launching one selected saved profile SHOULD apply a deterministic window position and window size instead of leaving Chrome at its default restored size.
- FR-032: The default single-profile window bounds SHOULD be consistent with the first cell of the `4x2` layout used by the multi-profile grid launcher so operators get predictable sizing.
- FR-033: When the operator launches saved profiles one at a time on Windows, each newly opened Chrome window SHOULD use the next available grid cell beside the already visible Chrome windows instead of reusing the first cell.
- FR-034: Sequential single-profile launches SHOULD avoid overlapping a previously launched Chrome window while free cells still exist in the `4x2` layout.

### User Experience

- FR-023: The GUI MUST make it easy to distinguish which saved profile is currently selected.
- FR-024: The GUI SHOULD surface enough saved-profile detail to avoid accidental launches of the wrong entry.
- FR-025: The GUI SHOULD support a fast launch flow where one click selects a profile and one click launches it.
- FR-026: The GUI MAY support a single-click launch affordance directly from the saved-profile list if it remains clear and safe.
- FR-027: The GUI MUST allow adding a new profile without overwriting existing saved profiles.

### Data and Maintainability

- FR-028: Saved-profile management logic MUST be implemented outside Tkinter widget code.
- FR-029: Persistence logic for multiple saved profiles MUST be isolated behind an application port or equivalent repository boundary.
- FR-030: The baseline implementation MUST include tests for saved-profile CRUD, persistence mapping, selection state, and launch orchestration.

## Non-Functional Requirements

- NFR-001: The project MUST target Python 3.11+.
- NFR-002: The feature MUST remain Windows-first for operator guidance.
- NFR-003: Operators SHOULD be able to launch a saved profile in under 5 seconds once the profile library is already configured.
- NFR-004: The profile library SHOULD remain understandable even when at least 10 saved profiles exist.

## Acceptance Scenarios

### Scenario 1: Save and Launch Two Different Profiles

- Given the operator has valid Chrome profile paths for `Profile A` and `Profile B`
- When the operator saves both profile entries in the GUI
- And the operator selects `Profile B`
- And the operator clicks launch
- Then Chrome opens with the saved configuration for `Profile B`
- And `https://chat.zalo.me` opens for that profile
- And the Chrome window opens with deterministic bounds instead of an arbitrary restored size on Windows
- And if another launched Chrome window is already visible, the new window uses the next grid cell beside it instead of overlapping it

### Scenario 2: Edit an Existing Saved Profile

- Given a saved profile entry exists
- When the operator updates its profile path or friendly name
- Then the updated profile is persisted
- And later launches use the updated values

### Scenario 3: Delete a Saved Profile

- Given multiple saved profile entries exist
- When the operator deletes one saved profile
- Then the deleted entry no longer appears in the GUI
- And other saved profiles remain unchanged

### Scenario 4: Prevent Launch of Invalid Saved Profile

- Given a saved profile points to a deleted or moved Chrome profile folder
- When the operator attempts to launch it
- Then no Chrome process is started
- And the GUI shows an actionable validation error for that saved profile

### Scenario 5: Migrate from Single-Profile Settings

- Given the operator previously used the single-profile Zalo launcher
- When the multi-profile manager starts for the first time
- Then the tool converts the older `user_data_dir + profile_directory` settings into one saved full profile path
- And the operator can continue launching without re-entering the same profile manually

## Edge Cases

- Two saved profiles point to the same Chrome profile path under different names.
- The operator renames a saved profile to a name already in use.
- The saved-profile library file is partially corrupt.
- The operator deletes the selected profile while it is selected.
- The last selected profile no longer exists when the app starts.
- Chrome is already running with the selected profile and still needs a new window request.
- Chrome ignores the requested window size on the first paint and needs a post-launch move/resize enforcement step.
- The operator selects the parent `User Data` directory instead of `Default` or `Profile 1`.

## Success Metrics

- Operators can maintain multiple Zalo launch targets without retyping Chrome profile paths.
- The most common switching flow is reduced to selecting a saved profile and launching it.
- Validation catches broken or duplicated saved profile paths before Chrome process creation.
- The multi-profile manager accepts the exact path shape operators already use in Chrome, such as `...\User Data\Profile 1`.
