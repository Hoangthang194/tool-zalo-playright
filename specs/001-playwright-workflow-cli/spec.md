# Feature Specification: Workflow-Driven Playwright Chrome CLI

## Status

Baseline feature defined for repository bootstrapping.

## Summary

Build a Python command-line tool that opens a browser with Playwright, preferably real Google Chrome when available, and executes browser actions from a declarative workflow file. The tool must be easy to maintain, readable for future contributors, and structured around clean architecture boundaries.

## Problem Statement

The project needs a maintainable way to automate browser actions without embedding brittle one-off scripts in source code. Operators need to run workflows from files, while maintainers need a codebase that can grow with new browser actions and validation rules without collapsing into framework-specific glue code.

## Goals

- Provide a CLI entrypoint that runs an automation workflow from a file.
- Open installed Google Chrome via Playwright when the workflow requests `channel: "chrome"`.
- Keep browser actions declarative and ordered.
- Validate workflow input before runtime execution.
- Preserve clean architecture boundaries so new actions are easy to add.
- Provide sample workflows and usage guidance for Windows-first environments.

## Non-Goals

- Recording workflows from browser sessions.
- Parallel multi-browser orchestration in the initial version.
- Authentication/session vault management.
- Visual test comparison or self-healing selectors.
- Remote execution infrastructure.

## Primary Users

### Automation Operator

Runs a workflow file from the terminal and expects the browser to perform the exact ordered actions.

### Maintainer

Adds new workflow actions or execution options without leaking Playwright-specific concerns across the whole codebase.

### Reviewer

Needs clear contracts, examples, and validation rules to understand whether a workflow or code change is correct.

## User Stories

1. As an automation operator, I want to run a single command with a workflow file so I can automate browser steps without writing Python code.
2. As an automation operator, I want the tool to open real Chrome when configured so I can validate against the browser I actually use.
3. As a maintainer, I want workflow actions modeled explicitly so I can add new actions with minimal impact on unrelated layers.
4. As a reviewer, I want invalid workflows to fail early with specific messages so I can diagnose issues before browser execution starts.
5. As a tester, I want workflows to generate screenshots as artifacts so I can confirm visible outcomes.

## Functional Requirements

### Workflow Input

- FR-001: The tool MUST accept a workflow file path as a required CLI argument.
- FR-002: The workflow file MUST define a workflow name, browser settings, and an ordered list of steps.
- FR-003: The tool MUST support JSON workflow definitions in the baseline version.
- FR-004: The tool MUST reject malformed JSON, missing required fields, unsupported actions, negative timeout values, and invalid type shapes before launching the browser.

### Browser Execution

- FR-005: The tool MUST support browser engines `chromium`, `firefox`, and `webkit`, while allowing a Chromium channel such as `chrome` when requested.
- FR-006: When `channel` is set to `"chrome"` with engine `chromium`, the tool SHOULD attempt to open installed Google Chrome.
- FR-007: The tool MUST create one browser context and one page per workflow execution in the baseline version.
- FR-008: The tool MUST execute workflow steps strictly in the order they are defined.

### Supported Workflow Actions

- FR-009: The baseline version MUST support `goto`.
- FR-010: The baseline version MUST support `click`.
- FR-011: The baseline version MUST support `fill`.
- FR-012: The baseline version MUST support `press`.
- FR-013: The baseline version MUST support `wait_for_selector`.
- FR-014: The baseline version MUST support `wait_for_timeout`.
- FR-015: The baseline version MUST support `screenshot`.

### Runtime Behavior

- FR-016: The tool MUST respect workflow timeout and viewport settings.
- FR-017: The tool MUST create missing parent directories for screenshot outputs.
- FR-018: The tool MUST log step execution progress at runtime.
- FR-019: The tool MUST exit with a non-zero code when validation or execution fails.
- FR-020: The tool MUST report successful completion with workflow name, number of executed steps, and selected browser channel.

### Maintainability

- FR-021: Domain entities MUST remain free of Playwright and CLI dependencies.
- FR-022: Use cases MUST coordinate workflow loading and browser execution via ports.
- FR-023: Infrastructure adapters MUST own Playwright integration and workflow-file parsing.
- FR-024: The repository MUST include sample workflows and tests that demonstrate the baseline flow.

## Non-Functional Requirements

- NFR-001: The project MUST target Python 3.11+.
- NFR-002: The initial operator experience MUST be documented for PowerShell on Windows.
- NFR-003: The codebase SHOULD remain small, readable, and framework-light outside Playwright.
- NFR-004: Runtime failures SHOULD be observable through logs and artifact output paths.

## Acceptance Scenarios

### Scenario 1: Run Sample Docs Workflow

- Given the environment has Python, Playwright, and Chrome installed
- And the operator runs the sample workflow
- When the workflow completes
- Then the browser visits the configured site
- And a screenshot artifact is created
- And the command exits successfully

### Scenario 2: Run Search Workflow

- Given the environment has Python, Playwright, and Chrome installed
- And the operator runs a workflow containing `fill` and `press`
- When the page loads and the selector is present
- Then the search input is filled
- And the Enter key is pressed
- And the workflow waits for the expected result heading

### Scenario 3: Invalid Workflow Fails Before Browser Launch

- Given a workflow file is missing a required field for a step
- When the operator runs the CLI
- Then the command exits with a non-zero code
- And the error message identifies the invalid field
- And no browser session is launched

### Scenario 4: Chrome Not Available

- Given a workflow requests `channel: "chrome"`
- And Chrome is not installed or cannot be launched
- When the operator runs the workflow
- Then the command exits with a non-zero code
- And Playwright launch failure is surfaced as an actionable error

## Edge Cases

- Workflow root is not an object.
- `steps` is empty or not an array.
- `browser.viewport` is not an object.
- Integer fields are provided as booleans.
- Negative `timeout_ms`, `slow_mo_ms`, or `milliseconds`.
- `screenshot` path points to a nested directory that does not exist yet.
- Relative URLs are used without a `base_url`.
- Selector-based steps target elements that never appear.

## Success Metrics

- A new contributor can identify where to add a new action in less than 10 minutes.
- Sample workflows run from a single documented command path.
- Validation catches common workflow authoring mistakes before browser launch.
- Future actions can be added without changing domain models outside explicit action enumeration.

