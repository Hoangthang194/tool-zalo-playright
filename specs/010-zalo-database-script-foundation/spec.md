# Feature Specification: Zalo Database Script Foundation

## Status

Proposed.

## Summary

Create a new database script that matches the current application structure instead of the older mixed schema. The new schema must persist:

- Chrome `profiles`
- `zalo_accounts`
- `Class Manage` click targets scoped to each account
- `messages` with only the required fields: `msgId`, `fromGroupId`, `toGroupId`, `fromAccountId`, and `content`

The goal of this feature is to define the database contract first so later implementation can replace or complement JSON persistence cleanly.

## Problem Statement

The current project stores operational data in local JSON files, while the checked `schema.sql` represents an older MariaDB schema that does not match the current GUI structure closely enough.

Current application structure:

- `Profiles` is a reusable Chrome profile library
- `Zalo Accounts` links one profile to one proxy and launch context
- `Class Manage` stores click targets used by `Test Element`

Requested changes:

- database-first script aligned with the current structure
- click targets stored per account, not as one global library
- a simplified `messages` table with a smaller field set than the older schema

Without a new schema spec, later implementation risks mixing old naming, old relationships, and current UI behavior into an inconsistent persistence model.

## Goals

- Define a new SQL script for database creation that matches the current product structure.
- Separate reusable Chrome profiles from Zalo accounts at the database level.
- Scope saved click targets to a specific Zalo account.
- Define a minimal `messages` table with the exact fields requested by the operator.
- Keep the schema compatible with future clean-architecture repository adapters.

## Non-Goals

- Implementing the live database repository in this feature.
- Migrating existing JSON data automatically in this feature.
- Adding full message-forwarding workflow logic.
- Defining every future analytics or audit table up front.
- Reusing the older `accounts`, `zalo_groups`, or forwarding tables if they do not fit the current app model.

## Primary Users

### Operator

Needs a database structure that reflects how the GUI is already organized: profiles, linked accounts, and account-specific click targets.

### Maintainer

Needs a stable schema contract before replacing JSON stores with SQL-backed repositories.

### Integrator

Needs a predictable script that can be applied to a fresh MariaDB database for later backend integration.

## User Stories

1. As an operator, I want reusable Chrome profiles stored separately from Zalo accounts so one profile record remains a first-class entity.
2. As an operator, I want each Zalo account to own its own click targets so selectors do not leak across unrelated accounts.
3. As an operator, I want messages stored with the exact fields I actually care about so the database stays simple.
4. As a maintainer, I want the schema to map cleanly to the current GUI tabs so repository implementation is straightforward.
5. As an integrator, I want one SQL creation script that I can apply to create the required tables and constraints in a fresh database.

## Data Model

### Table: `profiles`

Purpose: persist reusable Chrome profile definitions.

Required fields:

- `id`
- `name`
- `chrome_executable`
- `profile_path`
- `target_url`
- `created_at`
- `updated_at`

Rules:

- `id` MUST be the application-level profile identifier.
- `name` MUST be unique for operator clarity.
- `profile_path` SHOULD be unique because one Chrome profile folder should map to one saved profile record.

### Table: `zalo_accounts`

Purpose: persist launchable Zalo account records linked to one profile.

Required fields:

- `id`
- `name`
- `profile_id`
- `proxy`
- `created_at`
- `updated_at`

Rules:

- each account MUST reference exactly one saved profile
- `profile_id` MUST be a foreign key to `profiles.id`
- duplicate account records for the same `profile_id` SHOULD be prevented to preserve current application behavior

### Table: `account_click_targets`

Purpose: persist `Class Manage` targets under one specific account.

Required fields:

- `id`
- `account_id`
- `name`
- `selector_kind`
- `selector_value`
- `upload_file_path`
- `created_at`
- `updated_at`

Rules:

- `account_id` MUST be a foreign key to `zalo_accounts.id`
- a click target MUST belong to exactly one account
- target names SHOULD be unique within one account scope
- the same target name MAY exist on different accounts

### Table: `messages`

Purpose: persist simplified message records.

Required fields:

- `msgId`
- `fromGroupId`
- `toGroupId`
- `fromAccountId`
- `content`

Recommended supporting fields:

- `created_at`

Rules:

- `msgId` MUST be the primary key or otherwise uniquely constrained
- `fromAccountId` SHOULD reference `zalo_accounts.id`
- `fromGroupId` and `toGroupId` MAY remain plain string fields in this iteration unless a group table is introduced later

## Functional Requirements

### Schema Contract

- FR-001: The repository MUST define a new SQL creation script instead of extending the checked legacy schema in place.
- FR-002: The script MUST create a `profiles` table for reusable Chrome profile records.
- FR-003: The script MUST create a `zalo_accounts` table for launchable account records linked to profiles.
- FR-004: The script MUST create an `account_click_targets` table scoped to `zalo_accounts`.
- FR-005: The script MUST create a `messages` table containing `msgId`, `fromGroupId`, `toGroupId`, `fromAccountId`, and `content`.
- FR-006: The script MUST define primary keys for all persisted entities.
- FR-007: The script MUST define foreign-key integrity from `zalo_accounts.profile_id` to `profiles.id`.
- FR-008: The script MUST define foreign-key integrity from `account_click_targets.account_id` to `zalo_accounts.id`.
- FR-009: The script SHOULD define foreign-key integrity from `messages.fromAccountId` to `zalo_accounts.id`.
- FR-010: The script SHOULD include `created_at` and `updated_at` timestamps on tables that model editable application records.

### Current-Structure Alignment

- FR-011: The schema MUST reflect the current GUI separation between `Profiles` and `Zalo Accounts`.
- FR-012: The schema MUST NOT model click targets as one global library if the intended behavior is account-specific ownership.
- FR-013: The schema SHOULD preserve the current one-account-per-profile rule unless a future spec relaxes that behavior explicitly.
- FR-014: The schema MUST store selector metadata needed by `Class Manage`, including selector kind, selector value, and optional upload file path.
- FR-015: The schema MUST keep message persistence minimal and MUST NOT require the older forwarding tables for this feature.

### Script Delivery

- FR-016: The feature output MUST include one operator-usable SQL script file definition in the spec/plan/task set.
- FR-017: The SQL script SHOULD target MariaDB because the checked `schema.sql` is MariaDB-oriented.
- FR-018: The script SHOULD use names that are consistent with current Python models and use cases.

## Non-Functional Requirements

- NFR-001: The schema design SHOULD be simple enough to implement through clean-architecture repository ports later.
- NFR-002: The schema SHOULD avoid unnecessary legacy tables that are unrelated to the current GUI structure.
- NFR-003: Constraints SHOULD favor deterministic operator behavior over loosely validated data.
- NFR-004: The script SHOULD be idempotent enough for repeated application in development environments, for example through `CREATE TABLE IF NOT EXISTS` where appropriate.

## Acceptance Scenarios

### Scenario 1: Create a Fresh Database

- Given a fresh MariaDB instance
- When the operator applies the new SQL script
- Then the database contains tables for `profiles`, `zalo_accounts`, `account_click_targets`, and `messages`
- And the key relationships between profiles, accounts, and click targets exist

### Scenario 2: Save an Account-Specific Click Target

- Given one saved profile exists
- And one saved Zalo account links to that profile
- When the application later persists a click target for that account
- Then the target is stored under `account_click_targets`
- And the record references only that account

### Scenario 3: Store a Simplified Message

- Given one saved Zalo account exists
- When the application later writes a message record
- Then the row contains `msgId`, `fromGroupId`, `toGroupId`, `fromAccountId`, and `content`
- And the message does not require the older forwarding schema to exist

## Edge Cases

- A profile is deleted while one or more accounts still reference it.
- An account is deleted while click targets still reference it.
- Two profiles try to reuse the same `profile_path`.
- Two click targets under the same account try to reuse the same name.
- A message references an account that no longer exists.
- Existing JSON data uses IDs that must remain compatible with future SQL inserts.

## Success Metrics

- The new schema names and relationships map directly to the current app structure without legacy ambiguity.
- A future repository implementation can persist profiles, accounts, account-scoped click targets, and messages without inventing new tables.
- The message table stays limited to the requested field set plus minimal supporting metadata.
