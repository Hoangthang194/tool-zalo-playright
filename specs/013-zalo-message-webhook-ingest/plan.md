# Zalo Message Webhook Ingest to Database Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Receive incoming Zalo message events from a profile-bound browser extension via local HTTP webhook, resolve the sender through `listener_token`, enforce `Listen` mode, and persist normalized messages into MariaDB.

**Architecture:** A browser-resident listener attached to the logged-in `chat.zalo.me` session injects a WebSocket/event hook and forwards normalized events to a localhost webhook. The tool authenticates and resolves the listener by token, applies account-mode checks in the application layer, and persists accepted messages through a MariaDB repository with duplicate-safe behavior keyed by `msgId`.

**Tech Stack:** Chrome extension/injected script, local HTTP webhook service, Python application layer, MariaDB repository, automated tests for webhook/use-case/repository behavior.

---

## Overview

Add a webhook-ingest path that accepts incoming Zalo message events from a profile-bound listener and persists them into the MariaDB `messages` table.

The flow is:

1. observe message events from the existing `chat.zalo.me` browser session for one profile
2. extract those events through an injected WebSocket/event hook
3. forward normalized payload plus `listenerToken` to the local webhook endpoint
4. resolve `listenerToken` to the owning account/profile
5. resolve account operating mode
6. validate and normalize payload
7. persist message to DB
8. return accepted / duplicate / rejected result

This flow assumes the message source belongs to an account currently operating in `Listen` mode. It is intentionally aligned with a one-account-one-active-role model:

- `Listen` mode owns listener/webhook ingestion
- `Send` mode owns manual/browser interaction

The implementation plan must therefore include an account-mode decision point before normal ingest is allowed.
The implementation plan must also prefer a listener that attaches to the existing browser/profile session rather than opening a second standalone listener session for the same account.

## Technical Context

| Area | Decision |
| --- | --- |
| Ingest Interface | HTTP webhook endpoint |
| Endpoint Scope | localhost only |
| Database | MariaDB |
| Target Table | `messages` |
| Account Resolution | `listenerToken` -> internal account/profile mapping |
| Minimum Payload | `listenerToken`, `msgId`, `fromGroupId`, `toGroupId`, `content` |
| Duplicate Handling | keyed by `msgId` |
| Account Runtime Model | one account alternates between `Listen` and `Send` |
| Mode Enforcement | webhook accepts only `Listen`; `Send` causes conflict/rejection |
| Preferred Listener Source | extension/content-script/injected listener bound to active profile session |
| Preferred Capture Technique | injected script hook for page WebSocket/event flow |
| Unsafe Listener Pattern | second standalone Zalo session or duplicate direct WebSocket ownership |

## Constitution Check

### Spec Before Behavior Change

This feature is documented under `specs/013-zalo-message-webhook-ingest/` before implementation.

### Clean Architecture Boundaries

HTTP transport, message validation, and database persistence remain separated. Tkinter is not part of the ingest path.

### Workflow-First Automation

This feature does not change the generic workflow runner.

### Safe, Deterministic Execution

The message ingest path validates required fields up front, treats duplicate `msgId` deliveries deterministically, and must not assume simultaneous listener/manual ownership for one account.

### Testability and Observable Outcomes

Validation, duplicate handling, and insert behavior can be tested without opening the GUI.

### Incremental Delivery

Start with one minimum payload contract and one target table. Broader event models can come later.

## Architecture

### Transport Layer

- Add one localhost HTTP route for message ingest.
- Parse JSON payload.
- Forward normalized request data into an application use case.
- Reject requests with missing or unknown `listenerToken`.

### Browser Listener Layer

- Add a browser-resident listener design that attaches to the currently logged-in `chat.zalo.me` session for one profile.
- Inject a script to hook the page's WebSocket/event flow.
- Extract message events from the existing session context.
- Forward those events to the webhook endpoint with `listenerToken` and normalized message data.
- Avoid creating a second direct Zalo session for the same account.

### Application Layer

- Add a message-ingest request model.
- Validate required fields.
- Resolve `listenerToken` to the owning account/profile mapping.
- Resolve the account operating mode for the token-resolved account.
- Decide whether the message is new, duplicate, invalid, or in account-mode conflict.
- Return a structured ingest result.

### Infrastructure Layer

- Add a MariaDB-backed message repository/adapter.
- Insert into `messages`.
- Translate DB uniqueness and foreign-key failures into application outcomes.
- Read account-mode state from the selected runtime source and validate listener ownership before insert.
- Add token lookup infrastructure for `listenerToken` resolution if not already present in persistence/runtime state.

### Operational Mode Coordination

- Define where account mode is sourced from for this feature: persistence, runtime registry, or equivalent orchestration boundary.
- Ensure one account has only one active operating mode at a time.
- Ensure webhook ingestion is treated as valid work only while the account is active in `Listen`.
- Ensure `Send` mode blocks or flags webhook ingestion for the same account.
- Ensure the chosen listener design reuses the existing logged-in browser/profile session instead of duplicating it.
- Ensure the extension does not authoritatively choose `fromAccountId`; the tool resolves that internally from `listenerToken`.

## Key Decisions

1. Use `msgId` as the idempotency key because the table already models it as the primary key.
2. Keep the first payload contract minimal so it matches the current schema exactly.
3. Treat duplicate webhook deliveries as a first-class expected case rather than as a generic error.
4. Keep account existence checks aligned with the existing `zalo_accounts` foreign-key relation.
5. Align message ingest with `Listen` mode so the spec does not imply concurrent `Send` ownership for the same account.
6. Treat account-mode lookup as a required step in the ingest pipeline rather than an optional enhancement.
7. Prefer event extraction from the already-open browser session because a duplicate session or duplicate socket owner for one account is an unsafe design.
8. Trust `listenerToken` mapping inside the tool instead of trusting extension-supplied account identifiers.
9. Treat duplicate `msgId` deliveries as `already_processed`, not as hard failures.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| External listener payloads drift from the contract | High | Define one canonical payload shape and validate strictly |
| Duplicate retries create duplicate rows | High | Use `msgId` as the idempotent key |
| DB foreign-key failures confuse webhook callers | Medium | Translate them into clear rejected responses |
| Transport and persistence logic get mixed together | Medium | Keep route handler thin and use-case driven |
| One account receives webhook traffic while active in manual send mode | High | Model this as an account-mode conflict and surface it explicitly |
| Account mode is not stored consistently enough to enforce behavior | High | Define one authoritative mode source before implementation |
| Listener implementation opens a second live Zalo session and gets the account disconnected | High | Use a profile-bound in-browser listener that observes the existing session instead of creating another one |
| Extension spoofs another account ID | High | Resolve account identity from `listenerToken` inside the tool instead of trusting raw account IDs |

## Validation Strategy

### Automated

- Test valid `listenerToken` resolution.
- Test invalid `listenerToken` rejection.
- Test valid payload insertion.
- Test rejection of malformed payloads.
- Test duplicate `msgId` handling.
- Test unknown token/account mapping handling.
- Test accept behavior when account mode is `Listen`.
- Test reject/conflict behavior when account mode is `Send`.
- Test mode lookup failures or missing mode state according to the chosen enforcement rule.
- Test repository error translation.
- Test that the chosen listener contract assumes event extraction from the existing profile session rather than cookie reuse in a second session.

### Manual

- Post a valid sample payload to the webhook endpoint and verify the row appears in `messages`.
- Post the same payload twice and verify only one row exists.
- Post an invalid payload and verify no row is inserted.
- Post a payload for an account currently active in `Listen` and verify normal acceptance.
- Post a payload for an account currently marked as `Send` and verify the conflict behavior.
- Post a payload with an invalid `listenerToken` and verify it is rejected before persistence.
- Verify the listener runs inside the logged-in browser/profile session and does not trigger duplicate-session disconnect behavior during normal operation.
