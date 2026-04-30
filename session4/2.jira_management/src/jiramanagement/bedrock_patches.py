"""
Monkey-patches for CrewAI + Bedrock compatibility.

Import this module once before any CrewAI code runs to apply all patches.
"""
from crewai.agents.crew_agent_executor import CrewAgentExecutor
from crewai.llms.providers.bedrock.completion import BedrockCompletion
from crewai_tools.adapters.mcp_adapter import CrewAIToolAdapter


# ── Patch 1 ──────────────────────────────────────────────────────────────────
# Some Bedrock-hosted models reject the stopSequences field.
# Strip it out before the boto3 converse call.
_orig_get_inference_config = BedrockCompletion._get_inference_config

def _get_inference_config_no_stop(self):
    config = _orig_get_inference_config(self)
    config.pop("stopSequences", None)
    return config

BedrockCompletion._get_inference_config = _get_inference_config_no_stop


# ── Patch 2 ──────────────────────────────────────────────────────────────────
# CrewAI 1.14.x bug: _parse_native_tool_call uses `func_info.get("arguments", "{}")`
# which defaults to the non-empty string "{}" when the Bedrock response has no
# "function" wrapper. That truthy default short-circuits the `or` so the actual
# `input` dict from the Bedrock toolUse block is never read → empty args {} → validation error.
#
# Bedrock/Claude-Sonnet-4.6 secondary bug: when the "function" wrapper IS present,
# Bedrock serializes the name and arguments with extra wrapping single-quotes, e.g.:
#   "name": "'tavily_search'"  →  should be  "name": "tavily_search"
#   "arguments": "'{\"q\": 1}'"  →  should be  "arguments": "{\"q\": 1}"
# This makes tool-name lookup fail and JSON argument parsing fail.
#
# Only applies to crewai >= 1.14.x where _parse_native_tool_call exists.
if hasattr(CrewAgentExecutor, "_parse_native_tool_call"):
    _orig_parse = CrewAgentExecutor._parse_native_tool_call

    def _strip_bedrock_quotes(value: str) -> str:
        if isinstance(value, str) and len(value) >= 2 and value[0] == "'" and value[-1] == "'":
            return value[1:-1]
        return value

    def _parse_native_tool_call_fixed(self, tool_call):
        if isinstance(tool_call, dict):
            # Case 1 — raw Bedrock toolUse block (no "function" wrapper)
            if "input" in tool_call and "function" not in tool_call:
                from crewai.utilities.agent_utils import sanitize_tool_name
                call_id = (
                    tool_call.get("id")
                    or tool_call.get("toolUseId")
                    or f"call_{id(tool_call)}"
                )
                func_name = sanitize_tool_name(tool_call.get("name", ""))
                func_args = tool_call.get("input", {})
                return call_id, func_name, func_args

            # Case 2 — "function" wrapper present but name/arguments wrapped in extra single-quotes
            if "function" in tool_call:
                func = tool_call["function"]
                if isinstance(func, dict):
                    if isinstance(func.get("name"), str):
                        func["name"] = _strip_bedrock_quotes(func["name"])
                    if isinstance(func.get("arguments"), str):
                        func["arguments"] = _strip_bedrock_quotes(func["arguments"])

        return _orig_parse(self, tool_call)

    CrewAgentExecutor._parse_native_tool_call = _parse_native_tool_call_fixed


# ── Patch 3 ──────────────────────────────────────────────────────────────────
# crewai's create_model_from_schema sets default=None for every optional field.
# When the LLM omits those fields, Pydantic fills them in as None, and they get
# forwarded to the MCP server as explicit null values — causing schema validation
# errors on tools like createJiraIssue. Strip None values before the MCP call.
_orig_adapt = CrewAIToolAdapter.adapt

def _adapt_with_null_filter(self, func, mcp_tool):
    def filtered_func(kwargs):
        return func({k: v for k, v in (kwargs or {}).items() if v is not None})
    return _orig_adapt(self, filtered_func, mcp_tool)

CrewAIToolAdapter.adapt = _adapt_with_null_filter
