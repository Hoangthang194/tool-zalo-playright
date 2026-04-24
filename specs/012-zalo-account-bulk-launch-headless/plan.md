# Implementation Plan: Zalo Account Bulk Launch With Headless Option

## Overview

Add multi-selection and bulk launch to the `Zalo Accounts` tab, and introduce a launch-mode option for headless execution.

The implementation must preserve account ownership of launch context:

- linked profile
- proxy

while allowing one operator action to start several accounts together.

## Technical Context

| Area | Decision |
| --- | --- |
| Launch Surface | `Zalo Accounts` tab |
| Current Visible Launch | Existing account-launch use case with Chrome subprocess launch |
| New Batch Unit | Saved Zalo accounts, not saved profiles |
| Launch Modes | visible and headless |
| Headless Feasibility | May require a dedicated browser-launch adapter if the visible Chrome subprocess path is not sufficient |
| GUI Interaction | Multi-select account list plus one headless checkbox or equivalent |

## Constitution Check

### Spec Before Behavior Change

This feature is documented under `specs/012-zalo-account-bulk-launch-headless/` before implementation.

### Clean Architecture Boundaries

The GUI gathers selected accounts and launch mode only. Batch orchestration and headless-launch details remain in application and infrastructure layers.

### Workflow-First Automation

This feature affects the dedicated Zalo GUI launcher flow and does not change the generic workflow engine.

### Safe, Deterministic Execution

The batch must validate selected accounts before launch and return explicit success and failure details per account.

### Testability and Observable Outcomes

Visible and headless batch-launch results should be testable through use-case and adapter tests without launching the full GUI.

### Incremental Delivery

Start by defining batch-launch semantics and one headless option for the whole launch action. More granular per-account mode selection can come later if needed.

## Architecture

### Domain and Application

- Reuse saved account entities as the batch-launch unit.
- Add a batch-launch result model for per-account outcomes.
- Extend or add an account-launch use case that accepts:
  - multiple account IDs
  - launch mode

### Infrastructure

- Keep the visible launch path on the existing Chrome subprocess adapter where possible.
- Add or adapt a launch adapter for headless mode if the visible adapter cannot support hidden execution correctly.
- Keep mode-specific launch details behind infrastructure boundaries.

### Interface

- Update the account list to support multi-select.
- Add one headless control near the account launch action.
- Keep editing behavior safe when multiple accounts are selected.

## Key Decisions

1. Use `Zalo Accounts` as the batch-launch unit because accounts already own proxy-aware launch context.
2. Treat headless mode as a launch-mode switch for the current action instead of a permanent account property in the first version.
3. Preserve existing visible single-account launch behavior as the compatibility baseline.
4. Surface explicit operator messaging when headless mode limits follow-up UI actions such as manual selector testing.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Headless mode may not be technically equivalent to visible Chrome launch | High | Allow a separate adapter and document any feature gaps |
| Multi-select editing becomes ambiguous | Medium | Keep one primary selected account for editing and disable ambiguous destructive actions during multi-selection |
| Manual click-target testing may not work after headless launch | High | Surface clear operator messaging and keep the limitation explicit |
| Per-account proxy differences complicate batch launch | Medium | Launch each account independently inside one orchestrated batch result |
| Existing visible launch behavior regresses | High | Keep the single-account visible path intact and add regression coverage |

## Validation Strategy

### Automated

- Test batch account ordering by visible list order.
- Test that each launched account keeps its own linked profile and proxy.
- Test visible-mode batch result aggregation.
- Test headless-mode batch result aggregation.
- Test validation failure before batch launch begins.

### Manual

- Multi-select two or more saved accounts and verify one visible launch action starts them.
- Enable headless mode and verify the launch reports hidden execution.
- Verify single-account visible launch still works unchanged.
- Verify the UI communicates any manual-testing limitation after headless launch.
