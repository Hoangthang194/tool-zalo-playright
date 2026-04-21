# Implementation Plan: Zalo Tabbed Cookie and Account Manager

## Overview

Convert the current Zalo GUI into a tabbed desktop manager with separate areas for profile launching, cookie CRUD, and Zalo account CRUD.

## Technical Context

| Area | Decision |
| --- | --- |
| Language | Python 3.11+ |
| GUI Toolkit | Tkinter with `ttk.Notebook` for tabs |
| Existing Tab | Reuse the current profile manager as `Profiles` |
| New Data Types | Saved cookie entries and saved Zalo account entries |
| Persistence | JSON-backed local store under the existing app data folder |
| Architecture | Clean architecture with domain models, application use cases, infrastructure store, and Tkinter interface |

## Constitution Check

### Spec Before Behavior Change

This feature is documented under `specs/005-zalo-tabbed-cookie-account-manager/` before implementation.

### Clean Architecture Boundaries

Cookie and account CRUD plus persistence remain outside Tkinter callbacks. The GUI only binds controls to use cases and refreshes view state.

### Workflow-First Automation

This feature does not change the workflow-driven automation engine.

### Safe, Deterministic Execution

Cookie and account names are validated before persistence. Invalid or partial persistence payloads should degrade safely instead of crashing the GUI.

### Testability and Observable Outcomes

Cookie/account CRUD and JSON mapping are testable without opening the real GUI.

### Incremental Delivery

Start with local CRUD and persistence only. Do not bundle automatic Chrome cookie injection or login automation into this change.

## Architecture

### Domain Layer

- Add domain models for saved cookie entries, saved Zalo account entries, and a small combined library model.

### Application Layer

- Add a management use case for loading, selecting, saving, and deleting cookie and account records.
- Keep validation rules centralized in the use case.

### Infrastructure Layer

- Add a JSON-backed store for cookie and account libraries.
- Keep persistence tolerant of partially invalid JSON entries by skipping invalid records when reasonable.

### Interface Layer

- Wrap the current profile manager UI inside a `Profiles` tab.
- Add a `Cookies` tab with list/detail CRUD controls.
- Add a `Zalo Accounts` tab with list/detail CRUD controls.
- Use saved profile names and cookie names as operator-friendly choices where appropriate.

## Key Decisions

1. Use `ttk.Notebook` because the requested interaction is explicitly tab-based.
2. Store cookies and accounts locally in JSON so the feature works offline and matches the profile manager style.
3. Keep raw cookie payloads as text rather than forcing one cookie schema in this version.
4. Represent profile and cookie links in accounts as saved-entry IDs rather than duplicated names.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Tab refactor breaks the current profile manager flow | High | Keep the existing profile UI mostly intact inside the first tab |
| Cookie payloads are large and awkward in a normal entry widget | Medium | Use multi-line text controls |
| Stale profile or cookie references appear in account records | Medium | Store IDs, show empty fallback when missing, and keep editing possible |
| JSON file becomes partially invalid | Medium | Load defensively and skip invalid entries |

## Validation Strategy

### Automated

- Test cookie CRUD and account CRUD in the use case.
- Test JSON persistence round-trip for cookie and account entries.
- Smoke test that linked IDs are preserved.

### Manual

- Open the GUI and verify the three tabs render.
- Save, edit, and delete at least one cookie entry.
- Save, edit, and delete at least one account entry.
- Verify the `Profiles` tab still launches Chrome profiles correctly.
