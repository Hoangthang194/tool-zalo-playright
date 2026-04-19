# Implementation Plan: Workflow-Driven Playwright Chrome CLI

## Overview

Implement a Python CLI tool that executes declarative browser workflows with Playwright while preserving clean architecture boundaries. The baseline feature already exists in source form; this plan documents the intended architecture, constraints, and validation strategy so subsequent work remains aligned with the specification.

## Technical Context

| Area | Decision |
| --- | --- |
| Language | Python 3.11+ |
| Packaging | `pyproject.toml` with `setuptools` |
| Browser Automation | Playwright sync API |
| Primary Interface | CLI via `browser-automation` and `python -m browser_automation` |
| Input Format | JSON workflow files |
| Output Artifacts | Logs and optional screenshots |
| Supported OS | Windows-first documentation, cross-platform-friendly code |
| Architecture | Clean architecture with domain, application, infrastructure, interfaces |

## Constitution Check

### Spec Before Behavior Change

This feature is documented under `specs/001-playwright-workflow-cli/` before further implementation work.

### Clean Architecture Boundaries

The source layout keeps domain entities isolated from Playwright and file I/O, with ports in the application layer and adapters in infrastructure.

### Workflow-First Automation

Execution is driven by workflow files rather than handwritten automation flows inside the CLI.

### Safe, Deterministic Execution

The loader validates workflow structure before execution, and the gateway executes steps in declared order.

### Testability and Observable Outcomes

The baseline includes tests for the use case and workflow loader, with quickstart scenarios documenting manual validation.

### Incremental Delivery

Future work is broken into explicit phases in `tasks.md`, starting with hardening and then expanding action coverage.

## Architecture

### Domain Layer

- `BrowserSettings` models browser configuration.
- `AutomationStep` models each declarative step.
- `AutomationWorkflow` represents the root aggregate.
- Domain exceptions define validation and runtime error categories.

### Application Layer

- `WorkflowDefinitionLoader` abstracts workflow deserialization.
- `BrowserAutomationGateway` abstracts browser execution.
- `RunAutomationWorkflowUseCase` orchestrates load -> execute -> summarize.

### Infrastructure Layer

- `JsonWorkflowDefinitionLoader` parses and validates JSON workflows.
- `PlaywrightBrowserAutomationGateway` maps domain steps to Playwright sync API calls.

### Interfaces Layer

- CLI argument parsing, logging configuration, and process exit codes live in the interface layer.

## Repository Structure

```text
src/
  browser_automation/
    application/
    domain/
    infrastructure/
    interfaces/
examples/
tests/
.specify/
specs/
```

## Key Decisions

1. Use Playwright sync API for the baseline CLI to keep the entrypoint and mental model simple.
2. Keep workflows in JSON first, because it is unambiguous, easy to validate, and already supported in the current codebase.
3. Prefer real Chrome through `channel: "chrome"` when requested, while keeping Chromium-compatible engine configuration.
4. Use a single browser context and page per execution until a clear multi-page requirement appears.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Local environment missing Python or Playwright | Tool cannot be executed or tested | Keep setup instructions explicit and document prerequisites in quickstart |
| Chrome not installed while workflow requests it | Launch failure | Surface Playwright errors clearly and document the fallback path |
| Selector fragility in workflows | Runtime failures | Encourage explicit waits and small, reviewable workflow files |
| Action growth causing adapter sprawl | Maintainability risk | Add new actions through explicit contracts, tests, and isolated dispatch branches |

## Validation Strategy

### Automated

- Unit test the use case orchestration.
- Unit test JSON workflow loading and validation.
- Add adapter dispatch tests as new actions are introduced.

### Manual

- Run sample workflow against Playwright docs.
- Run search workflow against Wikipedia.
- Confirm screenshot artifacts are created.
- Confirm invalid workflows fail before browser launch.

## Out of Scope for This Feature

- Interactive workflow recording
- Persistent execution history storage
- Session reuse across multiple workflows
- Distributed or scheduled execution

