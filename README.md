# aiofm-adapter

Universal Python REST adapter for `dash.aiofm.cc` workspaces.

The goal is simple: any agent runtime that can run a shell command or make an HTTP request should be able to use the same workspace contract without MCP.

## What this gives you

- one public Python CLI
- one REST contract
- one prompt format for Claude Code, Codex, OpenHands, and generic shells
- no protocol framing, no session handshake, no custom transport runtime

## Install

Recommended:

```bash
uv tool install --refresh git+https://github.com/aiofmadmin/aiofm-adapter
```

Fallbacks:

```bash
pipx install git+https://github.com/aiofmadmin/aiofm-adapter
```

```bash
git clone https://github.com/aiofmadmin/aiofm-adapter
cd aiofm-adapter
python -m pip install -e .
```

## Environment

```bash
export AIOFM_BASE_URL="https://dash.aiofm.cc"
export AIOFM_WORKSPACE_ID="<workspace_id>"
export DASH_AIOFM_AGENT_KEY="<workspace_agent_key>"
```

## Quick start

```bash
aiofm-adapter doctor --json
aiofm-adapter manifest --json
aiofm-adapter tools list --json
aiofm-adapter tools call list_accounts --json
aiofm-adapter tools call create_post --input-json '{"social_account_id":"<account_id>","title":"Launch draft","scheduled_at":"2026-04-03T14:00:00Z","image_binary":"<base64>"}' --json
aiofm-adapter tools call report_activity --input-json '{"summary":"Prepared draft batch"}' --json
```

## Scheduling rules

- `create_post` must include `scheduled_at`
- if the operator does not specify a timezone, assume UTC
- dashboard times are displayed in browser-local time, but stored and enforced in UTC
- only one future post per hour is allowed for the same `social_account_id`
- if `scheduled_at` is missing or conflicts with spacing rules, surface the API error exactly

## Direct REST contract

Manifest:

```bash
curl -fsS "https://dash.aiofm.cc/api/adapter/workspaces/<workspace_id>/manifest" \
  -H "Authorization: Bearer <workspace_agent_key>"
```

List tools:

```bash
curl -fsS "https://dash.aiofm.cc/api/adapter/workspaces/<workspace_id>/tools" \
  -H "Authorization: Bearer <workspace_agent_key>"
```

Call a tool:

```bash
curl -fsS "https://dash.aiofm.cc/api/adapter/workspaces/<workspace_id>/tools/list_accounts" \
  -H "Authorization: Bearer <workspace_agent_key>" \
  -H "Content-Type: application/json" \
  -d '{"arguments":{}}'
```

## Runtime-specific prompts

Claude Code:

```bash
aiofm-adapter prompt claude
```

OpenAI Codex:

```bash
aiofm-adapter prompt codex
```

OpenHands:

```bash
aiofm-adapter prompt openhands
```

Generic shell/runtime:

```bash
aiofm-adapter prompt generic
```

## Supported commands

- `aiofm-adapter doctor`
- `aiofm-adapter manifest`
- `aiofm-adapter tools list`
- `aiofm-adapter tools call <tool_name>`
- `aiofm-adapter prompt <claude|codex|openhands|generic>`

## Supported tools

- `list_accounts`
- `list_posts`
- `get_post_status`
- `create_post`
- `update_post`
- `schedule_post`
- `submit_for_approval`
- `approve_post`
- `report_activity`

## Development

Run the built-in tests:

```bash
PYTHONPATH=src python -m unittest discover -s tests
```
