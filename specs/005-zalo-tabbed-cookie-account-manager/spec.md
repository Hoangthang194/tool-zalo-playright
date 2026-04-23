# Feature Specification: Zalo Profile-Proxy Account Manager

## Status

Implemented.

## Summary

Extend the Zalo desktop GUI into a tabbed manager with two operator-facing areas:

- `Profiles`: a library for declaring and maintaining reusable Chrome profile definitions only
- `Zalo Accounts`: a library of launchable account entries where each entry combines one saved profile with one proxy value

Chrome launch ownership belongs to `Zalo Accounts`, not `Profiles`, because proxy configuration is part of the account launch target.

## Problem Statement

Operators need two different layers of data:

- reusable Chrome profile definitions
- launchable Zalo account entries that add proxy configuration on top of those profiles

When launch remains in the `Profiles` tab, operators can bypass the proxy-bound account workflow and the UI no longer reflects the true launch unit. The desktop tool should treat profiles as base configuration and treat Zalo accounts as the actual runnable entries.

## Goals

- Keep the GUI tabbed.
- Keep `Profiles` as the place to create, edit, and delete saved Chrome profile definitions.
- Move launch responsibility out of `Profiles`.
- Keep only one secondary tab: `Zalo Accounts`.
- Let the operator create a Zalo account entry by selecting one saved profile and entering one proxy value.
- Launch the selected Zalo account from the `Zalo Accounts` tab using its linked profile plus proxy.
- Remove cookie management from the GUI and workspace model.
- Persist account-proxy data between launches.
- Keep tab logic, launch orchestration, persistence, and validation outside Tkinter widget event code.
- Make single-line input fields visually consistent in height.

## Non-Goals

- Launching Chrome directly from the `Profiles` tab.
- Logging into Zalo automatically.
- Remote synchronization of account-proxy data.
- Full account automation workflows after the browser opens.
- Cookie storage, cookie linking, or cookie CRUD.
- Phone, notes, or other extra account metadata.

## Primary Users

### Zalo Operator

Needs one desktop tool where profiles are reusable configuration records and Zalo accounts are the actual launch targets with proxy settings.

### Maintainer

Needs profile management, account management, and account launch orchestration to remain testable and separate from Tkinter widget code.

### Reviewer

Needs a clear contract for tab responsibilities, local persistence, CRUD rules, and proxy-aware launch ownership.

## User Stories

1. As a Zalo operator, I want the `Profiles` tab to only maintain Chrome profile definitions so I can treat it as a clean configuration library.
2. As a Zalo operator, I want the `Zalo Accounts` tab to let me choose a saved profile and assign a proxy to it.
3. As a Zalo operator, I want to launch from the `Zalo Accounts` tab so the selected proxy is always part of the launch flow.
4. As a Zalo operator, I do not want unused cookie, phone, or notes fields cluttering the workflow.
5. As a maintainer, I want account-proxy persistence and account launch behavior behind application boundaries so the GUI stays focused on rendering and invoking use cases.

## Functional Requirements

### Tabbed Shell

- FR-001: The GUI MUST render a tabbed layout.
- FR-002: The first tab MUST be `Profiles`.
- FR-003: The GUI MUST add exactly one secondary tab: `Zalo Accounts`.
- FR-004: The GUI MUST NOT render a `Cookies` tab.
- FR-005: Switching tabs MUST NOT clear unsaved state in other tabs unexpectedly during the same app session.

### Profiles Tab Responsibilities

- FR-006: The `Profiles` tab MUST allow the operator to create multiple saved Chrome profile entries.
- FR-007: Each saved profile entry MUST include a user-visible name, Chrome executable path, and full Chrome profile folder path.
- FR-008: The `Profiles` tab MUST allow the operator to edit an existing saved profile entry.
- FR-009: The `Profiles` tab MUST allow the operator to delete an existing saved profile entry.
- FR-010: The `Profiles` tab MUST persist the saved profile library between launches.
- FR-011: The `Profiles` tab MUST NOT be the place where Chrome sessions are launched.
- FR-012: The `Profiles` tab SHOULD surface enough saved-profile detail to avoid assigning the wrong profile in the account workflow.

### Zalo Account Management and Launch

- FR-013: The `Zalo Accounts` tab MUST display saved account entries in a selectable list.
- FR-014: The operator MUST be able to create, update, and delete a saved account entry.
- FR-015: Each saved account entry MUST link to exactly one saved Chrome profile.
- FR-016: Each saved account entry MUST provide one proxy field for that linked profile.
- FR-017: The account tab MUST NOT require phone, notes, cookie, or other extra fields.
- FR-018: The implementation MUST prevent duplicate account entries for the same linked profile.
- FR-019: The account list SHOULD display the linked profile in operator-friendly form and MAY show the configured proxy as supporting text.
- FR-020: The `Zalo Accounts` tab MUST provide an explicit launch action for the selected saved account.
- FR-021: Launching a saved account MUST open real Google Chrome using the linked profile definition and the saved proxy configuration for that account.
- FR-022: Launching a saved account MUST open `https://chat.zalo.me`.
- FR-023: A blank proxy value MUST be allowed and interpreted as direct access without proxy.
- FR-024: The tool MUST validate the linked profile before launching an account.
- FR-025: If the linked profile no longer exists or is invalid, account launch MUST fail with an actionable validation error.
- FR-026: The tool MUST prevent duplicate concurrent launch requests while an account launch is already in progress.
- FR-027: Launch failures MUST be surfaced without deleting the saved profile or account entry automatically.

### Persistence and Integration

- FR-028: Account-proxy data MUST persist between launches.
- FR-029: Account-proxy persistence MUST be isolated behind an application port or equivalent repository boundary.
- FR-030: The account tab MUST present saved profile choices in operator-friendly form.
- FR-031: Deleting a profile MUST NOT silently corrupt the stored account library; stale references MAY remain as stored IDs until edited, but account launch MUST not proceed against a missing profile.

### Maintainability and Verification

- FR-032: Profile CRUD logic MUST be implemented outside Tkinter widget event code.
- FR-033: Account CRUD logic MUST be implemented outside Tkinter widget event code.
- FR-034: Account launch orchestration MUST be implemented outside Tkinter widget event code.
- FR-035: The implementation MUST include tests for account CRUD, account launch orchestration, and JSON persistence mapping.
- FR-036: Single-line input widgets in the `Zalo Accounts` tab SHOULD be visually aligned to the same effective height.

## Non-Functional Requirements

- NFR-001: The feature MUST remain Windows-first.
- NFR-002: The tabbed UI SHOULD remain understandable without expanding the window beyond the current launcher footprint.
- NFR-003: Operators SHOULD be able to save or update a profile-linked proxy entry in under 10 seconds once the app is open.
- NFR-004: Operators SHOULD be able to launch a previously saved account in under 5 seconds once the app is already open and the selected profile is valid.

## Acceptance Scenarios

### Scenario 1: Manage Profiles Without Launch Controls

- Given the operator opens the app
- When the `Profiles` tab is selected
- Then the profile library can be created, edited, and deleted
- And the tab does not expose the primary launch action

### Scenario 2: Save a Zalo Account Proxy Entry

- Given the operator opens the `Zalo Accounts` tab
- When the operator selects a saved profile
- And enters a proxy value
- And saves the entry
- Then the account entry appears in the saved-account list
- And it is persisted for the next app launch

### Scenario 3: Launch a Saved Zalo Account

- Given a saved account entry links to a valid saved profile
- And that saved account has a proxy value
- When the operator selects the account and clicks launch
- Then Chrome opens using the linked saved profile
- And the configured proxy is applied to that launch
- And `https://chat.zalo.me` opens

### Scenario 4: Prevent Launch When Linked Profile Is Invalid

- Given a saved account entry points to a saved profile that is missing or invalid
- When the operator attempts to launch that account
- Then no Chrome process is started
- And the GUI shows an actionable validation error

### Scenario 5: Remove an Existing Account Entry

- Given a saved account entry exists
- When the operator deletes it
- Then it no longer appears in the account list
- And the rest of the tab data remains unchanged

### Scenario 6: Field Heights Stay Consistent

- Given the operator opens the `Zalo Accounts` tab
- When the form renders
- Then the single-line input widgets appear with consistent height
- And the tab looks visually aligned without mixed compact and tall fields

## Edge Cases

- The operator saves an account without selecting a linked profile.
- A proxy field is intentionally left blank to represent direct access.
- A linked profile is later removed from the profile library.
- The operator attempts to create a second account entry for the same linked profile.
- The selected account references a profile whose Chrome executable path is no longer valid.
- The operator requests launch again while a previous account launch is still in progress.
- The account workspace file contains partially invalid entries.

## Success Metrics

- Operators can manage Chrome profiles as reusable configuration records without mixing them with launch-specific proxy data.
- Operators launch Zalo sessions from `Zalo Accounts`, where the selected proxy is part of the saved launch target.
- Account-proxy records persist locally and survive app restarts.
