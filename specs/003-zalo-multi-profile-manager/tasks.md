# Tasks: Zalo Multi-Profile Chrome Manager

## Phase 1: Baseline Feature

- [x] T001 Add domain models for a saved Chrome profile entry and the saved-profile library.
- [x] T002 Add application ports for multi-profile persistence and Chrome process launching.
- [x] T003 Implement use cases for listing, creating, updating, deleting, selecting, and launching saved profiles.
- [x] T004 Implement a JSON-backed repository for the saved-profile library.
- [x] T005 Implement migration logic that converts legacy `user_data_dir + profile_directory` settings into one saved full profile path.
- [x] T006 Expand the Tkinter Zalo GUI to show a saved-profile list plus add/edit/delete actions.
- [x] T007 Add direct launch behavior for the selected saved profile.
- [x] T008 Add baseline tests for saved-profile CRUD, selection state, persistence mapping, and selected-profile launch orchestration.

## Phase 2: Hardening

- [ ] T009 Add stronger validation that distinguishes a real profile folder from the parent `User Data` root.
- [ ] T010 Add recovery behavior for a corrupt or partially invalid saved-profile library file.
- [ ] T011 Add clearer diagnostics when the saved Chrome profile path no longer exists.
- [ ] T012 Add safer selection behavior when a selected profile is deleted or renamed.
- [ ] T013 Add manual validation guidance for switching between multiple Zalo profiles.
- [x] T021 Add deterministic default window bounds for single-profile launch on Windows.
- [x] T022 Add regression coverage for single-profile launch window sizing.
- [x] T023 Place repeated single-profile launches into the next available grid cell instead of overlapping the previous window.

## Phase 3: Capability Expansion

- [ ] T014 Add profile search, sorting, or grouping behavior when the saved-profile count grows.
- [ ] T015 [P] Add optional duplicate-profile shortcuts to create a new entry from an existing one.
- [ ] T016 [P] Add optional profile notes or tags if operators need more context than a name alone.
- [ ] T017 Add regression tests for migration, deletion, and selection edge cases.

## Phase 4: Artifact Completion

- [ ] T018 Add `research.md` for persistence format, migration strategy, and GUI tradeoff decisions if this feature is taken to full artifact depth.
- [ ] T019 Add `data-model.md` for the saved-profile library schema and selected-profile state.
- [ ] T020 Add `quickstart.md` showing how to configure and launch multiple saved profiles from the GUI.
