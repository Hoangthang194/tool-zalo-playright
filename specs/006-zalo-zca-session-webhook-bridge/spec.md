# Feature Specification: Zalo Account Session Export for ZCA Webhook Listener

## Status

Proposed.

## Summary

Extend the `Zalo Accounts` launch workflow so the desktop tool can capture a ZCA-compatible browser session from the launched Chrome account and forward it to a configured webhook endpoint. The exported payload must include `cookie`, `userAgent`, and `imei` together with account metadata so an external service built on `zca-js` can call `zalo.login(credentials)` and start `api.listener.start()` without requiring QR login inside that service.

## Problem Statement

The current tool can launch Chrome with a saved profile, proxy, and post-launch click targets, but it stops once the browser window is open. A separate `zca-js` listener service cannot reuse that authenticated browser state unless it receives the credentials that `zca-js` expects for cookie-based login.

From the checked `zca-js` source and examples:

- cookie-based login requires `imei`, `cookie`, and `userAgent`
- the listener uses the browser `cookie` header and `user-agent` header for its websocket connection
- only one web listener can run per Zalo account at a time

Operators need one controlled handoff from the Python launcher to a ZCA webhook listener service so an already logged-in Chrome profile can bootstrap a listener without manually copying cookies.

## Goals

- Keep launch ownership in `Zalo Accounts`, where profile and proxy already meet.
- Capture authenticated Zalo Web session data from the launched Chrome session.
- Produce a `zca-js` compatible credential payload containing `cookie`, `userAgent`, and `imei`.
- Deliver the captured session to a configured webhook endpoint for downstream ZCA listener startup.
- Surface capture and webhook results clearly in the GUI.
- Preserve clean architecture by keeping session capture, credential mapping, and webhook delivery outside Tkinter event handlers.

## Non-Goals

- Implementing the external Node.js or Bun webhook listener service in this repository.
- Replacing `zca-js` QR login flows.
- Supporting more than one simultaneous web listener for the same Zalo account.
- Building a manual cookie editor or cookie CRUD tab.
- Automatically solving Zalo login when the launched profile is not yet authenticated.
- Synchronizing exported session credentials to cloud services or shared remote storage.

## Primary Users

### Zalo Operator

Launches saved Zalo accounts from Chrome profiles and wants the same account session to be handed off to a ZCA webhook listener automatically or with one explicit retry.

### ZCA Integration Owner

Runs a separate service based on `zca-js` and needs a stable payload contract for session bootstrap.

### Maintainer

Needs the session extraction and webhook delivery flow to fit the existing clean architecture instead of being buried inside Tkinter callbacks.

## User Stories

1. As a Zalo operator, I want a launched Zalo account to export its current browser session so my `zca-js` listener service can start without QR login.
2. As a Zalo operator, I want launch to continue opening Chrome even if session export is not ready yet, because I may still need to log in manually first.
3. As a Zalo operator, I want a retryable session sync action after manual login so I do not need to relaunch the account just to resend credentials.
4. As a ZCA integration owner, I want the webhook payload to already match the `zca-js` credential shape closely enough that my listener service only needs light mapping.
5. As a maintainer, I want a dedicated application flow for launch, session capture, and webhook dispatch so proxy launch logic, UI rendering, and integration transport stay separable.

## Functional Requirements

### Launch and Session Capture

- FR-001: The tool MUST keep launch ownership in the `Zalo Accounts` tab.
- FR-002: Launching a saved account with ZCA session sync enabled MUST still open real Google Chrome using the linked profile, proxy, and `https://chat.zalo.me`.
- FR-003: After launch, the tool MUST attempt to capture the active Zalo Web session from the launched browser instance through a supported automation/debugging adapter instead of relying on manually entered cookie text.
- FR-004: The captured session MUST include the browser `userAgent` value used by the launched session.
- FR-005: The captured session MUST include cookie data sufficient to reconstruct a `zca-js` `Credentials.cookie` value.
- FR-006: The tool MUST produce an `imei` value for the exported payload because `zca-js` cookie-based login requires it.
- FR-007: If a previously exported `imei` exists for the same saved account, the tool SHOULD reuse it on later exports; otherwise it MUST generate a new ZCA-compatible value and persist it for reuse.
- FR-008: If the launched Chrome profile is not yet authenticated to Zalo Web, the browser launch MUST still succeed, but session export MUST fail with an actionable status instead of sending an incomplete payload.
- FR-009: The tool SHOULD make one automatic session-capture attempt during the launch flow for already logged-in profiles.
- FR-010: The tool MUST provide an explicit session-sync retry action for the selected saved account that does not require relaunching Chrome.

### ZCA Webhook Delivery

- FR-011: The tool MUST support configuring one ZCA webhook endpoint URL for session delivery.
- FR-012: The tool MUST support an optional authentication secret or token for the webhook request.
- FR-013: A successful session capture MUST be delivered to the configured webhook endpoint as JSON.
- FR-014: The webhook payload MUST include account and launch context, including saved account ID, saved account name, linked profile ID, linked profile name, configured proxy, and export timestamp.
- FR-015: The webhook payload MUST include a `credentials` object containing `imei`, `userAgent`, and `cookie`.
- FR-016: The `cookie` field SHOULD be serialized in a structure that `zca-js` can consume directly, such as an array of serialized cookies.
- FR-017: The tool MUST treat any non-2xx webhook response, timeout, or transport failure as a delivery failure and surface it clearly to the operator.
- FR-018: The tool MUST NOT send a webhook request if required credential parts are missing.
- FR-019: The tool SHOULD allow the downstream service to correlate repeated exports for the same saved account through stable account identifiers in the payload.

### Persistence and Boundaries

- FR-020: Webhook configuration MUST persist between app launches behind an application port or equivalent repository boundary.
- FR-021: Per-account ZCA export metadata MUST persist between app launches, including at least the last export status, last export timestamp, and the reusable `imei` value.
- FR-022: Raw cookie values MUST be treated as sensitive runtime data and MUST NOT be shown in primary list views.
- FR-023: Raw cookie values and webhook secrets MUST NOT be written to plain-text status messages or logs.
- FR-024: Session capture logic MUST be implemented outside Tkinter widget event code.
- FR-025: Webhook transport logic MUST be implemented outside Tkinter widget event code.
- FR-026: The implementation MUST define dedicated models or result objects for captured ZCA session data and webhook delivery results instead of overloading click-target or proxy-only models.

### GUI Behavior

- FR-027: The `Zalo Accounts` tab MUST show the ZCA session sync state for the selected account.
- FR-028: The GUI MUST surface the distinct phases of `launching`, `capturing session`, `sending webhook`, `sync succeeded`, and `sync failed`.
- FR-029: The GUI MUST provide an explicit control to retry ZCA session sync for the selected account after manual login.
- FR-030: The GUI MUST validate that webhook configuration is present before a sync attempt starts.
- FR-031: The GUI SHOULD warn the operator that `zca-js` web listener operation is single-session-per-account, so using the same account in browser/web at the same time may stop the listener.
- FR-032: The additional controls and status labels introduced for ZCA sync SHOULD remain visually consistent with the shared UI component system already used by the app.

### Concurrency and Failure Modes

- FR-033: The tool MUST prevent duplicate concurrent ZCA sync attempts for the same account while one sync is already in progress.
- FR-034: If Chrome closes or becomes unreachable before session capture finishes, the tool MUST fail the sync attempt with an actionable error.
- FR-035: If capture succeeds but webhook delivery fails, the tool MUST preserve the launch result and show the failure only for the sync portion.
- FR-036: If click automation and ZCA session capture both depend on browser debugging access, the implementation MUST coordinate them without assigning conflicting ports or incompatible ownership of the same launched browser.

## Non-Functional Requirements

- NFR-001: The feature MUST remain Windows-first.
- NFR-002: Session sync feedback SHOULD be visible in the existing `Zalo Accounts` workspace without requiring a new full-screen flow.
- NFR-003: For an already logged-in profile, automatic capture and webhook dispatch SHOULD finish within 10 seconds after Chrome launch begins.
- NFR-004: Sensitive credential data SHOULD remain redacted in operator-visible status output.
- NFR-005: The design SHOULD allow the future addition of alternative session consumers besides `zca-js` without rewriting Tkinter views.

## Acceptance Scenarios

### Scenario 1: Launch and Sync an Already Logged-In Account

- Given a saved Zalo account links to a valid saved Chrome profile
- And the profile is already authenticated on `https://chat.zalo.me`
- And a valid ZCA webhook endpoint is configured
- When the operator launches that saved account
- Then Chrome opens using the linked profile and proxy
- And the tool captures `cookie`, `userAgent`, and `imei`
- And the tool sends a webhook payload for that account
- And the GUI shows a successful ZCA sync state

### Scenario 2: Launch Succeeds but Session Is Not Ready Yet

- Given a saved Zalo account links to a valid saved Chrome profile
- And the profile is not yet authenticated on `https://chat.zalo.me`
- When the operator launches that saved account
- Then Chrome still opens successfully
- And the ZCA sync attempt fails without sending incomplete credentials
- And the GUI tells the operator to complete login and retry session sync

### Scenario 3: Retry Sync After Manual Login

- Given Chrome is already open for the selected saved account
- And the operator manually completes login on Zalo Web
- When the operator clicks the retry session-sync action
- Then the tool captures the now-valid session from the running browser
- And the tool sends the webhook payload without relaunching Chrome

### Scenario 4: Webhook Delivery Fails

- Given the tool captured a valid ZCA session
- And the configured webhook endpoint returns an error or times out
- When delivery is attempted
- Then the launch remains successful
- And the GUI marks only the sync step as failed
- And the operator can retry delivery later

### Scenario 5: Prevent Duplicate Sync Attempts

- Given a ZCA session sync attempt is already running for one saved account
- When the operator clicks the sync action again immediately
- Then the tool rejects the duplicate request
- And the original sync attempt remains the only in-flight operation

## Edge Cases

- The launched account has no linked profile.
- The webhook URL is blank or malformed.
- The selected account launches with a blank proxy and direct network access.
- The browser returns some cookies but not the full authenticated Zalo session.
- The downstream webhook expects `cookie` as an array while the tool accidentally serializes a single cookie string.
- The operator logs out in Chrome after a previous successful export.
- Chrome is reachable for click automation but the session capture adapter cannot read cookies.
- The account already has an active ZCA listener elsewhere and the browser/web session causes listener shutdown.
- The app restarts after a sync failure and must still remember prior sync status and reusable `imei`.

## Success Metrics

- Operators can bootstrap a `zca-js` listener from an already logged-in Chrome account without manually copying cookies.
- Launch and sync results are clearly separated so browser launch remains usable even when webhook delivery fails.
- The session export flow introduces no direct cookie editing surface in the GUI.
- The new integration fits existing clean architecture boundaries and remains testable.
