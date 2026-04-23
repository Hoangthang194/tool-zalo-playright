# Feature Specification: Zalo Attribute-Based Click Targets

## Status

Implemented.

## Summary

Extend `Class Manage` selector handling so operators can target Zalo elements by custom attributes such as `data-id` and `anim-data-id` without writing raw CSS selectors manually.

## Problem Statement

Many Zalo Web elements do not expose a stable HTML `id` attribute. Instead, they use attributes such as `data-id` and `anim-data-id`. Requiring operators to switch to raw CSS every time increases friction and makes the click-target workflow less consistent.

## Goals

- Support direct selector types for `data-id` and `anim-data-id`.
- Keep selector normalization and CSS conversion in application logic, not Tkinter code.
- Preserve existing selector types such as `class`, `id`, `css`, and `html`.

## Functional Requirements

- FR-001: `Class Manage` MUST allow the operator to save a click target using selector type `data-id`.
- FR-002: `Class Manage` MUST allow the operator to save a click target using selector type `anim-data-id`.
- FR-003: The selector helper MUST convert `data-id` values into a valid CSS attribute selector.
- FR-004: The selector helper MUST convert `anim-data-id` values into a valid CSS attribute selector.
- FR-005: HTML snippet parsing SHOULD detect `anim-data-id` when it is the strongest available stable selector on an element.

## Acceptance Scenarios

### Scenario 1: Save and Test by Anim Data ID

- Given the operator has a Zalo element with `anim-data-id="g1509445607335510374"`
- When the operator saves a click target with selector type `anim-data-id`
- And enters `g1509445607335510374`
- And clicks `Test Element`
- Then the app resolves a CSS selector for that attribute
- And uses it for the explicit test click
