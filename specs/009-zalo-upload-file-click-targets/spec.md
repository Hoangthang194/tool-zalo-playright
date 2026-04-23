# Feature Specification: Zalo Upload File Click Targets

## Status

Implemented.

## Summary

Extend `Class Manage` so a saved click target can optionally include an upload file path. When the operator uses `Test Element` on a target that opens a file chooser or targets an `input[type=file]`, the app must provide the configured file automatically instead of leaving the workflow at the native Explorer dialog.

## Functional Requirements

- FR-001: A saved click target MAY include one upload file path.
- FR-002: The GUI MUST allow the operator to browse and save that file path.
- FR-003: `Test Element` MUST use the configured file path when the clicked selector triggers a file chooser.
- FR-004: `Test Element` SHOULD support direct `input[type=file]` targets without requiring a native dialog to stay open.
- FR-005: The upload file path MUST persist in the local Zalo workspace store.
