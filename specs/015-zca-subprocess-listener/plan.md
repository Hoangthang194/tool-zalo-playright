# ZCA Subprocess Listener Implementation Plan

**Goal:** Replace webhook/live-event ingest with a managed ZCA subprocess listener while keeping Playwright for sender accounts.

**Architecture:** The GUI keeps one shared account list but switches behavior by fixed `role`. Listener accounts start a Node-based ZCA adapter that emits JSONL to stdout. Python parses those events, persists `new_message` rows through the existing message store, and forwards readable log entries to the GUI and terminal logging.

**Tech Stack:** Python 3.11, Tkinter, Playwright, MariaDB, Node.js, `zca-js`

---

## Scope

- Add account-role and credentials-file persistence.
- Add one ZCA subprocess adapter and JSONL protocol.
- Add one application use case that starts/stops the listener and persists messages.
- Update the GUI to show sender/listener-specific controls.
- Add a console-friendly batch file for runtime logs.

## File Map

- Modify: `src/browser_automation/domain/zalo_workspace.py`
- Modify: `src/browser_automation/application/use_cases/manage_zalo_workspace.py`
- Modify: `src/browser_automation/infrastructure/chrome_launcher/json_zalo_workspace_store.py`
- Create: `src/browser_automation/application/ports/zca_listener_process.py`
- Create: `src/browser_automation/application/use_cases/monitor_zca_listener.py`
- Create: `src/browser_automation/infrastructure/zca/subprocess_zca_listener_process.py`
- Create: `src/browser_automation/infrastructure/zca/zca_listener_adapter.mjs`
- Create: `src/browser_automation/infrastructure/zca/package.json`
- Modify: `src/browser_automation/interfaces/gui/zalo_app.py`
- Modify: `src/browser_automation/domain/zalo_live_events.py`
- Create: `run-zalo-gui-console.bat`
- Modify: `README.md`
- Add tests under `tests/`

## Test Strategy

- Test workspace save/load migration from `mode` to `role`.
- Test listener-account validation.
- Test subprocess command construction and stdout JSONL parsing.
- Test listener use case persistence behavior for `new_message`, duplicate, and database failure.
- Test GUI role-based field visibility and listener log updates where practical.
