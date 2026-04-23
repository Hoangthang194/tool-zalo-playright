# Implementation Plan: Zalo Profile-Proxy Account Manager

## Overview

Convert the current Zalo GUI into a tabbed desktop manager where:

- `Profiles` is a reusable Chrome profile library only
- `Zalo Accounts` is the launch surface that combines a linked profile with a proxy

Launch ownership moves to `Zalo Accounts` so proxy-aware launching is defined by the account record instead of the raw profile record.

## Technical Context

| Area | Decision |
| --- | --- |
| Language | Python 3.11+ |
| GUI Toolkit | Tkinter with `ttk.Notebook` for tabs |
| Existing Tab | Reuse the current profile manager shell as `Profiles`, but reduce it to profile CRUD only |
| New Data Types | Saved Zalo account entries with linked profile and proxy |
| Persistence | JSON-backed local store under the existing app data folder |
| Launch Model | Launch selected Zalo account from `Zalo Accounts` using linked profile plus proxy |
| Architecture | Clean architecture with domain models, application use cases, infrastructure store, launcher adapter, and Tkinter interface |

## Constitution Check

### Spec Before Behavior Change

This feature is documented under `specs/005-zalo-tabbed-cookie-account-manager/` before implementation.

### Clean Architecture Boundaries

Profile CRUD, account CRUD, and account launch orchestration remain outside Tkinter callbacks. The GUI only binds controls to use cases and refreshes view state.

### Workflow-First Automation

This feature does not change the workflow-driven automation engine.

### Safe, Deterministic Execution

Linked profile selection is validated before persistence. Invalid or partial persistence payloads should degrade safely instead of crashing the GUI.

### Testability and Observable Outcomes

Account CRUD and JSON mapping are testable without opening the real GUI.

### Incremental Delivery

Start with profile CRUD plus account CRUD and proxy-aware account launch. Do not bundle cookie injection, login automation, or post-login workflows into this change.

## Architecture

### Domain Layer

- Keep a profile library model for saved Chrome profile definitions.
- Keep a workspace model for saved Zalo account entries linked to saved profiles.

### Application Layer

- Keep a management use case for loading, selecting, saving, and deleting profile records.
- Keep a management use case for loading, selecting, saving, and deleting account records.
- Add an account launch use case or equivalent orchestration path that composes linked profile data with proxy settings.
- Keep validation rules centralized in use cases.

### Infrastructure Layer

- Keep a JSON-backed store for the account workspace.
- Keep persistence tolerant of partially invalid JSON entries by skipping invalid records when reasonable.
- Reuse or extend the Chrome launcher adapter so proxy arguments can be applied during account launch.

### Interface Layer

- Keep the current profile manager UI inside a `Profiles` tab, but remove direct launch controls from that tab.
- Add a `Zalo Accounts` tab with list/detail CRUD controls plus launch controls.
- Present saved profile names in operator-friendly form.
- Keep single-line inputs visually aligned with matching height.

## Key Decisions

1. Use `ttk.Notebook` because the requested interaction is explicitly tab-based.
2. Keep profiles as reusable definitions and make accounts the actual launch target because proxy belongs to launch context.
3. Store account-proxy entries locally in JSON so the feature works offline and matches the profile manager style.
4. Represent linked profiles in accounts as saved-entry IDs rather than duplicated path data.
5. Derive operator-facing account labels from the linked profile so the form can stay minimal.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Moving launch out of `Profiles` breaks operator expectations | High | Make tab responsibilities explicit in the UI and keep account launch affordance obvious |
| Stale profile references appear in account records | Medium | Store IDs, show empty fallback when missing, and keep editing possible |
| JSON file becomes partially invalid | Medium | Load defensively and skip invalid entries |
| Proxy-aware launch requires launcher changes | Medium | Extend launch orchestration behind existing application and infrastructure boundaries |
| Tkinter single-line widgets render with uneven heights | Medium | Centralize field builders and apply consistent spacing/style rules |

## Validation Strategy

### Automated

- Test account CRUD in the use case.
- Test JSON persistence round-trip for account entries.
- Test account launch orchestration using linked profile plus proxy.
- Smoke test that linked profile IDs are preserved.

### Manual

- Open the GUI and verify the two tabs render.
- Verify the `Profiles` tab is limited to profile CRUD and no longer owns launch.
- Save, edit, delete, and launch at least one account entry with a linked profile and proxy.
- Verify launch from `Zalo Accounts` opens Chrome with the linked profile and target URL.
- Verify account-form single-line fields look aligned in height.
