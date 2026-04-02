from unittest import TestCase
from unittest.mock import patch

from aiofm_adapter.client import AdapterConfig, AdapterError, call_tool


class ClientValidationTests(TestCase):
    def setUp(self) -> None:
        self.config = AdapterConfig(
            base_url="https://dash.aiofm.cc",
            workspace_id="workspace-42",
            agent_key="agent-key-123",
        )

    def test_create_post_requires_scheduled_at_before_network_call(self) -> None:
        with patch("aiofm_adapter.client._request_json") as request_json:
            with self.assertRaises(AdapterError) as error_context:
                call_tool(
                    self.config,
                    tool_name="create_post",
                    arguments={
                        "social_account_id": "account-1",
                        "title": "Launch draft",
                        "image_binary": "YmFzZTY0",
                    },
                )

        self.assertEqual(str(error_context.exception), "create_post requires scheduled_at in ISO 8601 UTC format.")
        request_json.assert_not_called()

    def test_create_post_with_scheduled_at_reaches_request_layer(self) -> None:
        with patch("aiofm_adapter.client._request_json", return_value={"ok": True}) as request_json:
            payload = call_tool(
                self.config,
                tool_name="create_post",
                arguments={
                    "social_account_id": "account-1",
                    "title": "Launch draft",
                    "scheduled_at": "2026-04-03T14:00:00Z",
                    "image_binary": "YmFzZTY0",
                },
            )

        self.assertEqual(payload, {"ok": True})
        request_json.assert_called_once_with(
            url="https://dash.aiofm.cc/api/adapter/workspaces/workspace-42/tools/create_post",
            method="POST",
            config=self.config,
            payload={
                "arguments": {
                    "social_account_id": "account-1",
                    "title": "Launch draft",
                    "scheduled_at": "2026-04-03T14:00:00Z",
                    "image_binary": "YmFzZTY0",
                }
            },
        )
