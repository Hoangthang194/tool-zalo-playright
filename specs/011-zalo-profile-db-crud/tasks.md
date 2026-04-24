# Tasks: Zalo Profile Database CRUD

## Phase 1: Spec and Contract

- [ ] T001 Add `spec.md`, `plan.md`, and `tasks.md` for database-backed profile CRUD.
- [ ] T002 Confirm the `profiles` table in `schema.sql` is the authoritative persistence target.
- [ ] T003 Confirm current use-case behavior that must be preserved for add, save, edit, select, and delete.

## Phase 2: Repository Design

- [ ] T004 Define the SQL-backed profile repository/adapter contract against the existing application port.
- [ ] T005 Define row-to-domain mapping for `SavedChromeProfile`.
- [ ] T006 Define error translation from MariaDB failures into application-level persistence errors.

## Phase 3: CRUD Implementation

- [ ] T007 Implement profile load from the `profiles` table.
- [ ] T008 Implement new-profile insert into the `profiles` table.
- [ ] T009 Implement profile update by `profile_id`.
- [ ] T010 Implement profile delete by `id`.
- [ ] T011 Ensure update fails when the target profile row is missing.

## Phase 4: Validation Rules

- [ ] T012 Preserve unique-name validation behavior.
- [ ] T013 Preserve unique-profile-path validation behavior.
- [ ] T014 Preserve executable-path, profile-path, and target-URL validation behavior in the use case.
- [ ] T015 Preserve selected-profile behavior after save and delete.

## Phase 5: Verification

- [ ] T016 Add automated tests for insert, update, delete, and load behavior.
- [ ] T017 Add automated tests for duplicate name and duplicate profile path rejection.
- [ ] T018 Add automated tests for missing-profile update failure.
- [ ] T019 Manually verify add/save/edit behavior from the `Profiles` tab.
