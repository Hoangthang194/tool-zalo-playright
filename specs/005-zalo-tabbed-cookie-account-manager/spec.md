# Feature Specification: Zalo Tabbed Cookie and Account Manager

## Status

Implemented.

## Summary

Extend the Zalo desktop GUI into a tabbed manager with three operator-facing areas:

- `Profiles`: the current Chrome profile manager and launcher
- `Cookies`: a local library for saved Zalo cookie payloads
- `Zalo Accounts`: a local library for account records linked to saved profiles and cookies

## Problem Statement

Operators are no longer managing only Chrome profiles. They also need one place to keep cookie payloads and account notes for Zalo sessions. The current single-screen GUI mixes everything into one profile-focused layout and leaves no structured place to store cookie and account data.

## Goals

- Convert the current GUI into tabs.
- Keep the existing profile manager as the `Profiles` tab.
- Add a `Cookies` tab with local CRUD for saved cookie entries.
- Add a `Zalo Accounts` tab with local CRUD for saved account entries.
- Persist cookie and account data between launches.
- Keep tab logic, persistence, and validation outside Tkinter widget event code.

## Non-Goals

- Importing cookies directly into Chrome automatically.
- Logging into Zalo automatically.
- Remote synchronization of cookie or account data.
- Encrypting cookie data in this version.
- Full account automation workflows.

## Primary Users

### Zalo Operator

Needs one desktop tool that keeps profile launch targets, cookie payloads, and account references in the same place.

### Maintainer

Needs cookie and account management to remain testable and separate from Tkinter widget code.

### Reviewer

Needs a clear contract for tab structure, local persistence, and CRUD rules.

## User Stories

1. As a Zalo operator, I want the current profile manager to remain available in a dedicated tab so the existing launch workflow stays intact.
2. As a Zalo operator, I want to save cookie entries with a name and raw cookie payload so I can reuse or inspect them later.
3. As a Zalo operator, I want to save Zalo account records with a name, phone, notes, and optional links to a saved profile and cookie entry.
4. As a maintainer, I want cookie and account persistence behind application boundaries so the GUI stays focused on rendering and invoking use cases.

## Functional Requirements

### Tabbed Shell

- FR-001: The GUI MUST render a tabbed layout.
- FR-002: The first tab MUST contain the existing profile manager behavior.
- FR-003: The GUI MUST add a `Cookies` tab.
- FR-004: The GUI MUST add a `Zalo Accounts` tab.
- FR-005: Switching tabs MUST NOT clear unsaved state in other tabs unexpectedly during the same app session.

### Cookie Management

- FR-006: The `Cookies` tab MUST display saved cookie entries in a selectable list.
- FR-007: The operator MUST be able to create, update, and delete a saved cookie entry.
- FR-008: Each cookie entry MUST include a user-visible name and a raw cookie payload field.
- FR-009: A cookie entry MAY include notes.
- FR-010: A cookie entry MAY optionally reference one saved Chrome profile.
- FR-011: Cookie entry names MUST be non-empty.
- FR-012: Cookie entry names MUST be unique case-insensitively within the cookie library.

### Zalo Account Management

- FR-013: The `Zalo Accounts` tab MUST display saved account entries in a selectable list.
- FR-014: The operator MUST be able to create, update, and delete a saved account entry.
- FR-015: Each account entry MUST include a user-visible account name.
- FR-016: An account entry SHOULD allow storing a phone number or login identifier.
- FR-017: An account entry MAY include notes.
- FR-018: An account entry MAY optionally reference one saved Chrome profile.
- FR-019: An account entry MAY optionally reference one saved cookie entry.
- FR-020: Account entry names MUST be non-empty.
- FR-021: Account entry names MUST be unique case-insensitively within the account library.

### Persistence and Integration

- FR-022: Cookie and account data MUST persist between launches.
- FR-023: Cookie and account persistence MUST be isolated behind an application port or equivalent repository boundary.
- FR-024: The account tab SHOULD present saved profile and cookie choices in operator-friendly form.
- FR-025: Deleting a profile or cookie MUST NOT silently corrupt the stored account library; stale references MAY remain as stored IDs until edited.

### Maintainability and Verification

- FR-026: Cookie and account CRUD logic MUST be implemented outside Tkinter widget event code.
- FR-027: The implementation MUST include tests for cookie CRUD, account CRUD, and JSON persistence mapping.

## Non-Functional Requirements

- NFR-001: The feature MUST remain Windows-first.
- NFR-002: The tabbed UI SHOULD remain understandable without expanding the window beyond the current launcher footprint.
- NFR-003: Operators SHOULD be able to save a cookie or account entry in under 10 seconds once the app is open.

## Acceptance Scenarios

### Scenario 1: Manage Profiles in the First Tab

- Given the operator opens the app
- When the `Profiles` tab is selected
- Then the current profile manager remains available
- And profile launch behavior still works

### Scenario 2: Save a Cookie Entry

- Given the operator opens the `Cookies` tab
- When the operator enters a cookie name and raw cookie payload
- And saves the entry
- Then the cookie entry appears in the saved-cookie list
- And it is persisted for the next app launch

### Scenario 3: Save a Zalo Account Entry

- Given the operator opens the `Zalo Accounts` tab
- When the operator enters an account name and optional linked profile or cookie
- And saves the entry
- Then the account entry appears in the saved-account list
- And it is persisted for the next app launch

### Scenario 4: Delete a Cookie Entry

- Given a saved cookie entry exists
- When the operator deletes it
- Then it no longer appears in the cookie list
- And the rest of the tab data remains unchanged

## Edge Cases

- A cookie entry has a large raw payload.
- The operator saves an account without linking any profile or cookie.
- A linked profile is later removed from the profile library.
- A linked cookie is later removed from the cookie library.
- The cookie/account library file contains partially invalid entries.

## Success Metrics

- Operators can manage profiles, cookies, and accounts from one desktop app without mixing all fields into one screen.
- Profile launch behavior remains intact after the tabbed refactor.
- Cookie and account records persist locally and survive app restarts.
