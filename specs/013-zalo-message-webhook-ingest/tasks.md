# Tasks: Zalo Message Webhook Ingest to Database

## Phase 1: Spec and Contract

- [ ] T001 Add `spec.md`, `plan.md`, and `tasks.md` for webhook-based message ingest.
- [ ] T002 Define the canonical local webhook payload for `listenerToken`, `msgId`, `fromGroupId`, `toGroupId`, and `content`.
- [ ] T003 Confirm duplicate handling is keyed by `msgId`.
- [ ] T004 Align the webhook-ingest contract with the account-mode model where one account alternates between `Listen` and `Send`.
- [ ] T005 Define that the active mode option on an account decides whether that account may ingest webhook events or run send automation.
- [ ] T006 Define the preferred listener source as a browser-resident integration attached to the same logged-in profile/session.
- [ ] T007 Define `listenerToken` as the account-resolution mechanism and prohibit trusting raw account IDs from the extension payload.

## Phase 2: Application Design

- [ ] T008 Add an application request/result model for message ingest.
- [ ] T009 Define validation rules for required payload fields, especially `listenerToken` and `msgId`.
- [ ] T010 Add a `listenerToken` resolution step before normal ingest.
- [ ] T011 Add an account-mode resolution step for the token-resolved account before normal ingest.
- [ ] T012 Define application outcomes for accepted, duplicate, invalid-token, rejected, account-mode-conflict, and failed inserts.

## Phase 3: Infrastructure Design

- [ ] T013 Add a browser listener design that injects a script, hooks WebSocket/event flow in the existing `chat.zalo.me` profile session, and forwards events to the local webhook.
- [ ] T014 Add token lookup infrastructure for resolving `listenerToken` to the owning account/profile.
- [ ] T015 Add a MariaDB-backed repository/adapter for inserting into `messages`.
- [ ] T016 Translate duplicate-key and foreign-key DB failures into application-level results.
- [ ] T017 Add a localhost HTTP webhook handler that delegates to the application layer.
- [ ] T018 Add listener/send-mode conflict checking before persistence using the chosen account-mode source.
- [ ] T019 Reject or document unsafe listener designs that depend on opening a second standalone Zalo session for the same account.

## Phase 4: Verification

- [ ] T020 Write the failing tests first for valid token resolution and accepted insert behavior.
- [ ] T021 Write the failing tests first for malformed payload rejection.
- [ ] T022 Write the failing tests first for invalid `listenerToken` rejection.
- [ ] T023 Write the failing tests first for duplicate `msgId` returning `already_processed`.
- [ ] T024 Write the failing tests first for accept behavior when account mode is `Listen`.
- [ ] T025 Write the failing tests first for reject/conflict behavior when account mode is `Send`.
- [ ] T026 Write the failing tests first for repository/db error translation.
- [ ] T027 Add verification that the listener contract assumes reuse of the existing profile session rather than a second session.
- [ ] T028 Manually verify that local webhook payloads persist into `messages`.
