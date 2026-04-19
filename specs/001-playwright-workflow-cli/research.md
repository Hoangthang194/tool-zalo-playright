# Research Notes: Workflow-Driven Playwright Chrome CLI

## Decision 1: Use Playwright Sync API for the Baseline

- Decision: use Playwright's synchronous Python API for the initial CLI.
- Why: the tool currently runs one workflow from one command invocation, so synchronous control flow keeps the entrypoint simple and aligns with a single ordered execution path.
- Alternatives considered:
  - Async API: more flexible for future concurrency, but adds complexity without current need.
  - Selenium: broader ecosystem familiarity, but Playwright provides stronger modern browser automation ergonomics for this use case.

## Decision 2: Use JSON as the Baseline Workflow Format

- Decision: support JSON workflow definitions first.
- Why: JSON is straightforward to parse, easy to validate, and already maps directly to the current loader implementation.
- Alternatives considered:
  - YAML: easier for humans to author, but adds parser dependencies and format ambiguity that are unnecessary in the initial version.
  - Python scripts: more flexible, but violate the workflow-first principle.

## Decision 3: Prefer Real Chrome Through Chromium Channel Selection

- Decision: support `engine: "chromium"` with `channel: "chrome"` to open installed Google Chrome when requested.
- Why: many automation scenarios need parity with the user's real browser instead of Playwright's bundled Chromium.
- Alternatives considered:
  - Always use bundled Chromium: simpler setup, but weaker parity with operator expectations.
  - Require executable path configuration: more flexible, but unnecessarily heavy for the initial version.

## Decision 4: Keep One Context and One Page per Workflow

- Decision: run each workflow in a single browser context and page.
- Why: this covers the initial navigation and form automation use cases while keeping runtime behavior deterministic.
- Alternatives considered:
  - Multi-page workflows: more powerful, but introduces coordination complexity that is not required by the current examples.
  - Shared long-lived browser service: would optimize repeated runs, but complicates CLI lifecycle and error handling.

## Decision 5: Keep the CLI Minimal

- Decision: use `argparse` with a required workflow path and optional log level.
- Why: the tool needs a low-friction operator interface, and the current argument surface is small.
- Alternatives considered:
  - Click or Typer: richer DX, but unnecessary for the baseline command shape.
  - Config-only execution: removes CLI clarity and makes one-off runs harder.

