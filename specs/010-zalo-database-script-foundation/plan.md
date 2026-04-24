# Implementation Plan: Zalo Database Script Foundation

## Overview

Define a new MariaDB database script aligned with the current application model:

- `profiles` for reusable Chrome profiles
- `zalo_accounts` for launchable account entries linked to profiles
- `account_click_targets` for `Class Manage` records owned by one account
- `messages` for simplified message persistence with the requested field set

This feature is schema-first. It establishes the SQL contract before any repository implementation replaces JSON storage.

## Technical Context

| Area | Decision |
| --- | --- |
| Database | MariaDB |
| Current Persistence | Local JSON files under app data |
| Future Direction | SQL-backed repositories behind application ports |
| Schema Source | New script, not a direct extension of the checked legacy `schema.sql` |
| Account-Target Relation | One account owns many click targets |
| Message Model | Minimal row with `msgId`, `fromGroupId`, `toGroupId`, `fromAccountId`, `content` |

## Constitution Check

### Spec Before Behavior Change

This feature is documented under `specs/010-zalo-database-script-foundation/` before implementation.

### Clean Architecture Boundaries

The schema plan maps to application concepts already present in use cases and domain models. SQL details stay outside Tkinter code.

### Workflow-First Automation

This feature does not change the workflow-driven browser automation engine.

### Safe, Deterministic Execution

Foreign keys and uniqueness rules are preferred where they preserve the current deterministic app behavior.

### Testability and Observable Outcomes

The SQL script can later be validated independently from the GUI.

### Incremental Delivery

Start with schema creation only. Repository migration and runtime SQL persistence come later.

## Architecture Mapping

### Profiles

- Map to the current reusable Chrome profile records.
- Preserve fields already used by the profile manager use case.

### Zalo Accounts

- Map to current account records that link one profile and one proxy.
- Preserve the current linked-profile ownership model.

### Account Click Targets

- Replace the current global click-target library model with an account-scoped model in SQL.
- Keep selector data and optional upload file path.

### Messages

- Introduce a simplified persistence table for future send/forward history.
- Keep group identifiers as string references in this phase unless a future group schema is specified.

## Key Decisions

1. Create a brand-new schema contract because the current `schema.sql` does not mirror the active GUI model closely enough.
2. Keep `profiles` and `zalo_accounts` separate because the application already treats them as separate concepts.
3. Scope click targets to accounts because the user explicitly wants `Class Manage` per account.
4. Keep `messages` intentionally small to avoid dragging older forwarding abstractions into the new contract.
5. Favor application-generated string IDs for entity tables to stay compatible with current Python models.

## Proposed Tables

### `profiles`

Suggested columns:

- `id VARCHAR(64) PRIMARY KEY`
- `name VARCHAR(255) NOT NULL UNIQUE`
- `chrome_executable TEXT NOT NULL`
- `profile_path TEXT NOT NULL`
- `target_url TEXT NOT NULL`
- `created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP`
- `updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP`

Suggested constraints:

- unique logical path constraint where practical

### `zalo_accounts`

Suggested columns:

- `id VARCHAR(64) PRIMARY KEY`
- `name VARCHAR(255) NOT NULL`
- `profile_id VARCHAR(64) NOT NULL`
- `proxy TEXT NOT NULL DEFAULT ''`
- `created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP`
- `updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP`

Suggested constraints:

- foreign key `profile_id -> profiles.id`
- optional unique constraint on `profile_id` to preserve one-account-per-profile behavior

### `account_click_targets`

Suggested columns:

- `id VARCHAR(64) PRIMARY KEY`
- `account_id VARCHAR(64) NOT NULL`
- `name VARCHAR(255) NOT NULL`
- `selector_kind VARCHAR(50) NOT NULL`
- `selector_value TEXT NOT NULL`
- `upload_file_path TEXT NOT NULL DEFAULT ''`
- `created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP`
- `updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP`

Suggested constraints:

- foreign key `account_id -> zalo_accounts.id`
- unique `(account_id, name)`

### `messages`

Suggested columns:

- `msgId VARCHAR(100) PRIMARY KEY`
- `fromGroupId VARCHAR(100)`
- `toGroupId VARCHAR(100)`
- `fromAccountId VARCHAR(64)`
- `content TEXT NOT NULL`
- `created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP`

Suggested constraints:

- optional foreign key `fromAccountId -> zalo_accounts.id` with `ON DELETE SET NULL`

## Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Legacy schema and new schema overlap conceptually | High | Treat this feature as a new schema contract, not an in-place patch |
| Future repository code may still assume global click targets | High | Explicitly document account ownership for click targets in spec and plan |
| Message requirements may expand later | Medium | Keep the table minimal now and allow additive future specs |
| Existing JSON IDs may not match SQL assumptions | Medium | Keep entity IDs string-based and application-controlled |
| Unique profile/account rules may later need loosening | Medium | Document current rule as intentional and revisitable |

## Validation Strategy

### Automated Later

- Validate script creation against a MariaDB test database.
- Validate foreign-key behavior for account/profile and click-target/account relationships.
- Validate uniqueness rules for profile names and account-scoped click target names.

### Manual for This Planning Feature

- Review that every current GUI concept has one clear table owner.
- Review that `Class Manage` is explicitly scoped per account.
- Review that `messages` contains the exact requested business fields.
- Review that no unused legacy forwarding tables are required by this spec.
