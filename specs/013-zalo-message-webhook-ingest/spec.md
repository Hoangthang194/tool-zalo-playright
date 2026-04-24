# Feature Specification: Zalo Message Webhook Ingest to Database

## Status

Implemented in code. Manual MariaDB verification is still pending.

## Summary

Design a webhook-based message ingest flow so a profile-bound Zalo listener can send incoming message events into this tool, and the tool can persist them into the `messages` table in MariaDB.

The flow must support a per-account operating mode where one account is explicitly activated as either `Listen` or `Send`.

When an account is active in `Listen`, the preferred listener model is a browser extension or equivalent in-browser integration attached to that same Chrome profile and Zalo Web session. That listener may post incoming message events into this tool and the tool persists them into the `messages` table in MariaDB.

When an account is active in `Send`, that same account is reserved for browser/manual automation and webhook ingest for that account must not proceed as a normal accepted delivery.

Accepted listener deliveries must store the normalized result in:

- `messages.msgId`
- `messages.fromGroupId`
- `messages.toGroupId`
- `messages.fromAccountId`
- `messages.content`

## Problem Statement

The project now has a database schema with a minimal `messages` table, but no defined ingestion contract for how message events arrive from running Zalo sessions.

The desktop tool can launch Zalo accounts and already has adjacent specs around session export and webhook integration, but there is no formal feature contract for:

- receiving incoming message payloads from a listener attached to the active browser/profile session
- validating and normalizing those payloads
- mapping them to the current `messages` schema
- persisting them safely into the database

There is also an important runtime constraint for Zalo Web sessions: one account should not be treated as both a live manual-send session and a live listener owner at the same time. The system therefore needs message ingest behavior aligned with an account-mode model:

- `Listen` mode: the account is owned by the listener side
- `Send` mode: the account is owned by the manual/browser side

Webhook ingest belongs to the `Listen` side of that split, and the active mode on an account determines which runtime path is allowed to execute.

There is an additional integration constraint: a separate out-of-process listener that opens another Zalo WebSocket connection for the same account may trigger duplicate-connection behavior and destabilize the logged-in session. This feature therefore prefers an in-profile listener model that observes the existing browser session instead of establishing a second session for the same account.

Without this spec, the message table risks remaining unused or being populated inconsistently across profiles and accounts.

## Goals

- Define the account-mode behavior for `Listen` and `Send` as it applies to webhook ingest.
- Define a webhook ingest contract for incoming Zalo messages.
- Prefer a listener architecture that stays inside the same Chrome profile/session already used by Zalo Web.
- Accept message events associated with a Zalo account that is active in `Listen` mode.
- Normalize the payload into the current `messages` table shape.
- Persist messages into MariaDB safely and idempotently.
- Keep webhook transport, payload validation, and database persistence outside Tkinter code.

## Non-Goals

- Implementing the browser extension or injected listener itself in this feature.
- Reworking the current `messages` table schema.
- Building a full message-forwarding engine.
- Rendering a new message-monitoring dashboard in the GUI.
- Supporting arbitrary third-party payload formats without a defined contract.
- Defining a second standalone Zalo session for the same account just for listening.

## Primary Users

### Zalo Operator

Needs incoming Zalo messages captured from running profiles/accounts and written into the database.

### Integrator

Needs a stable webhook contract so a profile-bound listener can post message events reliably.

### Maintainer

Needs message ingest, validation, and persistence to fit existing clean architecture boundaries.

## User Stories

1. As an operator, I want incoming messages from my launched Zalo sessions saved to the database so they can be reviewed or processed later.
2. As an integrator, I want a stable webhook payload contract so my profile-bound listener can post messages without guessing field names.
3. As a maintainer, I want message ingest to map cleanly into the existing `messages` table so persistence is deterministic.
4. As a maintainer, I want duplicate webhook deliveries to be safe so retries do not create duplicate message rows.
5. As an operator, I want one account to alternate between `Listen` and `Send` responsibilities instead of trying to perform both simultaneously.
6. As an operator, I want the active option on an account to decide whether that account listens for incoming messages or performs send automation.

## Data Contract

### Target Table: `messages`

The feature MUST persist into the existing `messages` table.

Required destination fields:

- `msgId`
- `fromGroupId`
- `toGroupId`
- `fromAccountId`
- `content`

### Proposed Webhook Payload

The ingest endpoint SHOULD accept JSON shaped like:

```json
{
  "listenerToken": "ltkn_123",
  "msgId": "msg-123",
  "fromGroupId": "group-a",
  "toGroupId": "group-b",
  "content": "hello"
}
```

The preferred local endpoint is an HTTP webhook exposed by the tool on localhost, for example:

- `POST http://127.0.0.1:<port>/webhooks/zalo/messages`

Additional optional metadata MAY be accepted later, but this feature MUST define the above fields as the canonical minimum payload sent by the extension/listener.

The sender of this payload SHOULD be a listener component attached to the same Chrome profile/session that is already logged into `chat.zalo.me`.

Rules:

- `listenerToken` MUST be present and non-empty
- `msgId` MUST be present and non-empty
- `content` MUST be present, though it MAY be an empty string only if later business rules explicitly allow that
- `fromGroupId` and `toGroupId` MAY be null or blank if the listener cannot resolve them, but the behavior must be specified
- the tool MUST resolve `listenerToken` to a known account/profile mapping before persistence
- the tool MUST NOT trust the extension to authoritatively choose `fromAccountId` in the persistence layer

### Listener Source Contract

The preferred message source for this feature is:

- a Chrome extension, content script, injected page script, or equivalent browser-resident listener
- attached to the same Chrome profile already used for the account
- observing the already-active `chat.zalo.me` session
- extracting message events by injecting a script that hooks the page's WebSocket/event flow
- forwarding normalized message payloads to the webhook endpoint

The feature SHOULD avoid a design that:

- extracts cookies from one session into a second independent listener process
- opens a second direct Zalo WebSocket connection for the same logged-in account
- depends on concurrent duplicate live connections for one account

## Account Mode Alignment

The webhook-ingest flow MUST align with an account-mode model in which one account has one active responsibility at a time:

- `Listen`: the account is owned by the listener/webhook pipeline
- `Send`: the account is owned by the visible/manual send pipeline

Rules:

- the account must expose a selectable operating option that resolves to `Listen` or `Send`
- only one operating mode may be active for a given account at a time
- activating `Listen` means that account is eligible for webhook ingest and should be considered listener-owned
- activating `Send` means that account is eligible for browser/manual send automation and should be considered send-owned
- webhook ingest is valid only for accounts that are active in `Listen` mode or otherwise designated as listener-owned
- webhook ingest for an account active in `Send` mode MUST be rejected or surfaced as a mode conflict instead of being silently accepted
- a message webhook MUST NOT be treated as proof that one account can safely perform simultaneous listener and manual-send ownership
- this feature assumes account-mode coordination is enforced by adjacent account-mode features or by runtime orchestration outside the webhook route itself

Listener ownership for `Listen` mode SHOULD be implemented by attaching the listener to that same profile's active browser session, not by opening a separate duplicate session for the same account.

### Operational Interpretation

For this feature, the intended runtime behavior is:

- if the operator activates `Listen` on an account, that account handles message-listening responsibilities and webhook deliveries for that account may be accepted
- if the operator activates `Send` on an account, that account handles message-sending/browser responsibilities and webhook deliveries for that account must not continue as normal ingest
- if the active mode changes while a listener delivery is in flight, the ingest flow must resolve the request deterministically as accepted, duplicate, or rejected-conflict based on the mode check used by the implementation
- if the implementation uses a browser extension or injected listener, that listener should observe the existing logged-in tab/session for the profile instead of creating an additional parallel Zalo session
- if the implementation uses `listenerToken`, token resolution inside the tool must determine the final `fromAccountId` used for persistence

## Functional Requirements

### Webhook Endpoint

- FR-001: The system MUST define one webhook endpoint for incoming message events.
- FR-002: The webhook endpoint MUST accept JSON payloads over HTTP on a local tool endpoint.
- FR-003: The webhook endpoint MUST validate that the payload contains the required message fields before persistence.
- FR-004: The webhook endpoint SHOULD support an authentication secret or token if webhook security is enabled in configuration.
- FR-005: The webhook endpoint MUST return an explicit success or validation-failure response to the caller.

### Listener Source and Session Safety

- FR-006: The feature SHOULD treat an in-browser, profile-bound listener as the preferred event source for webhook deliveries.
- FR-007: The preferred listener source SHOULD attach to the same Chrome profile and active `chat.zalo.me` session already used by the operator.
- FR-008: The feature MUST NOT require opening a second standalone Zalo Web session for the same account in order to ingest messages.
- FR-009: If a listener implementation would create a duplicate live session or duplicate direct WebSocket ownership for the same account, that design SHOULD be rejected or called out as unsafe.
- FR-010: The preferred listener extraction strategy SHOULD inject a script into `chat.zalo.me` and hook the page's WebSocket/event flow rather than relying on DOM scraping alone.

### Payload Validation and Normalization

- FR-011: The ingest flow MUST validate `listenerToken` as required.
- FR-012: The ingest flow MUST validate `msgId` as required.
- FR-013: The ingest flow MUST validate `content` according to the agreed minimum message contract.
- FR-014: The ingest flow MUST resolve `listenerToken` to an internal account/profile mapping before insert.
- FR-015: The ingest flow MUST derive persisted `fromAccountId` from that internal mapping rather than trusting an extension-supplied account ID.
- FR-016: The ingest flow MUST normalize payload fields into the exact `messages` table column names or an equivalent application model before insert.
- FR-017: If the payload is malformed or missing required fields, the message MUST NOT be inserted.

### Account Mode Behavior

- FR-018: The message-ingest flow MUST treat the profile-bound listener as the active owner of an account in `Listen` mode.
- FR-019: The feature MUST assume that one account is not intended to perform `Listen` and `Send` ownership simultaneously.
- FR-020: The system MUST define account-mode state in configuration, persistence, or runtime orchestration so the webhook ingest path can determine whether the token-resolved account is currently allowed to ingest listener events.
- FR-021: If the token-resolved account is currently active in `Send` mode, the webhook ingest path MUST reject or flag the delivery as an account-mode conflict.
- FR-022: The system MUST treat account-mode activation as mutually exclusive per account.
- FR-023: The system SHOULD expose account mode to the operator as an explicit option or equivalent account setting rather than inferring it from webhook traffic alone.

### Persistence

- FR-024: A valid webhook message MUST be inserted into the `messages` table.
- FR-025: The ingest flow MUST persist `msgId`, `fromGroupId`, `toGroupId`, token-resolved `fromAccountId`, and `content`.
- FR-026: The database insert MUST be idempotent for repeated deliveries of the same `msgId`.
- FR-027: If the same `msgId` is received again, the system MUST avoid creating duplicate rows and SHOULD return `already_processed` or an equivalent duplicate-safe result.
- FR-028: Database failures MUST be surfaced as webhook-ingest failures rather than silently ignored.
- FR-029: If `listenerToken` cannot be resolved to a known account, the endpoint MUST return an actionable authentication or mapping failure.
- FR-030: If token resolution succeeds but the resolved `fromAccountId` cannot be persisted under the current schema, the endpoint MUST return an actionable failure.

### Architecture Boundaries

- FR-031: Webhook transport handling MUST remain outside Tkinter code.
- FR-032: Message validation, token resolution, and normalization MUST live in application-layer logic or equivalent service boundaries.
- FR-033: MariaDB insert logic MUST live in repository or infrastructure adapters, not in the HTTP route handler itself.
- FR-034: The feature SHOULD define a dedicated application request/result model for message ingest instead of inserting raw JSON directly from the HTTP handler.
- FR-035: If a browser extension or injected listener is used, its responsibility MUST stop at event extraction and webhook delivery rather than direct database writes.

### Observability and Safety

- FR-036: The ingest flow MUST return enough response detail for the caller to know whether the message was accepted, rejected, or skipped as duplicate.
- FR-037: The system SHOULD log webhook-ingest failures without leaking secrets.
- FR-038: The system SHOULD distinguish validation failure, invalid token, duplicate delivery, account-mode conflict, and database failure in logs or results.
- FR-039: The system SHOULD log or surface when a listener design is rejected because it would create duplicate live-session ownership for the same account.

## Non-Functional Requirements

- NFR-001: The webhook ingest path SHOULD be simple enough to run as a small service endpoint alongside later integration features.
- NFR-002: Duplicate delivery handling SHOULD be deterministic.
- NFR-003: The feature SHOULD remain compatible with the existing MariaDB schema without requiring schema changes.
- NFR-004: The implementation SHOULD be testable without launching the GUI.

## Acceptance Scenarios

### Scenario 1: Persist a Valid Message

- Given a valid Zalo account exists in `zalo_accounts`
- And that account is active in `Listen` mode
- And the webhook endpoint receives a valid JSON payload from the same profile-bound browser listener
- And the payload contains a valid `listenerToken`
- When the payload includes `msgId`, `fromGroupId`, `toGroupId`, and `content`
- Then the message is inserted into `messages`
- And the endpoint returns success

### Scenario 2: Reject Invalid Payload

- Given the webhook endpoint receives a payload missing `msgId`
- When validation runs
- Then the payload is rejected
- And no row is inserted into `messages`

### Scenario 3: Ignore Duplicate Delivery

- Given a message with `msgId = msg-123` already exists
- When the webhook endpoint receives the same `msgId` again
- Then the system does not insert a duplicate row
- And the response indicates the delivery was duplicate or already processed

### Scenario 4: Reject Unknown Account

- Given the payload contains a `listenerToken` that does not map to a known account
- When token resolution is attempted
- Then the endpoint returns an actionable authentication or mapping failure
- And the invalid row is not inserted

### Scenario 5: Reject or Flag Send-Mode Conflict

- Given the payload contains a valid `listenerToken` for an account that is currently active in `Send` mode
- When the webhook endpoint processes the payload
- Then the system rejects or flags the delivery as an account-mode conflict according to runtime configuration
- And the conflict is surfaced clearly in the result

### Scenario 6: Accept Listen-Mode Ownership

- Given an operator has activated `Listen` for one account
- And the listener is attached to that same logged-in browser profile/session
- When the listener posts a valid payload for that same account
- Then the webhook flow accepts normal ingest for that account
- And the account is treated as listener-owned for this feature

### Scenario 7: Mode Option Switches Account Responsibility

- Given an account was previously active in `Listen`
- When the operator switches that account to `Send`
- Then subsequent webhook deliveries for that account are no longer processed as normal listener ingests
- And browser/manual send behavior becomes the active responsibility for that account

### Scenario 8: Reject Unsafe Duplicate-Session Listener Design

- Given an implementation proposal would open a second direct Zalo session or duplicate WebSocket ownership for an already logged-in account
- When the listener architecture is evaluated for this feature
- Then that design is treated as unsafe for the preferred implementation path
- And the feature instead prefers a listener attached to the existing profile/session

## Edge Cases

- The webhook payload is valid JSON but contains blank strings for required fields.
- The listener retries after a timeout but the previous insert already succeeded.
- The database is temporarily unavailable.
- The payload uses a message ID longer than expected by the schema.
- The account exists but `fromGroupId` or `toGroupId` is missing.
- The account is switching between `Listen` and `Send` while a webhook delivery arrives.
- A proposed listener implementation opens another direct Zalo connection and triggers duplicate-connection behavior.
- The extension sends an expired, unknown, or mismatched `listenerToken`.

## Success Metrics

- Incoming Zalo messages from external listener services can be written into the `messages` table reliably.
- Duplicate webhook retries do not create duplicate message rows.
- Message persistence behavior is clearly defined before implementation.
- The feature contract no longer implies that one account should be both listener-owned and manual-send-owned at the same time.
- The active option on an account clearly determines whether that account is currently used for `Listen` or `Send`.
- The preferred listener architecture avoids opening a second live Zalo session for the same account.
- The tool trusts `listenerToken` resolution rather than raw account IDs from the extension payload.
