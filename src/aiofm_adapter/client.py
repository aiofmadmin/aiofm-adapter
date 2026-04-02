from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any
from urllib import error, request


AGENT_KEY_ENV_NAME = "DASH_AIOFM_AGENT_KEY"
BASE_URL_ENV_NAME = "AIOFM_BASE_URL"
WORKSPACE_ID_ENV_NAME = "AIOFM_WORKSPACE_ID"
DEFAULT_CLIENT_NAME = "aiofm-adapter"
DEFAULT_CLIENT_VERSION = "0.1.0"
DEFAULT_TIMEOUT_SECONDS = 30
INVALID_INPUT_STATUS_CODE = 10


class AdapterError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None, payload: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload or {}


@dataclass(slots=True)
class AdapterConfig:
    base_url: str
    workspace_id: str
    agent_key: str
    client_name: str = DEFAULT_CLIENT_NAME
    client_version: str = DEFAULT_CLIENT_VERSION
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS

    @property
    def normalized_base_url(self) -> str:
        return self.base_url.rstrip("/")

    @property
    def rest_endpoint(self) -> str:
        return f"{self.normalized_base_url}/api/adapter/workspaces/{self.workspace_id}"

    @property
    def manifest_url(self) -> str:
        return f"{self.rest_endpoint}/manifest"

    @property
    def tools_url(self) -> str:
        return f"{self.rest_endpoint}/tools"


def build_config(
    *,
    base_url: str | None,
    workspace_id: str | None,
    agent_key: str | None,
    client_name: str | None = None,
    client_version: str | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> AdapterConfig:
    resolved_base_url = (base_url or os.getenv(BASE_URL_ENV_NAME) or "").strip()
    resolved_workspace_id = (workspace_id or os.getenv(WORKSPACE_ID_ENV_NAME) or "").strip()
    resolved_agent_key = (agent_key or os.getenv(AGENT_KEY_ENV_NAME) or "").strip()

    if not resolved_base_url:
        raise AdapterError(f"Missing base URL. Set --base-url or {BASE_URL_ENV_NAME}.")

    if not resolved_workspace_id:
        raise AdapterError(f"Missing workspace id. Set --workspace-id or {WORKSPACE_ID_ENV_NAME}.")

    if not resolved_agent_key:
        raise AdapterError(f"Missing agent key. Set --agent-key or {AGENT_KEY_ENV_NAME}.")

    return AdapterConfig(
        base_url=resolved_base_url,
        workspace_id=resolved_workspace_id,
        agent_key=resolved_agent_key,
        client_name=(client_name or DEFAULT_CLIENT_NAME).strip() or DEFAULT_CLIENT_NAME,
        client_version=(client_version or DEFAULT_CLIENT_VERSION).strip() or DEFAULT_CLIENT_VERSION,
        timeout_seconds=timeout_seconds,
    )


def _build_headers(config: AdapterConfig, *, include_json_content_type: bool = False) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {config.agent_key}",
        "X-Aiofm-Client-Name": config.client_name,
        "X-Aiofm-Client-Version": config.client_version,
    }

    if include_json_content_type:
        headers["Content-Type"] = "application/json"

    return headers


def _parse_response_body(response_body: bytes) -> dict[str, Any]:
    if not response_body:
        return {}

    try:
        parsed = json.loads(response_body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise AdapterError("Server returned invalid JSON.") from exc

    if not isinstance(parsed, dict):
        raise AdapterError("Server returned a non-object JSON payload.")

    return parsed


def _request_json(
    *,
    url: str,
    method: str,
    config: AdapterConfig,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    encoded_payload = None
    if payload is not None:
        encoded_payload = json.dumps(payload).encode("utf-8")

    prepared_request = request.Request(
        url=url,
        method=method,
        headers=_build_headers(config, include_json_content_type=payload is not None),
        data=encoded_payload,
    )

    try:
        with request.urlopen(prepared_request, timeout=config.timeout_seconds) as response:
            return _parse_response_body(response.read())
    except error.HTTPError as exc:
        payload_data = _parse_response_body(exc.read())
        detail = payload_data.get("detail") if isinstance(payload_data, dict) else None
        message = detail if isinstance(detail, str) else f"HTTP {exc.code} from adapter server."
        raise AdapterError(message, status_code=exc.code, payload=payload_data) from exc
    except error.URLError as exc:
        raise AdapterError(f"Failed to reach adapter server: {exc.reason}") from exc


def _validate_tool_arguments(*, tool_name: str, arguments: dict[str, Any]) -> None:
    if tool_name != "create_post":
        return

    scheduled_at = arguments.get("scheduled_at")
    if isinstance(scheduled_at, str) and scheduled_at.strip():
        return

    raise AdapterError(
        "create_post requires scheduled_at in ISO 8601 UTC format.",
        status_code=INVALID_INPUT_STATUS_CODE,
    )


def get_manifest(config: AdapterConfig) -> dict[str, Any]:
    return _request_json(url=config.manifest_url, method="GET", config=config)


def list_tools(config: AdapterConfig) -> dict[str, Any]:
    return _request_json(url=config.tools_url, method="GET", config=config)


def call_tool(config: AdapterConfig, *, tool_name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    normalized_arguments = arguments or {}
    _validate_tool_arguments(tool_name=tool_name, arguments=normalized_arguments)

    return _request_json(
        url=f"{config.tools_url}/{tool_name}",
        method="POST",
        config=config,
        payload={"arguments": normalized_arguments},
    )
