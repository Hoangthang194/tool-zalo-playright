# Tasks: Zalo Chrome Profile GUI Launcher

## Phase 1: Baseline Feature

- [ ] T001 Add domain models and validation rules for Chrome executable path, user data directory, profile directory, and Zalo target URL.
- [ ] T002 Add application ports for Chrome discovery, Chrome process launching, and launcher settings persistence.
- [ ] T003 Implement the use case that validates launch configuration, delegates process startup, and returns a launch result for the GUI.
- [ ] T004 Implement an infrastructure adapter for discovering installed Google Chrome on Windows, with explicit path override support.
- [ ] T005 Implement an infrastructure adapter that builds and launches the Chrome command with `--user-data-dir`, `--profile-directory`, and `https://chat.zalo.me`.
- [ ] T006 Implement lightweight settings persistence for the last-used launcher configuration in a documented JSON file.
- [ ] T007 Implement a dedicated Tkinter GUI for selecting Chrome path, user data directory, profile directory, and launching Zalo.
- [ ] T008 Wire the GUI into project entrypoints and update operator-facing usage documentation.
- [ ] T009 Add baseline tests for configuration validation, launch argument construction, and use case orchestration.

## Phase 2: Hardening

- [ ] T010 Add tests for missing executable paths, missing user data directories, missing profile directories, and stale remembered settings.
- [ ] T011 Prevent duplicate concurrent launch requests from repeated GUI clicks and expose clear in-progress state.
- [ ] T012 Add profile discovery helpers or profile-picker behavior based on directories found under the selected user data directory.
- [ ] T013 Add clearer diagnostics for profile-locked, process-startup, and invalid-executable failure modes.
- [ ] T014 Add manual validation guidance that separates browser-launch success from Zalo login or network state.

## Phase 3: Capability Expansion

- [ ] T015 Add optional support for opening additional Zalo-related URLs or tabs after the primary launch.
- [ ] T016 [P] Add friendly profile labels or recent-profile shortcuts for faster repeated launches.
- [ ] T017 [P] Add packaging or distribution guidance for non-developer operators.
- [ ] T018 Add regression tests for any new launcher options and persisted-settings migration behavior.

## Phase 4: Artifact Completion

- [ ] T019 Add `research.md` to capture launcher-specific implementation decisions if this feature is promoted to the same artifact depth as `001`.
- [ ] T020 Add `data-model.md` and `quickstart.md` so feature `002` matches the surrounding spec set more closely.
- [ ] T021 Add contracts or UI-state notes if implementation review requires stricter launcher behavior documentation.
