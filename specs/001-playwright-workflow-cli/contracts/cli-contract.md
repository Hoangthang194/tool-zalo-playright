# CLI Contract

## Command

```powershell
browser-automation <workflow-path> [--log-level DEBUG|INFO|WARNING|ERROR]
```

Equivalent module invocation:

```powershell
python -m browser_automation <workflow-path> [--log-level DEBUG|INFO|WARNING|ERROR]
```

## Inputs

| Argument | Required | Description |
| --- | --- | --- |
| `<workflow-path>` | Yes | Path to a JSON workflow file |
| `--log-level` | No | Logging verbosity, defaults to `INFO` |

## Exit Codes

| Exit Code | Meaning |
| --- | --- |
| `0` | Workflow executed successfully |
| `1` | Validation error, file error, browser launch error, or runtime execution error |

## Observable Output

- On success, the command logs workflow completion with workflow name, executed step count, and browser channel.
- On failure, the command logs a single actionable error message and exits non-zero.

## Error Contract

The CLI must surface at least these categories of failures:

- Workflow file not found
- Workflow file is invalid JSON
- Workflow schema validation failure
- Unsupported browser engine
- Unsupported step action
- Playwright runtime failure

