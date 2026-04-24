# Tasks: Zalo Account Bulk Launch With Headless Option

## Phase 1: Spec and Modeling

- [ ] T001 Add `spec.md`, `plan.md`, and `tasks.md` for bulk account launch with headless mode.
- [ ] T002 Define the batch-launch request and result model for saved Zalo accounts.
- [ ] T003 Define the launch-mode contract for visible vs. headless execution.

## Phase 2: Application Layer

- [ ] T004 Extend or add an account-launch use case that accepts multiple selected account IDs.
- [ ] T005 Validate all selected accounts before any account is launched.
- [ ] T006 Return per-account outcomes and aggregate batch status.

## Phase 3: Infrastructure Layer

- [ ] T007 Reuse the current visible account-launch path for visible mode where possible.
- [ ] T008 Add or adapt a headless browser-launch adapter behind an application port if required.
- [ ] T009 Ensure account-level proxy and linked profile settings are preserved in both modes.

## Phase 4: GUI Integration

- [ ] T010 Change the `Zalo Accounts` list to support multi-selection.
- [ ] T011 Add a headless checkbox or equivalent control near the launch action.
- [ ] T012 Keep single-account editing safe while multi-select launch is enabled.
- [ ] T013 Surface clear visible/headless batch status messages in the account tab.

## Phase 5: Verification

- [ ] T014 Add automated tests for visible multi-account launch ordering and result aggregation.
- [ ] T015 Add automated tests for headless launch-mode behavior.
- [ ] T016 Add automated tests for pre-launch validation failures.
- [ ] T017 Manually verify visible and headless multi-account launch from the `Zalo Accounts` tab.
