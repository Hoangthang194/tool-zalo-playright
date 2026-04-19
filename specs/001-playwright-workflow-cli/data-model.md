# Data Model: Workflow-Driven Playwright Chrome CLI

## Entity: BrowserSettings

Represents runtime browser configuration for one workflow execution.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `engine` | string | Yes | Expected values: `chromium`, `firefox`, `webkit` |
| `channel` | string or null | No | Valid only with `engine = "chromium"` |
| `headless` | boolean | Yes | Defaults to `false` |
| `slow_mo_ms` | integer | Yes | Must be `>= 0` |
| `timeout_ms` | integer | Yes | Must be `>= 0` |
| `base_url` | string or null | No | Enables relative `goto` URLs |
| `viewport_width` | integer | Yes | Must be `> 0` |
| `viewport_height` | integer | Yes | Must be `> 0` |

## Entity: AutomationStep

Represents one ordered browser action in a workflow.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | string | Yes | Human-readable step label |
| `action` | enum | Yes | Supported baseline actions are `goto`, `click`, `fill`, `press`, `wait_for_selector`, `wait_for_timeout`, `screenshot` |
| `selector` | string or null | Conditional | Required for selector-based actions |
| `url` | string or null | Conditional | Required for `goto` |
| `text` | string or null | Conditional | Required for `fill` |
| `key` | string or null | Conditional | Required for `press` |
| `milliseconds` | integer or null | Conditional | Required for `wait_for_timeout`, must be `>= 0` |
| `path` | string or null | Conditional | Required for `screenshot` |
| `full_page` | boolean | No | Defaults to `true` for screenshots |
| `timeout_ms` | integer or null | No | Step-level override, must be `>= 0` if provided |

## Entity: AutomationWorkflow

Aggregate root for a complete CLI execution request.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | string | Yes | Defaults to `unnamed-workflow` when omitted in JSON |
| `browser` | `BrowserSettings` | Yes | Workflow-scoped browser config |
| `steps` | ordered tuple of `AutomationStep` | Yes | Must contain at least one step |

## Entity: WorkflowExecutionResult

Represents the post-run summary returned by the application use case.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `workflow_name` | string | Yes | Mirrors workflow input |
| `steps_executed` | integer | Yes | Number of executed steps |
| `browser_channel` | string or null | No | Selected channel if set |

## Relationships

- One `AutomationWorkflow` owns exactly one `BrowserSettings`.
- One `AutomationWorkflow` owns one or more `AutomationStep` records in strict execution order.
- One successful execution yields one `WorkflowExecutionResult`.

## Validation Rules

- Integer-typed fields cannot be booleans.
- `channel` is valid only for Chromium-based execution.
- `steps` cannot be empty.
- Conditional fields are enforced by action type.
- Screenshot outputs are file-path strings and may target directories that do not yet exist.

