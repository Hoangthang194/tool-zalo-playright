# Workflow JSON Contract

## Root Shape

```json
{
  "name": "string",
  "browser": {},
  "steps": []
}
```

## Browser Object

```json
{
  "engine": "chromium",
  "channel": "chrome",
  "headless": false,
  "slow_mo_ms": 200,
  "timeout_ms": 15000,
  "base_url": "https://example.com",
  "viewport": {
    "width": 1440,
    "height": 900
  }
}
```

### Browser Rules

- `engine` defaults to `chromium` when omitted.
- `channel` is optional and only valid with `engine = "chromium"`.
- `slow_mo_ms` and `timeout_ms` must be integers `>= 0`.
- `viewport.width` and `viewport.height` must be integers `> 0`.

## Step Object

```json
{
  "name": "Open home page",
  "action": "goto",
  "url": "/"
}
```

## Supported Baseline Actions

### `goto`

Required fields:

- `url`

### `click`

Required fields:

- `selector`

### `fill`

Required fields:

- `selector`
- `text`

### `press`

Required fields:

- `selector`
- `key`

### `wait_for_selector`

Required fields:

- `selector`

### `wait_for_timeout`

Required fields:

- `milliseconds`

### `screenshot`

Required fields:

- `path`

Optional fields:

- `full_page`

## Shared Step Rules

- Each step may include `name`.
- Each step may include `timeout_ms` as a per-step override.
- Integer fields must not be booleans.
- Unsupported actions must be rejected before browser execution.

