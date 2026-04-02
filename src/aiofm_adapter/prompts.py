from __future__ import annotations

from aiofm_adapter.client import AGENT_KEY_ENV_NAME, BASE_URL_ENV_NAME, WORKSPACE_ID_ENV_NAME, AdapterConfig


def build_env_block(config: AdapterConfig) -> str:
    return "\n".join(
        [
            f'{BASE_URL_ENV_NAME}="{config.normalized_base_url}"',
            f'{WORKSPACE_ID_ENV_NAME}="{config.workspace_id}"',
            f'{AGENT_KEY_ENV_NAME}="{config.agent_key}"',
        ]
    )


def build_agent_brief(config: AdapterConfig) -> str:
    return f"""You are the content maker for workspace {config.workspace_id} in dash.aiofm.cc.

Use only the official aiofm REST adapter `aiofm-adapter` or the documented REST endpoints as the source of truth.

Workflow:
1. Start with list_accounts.
2. Review existing drafts with list_posts or get_post_status before editing.
3. Create or update drafts with create_post or update_post.
4. Use submit_for_approval when approval is required.
5. Use schedule_post only when approval policy allows it.
6. Use report_activity after each meaningful batch.

Strict rules:
- If the adapter is unavailable, stop and report `Adapter not attached`.
- Do not invent hidden endpoints or undocumented request fields.
- Do not send requests outside the documented REST adapter contract.
- Never invent publish success, approval state, or account health.
- If an account or provider looks broken, report it and continue preparing drafts.
- Ask for missing goal, audience, CTA, language, or timing when required.
- create_post must include scheduled_at.
- If the operator does not specify a timezone, assume UTC.
- Dashboard times are displayed in browser-local time, but stored and enforced in UTC.
- Only one future post per hour is allowed for the same social_account_id.
- If scheduled_at is missing or conflicts with spacing rules, stop and surface the API error exactly.

Connection:
- rest_endpoint: {config.rest_endpoint}
- manifest_url: {config.manifest_url}
- tools_url: {config.tools_url}
- preferred_cli: aiofm-adapter tools list --json"""


def build_install_block(repo_url: str) -> str:
    return f"""Install
uv tool install --refresh git+{repo_url}

Fallback
pipx install git+{repo_url}

Editable clone
git clone {repo_url}
cd aiofm-adapter
python -m pip install -e ."""


def build_runtime_prompt(*, runtime_name: str, config: AdapterConfig, repo_url: str) -> str:
    return f"""{runtime_name} setup

{build_install_block(repo_url)}

Runtime environment
{build_env_block(config)}

Prompt
{build_agent_brief(config)}

Execution rules
- Prefer shell calls to `aiofm-adapter` over handwritten curl when both are possible.
- Always request JSON output.
- Call `aiofm-adapter tools list --json` once before the first tool call in a fresh session.
- Send tool inputs only through the adapter or the documented `arguments` JSON field.
- Keep {AGENT_KEY_ENV_NAME} out of chat history, logs, screenshots, and commits."""


def build_generic_setup(config: AdapterConfig, *, repo_url: str) -> str:
    return f"""Environment
{build_env_block(config)}

REST endpoints
rest_endpoint: {config.rest_endpoint}
manifest_url: {config.manifest_url}
tools_url: {config.tools_url}

{build_install_block(repo_url)}

CLI quickstart
aiofm-adapter tools list --json
aiofm-adapter tools call list_accounts --json
aiofm-adapter tools call create_post --input-json '{{"social_account_id":"<account_id>","title":"Launch draft","scheduled_at":"2026-04-03T14:00:00Z","image_binary":"<base64>"}}' --json
aiofm-adapter tools call report_activity --input-json '{{"summary":"Prepared draft batch"}}' --json

Scheduling rules
- create_post must include scheduled_at.
- If the operator does not specify a timezone, assume UTC.
- Dashboard times are displayed in browser-local time, but stored and enforced in UTC.
- Only one future post per hour is allowed for the same social_account_id.
- If scheduled_at is missing or conflicts with the one-post-per-hour rule, stop and report the API error exactly.

Raw REST examples
curl -fsS {config.manifest_url} -H "Authorization: Bearer {config.agent_key}"
curl -fsS {config.tools_url} -H "Authorization: Bearer {config.agent_key}"
curl -fsS {config.rest_endpoint}/tools/list_accounts \\
  -H "Authorization: Bearer {config.agent_key}" \\
  -H "Content-Type: application/json" \\
  -d '{{"arguments":{{}}}}'"""


def build_prompt_for_target(*, target: str, config: AdapterConfig, repo_url: str) -> str:
    normalized_target = target.lower()

    if normalized_target == "claude":
        return build_runtime_prompt(runtime_name="Claude Code", config=config, repo_url=repo_url)

    if normalized_target == "codex":
        return build_runtime_prompt(runtime_name="OpenAI Codex", config=config, repo_url=repo_url)

    if normalized_target == "openhands":
        return build_runtime_prompt(runtime_name="OpenHands", config=config, repo_url=repo_url)

    if normalized_target == "generic":
        return build_generic_setup(config, repo_url=repo_url)

    raise ValueError(f"Unsupported prompt target: {target}")
