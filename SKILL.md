---
name: aiofm-adapter
description: Use this skill when an agent needs to work with a dash.aiofm.cc workspace through the public Python REST adapter instead of MCP. It covers install, environment setup, tool discovery, tool calls, and prompt generation for Claude Code, Codex, OpenHands, or generic shell-based runtimes.
---

# aiofm-adapter

Use this repository as the default integration path for `dash.aiofm.cc` workspaces when the runtime can execute shell commands or HTTP requests but MCP is unavailable or unreliable.

## Quick start

1. Ensure these environment variables are available:
   - `AIOFM_BASE_URL`
   - `AIOFM_WORKSPACE_ID`
   - `DASH_AIOFM_AGENT_KEY`
2. Prefer the installed CLI:
   - `aiofm-adapter doctor --json`
   - `aiofm-adapter manifest --json`
   - `aiofm-adapter tools list --json`
3. Call tools through the adapter:
   - `aiofm-adapter tools call list_accounts --json`
   - `aiofm-adapter tools call report_activity --input-json '{"summary":"Prepared draft batch"}' --json`

## Fallback

If the console script is unavailable, use the module path from the repo root:

```bash
PYTHONPATH=src python -m aiofm_adapter.cli tools list --json
```

## Tool contract

- Authenticate with `Authorization: Bearer <workspace_agent_key>`
- Read `/manifest` or `/tools` before the first call in a fresh runtime
- Send tool inputs only inside the JSON field `arguments`
- Treat the adapter response as the source of truth
- If the adapter is unavailable, stop and report `Adapter not attached`

## Prompt generation

Use the built-in prompt generator when the runtime needs copy-ready setup text:

- `aiofm-adapter prompt claude`
- `aiofm-adapter prompt codex`
- `aiofm-adapter prompt openhands`
- `aiofm-adapter prompt generic`

## When to read other files

- Read [README.md](README.md) for end-user install snippets and raw `curl` examples
- Read [src/aiofm_adapter/cli.py](src/aiofm_adapter/cli.py) only when changing command behavior
- Read [src/aiofm_adapter/client.py](src/aiofm_adapter/client.py) only when changing HTTP/auth behavior
