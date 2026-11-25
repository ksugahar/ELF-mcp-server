from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

import pytest

from elf_mcp_server.case_dispatch import CASE_TOOL_NAMES
from elf_mcp_server.tool_definitions import TOOL_CONTRACTS
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import Implementation
from pydantic import AnyUrl


_REPLAY_GATE_SCHEMAS = {
    "elf_beam_trajectory_run_contract_gate": "elf-beam-trajectory-run-contract/v1",
    "elf_charged_particle_replay_contract_gate": "elf-charged-particle-replay-contract/v1",
    "elf_product_corpus_replay_contract_gate": "elf-product-corpus-replay-contract/v1",
    "elf_electrostatic_replay_contract_gate": "elf-electrostatic-replay-contract/v1",
    "elf_age_torque_replay_contract_gate": "elf-age-torque-replay-contract/v1",
    "elf_history_harmonic_replay_contract_gate": "elf-history-harmonic-replay-contract/v2",
}


async def _probe_stdio(legacy_tools: str | None) -> dict:
    repo = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env.pop("ELF_MCP_LEGACY_TOOLS", None)
    if legacy_tools is not None:
        env["ELF_MCP_LEGACY_TOOLS"] = legacy_tools
    source_root = repo / "src"
    if source_root.is_dir():
        env["PYTHONPATH"] = os.pathsep.join(
            [str(source_root), env.get("PYTHONPATH", "")]
        ).rstrip(os.pathsep)
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "elf_mcp_server.server"],
        cwd=str(repo),
        env=env,
    )
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(
            read_stream,
            write_stream,
            client_info=Implementation(
                name="cae-lab-elf-probe",
                title="CAE Lab ELF Probe",
                version="2026.09",
            ),
        ) as session:
            initialized = await session.initialize()
            listed = await session.list_tools()
            tools = listed.tools
            replay_gates = {
                tool.name: tool for tool in tools if tool.name in _REPLAY_GATE_SCHEMAS
            }
            assert replay_gates.keys() == _REPLAY_GATE_SCHEMAS.keys()
            for name, schema in _REPLAY_GATE_SCHEMAS.items():
                tool = replay_gates[name]
                assert tool.annotations is not None, name
                assert tool.annotations.readOnlyHint is True, name
                assert tool.inputSchema["required"] == ["summary_json"], name
                summary = {}
                if name == "elf_beam_trajectory_run_contract_gate":
                    summary = {
                        "interaction_mode": "transit",
                        "field_mode": "magnetic_only",
                        "source_current_a": 0.0,
                        "terminal_current_a": 0.0,
                        "collision_power_w": 0.0,
                        "maximum_relative_energy_drift": 0.0,
                    }
                result = await session.call_tool(
                    name, {"summary_json": json.dumps(summary)}
                )
                assert not result.isError, (name, result.content)
                payload = json.loads(result.content[0].text)
                assert payload["schema"] == schema, name
                assert payload["status"] == "needs_attention", name
            called = await session.call_tool("elf_overview", {})
            suggestion = await session.call_tool(
                "elf_suggest_example", {"goal": "Hall-effect sensor"}
            )
            suggestion_tool = next(tool for tool in tools if tool.name == "elf_suggest_example")
            case_list = await session.call_tool("elf_case_list", {"group": "gate"})
            case_check = await session.call_tool(
                "elf_case_check", {"case_id": "mtpa_search_plan", "inputs": {"pole_pairs": "4"}}
            )
            bad_case = await session.call_tool(
                "elf_case_check", {"case_id": "mtpa_search_plan", "inputs": {"pole_pairs": "invalid"}}
            )
            profiled = await session.call_tool("elf_agentic_profile", {})
            profile_payload = json.loads(profiled.content[0].text)
            searched = await session.call_tool(
                "elf_search", {"query": "electrostatic", "source": "help", "top_k": 3}
            )
            detected = await session.call_tool("elf_product_detect", {})
            resources = await session.list_resources()
            templates = await session.list_resource_templates()
            read = await session.read_resource(AnyUrl("elf://guides/overview"))
            prompts = await session.list_prompts()
            prompted = await session.get_prompt(
                "new_elf_analysis",
                {"geometry": "parallel-plate capacitor", "solver": "ELFIN"},
            )
            profile_after_calls = json.loads(
                (await session.call_tool("elf_agentic_profile", {})).content[0].text
            )
            hints = (
                "readOnlyHint",
                "destructiveHint",
                "idempotentHint",
                "openWorldHint",
            )
            return {
                "server_name": initialized.serverInfo.name,
                "server_version": initialized.serverInfo.version,
                "protocol_version": initialized.protocolVersion,
                "instructions": initialized.instructions,
                "tool_names": {tool.name for tool in tools},
                "case_list": case_list.structuredContent,
                "case_check": case_check.structuredContent,
                "bad_case": bad_case.structuredContent,
                "missing_titles": [tool.name for tool in tools if not tool.title],
                "missing_annotations": [
                    tool.name
                    for tool in tools
                    if tool.annotations is None
                    or any(getattr(tool.annotations, hint) is None for hint in hints)
                ],
                "suggestion_is_error": bool(suggestion.isError),
                "suggestion": json.loads(suggestion.content[0].text),
                "suggestion_description": suggestion_tool.description,
                "probe_is_error": bool(called.isError),
                "probe_has_content": bool(called.content),
                "client_connection": profile_payload["client_connection"],
                "connection_count_after_calls": profile_after_calls["client_connection"]["connection_count"],
                "structured_is_error": bool(searched.isError),
                "structured_schema": (searched.structuredContent or {}).get("schema_version"),
                "product_detect_is_error": bool(detected.isError),
                "product_detect_has_content": bool(detected.content),
                "resource_count": len(resources.resources),
                "template_count": len(templates.resourceTemplates),
                "resource_read": read.contents[0].text,
                "prompt_names": [prompt.name for prompt in prompts.prompts],
                "prompt_text": prompted.messages[0].content.text,
            }


@pytest.mark.parametrize("legacy_tools", [None, "0"])
def test_stdio_initialize_list_and_safe_call_contract(legacy_tools: str | None) -> None:
    result = asyncio.run(asyncio.wait_for(_probe_stdio(legacy_tools), timeout=45))
    assert result["server_name"] == "elf-mcp-server"
    assert result["server_version"]
    assert result["protocol_version"]
    assert result["instructions"]
    hidden = set(CASE_TOOL_NAMES) if legacy_tools == "0" else set()
    assert result["tool_names"] == set(TOOL_CONTRACTS) - hidden
    assert result["case_list"]["legacy_tools_listed"] is (legacy_tools is None)
    assert result["case_list"]["cases"]
    assert all(case["group"] == "gate" for case in result["case_list"]["cases"])
    assert result["case_check"]["ok"] is True
    assert result["case_check"]["case_id"] == "mtpa_search_plan"
    assert result["case_check"]["result"].startswith("# ELF Python Motor MTPA Search Plan")
    assert result["bad_case"]["error"]["code"] == "case_check_failed"
    assert result["missing_titles"] == []
    assert result["missing_annotations"] == []
    assert result["suggestion_is_error"] is False
    assert result["suggestion"]["kind"] == "magnetic_sensor"
    assert "starter template" in result["suggestion"]["title"]
    assert "before running" in result["suggestion_description"]
    assert result["probe_is_error"] is False
    assert result["probe_has_content"] is True
    assert result["client_connection"] == {
        "connection_count": 1,
        "latest": {
            "name": "cae-lab-elf-probe",
            "title": "CAE Lab ELF Probe",
            "version": "2026.09",
        },
        "recent": [{
            "name": "cae-lab-elf-probe",
            "title": "CAE Lab ELF Probe",
            "version": "2026.09",
        }],
    }
    assert result["connection_count_after_calls"] == 1
    assert result["structured_is_error"] is False
    assert result["structured_schema"] == "elf.search.v1"
    assert result["resource_count"] == 5
    assert result["template_count"] == 1
    assert "Python/ctypes bridge" in result["resource_read"]
    assert result["product_detect_is_error"] is False
    assert result["product_detect_has_content"] is True
    assert result["prompt_names"] == ["new_elf_analysis"]
    assert "electrostatic" in result["prompt_text"]
