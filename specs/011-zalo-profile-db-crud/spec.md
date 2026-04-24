# Feature Specification: Zalo Profile Database CRUD

## Status

Proposed.

## Summary

Implement profile persistence against the new `profiles` database table so the application can add, save, edit, load, select, and delete reusable Chrome profile records from MariaDB instead of relying only on the local JSON profile library.

This feature is focused on the `Profiles` business flow:

- add a new profile
- save a profile
- edit and update a saved profile
- load saved profiles from the database

## Problem Statement

The current `Profiles` tab and `ZaloProfileManagerUseCase` work with a JSON-backed store. After introducing the new database contract in `schema.sql`, the profile CRUD flow still has no defined behavior for SQL-backed persistence.

Without a dedicated profile CRUD spec for the database flow:

- the UI behavior may drift from current profile-manager rules
- repository implementation may not preserve current validation behavior
- profile add/edit semantics may become ambiguous once SQL is introduced

The app already has clear profile behavior in code. This feature defines how that behavior must map to the new `profiles` table.

## Goals

- Persist reusable Chrome profiles in the `profiles` table.
- Preserve the current business behavior for add, save, and edit.
- Keep profile validation in application use cases, not in Tkinter event handlers.
- Support loading and selecting saved profiles from the database-backed store.
- Keep repository boundaries aligned with clean architecture.

## Non-Goals

- Migrating all existing JSON profile data automatically in this feature.
- Implementing account or click-target database CRUD in this feature.
- Changing how Chrome launch works.
- Redesigning the `Profiles` tab layout.

## Primary Users

### Operator

Needs to create, update, and reuse Chrome profiles from the `Profiles` tab with the same behavior as today.

### Maintainer

Needs a clean database-backed profile repository that preserves use-case validation and avoids pushing SQL into the GUI layer.

### Integrator

Needs profile data to exist in MariaDB so other services or tools can inspect or synchronize it later.

## User Stories

1. As an operator, I want to add a new Chrome profile so I can reuse it later from the GUI.
2. As an operator, I want saving a profile to write it into the database instead of only local JSON.
3. As an operator, I want to edit an existing profile without creating a duplicate record.
4. As a maintainer, I want profile validation to remain in the use case so the GUI stays thin.
5. As an integrator, I want saved profiles to live in the `profiles` table with stable IDs and timestamps.

## Current Business Behavior to Preserve

From the current `ZaloProfileManagerUseCase`:

- a profile requires `name`, `chrome_executable`, `profile_path`, and `target_url`
- `name` must be unique
- `profile_path` must be unique
- edit updates an existing record when `profile_id` is supplied
- create inserts a new record when `profile_id` is missing
- after save, the saved profile becomes the selected profile
- loading profile state returns all profiles plus the selected profile ID

## Data Model Mapping

### Source Table: `profiles`

The feature MUST use the `profiles` table created by `schema.sql`.

Column mapping:

- application `SavedChromeProfile.id` -> `profiles.id`
- application `SavedChromeProfile.name` -> `profiles.name`
- application `SavedChromeProfile.chrome_executable` -> `profiles.chrome_executable`
- application `SavedChromeProfile.profile_path` -> `profiles.profile_path`
- application `SavedChromeProfile.target_url` -> `profiles.target_url`

Supporting metadata:

- `created_at`
- `updated_at`

## Functional Requirements

### Load and State

- FR-001: The profile management flow MUST load saved profile records from the `profiles` table.
- FR-002: Loaded records MUST map into the existing application profile model shape.
- FR-003: If the database returns no profile rows, the profile manager state MUST load as empty without crashing.
- FR-004: The profile manager SHOULD still expose discovered default Chrome executable and profile root values for the form even when the database is empty.

### Add and Save

- FR-005: Saving a new profile without `profile_id` MUST insert a new row into `profiles`.
- FR-006: The inserted row MUST contain `id`, `name`, `chrome_executable`, `profile_path`, and `target_url`.
- FR-007: The save flow MUST keep the current validation rules for executable path, profile path, and target URL.
- FR-008: The save flow MUST reject a duplicate profile `name`.
- FR-009: The save flow MUST reject a duplicate `profile_path`.
- FR-010: After a successful insert, the saved profile MUST become the selected profile in returned state.

### Edit and Update

- FR-011: Saving a profile with an existing `profile_id` MUST update the matching row instead of inserting a new one.
- FR-012: Editing a profile MUST preserve its `id`.
- FR-013: Editing a profile MUST still enforce unique `name` across other records.
- FR-014: Editing a profile MUST still enforce unique `profile_path` across other records.
- FR-015: Updating a profile MUST refresh `updated_at`.
- FR-016: If the requested `profile_id` does not exist during update, the operation MUST fail with an actionable profile-not-found error instead of silently inserting a new row.

### Selection and Deletion

- FR-017: The profile manager MUST support selecting one saved profile after database load.
- FR-018: The selected profile ID SHOULD remain application-managed and MUST stay consistent with the loaded result set.
- FR-019: Deleting a saved profile MUST remove the corresponding row from `profiles`.
- FR-020: Deleting a selected profile MUST recalculate the selected profile ID consistently with current behavior.

### Repository Boundaries

- FR-021: SQL access for profile CRUD MUST live behind an application port or equivalent repository boundary.
- FR-022: Tkinter callbacks MUST NOT issue SQL statements directly.
- FR-023: The use case MUST remain responsible for business validation and conflict detection.
- FR-024: Database-specific errors SHOULD be translated into application-level persistence or validation errors before reaching the GUI.

### Timestamps and Identity

- FR-025: Application-generated profile IDs MUST remain compatible with the `profiles.id` schema type.
- FR-026: New profile rows MUST populate `created_at` and `updated_at` through the database defaults or equivalent SQL behavior.
- FR-027: Update operations MUST NOT overwrite `created_at`.

## Non-Functional Requirements

- NFR-001: The profile CRUD implementation SHOULD preserve current user-visible behavior of the `Profiles` tab.
- NFR-002: The implementation SHOULD remain testable without starting the Tkinter GUI.
- NFR-003: Database persistence failures SHOULD surface as actionable errors rather than generic crashes.
- NFR-004: The implementation SHOULD allow future coexistence of JSON migration tooling without coupling migration logic into the use case.

## Acceptance Scenarios

### Scenario 1: Add a New Profile

- Given the database is reachable
- And no existing profile uses the same name or profile path
- When the operator enters a valid profile and clicks save
- Then the app inserts a row into `profiles`
- And the returned state includes that new profile as the selected one

### Scenario 2: Edit an Existing Profile

- Given a saved profile row already exists in `profiles`
- When the operator edits the profile name or path and clicks save
- Then the app updates that same row
- And the profile keeps the same `id`
- And `updated_at` changes

### Scenario 3: Reject Duplicate Name

- Given one saved profile named `Work`
- When the operator tries to save another profile named `Work`
- Then the app rejects the save with a conflict error
- And no second row is inserted

### Scenario 4: Reject Duplicate Profile Path on Edit

- Given two saved profiles exist with different paths
- When the operator edits one profile to use the other profile's path
- Then the app rejects the update with a conflict error

### Scenario 5: Load Profiles After App Restart

- Given one or more profiles are already stored in `profiles`
- When the application loads profile state
- Then the `Profiles` tab shows those saved profiles
- And the form can load a selected profile into edit mode

## Edge Cases

- The database is unavailable during profile load.
- The database is unavailable during save or delete.
- A row exists in `profiles` with invalid or partial data.
- The saved selected profile ID no longer exists after a delete.
- The operator tries to update a profile ID that was deleted by another process.
- The database enforces uniqueness before the application catches a conflict.

## Success Metrics

- Operators can add and edit profiles with the same behavior they already expect from the current GUI.
- The `profiles` table becomes the authoritative persistence layer for reusable Chrome profiles.
- The database-backed repository can be implemented without leaking SQL logic into Tkinter code.
