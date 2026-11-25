from __future__ import annotations

import asyncio

from elf_mcp_server.case_dispatch import CASE_TOOL_NAMES
from elf_mcp_server.handlers import mcp
from elf_mcp_server.tool_definitions import TOOL_CONTRACTS


def test_case_catalog_and_dispatch_errors(monkeypatch):
    tools = {tool.name: tool for tool in mcp._tool_manager.list_tools()}
    list_cases = tools["elf_case_list"].fn
    run_case = tools["elf_case_check"].fn
    listing = list_cases()
    monkeypatch.setenv("ELF_MCP_LEGACY_TOOLS", "0" if listing["legacy_tools_listed"] else "1")
    assert list_cases()["legacy_tools_listed"] == listing["legacy_tools_listed"]
    assert {case["legacy_tool"] for case in listing["cases"]} == set(CASE_TOOL_NAMES)
    assert "elf_contract_gate" not in CASE_TOOL_NAMES
    assert all(TOOL_CONTRACTS[name].read_only for name in CASE_TOOL_NAMES)

    missing = asyncio.run(run_case("not-a-case"))
    assert missing == {
        "ok": False,
        "case_id": "not-a-case",
        "legacy_tool": None,
        "result": None,
        "error": {
            "code": "unknown_case_id",
            "message": "Call elf_case_list() to see available case IDs.",
        },
    }
    invalid = asyncio.run(run_case("elf_python_motor_mtpa_search_plan", {"bogus": 1}))
    assert set(invalid) == set(missing)
    assert invalid["case_id"] == "mtpa_search_plan"
    assert invalid["legacy_tool"] == "elf_python_motor_mtpa_search_plan"
    assert invalid["error"] == {"code": "invalid_inputs", "message": "Unexpected inputs: bogus"}
