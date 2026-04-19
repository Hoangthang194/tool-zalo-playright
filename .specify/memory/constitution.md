<!--
Sync Impact Report
Version change: N/A -> 1.0.0
Modified principles:
- Initial adoption
Added sections:
- Core Principles
- Delivery Workflow
- Governance
Removed sections:
- None
Templates requiring updates:
- N/A (this repository was scaffolded manually to follow the Spec Kit artifact layout)
Follow-up TODOs:
- If `specify init` is introduced later, keep this constitution as the source of truth and align generated templates with it.
-->
# Tool Automation Zalo Constitution

## Scope

This constitution governs browser automation tooling in this repository, including workflow definitions, command-line interfaces, runtime adapters, tests, and supporting documentation.

## Core Principles

### 1. Specification Before Behavior Change

Every meaningful feature, workflow capability, or behavior change MUST begin with a feature specification under `specs/`. The spec defines the user-facing outcome, acceptance criteria, constraints, and failure modes before implementation begins.

Rationale: this repository is intended to follow spec-driven development, so intent must remain the source of truth instead of ad hoc code changes.

### 2. Clean Architecture Boundaries

Domain, application, infrastructure, and interface responsibilities MUST remain separated. Domain objects cannot depend on Playwright, CLI parsing, or file-system concerns. Infrastructure code cannot bypass application use cases for core execution flows.

Rationale: the tool is expected to evolve with more actions and more adapters; maintainability depends on explicit boundaries.

### 3. Workflow-First Automation

Browser behavior MUST be described declaratively through workflow files rather than hard-coded scripts. New automation capabilities SHOULD first be introduced as workflow actions or execution options with documented contracts.

Rationale: workflow files are the stable interface used by operators, reviewers, and future agents.

### 4. Safe, Deterministic Execution

The tool MUST fail fast on invalid workflow input, preserve step ordering, and return actionable errors for missing files, invalid selectors, unsupported actions, or browser launch failures. Any new side effect, such as writing artifacts or logs, MUST have an explicit output location.

Rationale: automation that silently diverges from expected behavior is more costly than a visible failure.

### 5. Testability and Observable Outcomes

Each new workflow action or validation rule MUST be backed by targeted tests or explicit validation scenarios. User-visible outcomes such as exit codes, generated artifacts, and log messages MUST be documented in contracts or quickstart guidance.

Rationale: browser automation is inherently integration-heavy; stable maintenance requires observable, repeatable outcomes.

### 6. Incremental Delivery Over Large Dumps

Work MUST be broken into small, reviewable tasks with clear dependencies. Large feature additions SHOULD be introduced in phases, starting with the smallest end-to-end slice that can be validated in isolation.

Rationale: this matches the Spec Kit workflow and reduces ambiguity for both humans and coding agents.

## Delivery Workflow

1. Create or update the governing feature specification in `specs/<feature>/spec.md`.
2. Clarify ambiguous requirements before planning implementation details.
3. Produce a technical plan, research notes, data model, contracts, and validation scenarios.
4. Generate an executable task list with explicit sequencing and safe parallelization points.
5. Implement only against reviewed tasks, then update docs and tests alongside code.

## Governance

- This constitution is authoritative when requirements, plans, tasks, and implementation disagree.
- Amendments require updating this file and any impacted spec artifacts in the same change set.
- Versioning policy:
  - MAJOR for incompatible principle or governance changes.
  - MINOR for new principles or materially expanded rules.
  - PATCH for clarifications that do not change expected behavior.
- Compliance review is required for all feature branches or manual feature folders before implementation is considered complete.

**Version**: 1.0.0  
**Ratified**: 2026-04-19  
**Last Amended**: 2026-04-19

