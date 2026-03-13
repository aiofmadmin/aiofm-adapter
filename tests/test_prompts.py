from unittest import TestCase

from aiofm_adapter.client import AdapterConfig
from aiofm_adapter.prompts import build_agent_brief, build_env_block, build_prompt_for_target


class PromptTests(TestCase):
    def setUp(self) -> None:
        self.config = AdapterConfig(
            base_url="https://dash.aiofm.cc",
            workspace_id="workspace-42",
            agent_key="agent-key-123",
        )

    def test_build_env_block_includes_all_required_variables(self) -> None:
        block = build_env_block(self.config)

        self.assertIn('AIOFM_BASE_URL="https://dash.aiofm.cc"', block)
        self.assertIn('AIOFM_WORKSPACE_ID="workspace-42"', block)
        self.assertIn('DASH_AIOFM_AGENT_KEY="agent-key-123"', block)

    def test_build_agent_brief_mentions_rest_endpoints(self) -> None:
        brief = build_agent_brief(self.config)

        self.assertIn("Use only the official aiofm REST adapter `aiofm-adapter`", brief)
        self.assertIn(self.config.manifest_url, brief)
        self.assertIn("submit_for_approval", brief)

    def test_build_prompt_for_claude_contains_runtime_title(self) -> None:
        prompt = build_prompt_for_target(
            target="claude",
            config=self.config,
            repo_url="https://github.com/aiofmadmin/aiofm-adapter",
        )

        self.assertIn("Claude Code setup", prompt)
        self.assertIn("uv tool install --refresh", prompt)
