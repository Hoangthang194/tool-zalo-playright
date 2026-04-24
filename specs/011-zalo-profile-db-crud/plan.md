# Implementation Plan: Zalo Profile Database CRUD

## Overview

Move profile CRUD persistence from the JSON profile library toward the MariaDB `profiles` table while preserving the current `Profiles` tab behavior and the existing `ZaloProfileManagerUseCase` business rules.

This feature covers:

- load profiles from DB
- add a profile
- save a profile
- edit/update a profile
- delete a profile

## Technical Context

| Area | Decision |
| --- | --- |
| Database | MariaDB |
| Target Table | `profiles` |
| Current Persistence | `JsonSavedProfileLibraryStore` |
| Future Persistence | SQL-backed profile store behind the existing application port |
| Use Case | `ZaloProfileManagerUseCase` |
| GUI Surface | `Profiles` tab in `zalo_app.py` |

## Constitution Check

### Spec Before Behavior Change

This feature is documented under `specs/011-zalo-profile-db-crud/` before implementation.

### Clean Architecture Boundaries

Profile CRUD remains in the application use case and repository port. The GUI keeps binding and status updates only.

### Workflow-First Automation

This feature does not change workflow execution logic.

### Safe, Deterministic Execution

Uniqueness and validation rules remain explicit and deterministic. Duplicate names and duplicate profile paths continue to fail predictably.

### Testability and Observable Outcomes

The repository adapter and use case can be tested without launching the GUI.

### Incremental Delivery

Start with profile CRUD only. Do not bundle account DB CRUD or click-target DB CRUD into this feature.

## Architecture

### Domain and Application

- Keep `SavedChromeProfile` and `SavedProfileLibrary` as the main application-facing models.
- Keep `SavedProfileLibraryStore` or replace it with an equivalent port that still serves the use case cleanly.
- Preserve current use-case validation for executable path, profile path, and fixed target URL.

### Infrastructure

- Add a MariaDB-backed profile store implementation for the `profiles` table.
- Map SQL rows into `SavedChromeProfile`.
- Translate SQL and connector failures into application persistence errors.

### Interface

- Keep the `Profiles` tab form and list behavior unchanged where possible.
- Avoid SQL-specific logic in Tkinter callbacks.

## Key Decisions

1. Reuse the existing profile management use case because the business rules already exist and are coherent.
2. Keep application-generated IDs instead of switching to auto-increment IDs, because the current code already expects string IDs.
3. Preserve uniqueness on both `name` and `profile_path` because current operator behavior depends on these constraints.
4. Fail updates for missing profile IDs rather than silently inserting, because edit semantics should stay explicit.

## Repository Strategy

### Read Path

- Select all rows from `profiles`
- Map them to `SavedChromeProfile`
- Return them as `SavedProfileLibrary`

### Insert Path

- Validate at the use-case layer first
- Insert a new row with application-generated `id`

### Update Path

- Confirm the target row exists
- Update mutable fields:
  - `name`
  - `chrome_executable`
  - `profile_path`
  - `target_url`

### Delete Path

- Delete by `id`
- Let the use case recalculate selected profile behavior

## Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| SQL uniqueness conflicts and use-case uniqueness checks diverge | High | Preserve both application checks and DB constraints |
| DB repository shape does not fit `SavedProfileLibraryStore` cleanly | Medium | Keep adapter behavior aligned with current port contract |
| Existing GUI assumes JSON store semantics | Medium | Preserve returned state shape and selection behavior |
| Partial or invalid rows in DB cause crashes | Medium | Load defensively and translate row problems into manageable outcomes |
| Missing selected-profile persistence in DB-backed flow creates UX drift | Medium | Keep selected-profile handling in application state until a dedicated DB selection strategy is specified |

## Validation Strategy

### Automated

- Test profile row mapping from SQL data to domain models.
- Test insert, update, and delete behavior through the repository adapter.
- Test duplicate name and duplicate path conflicts through the use case.
- Test update failure when the target profile ID does not exist.

### Manual

- Open the `Profiles` tab and add a new profile.
- Edit a saved profile and verify the change persists.
- Restart the app and verify profiles reload from DB.
- Try saving duplicate names and paths and verify operator-visible errors remain actionable.
