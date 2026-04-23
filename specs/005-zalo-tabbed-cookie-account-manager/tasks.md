# Tasks: Zalo Profile-Proxy Account Manager

## Phase 1: Spec and Modeling

- [x] T001 Add `spec.md`, `plan.md`, and `tasks.md` for the Zalo profile-proxy account manager.
- [x] T002 Add domain models for saved Zalo account entries and the combined workspace state.
- [x] T003 Add an application port for account workspace persistence.

## Phase 2: Application and Persistence

- [x] T004 Implement a use case for loading, selecting, saving, and deleting Zalo account entries.
- [x] T005 Implement a JSON-backed store for account workspace persistence.
- [x] T006 Remove cookie management from the workspace model while keeping old files safe to load.

## Phase 3: GUI Tabs

- [x] T007 Refactor the current profile manager UI into a `Profiles` tab.
- [x] T008 Remove the `Cookies` tab from the GUI.
- [x] T009 Simplify the `Zalo Accounts` tab to linked profile + proxy only.
- [x] T010 Make account-form single-line fields render at consistent height.

## Phase 4: Launch Ownership Refactor

- [x] T011 Remove direct Chrome launch controls from the `Profiles` tab so it becomes profile CRUD only.
- [x] T012 Add account-launch orchestration that combines the linked saved profile with the saved proxy.
- [x] T013 Extend the launcher path to pass proxy configuration during account launch.
- [x] T014 Add launch controls and launch status handling to the `Zalo Accounts` tab.

## Phase 5: Verification and Docs

- [x] T015 Update automated tests for account CRUD, account launch orchestration, and JSON persistence mapping.
- [x] T016 Update `README.md` for the profile-library plus account-launch workflow.
- [x] T017 Run the relevant test suite after the launch refactor.
