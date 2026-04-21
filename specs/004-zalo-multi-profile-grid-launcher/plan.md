# Implementation Plan: Zalo Multi-Profile Grid Launcher

## Overview

Add a bulk-launch mode to the Zalo multi-profile manager so operators can select several saved Chrome profiles, open them in one action, and tile the detected Chrome windows into a fixed `4x2` grid on the primary monitor.

## Technical Context

| Area | Decision |
| --- | --- |
| Language | Python 3.11+ |
| GUI Toolkit | Tkinter |
| Browser Launching | Existing subprocess-based Chrome launcher |
| Saved Profile Model | Reuse saved full profile folder path such as `...\User Data\Profile 1` |
| Bulk Launch Limit | `8` profiles per grid action |
| Grid Layout | `4 columns x 2 rows` |
| Placement Target | Primary monitor work area |
| Window Management | Windows Win32 API adapter behind an application port |
| Ordering Rule | Visible saved-profile list order |

## Constitution Check

### Spec Before Behavior Change

This feature is defined under `specs/004-zalo-multi-profile-grid-launcher/` before implementation.

### Clean Architecture Boundaries

The GUI only gathers multi-selection state and triggers a use case. Launch batching, window detection, and grid placement remain behind application boundaries and infrastructure adapters.

### Workflow-First Automation

This feature only affects the dedicated Zalo GUI flow and does not change workflow-driven Playwright automation.

### Safe, Deterministic Execution

The implementation validates selected profiles before launch, caps the batch at eight profiles, preserves list order, and returns clear partial-success outcomes when some windows are not detected.

### Testability and Observable Outcomes

Bulk launch ordering, cap behavior, and grid geometry are covered with automated tests. Operators see explicit GUI status for full success, partial tiling, or omitted profiles.

### Incremental Delivery

Implementation keeps existing single-profile launch intact while adding a second orchestration path for bulk grid launch.

## Architecture

### Domain Layer

- Reuse `SavedChromeProfile` and `ChromeLaunchConfig`.
- Add result models for bulk grid launches and detected-window outcomes if needed.

### Application Layer

- Extend the profile manager use case with a bulk-launch operation for multiple selected profile IDs.
- Persist one primary selected profile for compatibility with the existing saved-library model.
- Delegate window discovery and placement to a new application port.

### Infrastructure Layer

- Add a Windows-specific Chrome window arranger using Win32 APIs.
- Detect visible top-level Chrome windows, wait for newly opened ones, and move them into the computed grid rectangles.
- Expose grid-cell geometry so launch commands can be seeded with matching `window-size` and `window-position` arguments before the Win32 enforcement pass runs.
- Keep grid geometry logic isolated and unit-testable.

### Interface Layer

- Change the Tkinter listbox to support extended selection.
- Preserve safe single-profile editing while enabling multi-profile launch from the same list.
- Surface clear instructions for `Ctrl` / `Shift` multi-select and grid-launch limits.

## Key Decisions

1. Preserve the existing saved-profile model instead of introducing a second profile-store format.
2. Launch selected profiles in one background operation while tracking windows in selection order.
3. Cap the first version at eight profiles because the requested layout is fixed at `4x2`.
4. Use primary monitor work area instead of full screen so the taskbar stays accessible.
5. Seed Chrome with target `window-size` and `window-position` arguments for each grid cell, then still use Win32 tiling as the enforcement step.
6. Treat window-detection misses as partial success rather than total failure when launches already occurred.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Chrome window detection is slower than process launch | Wrong or missing tiling | Poll for new windows with timeout and return partial-success diagnostics |
| Existing Chrome windows confuse detection | Wrong window moved | Take a baseline window snapshot before bulk launch and only tile newly detected windows |
| Multi-select editing becomes ambiguous | Wrong profile edited accidentally | Keep one primary selected profile for the form and disable destructive edit actions during multi-selection |
| Screen dimensions do not divide evenly into `4x2` | Gaps or overlap | Use integer boundary math derived from the work area extents |
| More than eight selected profiles | Unclear operator expectation | Enforce a documented eight-profile cap and report omitted count explicitly |

## Validation Strategy

### Automated

- Test that bulk launch preserves requested profile order.
- Test that bulk launch injects launch-time window bounds that match the target grid cells.
- Test that bulk launch caps to eight profiles.
- Test grid rectangle calculation for a `4x2` layout.
- Test partial detection behavior without calling real Win32 APIs.

### Manual

- Save at least three profiles, multi-select them, and verify one launch action opens and arranges them.
- Save at least eight profiles and verify the first eight fill the `4x2` grid in list order.
- Select more than eight profiles and verify the GUI reports omitted profiles.
- Verify single-profile launch still opens one profile normally.
