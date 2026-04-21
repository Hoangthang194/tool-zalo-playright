# Tasks: Zalo Multi-Profile Grid Launcher

## Phase 1: Spec and Modeling

- [x] T001 Add `spec.md`, `plan.md`, and `tasks.md` for the `4x2` multi-profile grid-launch feature.
- [x] T002 Define the application contract for detecting and arranging Chrome windows outside the GUI layer.
- [x] T003 Define bulk-launch result data that can report full success, partial tiling, and omitted profiles.

## Phase 2: Application and Infrastructure

- [x] T004 Extend the profile manager use case with a bulk-launch path for multiple selected profile IDs.
- [x] T005 Add a Windows Chrome window arranger that snapshots existing windows, waits for newly opened windows, and tiles them into a `4x2` grid.
- [x] T006 Preserve existing single-profile launch behavior while allowing the bulk-launch path to persist one primary selected profile.
- [x] T013 Seed each grid launch with launch-time window size and position that match the target grid cell.

## Phase 3: GUI Integration

- [x] T007 Change the saved-profile list to support multi-selection and surface clear instructions for `Ctrl` / `Shift` selection.
- [x] T008 Update launch behavior so one selected profile uses the single-profile path and multiple selected profiles use the grid-launch path.
- [x] T009 Disable ambiguous edit or delete actions during multi-selection while keeping launch available.

## Phase 4: Verification and Docs

- [x] T010 Add automated tests for bulk-launch ordering, grid-cap behavior, and grid geometry.
- [x] T011 Update `README.md` so operators know how to multi-select profiles and what the `4x2` limit means.
- [x] T012 Run the test suite and confirm the feature does not regress the existing Zalo manager behavior.
- [x] T014 Add regression tests for launch-time `window-size` and `window-position` arguments.
