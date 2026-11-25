"""Consolidated entry points for public, read-only ELF gates and plans."""
from __future__ import annotations

import inspect
import json
import os
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.server.fastmcp.tools.base import Tool
from pydantic_core import to_jsonable_python

from .tool_definitions import TOOL_CONTRACTS


CASE_TOOL_NAMES = (
    "elf_complex_field_run_contract_gate",
    "elf_conductive_shield_frequency_contract_gate",
    "elf_demagnetization_run_contract_gate",
    "elf_emfm_star_power_balance_gate",
    "elf_flux_linkage_inductance_contract_gate",
    "elf_force_method_profile_contract_gate",
    "elf_force_pair_run_contract_gate",
    "elf_ipm_two_run_ldlq_contract_gate",
    "elf_leakage_inductance_contract_gate",
    "elf_magnet_model_producer_contract_gate",
    "elf_magnetization_group_handoff_contract_gate",
    "elf_material_force_contrast_contract_gate",
    "elf_mesh_solver_pipeline_gate",
    "elf_momc_force_triplet_contract_gate",
    "elf_nonlinear_magnetic_conductor_validation_gate",
    "elf_project_feature_inventory_contract_gate",
    "elf_python_induction_slip_sweep_plan",
    "elf_python_meg_generation_plan",
    "elf_python_motor_airgap_harmonics_nvh_plan",
    "elf_python_motor_cogging_ripple_plan",
    "elf_python_motor_demag_margin_plan",
    "elf_python_motor_design_plan",
    "elf_python_motor_dq_axis_map_plan",
    "elf_python_motor_drive_cycle_plan",
    "elf_python_motor_efficiency_map_plan",
    "elf_python_motor_inverter_pwm_harmonic_plan",
    "elf_python_motor_manufacturing_tolerance_plan",
    "elf_python_motor_material_variation_plan",
    "elf_python_motor_mtpa_search_plan",
    "elf_python_motor_optimization_study_plan",
    "elf_python_motor_rotor_stress_retention_plan",
    "elf_python_motor_saturation_inductance_map_plan",
    "elf_python_motor_thermal_network_plan",
    "elf_python_motor_topology_parameter_plan",
    "elf_python_motor_voltage_field_weakening_plan",
    "elf_python_motor_winding_layout_plan",
    "elf_python_ngsolve_validation_plan",
    "elf_python_phase_flux_run_contract_gate",
    "elf_python_reluctance_motor_design_plan",
    "elf_rotating_conductor_periodic_contract_gate",
    "elf_source_off_relaxation_contract_gate",
    "elf_transient_induced_current_contract_gate",
    "elf_two_winding_frequency_contract_gate",
)


def _short_case_id(name: str) -> str:
    for prefix in ("elf_python_motor_", "elf_python_", "elf_"):
        if name.startswith(prefix):
            return name[len(prefix):]
    raise ValueError(f"Invalid ELF case tool name: {name}")


def add_case_dispatch_tools(mcp: FastMCP) -> tuple[str, ...]:
    """Register the consolidated tools and return the legacy names to hide."""
    legacy_setting = os.environ.get("ELF_MCP_LEGACY_TOOLS", "1").strip().lower()
    legacy_tools_listed = legacy_setting not in {"0", "false", "no", "off"}
    registered = {tool.name: tool for tool in mcp._tool_manager.list_tools()}
    cases: dict[str, Tool] = {}
    for name in CASE_TOOL_NAMES:
        contract = TOOL_CONTRACTS[name]
        if not contract.read_only or not contract.idempotent or contract.open_world:
            raise RuntimeError(f"ELF case target must be local, read-only and idempotent: {name}")
        case_id = _short_case_id(name)
        if case_id in cases:
            raise RuntimeError(f"Duplicate ELF case ID: {case_id}")
        cases[case_id] = registered[name]
    aliases = {tool.name: case_id for case_id, tool in cases.items()}

    @mcp.tool()
    def elf_case_list(group: str = "") -> dict[str, Any]:
        """List available ELF cases. Filter by gate or plan to narrow the catalog."""
        selected_group = group.strip().lower()
        items = []
        for case_id, tool in cases.items():
            case_group = tool.name.rsplit("_", 1)[-1]
            if selected_group and selected_group != case_group:
                continue
            items.append({
                "case_id": case_id,
                "group": case_group,
                "legacy_tool": tool.name,
                "signature": str(inspect.signature(tool.fn)),
                "summary": tool.description.splitlines()[0] if tool.description else "",
            })
        return {
            "legacy_tools_listed": legacy_tools_listed,
            "total_cases": len(items),
            "cases": items,
        }

    @mcp.tool()
    async def elf_case_check(case_id: str, inputs: dict[str, Any] | None = None) -> dict[str, Any]:
        """Run a read-only ELF gate or plan by case ID or legacy tool name."""
        target = case_id.strip()
        resolved_id = aliases.get(target, target)
        tool = cases.get(resolved_id)
        response: dict[str, Any] = {
            "ok": False,
            "case_id": resolved_id,
            "legacy_tool": tool.name if tool else None,
            "result": None,
            "error": None,
        }
        if tool is None:
            response["error"] = {
                "code": "unknown_case_id",
                "message": "Call elf_case_list() to see available case IDs.",
            }
            return response

        arguments = inputs or {}
        unknown_keys = sorted(arguments.keys() - tool.parameters.get("properties", {}).keys())
        if unknown_keys:
            response["error"] = {
                "code": "invalid_inputs",
                "message": "Unexpected inputs: " + ", ".join(unknown_keys),
            }
            return response
        try:
            result = await tool.run(arguments)
        except ToolError as exc:
            response["error"] = {"code": "case_check_failed", "message": str(exc)}
            return response
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except json.JSONDecodeError:
                pass
        response["result"] = to_jsonable_python(result)
        response["ok"] = True
        return response

    return () if legacy_tools_listed else CASE_TOOL_NAMES


def hide_legacy_case_tools(mcp: FastMCP, names: tuple[str, ...]) -> None:
    """Remove direct legacy entry points after the full contract has been applied."""
    for name in names:
        mcp.remove_tool(name)
