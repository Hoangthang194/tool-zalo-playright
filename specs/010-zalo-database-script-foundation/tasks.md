# Tasks: Zalo Database Script Foundation

## Phase 1: Specification

- [ ] T001 Add `spec.md`, `plan.md`, and `tasks.md` for the new database script foundation.
- [ ] T002 Confirm the SQL target is MariaDB and that the script replaces, rather than extends, the legacy conceptual schema.
- [ ] T003 Confirm the canonical table set: `profiles`, `zalo_accounts`, `account_click_targets`, and `messages`.

## Phase 2: Schema Design

- [ ] T004 Define the `profiles` table columns and constraints from the current profile manager model.
- [ ] T005 Define the `zalo_accounts` table columns and constraints from the current account manager model.
- [ ] T006 Define the `account_click_targets` table so click targets belong to one account.
- [ ] T007 Define the `messages` table with fields `msgId`, `fromGroupId`, `toGroupId`, `fromAccountId`, and `content`.
- [ ] T008 Define timestamp columns and primary-key strategy for all editable entities.
- [ ] T009 Define foreign-key behavior for profile-account, account-click-target, and message-account references.

## Phase 3: Script Authoring

- [ ] T010 Create a new SQL script file for database creation using the approved table structure.
- [ ] T011 Add idempotent create statements and required indexes or unique constraints.
- [ ] T012 Ensure the script does not depend on obsolete forwarding tables or the older group schema.

## Phase 4: Verification

- [ ] T013 Review the script against the current GUI structure: `Profiles`, `Zalo Accounts`, and account-specific `Class Manage`.
- [ ] T014 Review the script against the requested simplified message model.
- [ ] T015 Validate naming consistency between SQL tables and current Python concepts.

## Phase 5: Follow-Up Implementation Planning

- [ ] T016 Identify which current JSON stores would later map to `profiles` and `zalo_accounts`.
- [ ] T017 Identify the current click-target persistence path that would later move to `account_click_targets`.
- [ ] T018 Identify the repository ports and use cases that will need SQL-backed implementations in a later feature.
