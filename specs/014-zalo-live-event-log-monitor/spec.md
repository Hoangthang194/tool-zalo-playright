# Feature Specification: Zalo Live Event Log Monitor

## Status

Implemented in code. Manual browser verification is still pending.

## Summary

Add a live event monitor to the `Zalo Accounts` tab so the operator can attach to the currently launched `chat.zalo.me` tab, observe real-time `new_message`, `delivered`, and `seen` signals from that active session, and display a rolling log inside the desktop tool.

The monitor must reuse the same visible Chrome session already launched by the tool. It must not open a second standalone Zalo Web session for the same account.

## Goals

- Add `Start Listen` and `Stop Listen` controls to the `Zalo Accounts` tab.
- Attach to the already launched Zalo tab by using the tracked remote debugging port.
- Surface live event logs directly in the GUI without blocking the UI thread.
- Reuse the existing Zalo browser session instead of creating a duplicate session.

## Non-Goals

- Building a separate browser extension.
- Replacing the webhook ingest flow.
- Rendering a searchable message history dashboard.

## Functional Requirements

- FR-001: The feature MUST add one log panel under the account controls in the `Zalo Accounts` tab.
- FR-002: The feature MUST add `Start Listen` and `Stop Listen` controls.
- FR-003: `Start Listen` MUST require one visible launched Zalo account with a usable remote debugging port.
- FR-004: The live listener MUST attach to the existing `chat.zalo.me` page rather than launching another browser session.
- FR-005: The feature MUST log `new_message` signals from the active Zalo tab.
- FR-006: The feature SHOULD log `delivered` and `seen` receipt signals detected from the active Zalo tab.
- FR-007: The GUI MUST remain responsive while live monitoring runs.
- FR-008: The feature MUST surface listener lifecycle messages such as started, already installed, stopped, and unexpected stop.

## Architecture Notes

- The GUI owns the log panel and buttons.
- The application layer owns the start/stop use case contract.
- The Playwright/CDP adapter owns attaching to Chrome, installing page hooks, and streaming events back to Python.
- The implementation SHOULD use the active launched page/session, not a second Zalo session.

## Acceptance Scenarios

### Scenario 1: Start Listening

- Given one visible Zalo account has already been launched
- When the operator clicks `Start Listen`
- Then the tool attaches to the active `chat.zalo.me` tab
- And the log panel starts receiving listener lifecycle entries

### Scenario 2: Log a New Message Signal

- Given the live listener is attached
- When a new user or group message signal arrives in the active session
- Then the log panel shows a new `new_message` entry

### Scenario 3: Stop Listening

- Given the live listener is attached
- When the operator clicks `Stop Listen`
- Then the listener detaches cleanly
- And the log panel shows a stop entry
