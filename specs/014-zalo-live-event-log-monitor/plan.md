# Zalo Live Event Log Monitor Implementation Plan

## Goal

Attach to the currently launched `chat.zalo.me` tab, observe live session events, and show them in a log panel under `Zalo Accounts`.

## Decisions

- Use the tracked remote debugging port from the visible launched account.
- Keep monitoring in a background thread so Tkinter remains responsive.
- Surface logs through a GUI panel instead of a separate CLI process.
- Prefer the active session and avoid a second Zalo Web session.

## Work Items

1. Add a domain model and application use case for starting/stopping live monitoring.
2. Add a Playwright/CDP listener adapter that attaches to the current page and installs page hooks.
3. Add `Start Listen`, `Stop Listen`, and a rolling log panel in `Zalo Accounts`.
4. Add automated tests for the use case contract and log formatting.
5. Manually verify listener behavior against a real launched Zalo browser.
