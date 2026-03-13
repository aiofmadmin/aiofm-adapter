from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from aiofm_adapter.client import (
    DEFAULT_CLIENT_NAME,
    DEFAULT_CLIENT_VERSION,
    AdapterError,
    build_config,
    call_tool,
    get_manifest,
    list_tools,
)
from aiofm_adapter.prompts import build_agent_brief, build_prompt_for_target


REPO_URL = "https://github.com/aiofmadmin/aiofm-adapter"
EXIT_INVALID_INPUT = 10
EXIT_CONFIGURATION = 20
EXIT_REMOTE_ERROR = 30


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aiofm-adapter", description="Universal Python REST adapter for dash.aiofm.cc workspaces")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor_parser = subparsers.add_parser("doctor", help="Validate config resolution and print derived URLs")
    _add_connection_arguments(doctor_parser)
    doctor_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    doctor_parser.set_defaults(handler=_handle_doctor)

    manifest_parser = subparsers.add_parser("manifest", help="Fetch adapter manifest")
    _add_connection_arguments(manifest_parser)
    manifest_parser.add_argument("--json", action="store_true", help="Print raw JSON response")
    manifest_parser.set_defaults(handler=_handle_manifest)

    prompt_parser = subparsers.add_parser("prompt", help="Generate a copy-ready prompt block for a runtime")
    _add_connection_arguments(prompt_parser)
    prompt_parser.add_argument("target", choices=["claude", "codex", "openhands", "generic"])
    prompt_parser.set_defaults(handler=_handle_prompt)

    tools_parser = subparsers.add_parser("tools", help="List tools or call a tool")
    tools_subparsers = tools_parser.add_subparsers(dest="tools_command", required=True)

    tools_list_parser = tools_subparsers.add_parser("list", help="Fetch the tool catalog")
    _add_connection_arguments(tools_list_parser)
    tools_list_parser.add_argument("--json", action="store_true", help="Print raw JSON response")
    tools_list_parser.set_defaults(handler=_handle_tools_list)

    tools_call_parser = tools_subparsers.add_parser("call", help="Call a tool through the REST adapter")
    _add_connection_arguments(tools_call_parser)
    tools_call_parser.add_argument("tool_name")
    tools_call_parser.add_argument("--input-json", default="", help="Inline JSON object for the arguments payload")
    tools_call_parser.add_argument("--input-file", default="", help="Path to a JSON file containing arguments")
    tools_call_parser.add_argument("--stdin", action="store_true", help="Read arguments JSON from stdin")
    tools_call_parser.add_argument("--json", action="store_true", help="Print raw JSON response")
    tools_call_parser.set_defaults(handler=_handle_tools_call)

    return parser


def _add_connection_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--base-url", default="")
    parser.add_argument("--workspace-id", default="")
    parser.add_argument("--agent-key", default="")
    parser.add_argument("--client-name", default=DEFAULT_CLIENT_NAME)
    parser.add_argument("--client-version", default=DEFAULT_CLIENT_VERSION)
    parser.add_argument("--timeout-seconds", type=int, default=30)


def _print_payload(payload: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, ensure_ascii=True))
        return

    print(json.dumps(payload, indent=2, ensure_ascii=True))


def _load_arguments(arguments: argparse.Namespace) -> dict[str, Any]:
    if arguments.stdin:
        raw_value = sys.stdin.read().strip()
        return _parse_json_object(raw_value)

    if arguments.input_file:
        with open(arguments.input_file, "r", encoding="utf-8") as input_file:
            return _parse_json_object(input_file.read())

    if arguments.input_json:
        return _parse_json_object(arguments.input_json)

    return {}


def _parse_json_object(raw_value: str) -> dict[str, Any]:
    if not raw_value.strip():
        return {}

    try:
        parsed = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise AdapterError("Arguments must be valid JSON.", status_code=EXIT_INVALID_INPUT) from exc

    if not isinstance(parsed, dict):
        raise AdapterError("Arguments JSON must be an object.", status_code=EXIT_INVALID_INPUT)

    return parsed


def _resolve_config(arguments: argparse.Namespace):
    return build_config(
        base_url=arguments.base_url,
        workspace_id=arguments.workspace_id,
        agent_key=arguments.agent_key,
        client_name=arguments.client_name,
        client_version=arguments.client_version,
        timeout_seconds=arguments.timeout_seconds,
    )


def _handle_doctor(arguments: argparse.Namespace) -> int:
    config = _resolve_config(arguments)
    payload = {
        "ok": True,
        "base_url": config.normalized_base_url,
        "workspace_id": config.workspace_id,
        "rest_endpoint": config.rest_endpoint,
        "manifest_url": config.manifest_url,
        "tools_url": config.tools_url,
        "client_name": config.client_name,
        "client_version": config.client_version,
    }
    _print_payload(payload, as_json=arguments.json)
    return 0


def _handle_manifest(arguments: argparse.Namespace) -> int:
    config = _resolve_config(arguments)
    payload = get_manifest(config)
    _print_payload(payload, as_json=arguments.json)
    return 0


def _handle_tools_list(arguments: argparse.Namespace) -> int:
    config = _resolve_config(arguments)
    payload = list_tools(config)
    _print_payload(payload, as_json=arguments.json)
    return 0


def _handle_tools_call(arguments: argparse.Namespace) -> int:
    config = _resolve_config(arguments)
    payload = call_tool(config, tool_name=arguments.tool_name, arguments=_load_arguments(arguments))
    _print_payload(payload, as_json=arguments.json)
    if payload.get("ok") is False:
        return EXIT_REMOTE_ERROR
    return 0


def _handle_prompt(arguments: argparse.Namespace) -> int:
    config = _resolve_config(arguments)
    print(build_prompt_for_target(target=arguments.target, config=config, repo_url=REPO_URL))
    return 0


def main() -> None:
    parser = _build_parser()
    arguments = parser.parse_args()

    try:
        exit_code = arguments.handler(arguments)
    except AdapterError as exc:
        print(str(exc), file=sys.stderr)
        if exc.status_code == EXIT_INVALID_INPUT:
            raise SystemExit(EXIT_INVALID_INPUT) from exc
        if exc.status_code is not None and exc.status_code >= 400:
            raise SystemExit(EXIT_REMOTE_ERROR) from exc
        raise SystemExit(EXIT_CONFIGURATION) from exc
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(EXIT_INVALID_INPUT) from exc

    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
