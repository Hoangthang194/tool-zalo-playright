# Feature Specification: Zalo Manual Click Target Testing

## Status

Implemented.

## Summary

Adjust the Zalo GUI so launching a saved account only opens Chrome and prepares follow-up tooling. Saved click targets in `Class Manage` must no longer auto-run during account launch. Element clicking must happen only when the operator explicitly uses `Test Element`.

## Problem Statement

The current launch flow opens Chrome and immediately executes saved click targets. That surprises operators who expect launch to only open the browser. It also makes debugging harder because the browser state changes before the operator chooses to test a selector.

## Goals

- Keep `Launch Account` focused on opening Chrome with the selected profile and proxy.
- Preserve remote debugging availability for follow-up selector testing.
- Make `Test Element` the only explicit UI action that performs element clicking.
- Update GUI copy so the operator is not told that selectors auto-run on launch.

## Non-Goals

- Removing saved click target persistence.
- Removing the `Class Manage` tab.
- Replacing Playwright-based selector testing.

## Functional Requirements

- FR-001: Launching a saved Zalo account MUST NOT execute saved click targets automatically.
- FR-002: Launching a saved Zalo account SHOULD still expose a remote debugging port when selector testing support is available.
- FR-003: The `Class Manage` tab MUST keep saved click targets available for explicit manual testing.
- FR-004: Clicking `Test Element` MUST execute the selected selector against the active launched browser session.
- FR-005: Operator-facing launch status messages MUST NOT claim that saved targets were clicked during launch.
- FR-006: Operator-facing helper text MUST describe click targets as manual test actions, not auto-run launch actions.

## Acceptance Scenarios

### Scenario 1: Launch Does Not Click

- Given a saved account exists
- And saved click targets also exist
- When the operator clicks `Launch Account`
- Then Chrome opens with the selected profile and proxy
- And no saved click target is executed automatically

### Scenario 2: Manual Test Element Clicks

- Given an account has already been launched successfully
- And a saved click target is selected in `Class Manage`
- When the operator clicks `Test Element`
- Then the app attaches to the launched Chrome session
- And executes only that explicit selector test

## Success Metrics

- Operators can launch Chrome without unexpected UI interactions.
- Selector testing happens only through the explicit `Test Element` action.
