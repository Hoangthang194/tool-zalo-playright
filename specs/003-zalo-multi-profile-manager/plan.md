# Implementation Plan: Zalo Multi-Profile Chrome Manager

## Overview

Extend the existing Zalo Chrome launcher into a multi-profile manager that stores multiple saved Chrome profile entries as full profile folder paths, such as `...\User Data\Profile 1`, and launches the selected one directly into `https://chat.zalo.me`.

## Technical Context

| Area | Decision |
| --- | --- |
| Language | Python 3.11+ |
| Packaging | `pyproject.toml` with `setuptools` |
| GUI Toolkit | Tkinter |
| Browser Launching | Reuse subprocess-based Chrome launcher |
| Primary Interface | Desktop GUI with saved-profile list and edit form |
| Persistence | JSON-based multi-profile settings store |
| Saved Profile Inputs | Friendly name, Chrome executable path, full Chrome profile folder path |
| Default Target URL | `https://chat.zalo.me` |
| Backward Compatibility | Convert legacy `user_data_dir + profile_directory` settings into one full profile path when possible |
| Supported OS | Windows-first documentation, cross-platform-friendly code where practical |
| Architecture | Clean architecture with domain, application, infrastructure, interfaces |

## Constitution Check

### Spec Before Behavior Change

This feature is documented under `specs/003-zalo-multi-profile-manager/` before implementation.

### Clean Architecture Boundaries

Saved-profile CRUD, validation rules, migration logic, and launch orchestration remain outside GUI event handlers. GUI code should render and invoke use cases only.

### Workflow-First Automation

This feature does not change the workflow-driven automation engine. It extends the dedicated Zalo launcher path only.

### Safe, Deterministic Execution

Saved profiles are validated before launch, selection is explicit, and invalid saved entries fail before process creation.

### Testability and Observable Outcomes

Profile persistence, migration, and launch orchestration are testable without opening a real browser. Manual validation can confirm that a selected saved profile opens the expected Chrome session.

### Incremental Delivery

Implementation starts with a small saved-profile library and selected-profile launch flow, then hardens with GUI convenience and diagnostics.

## Architecture

### Domain Layer

- `SavedChromeProfile` models one reusable Zalo launch target using a full Chrome profile folder path.
- `SavedProfileLibrary` models the stored collection and selected-profile metadata.
- Validation rules cover required fields, unique names, and exact-path uniqueness.

### Application Layer

- A profile-library use case set supports list, create, update, delete, select, and launch operations.
- Launch behavior derives `user_data_dir` from the profile path parent folder and `profile_directory` from the profile folder name.
- Single-profile launch on Windows reuses the first `4x2` grid cell as its default window bounds so the browser does not open at an arbitrary restored size.
- Repeated single-profile launches on Windows choose the next available `4x2` grid cell based on already visible Chrome windows so successive launches land side by side.
- Ports abstract multi-profile persistence and Chrome process launching.

### Infrastructure Layer

- A JSON repository persists the full saved-profile library.
- Legacy settings migration converts the older single-profile launcher settings into one saved full profile path.
- Existing Chrome discovery and subprocess launcher adapters are reused.

### Interfaces Layer

- The Tkinter GUI is expanded to include a saved-profile list, edit form, selection state, and launch actions.
- The GUI accepts one full profile path field such as `...\User Data\Profile 1` instead of separate `user_data_dir` and `profile_directory` inputs for multi-profile management.

## Repository Structure

```text
src/
  browser_automation/
    application/
    domain/
    infrastructure/
    interfaces/
examples/
tests/
.specify/
specs/
```

## Key Decisions

1. Store the full Chrome profile folder path because that matches the operator's mental model and Windows file paths directly.
2. Derive Chrome launch arguments from that full path rather than asking the operator to split the same information into two fields.
3. Keep requesting a new Chrome window on launch to reduce tab reuse behavior.
4. Support migration from the older single-profile settings format by composing one full profile path from existing settings.
5. Keep one selected profile at a time in the GUI instead of attempting bulk launching.
6. Reuse the first `4x2` grid cell as the default single-profile launch size on Windows for consistent operator expectations.
7. When launching one profile at a time, place each newly opened Chrome window into the next visible grid cell instead of always reusing cell one.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Operator selects the `User Data` root instead of a real profile folder | Wrong launch arguments | Validate that the selected folder looks like an actual Chrome profile directory |
| Duplicate saved paths create ambiguity | Wrong profile may be opened | Enforce exact-path uniqueness |
| GUI becomes cluttered as profile count grows | Slower operator workflow | Use a clear list layout, selection state, and compact edit form |
| Legacy settings fail to migrate cleanly | User confusion | Convert `user_data_dir + profile_directory` into one full path explicitly and test it |
| Launch code diverges from saved model | Higher maintenance cost | Keep launch derivation centralized in the multi-profile use case |

## Validation Strategy

### Automated

- Unit test saved-profile library CRUD behavior.
- Unit test persistence mapping and migration from the single-profile settings format.
- Unit test selected-profile launch orchestration using fakes around the Chrome launcher.
- Unit test that single-profile launches receive deterministic window bounds when the Windows window arranger is available.
- Unit test that repeated single-profile launches choose the next grid cell instead of overlapping the prior window.
- Unit test duplicate-name and duplicate-path validation rules.

### Manual

- Add two or more saved profiles using full paths such as `...\User Data\Profile 1` and launch each one from the GUI.
- Edit a saved profile and verify the next launch uses the updated path.
- Delete a saved profile and verify it is removed without affecting others.
- Verify first-run migration from the single-profile launcher settings.

## Out of Scope for This Feature

- Launching all saved profiles in one action
- Creating new Chrome profiles on disk automatically
- Zalo message automation or data extraction
- Remote synchronization of profile libraries between machines
