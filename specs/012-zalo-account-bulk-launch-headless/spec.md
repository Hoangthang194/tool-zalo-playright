# Feature Specification: Zalo Account Bulk Launch With Headless Option

## Status

Proposed.

## Summary

Extend the `Zalo Accounts` tab so operators can select multiple saved accounts and launch them in one action. The launch flow must support two modes:

- visible browser launch
- hidden browser launch through a headless option

This feature moves bulk launch to the actual account-launch surface instead of limiting it to the reusable `Profiles` tab.

## Problem Statement

The current application structure makes `Zalo Accounts` the real launch unit because an account combines:

- one linked profile
- one proxy setting

However, the current bulk-launch behavior was specified around saved profiles rather than saved accounts. That leaves a gap for operators who need to start several account-specific sessions at once from the place where proxy configuration actually lives.

There is also no formal operator-facing option to launch without showing browser windows. Some workflows need the browser hidden or headless for reduced UI noise or unattended runs.

Without a dedicated spec:

- multi-account launch behavior in `Zalo Accounts` remains ambiguous
- headless behavior may conflict with visible launch assumptions
- manual selector-testing expectations may be incorrectly carried into headless runs

## Goals

- Allow selecting multiple saved Zalo accounts in the `Zalo Accounts` tab.
- Launch selected accounts in one action from the account tab.
- Preserve account-level proxy configuration for each launched session.
- Add a clear operator option to run launches headlessly.
- Keep launch orchestration outside Tkinter callbacks.

## Non-Goals

- Replacing the existing single-account launch path.
- Free-form per-account launch-mode customization inside one batch.
- Implementing message sending or account automation after launch.
- Solving all Chrome/Playwright engine-selection details in this spec if a later technical spike is needed.
- Changing `Profiles` tab ownership back from accounts to profiles.

## Primary Users

### Multi-Account Operator

Needs to start several account sessions together from the `Zalo Accounts` tab, with their saved proxies preserved.

### Background-Run Operator

Needs to start account sessions without showing browser windows.

### Maintainer

Needs clear contracts for account-level bulk launch, headless behavior, and operator-visible constraints.

## User Stories

1. As an operator, I want to select multiple saved accounts and launch them together so I do not need to start them one by one.
2. As an operator, I want each launched account to keep using its own linked profile and saved proxy.
3. As an operator, I want a checkbox or equivalent control to run accounts headlessly so I can hide browser windows.
4. As a maintainer, I want account launch mode and batching logic in use cases and ports rather than inside Tkinter event handlers.

## Functional Requirements

### Multi-Selection in `Zalo Accounts`

- FR-001: The `Zalo Accounts` list MUST support selecting multiple saved accounts at once.
- FR-002: The GUI MUST preserve visible account-list order when resolving a bulk launch request.
- FR-003: The GUI MUST still support single-account selection for normal editing and single-account launch.
- FR-004: The GUI MUST make it clear when the current selection will trigger a multi-account launch instead of a single-account launch.

### Bulk Launch From Accounts

- FR-005: The operator MUST be able to launch multiple selected saved accounts in one action from the `Zalo Accounts` tab.
- FR-006: Each selected account MUST launch with its linked saved profile.
- FR-007: Each selected account MUST launch with its own saved proxy configuration.
- FR-008: The bulk-launch action MUST reject an empty selection.
- FR-009: Validation failures for one selected account MUST prevent the batch before any launch begins.
- FR-010: The implementation SHOULD define and surface a practical batch limit if runtime constraints require one.

### Headless Option

- FR-011: The `Zalo Accounts` tab MUST provide an operator-visible option to run launches headlessly.
- FR-012: When headless mode is enabled, the selected accounts MUST be launched without showing browser windows.
- FR-013: When headless mode is disabled, launch behavior MUST remain consistent with the current visible-browser path.
- FR-014: The chosen headless setting MUST apply to the whole current launch action.
- FR-015: The GUI SHOULD make the current launch mode explicit before launch begins.

### Launch Semantics and Constraints

- FR-016: Visible multi-account launch SHOULD preserve current visible launch semantics as much as possible, including account-level status feedback.
- FR-017: Headless launch MAY use a different browser-launch adapter than the visible Chrome subprocess path if needed for technical feasibility, but the operator-facing account semantics MUST remain the same.
- FR-018: If headless mode cannot support a feature that visible mode supports, the GUI MUST communicate that constraint clearly.
- FR-019: Manual `Test Element` behavior MUST remain tied to a debuggable browser session. If headless mode makes manual selector testing unavailable or limited, that limitation MUST be surfaced to the operator before or during launch.
- FR-020: If window tiling logic exists for visible multi-launch, it MUST NOT be applied to headless launches.

### Status and Results

- FR-021: The bulk-launch flow MUST return account-level outcomes so the operator can tell which accounts launched successfully and which failed.
- FR-022: The GUI MUST distinguish between full success, partial success, and total failure for a multi-account launch.
- FR-023: For headless runs, operator-facing status MUST indicate that the accounts were launched without visible windows.
- FR-024: If the launch mode is headless, the status output MUST NOT claim that windows were tiled or shown.

### Architecture Boundaries

- FR-025: Account-level bulk-launch orchestration MUST live in an application use case or equivalent service boundary.
- FR-026: Any headless browser adapter MUST remain behind an application port or infrastructure adapter boundary.
- FR-027: Tkinter callbacks MUST NOT contain direct launch batching logic beyond gathering selection and invoking the use case.

## Non-Functional Requirements

- NFR-001: The feature MUST remain Windows-first.
- NFR-002: The visible-launch path MUST not regress current single-account launch behavior.
- NFR-003: The headless-launch path SHOULD remain deterministic and should not silently fall back to visible mode without telling the operator.
- NFR-004: Operator-visible launch status SHOULD remain understandable even when several accounts are launched together.

## Acceptance Scenarios

### Scenario 1: Launch Three Accounts Visibly

- Given three saved Zalo accounts exist
- And each account links to a valid profile
- When the operator selects those three accounts in the `Zalo Accounts` tab
- And launches them with headless mode disabled
- Then all three accounts launch with their own linked profile and proxy
- And the GUI reports visible multi-account launch success

### Scenario 2: Launch Three Accounts Headlessly

- Given three saved Zalo accounts exist
- And each account links to a valid profile
- When the operator selects those three accounts
- And enables the headless option
- And launches them
- Then all three accounts launch without visible browser windows
- And the GUI reports headless multi-account launch success

### Scenario 3: Partial Failure in Multi-Account Launch

- Given three saved Zalo accounts are selected
- And one account references an invalid linked profile
- When the operator launches the batch
- Then the tool rejects the launch before starting any account
- And the GUI surfaces the validation problem clearly

### Scenario 4: Headless Mode and Manual Test Limitation

- Given an operator launches an account batch with headless mode enabled
- When the operator later attempts a manual visible-browser action that requires an attached UI session
- Then the app explains the limitation instead of implying the action is fully available

## Edge Cases

- The operator selects accounts in non-contiguous rows.
- Two selected accounts resolve to conflicting runtime resources.
- One selected account uses direct access while another uses a proxy.
- The operator switches the headless option while a launch is already in progress.
- A headless launch path cannot support the same browser executable/profile combination as visible mode.
- A future implementation supports only single-account headless launch at first and must reject batch headless launch explicitly.

## Success Metrics

- Operators can start multiple saved accounts from the actual launch surface instead of launching one at a time.
- Headless mode is explicit and does not surprise operators with hidden behavior changes.
- Visible and headless launch outcomes are clearly distinguished in the GUI.
