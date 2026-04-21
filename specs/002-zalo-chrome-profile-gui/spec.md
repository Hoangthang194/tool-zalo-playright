# Feature Specification: Zalo Chrome Profile GUI Launcher

## Status

Proposed feature for the next implementation slice.

## Summary

Build a Python desktop GUI that launches real Google Chrome with a selected Chrome user profile and opens `https://chat.zalo.me` directly. This feature is intentionally not workflow-driven: operators should be able to start the Zalo chat session from a simple GUI without preparing JSON workflow files.

## Problem Statement

The current repository centers on workflow-based browser automation. That model is useful for scripted actions, but it is heavier than necessary for the primary Zalo use case: open Chrome with an existing logged-in profile and go straight to Zalo Web. Operators need a direct launcher experience that reuses Chrome profile state, avoids workflow authoring, and exposes only the minimum inputs required to start a Zalo session safely.

## Goals

- Provide a dedicated GUI entrypoint for launching Zalo Web.
- Launch installed Google Chrome instead of Playwright's bundled Chromium.
- Reuse an existing Chrome profile so Zalo sessions, cookies, and local state are preserved.
- Open `https://chat.zalo.me` automatically after launch.
- Keep the implementation aligned with clean architecture boundaries.
- Provide clear validation and actionable launch errors for Windows-first operators.

## Non-Goals

- Running JSON workflow files to reach Zalo.
- Automating chat actions such as sending messages, scraping chats, or reading contacts.
- Managing Zalo credentials, QR login flows, or bypassing authentication.
- Replacing the existing workflow-driven feature set.
- Multi-profile parallel session orchestration in the baseline version.

## Primary Users

### Zalo Operator

Starts a GUI, selects or confirms a Chrome profile, and opens Zalo Web with as few steps as possible.

### Maintainer

Needs the launcher logic, validation rules, and GUI concerns to remain separated so the tool can later grow into broader Zalo-specific capabilities.

### Reviewer

Needs an explicit contract for profile selection, launch behavior, and failure modes before implementation begins.

## User Stories

1. As a Zalo operator, I want to open `chat.zalo.me` from a GUI so I do not need to remember terminal commands.
2. As a Zalo operator, I want the tool to use my existing Chrome profile so my current Zalo login session can be reused.
3. As a Zalo operator, I want the tool to remember or quickly reselect my last-used profile so repeated daily launches are fast.
4. As a maintainer, I want the launch behavior modeled explicitly instead of buried in GUI code so validation and testing stay straightforward.
5. As a reviewer, I want invalid Chrome paths or profile selections to fail before launch so configuration issues are obvious.

## Functional Requirements

### GUI Entry and Configuration

- FR-001: The tool MUST provide a desktop GUI entrypoint dedicated to the Zalo launcher flow.
- FR-002: The Zalo launcher flow MUST NOT require a workflow file as input.
- FR-003: The GUI MUST allow the operator to choose or enter a Chrome user data directory.
- FR-004: The GUI MUST allow the operator to choose or enter a Chrome profile directory name such as `Default` or `Profile 1`.
- FR-005: The GUI MUST display the target URL as `https://chat.zalo.me` and use it as the default launch destination.
- FR-006: The GUI MUST provide a launch action that starts Chrome with the selected configuration.
- FR-007: The GUI SHOULD persist the most recently used Chrome path, user data directory, and profile directory for the next launch.
- FR-008: If configuration persistence is implemented, the storage location MUST be explicit and documented.

### Chrome Discovery and Validation

- FR-009: The tool MUST attempt to locate an installed Google Chrome executable on supported systems.
- FR-010: The GUI MUST allow overriding the detected Chrome executable path when auto-discovery is insufficient.
- FR-011: The tool MUST validate that the selected Chrome executable exists before launch.
- FR-012: The tool MUST validate that the selected Chrome user data directory exists before launch.
- FR-013: The tool MUST validate that the selected Chrome profile directory exists within the user data directory before launch.
- FR-014: The tool MUST provide actionable validation errors in the GUI when required inputs are missing or invalid.

### Launch Behavior

- FR-015: The tool MUST launch real Google Chrome as a separate process, not Playwright's default browser runtime.
- FR-016: The tool MUST pass launch arguments that instruct Chrome to use the selected user data directory and profile directory.
- FR-017: The tool MUST open `https://chat.zalo.me` in the launched Chrome session.
- FR-018: The tool MUST support Windows paths containing spaces.
- FR-019: The tool MUST prevent duplicate concurrent launch requests from repeated clicks while a launch is already being processed.
- FR-020: The tool MUST report whether the launch request was started successfully or failed before process creation.
- FR-021: When Chrome cannot be started, the tool MUST surface an actionable error message rather than failing silently.

### Runtime Expectations

- FR-022: The baseline launcher MUST preserve the selected profile's existing browser state and MUST NOT create a new temporary profile by default.
- FR-023: The tool MUST tolerate the case where `chat.zalo.me` requires the operator to log in manually because no session exists in the selected profile.
- FR-024: The tool MUST make the chosen profile and launch target visible to the operator before launch.

### Maintainability and Testability

- FR-025: Domain and application logic for launch configuration validation MUST remain independent from GUI toolkit code.
- FR-026: Process-launch integration MUST be isolated behind an application port or equivalent adapter boundary.
- FR-027: The baseline implementation MUST include tests for configuration validation and launch argument construction.
- FR-028: The repository MUST include operator guidance for starting the GUI launcher.

## Non-Functional Requirements

- NFR-001: The project MUST target Python 3.11+.
- NFR-002: The initial operator experience MUST be documented for Windows and PowerShell first.
- NFR-003: The GUI SHOULD be simple enough for an operator to launch Zalo in under 10 seconds after opening the app.
- NFR-004: Errors SHOULD be understandable without requiring stack traces or source-code knowledge.
- NFR-005: The solution SHOULD remain lightweight and avoid introducing workflow concepts into the launcher path.

## Acceptance Scenarios

### Scenario 1: Launch Zalo with an Existing Chrome Profile

- Given Chrome is installed
- And the operator selects a valid user data directory
- And the operator selects a valid profile directory
- When the operator clicks the launch button
- Then Chrome starts with the selected profile
- And `https://chat.zalo.me` opens in that session

### Scenario 2: Launch with Remembered Configuration

- Given the operator has previously launched the tool successfully
- And configuration persistence is enabled
- When the operator opens the GUI again
- Then the last-used Chrome path, user data directory, and profile directory are prefilled
- And the operator can launch Zalo without re-entering the same values

### Scenario 3: Invalid Profile Prevents Launch

- Given the operator selects a user data directory
- And the entered profile directory does not exist inside it
- When the operator clicks the launch button
- Then no Chrome process is started
- And the GUI shows an actionable validation message identifying the missing profile

### Scenario 4: Chrome Executable Not Found

- Given Chrome auto-discovery fails or the configured path is invalid
- When the operator attempts to launch Zalo
- Then no browser process is started
- And the GUI shows an actionable error explaining that Chrome could not be found

### Scenario 5: Profile Requires Manual Login

- Given the selected profile does not contain an active Zalo session
- When Chrome opens `https://chat.zalo.me`
- Then the page may show the normal Zalo login flow
- And the launcher still counts the browser launch as successful

## Edge Cases

- Chrome is already running and the selected profile is locked by another Chrome process.
- The operator points to a non-Chrome executable.
- The selected user data directory exists but contains no matching profile directory.
- The profile directory name contains spaces or mixed case.
- The operator double-clicks the launch button quickly.
- `chat.zalo.me` is unreachable because of network issues, even though Chrome launches successfully.
- The remembered configuration points to paths that were deleted after the last run.

## Success Metrics

- An operator can launch Zalo Web from the GUI with no workflow file and no terminal command.
- The most common happy path requires at most one explicit launch action after initial setup.
- Validation catches invalid Chrome paths and invalid profile selections before process launch.
- Future Zalo-specific features can be added without coupling process-launch logic directly to the GUI layer.
