# Quickstart: Workflow-Driven Playwright Chrome CLI

## Prerequisites

- Python 3.11+
- PowerShell
- Google Chrome installed if you want to run with `channel: "chrome"`

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m playwright install
```

## Validation Scenario 1: Run the Docs Sample

```powershell
python -m browser_automation examples\sample_workflow.json
```

Expected result:

- Browser opens
- Playwright docs page is visited
- `artifacts/playwright-docs.png` is created
- Command exits with code `0`

## Validation Scenario 2: Run the Search Sample

```powershell
python -m browser_automation examples\wikipedia_search_workflow.json
```

Expected result:

- Browser opens
- Search input is filled with `Playwright`
- Search is submitted with Enter
- `artifacts/wikipedia-playwright.png` is created

## Validation Scenario 3: Invalid Workflow Fails Fast

Create an invalid JSON workflow with a `click` step missing `selector`, then run:

```powershell
python -m browser_automation path\to\invalid-workflow.json
```

Expected result:

- No browser window is launched
- The CLI logs a validation error
- Command exits with code `1`

