# Browser Automation Tool

Python toolset for two related use cases:

- Playwright-driven browser automation from JSON workflows.
- A dedicated Zalo profile manager GUI that saves multiple Chrome profile paths and opens `chat.zalo.me` in the selected one.

## Goals

- Easy to maintain with clean architecture.
- Clear separation between domain, use case, Playwright adapter, and CLI.
- Easy to extend with new actions such as `select_option`, `upload_file`, or `evaluate`.

## Structure

```text
src/
  browser_automation/
    application/
      ports/
      use_cases/
    domain/
    infrastructure/
      playwright_adapter/
    interfaces/
      cli/
examples/
tests/
```

## Clean Architecture Mapping

- `domain`: entities and validation rules for automation workflows.
- `application`: use cases and abstract ports.
- `infrastructure`: JSON workflow loader and Playwright adapter.
- `interfaces`: CLI entrypoint.

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m playwright install
```

To open real Google Chrome instead of the default Playwright Chromium build, ensure Chrome is installed and keep `channel` set to `"chrome"` in the workflow.

## Run

```powershell
browser-automation examples\sample_workflow.json
```

Or:

```powershell
python -m browser_automation examples\sample_workflow.json
```

## Run Zalo Launcher GUI

```powershell
browser-automation-zalo-gui
```

The Zalo GUI now has two tabs:

- `Profiles`: save reusable Chrome profile definitions
- `Zalo Accounts`: store one proxy setting for each linked profile and launch `https://chat.zalo.me`

The `Profiles` tab lets you save multiple Chrome profile folders such as `...\User Data\Profile 1` and use them later inside the account workflow.
The `Zalo Accounts` tab lets you pick a saved profile, assign an optional proxy such as `127.0.0.1:8080` or `user:pass@host:port`, and launch real Google Chrome into `https://chat.zalo.me`.

Launching one saved account opens Chrome with deterministic window bounds based on the first `4x2` grid cell instead of Chrome's arbitrary restored size.
If another launched Chrome window is already visible, the next account launch uses the next grid cell beside it instead of overlapping the first one.

Windows defaults:

- Chrome executable is usually under `%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe`
- Chrome profiles usually live under `%LOCALAPPDATA%\Google\Chrome\User Data`
- Examples of profile folders are `%LOCALAPPDATA%\Google\Chrome\User Data\Default` and `%LOCALAPPDATA%\Google\Chrome\User Data\Profile 1`
- In the GUI, save the full profile folder path, not just the parent `User Data` directory

The saved profile library is stored in:

```text
%APPDATA%\browser-automation\zalo-profiles.json
```

The Zalo account workspace is stored in:

```text
%APPDATA%\browser-automation\zalo-workspace.json
```

If you already used the older single-profile launcher, its legacy settings are still stored at:

```text
%APPDATA%\browser-automation\zalo-launcher.json
```

The multi-profile manager can convert that older `user_data_dir + profile_directory` configuration into one saved full profile path automatically.

## Sample Workflow

```json
{
  "name": "playwright-docs-demo",
  "browser": {
    "engine": "chromium",
    "channel": "chrome",
    "headless": false,
    "slow_mo_ms": 200,
    "timeout_ms": 15000,
    "base_url": "https://playwright.dev",
    "viewport": {
      "width": 1440,
      "height": 900
    }
  },
  "steps": [
    { "name": "Open home", "action": "goto", "url": "/" },
    { "name": "Wait hero", "action": "wait_for_selector", "selector": "text=Playwright enables reliable end-to-end testing" },
    { "name": "Click get started", "action": "click", "selector": "text=Get started" },
    { "name": "Take screenshot", "action": "screenshot", "path": "artifacts/playwright-docs.png", "full_page": true }
  ]
}
```

## Supported Actions

- `goto`
- `click`
- `fill`
- `press`
- `wait_for_selector`
- `wait_for_timeout`
- `screenshot`

## Extension Ideas

- Add persistence adapters to store execution history.
- Add a YAML parser if the workflow should be easier to read for non-developers.
- Add focused unit tests for each action mapping as the number of supported steps grows.

## Spec-Driven Artifacts

This repository now includes Spec Kit-style artifact sets for the implemented workflow engine and the Zalo launcher GUI:

- Constitution: `.specify/memory/constitution.md`
- Feature spec: `specs/001-playwright-workflow-cli/spec.md`
- Technical plan: `specs/001-playwright-workflow-cli/plan.md`
- Tasks: `specs/001-playwright-workflow-cli/tasks.md`
- Supporting docs: `research.md`, `data-model.md`, `contracts/`, `quickstart.md`
- Feature spec: `specs/002-zalo-chrome-profile-gui/spec.md`
- Technical plan: `specs/002-zalo-chrome-profile-gui/plan.md`
- Tasks: `specs/002-zalo-chrome-profile-gui/tasks.md`
- Feature spec: `specs/003-zalo-multi-profile-manager/spec.md`
- Technical plan: `specs/003-zalo-multi-profile-manager/plan.md`
- Tasks: `specs/003-zalo-multi-profile-manager/tasks.md`
- Feature spec: `specs/004-zalo-multi-profile-grid-launcher/spec.md`
- Technical plan: `specs/004-zalo-multi-profile-grid-launcher/plan.md`
- Tasks: `specs/004-zalo-multi-profile-grid-launcher/tasks.md`
- Feature spec: `specs/005-zalo-tabbed-cookie-account-manager/spec.md`
- Technical plan: `specs/005-zalo-tabbed-cookie-account-manager/plan.md`
- Tasks: `specs/005-zalo-tabbed-cookie-account-manager/tasks.md`
- Feature spec: `specs/006-zalo-zca-session-webhook-bridge/spec.md`
- Feature spec: `specs/007-zalo-manual-click-target-testing/spec.md`

These files are intended to be the source of truth for future changes to the workflow-driven browser automation tool.
