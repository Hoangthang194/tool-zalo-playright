# Implementation Plan: Zalo Chrome Profile GUI Launcher

## Overview

Implement a dedicated Python desktop GUI that launches real Google Chrome with a selected Chrome user profile and opens `https://chat.zalo.me` directly. This feature is intentionally separate from the repository's workflow-driven automation path: it provides a focused launcher experience for Zalo operators while preserving clean architecture boundaries and explicit validation.

## Technical Context

| Area | Decision |
| --- | --- |
| Language | Python 3.11+ |
| Packaging | `pyproject.toml` with `setuptools` |
| GUI Toolkit | Tkinter for the baseline desktop interface |
| Browser Launching | Native Chrome process launch via `subprocess` |
| Primary Interface | Desktop GUI launcher |
| Runtime Inputs | Chrome executable path, user data directory, profile directory |
| Default Target URL | `https://chat.zalo.me` |
| Settings Persistence | Lightweight JSON settings file at a documented location |
| Supported OS | Windows-first documentation, cross-platform-friendly validation where practical |
| Architecture | Clean architecture with domain, application, infrastructure, interfaces |

## Constitution Check

### Spec Before Behavior Change

This feature is documented under `specs/002-zalo-chrome-profile-gui/` before implementation.

### Clean Architecture Boundaries

Launch configuration validation and orchestration remain outside GUI toolkit code. Chrome process discovery and process launching remain infrastructure concerns.

### Workflow-First Automation

This feature does not introduce new browser automation behavior. It is a direct launcher for a fixed destination and intentionally does not reuse the JSON workflow engine. The existing workflow-driven path remains unchanged.

### Safe, Deterministic Execution

The launcher validates executable and profile inputs before process creation, builds explicit Chrome arguments, and surfaces actionable errors when launch cannot start.

### Testability and Observable Outcomes

Validation and argument construction are testable without opening a browser. Manual validation can confirm that Chrome launches with the expected profile and destination URL.

### Incremental Delivery

The feature is split into a small baseline launcher first, followed by hardening around profile discovery, duplicate-click protection, and operator convenience.

## Architecture

### Domain Layer

- `ChromeLaunchConfig` models the selected Chrome executable, user data directory, profile directory, and target URL.
- `ChromeLaunchResult` models whether the launch request started successfully and what configuration was used.
- Domain validation errors define invalid path, missing profile, and invalid configuration cases.

### Application Layer

- A launch use case validates configuration, requests Chrome launch through a port, and returns a result for the GUI.
- Optional settings-loading logic provides a remembered last-used configuration without coupling persistence to the GUI.
- Ports abstract Chrome discovery, settings persistence, and process launch execution.

### Infrastructure Layer

- A Chrome discovery adapter locates installed Google Chrome on Windows and supports explicit path override.
- A process launcher adapter builds and executes the Chrome command with `--user-data-dir`, `--profile-directory`, and the fixed Zalo URL.
- A JSON settings adapter persists last-used launcher configuration in a documented file path.

### Interfaces Layer

- A Tkinter GUI presents fields for Chrome path, user data directory, profile directory, current target URL, and launch status.
- The GUI handles browse dialogs, in-progress state, and error display, but delegates validation and launching to application services.

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

1. Use Tkinter for the baseline launcher because the repository already includes a Tkinter GUI path and this avoids adding heavy GUI dependencies.
2. Launch Chrome with `subprocess` instead of Playwright because the goal is to reuse a persistent Chrome profile, not to automate browser actions.
3. Model `user_data_dir` and `profile_directory` as separate inputs because Chrome uses both values explicitly at launch time.
4. Treat successful process creation as launch success even if `chat.zalo.me` later requires manual login or encounters network issues.
5. Persist the last-used launcher configuration in a lightweight JSON file so repeated daily launches stay fast for operators.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Chrome executable cannot be auto-discovered | Launcher cannot start | Allow explicit executable override and validate before launch |
| Selected profile is invalid or missing | Launch fails or opens wrong session | Validate profile directory existence before process creation |
| Profile is locked by an existing Chrome session | Chrome may refuse requested profile behavior | Surface actionable launch diagnostics and document operator expectations |
| GUI code absorbs validation logic | Maintainability degrades | Keep validation and launch orchestration in application/domain layers |
| Remembered settings become stale | Confusing startup errors | Revalidate persisted paths at launch and show clear correction prompts |

## Validation Strategy

### Automated

- Unit test configuration validation rules.
- Unit test Chrome launch argument construction.
- Unit test use case orchestration with fake discovery, launcher, and settings adapters.

### Manual

- Launch Zalo with a valid existing Chrome profile.
- Verify the app opens `https://chat.zalo.me`.
- Verify invalid executable and missing profile cases fail before process launch.
- Verify remembered settings repopulate the GUI when enabled.

## Out of Scope for This Feature

- Sending Zalo messages automatically
- Reading conversations or contacts automatically
- Workflow-file-based execution for the launcher path
- Multi-profile parallel orchestration
- Authentication/session management beyond reusing the chosen Chrome profile
