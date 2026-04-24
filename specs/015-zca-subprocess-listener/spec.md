# Feature Specification: ZCA Subprocess Listener with Sender/Listener Account Split

## Status

Implemented in code. Manual ZCA runtime verification is still pending.

## Summary

Replace the current webhook-driven and Playwright live-event listener flow with a ZCA-based listener process managed directly by the Python tool.

The tool must support two fixed account roles:

- `sender`: launches Chrome with Playwright-compatible debugging and is used for browser/manual send actions
- `listener`: starts one managed ZCA subprocess that logs in from a stored credentials file and writes incoming messages into the existing MariaDB `messages` table

The listener process must not use the old localhost webhook path. Instead, the Python app must read structured JSON lines from the child process, persist `new_message` events into the database, and surface runtime logs in both the GUI and the terminal when the app is started from a console-capable entrypoint.

## Goals

- Remove the webhook ingest flow from the main runtime path.
- Remove the Playwright live-event monitor from the main runtime path.
- Split saved Zalo accounts into fixed `sender` and `listener` roles.
- Keep `sender` accounts on the current Chrome/Playwright launch flow.
- Start one managed ZCA subprocess for one selected `listener` account.
- Read listener events from child-process JSONL output instead of HTTP webhook callbacks.
- Persist `new_message` events into the existing `messages` table.
- Show listener lifecycle and message-persistence logs in the GUI.
- Allow operators to see the same logs in a terminal run mode.

## Non-Goals

- Replacing the current Playwright send automation flow.
- Storing receipt-only events such as `delivered` or `seen` in the `messages` table.
- Supporting more than one simultaneous ZCA listener process in phase one.
- Building a full Node.js service mesh or external webhook bridge.
- Requiring the listener account to attach to a visible Chrome instance at runtime.

## Data Model

### Saved Zalo Account

The workspace account model must support:

- `id`
- `name`
- `role`
- `profile_id`
- `proxy`
- `credentials_file_path`

Rules:

- `role` MUST be either `sender` or `listener`
- `profile_id` MUST be required for `sender`
- `credentials_file_path` MUST be required for `listener`
- `proxy` applies only to `sender`
- `listener_token` is deprecated and must not be used by the new runtime flow

### Legacy Migration

When loading older workspace JSON:

- `mode=send` or missing `mode` maps to `role=sender`
- `mode=listen` maps to `role=listener`
- `listener_token` may be ignored
- old payloads must remain loadable without manual migration

## Functional Requirements

### Account Roles

- FR-001: The system MUST replace the operator-facing account `mode` concept with a fixed account `role`.
- FR-002: The system MUST support exactly two roles: `sender` and `listener`.
- FR-003: A `sender` account MUST require a linked Chrome profile.
- FR-004: A `listener` account MUST require a credentials file path.
- FR-005: A `sender` account MUST continue using the current Chrome launch flow.
- FR-006: A `listener` account MUST NOT require a launched Chrome instance in order to start listening.

### ZCA Listener Process

- FR-007: The tool MUST start one managed ZCA child process for one selected `listener` account.
- FR-008: The ZCA child process MUST read credentials from a file containing `cookie`, `userAgent`, and `imei`.
- FR-009: The ZCA child process MUST emit structured JSON lines on standard output.
- FR-010: The Python tool MUST parse those JSON lines and convert them into application events.
- FR-011: The Python tool MUST support `listener_started`, `listener_ready`, `new_message`, `delivery_update`, `listener_error`, and `listener_stopped` event types.
- FR-012: The Python tool MUST allow only one active listener process at a time in phase one.
- FR-013: The Python tool MUST stop the active listener process when the operator clicks `Stop Listener` or closes the GUI.

### Message Persistence

- FR-014: Only `new_message` events MUST be written into the `messages` table.
- FR-015: The tool MUST persist `msgId`, `fromGroupId`, `toGroupId`, `fromAccountId`, and `content`.
- FR-016: `fromAccountId` MUST be resolved from the selected saved listener account, not trusted from child-process payloads.
- FR-017: Duplicate `msgId` inserts MUST return `already_processed` and must not be treated as fatal listener failures.
- FR-018: Database failures for one message MUST be surfaced in logs and MUST NOT force-stop the listener process.

### GUI

- FR-019: The `Zalo Accounts` tab MUST expose `sender` and `listener` roles.
- FR-020: When `sender` is selected, the GUI MUST show profile/proxy controls and launch actions.
- FR-021: When `listener` is selected, the GUI MUST show credentials-file controls and listener start/stop actions.
- FR-022: The GUI MUST hide irrelevant controls for the inactive role.
- FR-023: The existing account log panel MUST be repurposed into a ZCA listener log panel.
- FR-024: The GUI MUST stay responsive while the listener subprocess runs.

### Terminal Logs

- FR-025: The tool MUST support a console-capable run path where listener logs are visible in the terminal.
- FR-026: The Python GUI entrypoint SHOULD configure standard logging so listener lifecycle and persistence results are printed when the app is launched from `python.exe` or an equivalent terminal-capable command.
- FR-027: The repository SHOULD provide a dedicated Windows batch entrypoint for console logging.

## Acceptance Scenarios

### Scenario 1: Save a Listener Account

- Given the operator creates a Zalo account entry with role `listener`
- When they provide a valid credentials file path and save
- Then the workspace persists the account with role `listener`
- And the GUI no longer requires a linked Chrome profile for that account

### Scenario 2: Start the Listener

- Given a saved listener account has a readable credentials file
- When the operator clicks `Start Listener`
- Then the tool starts one ZCA subprocess
- And the GUI log shows listener startup events

### Scenario 3: Persist a New Message

- Given the ZCA subprocess emits a valid `new_message` JSON line
- When the Python tool processes that event
- Then the message is inserted into `messages`
- And the GUI log shows whether the insert was accepted or already processed

### Scenario 4: Show Logs in Terminal

- Given the operator starts the GUI from a console-capable run command
- When the listener starts and receives events
- Then the same runtime log stream is visible in the terminal

## Superseded Runtime Paths

This feature supersedes the main runtime use of:

- `specs/013-zalo-message-webhook-ingest`
- `specs/014-zalo-live-event-log-monitor`

Those artifacts may remain in the repository for reference, but the GUI runtime path must prefer this ZCA subprocess design.
