# Browser Automation Tool

Python tool using Playwright to open Chrome and execute browser actions from a JSON workflow.

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

This repository now includes a Spec Kit-style artifact set for the baseline feature:

- Constitution: `.specify/memory/constitution.md`
- Feature spec: `specs/001-playwright-workflow-cli/spec.md`
- Technical plan: `specs/001-playwright-workflow-cli/plan.md`
- Tasks: `specs/001-playwright-workflow-cli/tasks.md`
- Supporting docs: `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

These files are intended to be the source of truth for future changes to the workflow-driven browser automation tool.
