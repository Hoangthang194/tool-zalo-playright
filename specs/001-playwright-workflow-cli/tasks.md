# Tasks: Workflow-Driven Playwright Chrome CLI

## Phase 1: Baseline Feature

- [x] T001 Scaffold the Python package with clean architecture folders under `src/browser_automation/`.
- [x] T002 Add CLI entrypoints for console-script and `python -m` execution.
- [x] T003 Implement domain entities and application ports for workflow execution.
- [x] T004 Implement JSON workflow loading with structural and semantic validation.
- [x] T005 Implement Playwright browser gateway with baseline actions: `goto`, `click`, `fill`, `press`, `wait_for_selector`, `wait_for_timeout`, `screenshot`.
- [x] T006 Add sample workflow files and baseline README instructions.
- [x] T007 Add baseline tests for workflow loading and use case orchestration.

## Phase 2: Hardening

- [ ] T008 Add tests for invalid JSON, negative integer fields, and invalid browser channel combinations.
- [ ] T009 Add tests for Playwright action dispatch using mocks or fakes around the gateway.
- [ ] T010 Add a validation-only or dry-run mode so operators can check workflows without launching a browser.
- [ ] T011 Add structured execution artifact output for step timing and terminal status.

## Phase 3: Capability Expansion

- [ ] T012 Add new workflow actions such as `hover`, `check`, `select_option`, and `upload_file`.
- [ ] T013 [P] Add contract and validation updates for each new workflow action.
- [ ] T014 [P] Add example workflows that demonstrate each newly supported action.
- [ ] T015 Add regression tests for new action mappings and failure modes.

## Phase 4: Spec-Driven Workflow Adoption

- [ ] T016 Add local Spec Kit templates or overrides if the `specify` CLI is later introduced in this repository.
- [ ] T017 Add a contributor workflow that requires updating `spec.md`, `plan.md`, and `tasks.md` for future features.
- [ ] T018 Add a repository index or architecture overview artifact for faster brownfield onboarding.

