"""Public-safe metadata contract for GUI-free BEAM trajectory replay."""

from __future__ import annotations

import json
import math


def _finite_number(value: object, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def beam_trajectory_run_contract_gate(summary_json: str) -> dict:
    """Validate ownership, accounting, and magnetic-work invariants.

    This gate consumes caller-supplied metadata only.  It does not open product
    files, expose trajectory values, or launch a licensed solver.
    """
    try:
        summary = json.loads(summary_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"summary_json must be valid JSON: {exc.msg}") from exc
    if not isinstance(summary, dict):
        raise ValueError("summary_json must decode to an object")

    mode = str(summary.get("interaction_mode") or "").strip().lower()
    if mode not in {"transit", "collision"}:
        raise ValueError("interaction_mode must be 'transit' or 'collision'")
    field_mode = str(summary.get("field_mode") or "").strip().lower()
    if field_mode not in {"magnetic_only", "electromagnetic"}:
        raise ValueError("field_mode must be 'magnetic_only' or 'electromagnetic'")

    particle_count = int(summary.get("particle_count") or 0)
    trajectory_count = int(summary.get("trajectory_count") or 0)
    hit_count = int(summary.get("boundary_hit_count") or 0)
    source_current = _finite_number(summary.get("source_current_a"), "source_current_a")
    terminal_current = _finite_number(
        summary.get("terminal_current_a"), "terminal_current_a"
    )
    collision_power = _finite_number(
        summary.get("collision_power_w"), "collision_power_w"
    )
    energy_drift = _finite_number(
        summary.get("maximum_relative_energy_drift"),
        "maximum_relative_energy_drift",
    )
    current_error = abs(terminal_current - source_current) / max(
        abs(source_current), 1.0e-300
    )
    run_id = str(summary.get("run_id") or "")

    checks = {
        "beam_solver_family_recorded": summary.get("solver_family") == "BEAM",
        "direct_cli_without_launcher": summary.get("execution_route")
        == "direct_beam_solver_no_gui",
        "gui_and_completion_dialog_disabled": summary.get("gui_visible") is False
        and summary.get("completion_dialog") is False,
        "solver_version_and_run_date_recorded": bool(
            str(summary.get("solver_version") or "").strip()
        )
        and bool(str(summary.get("run_date_utc") or "").strip()),
        "source_particle_and_field_digests_recorded": summary.get(
            "source_digest_count"
        )
        == 3,
        "primary_mao_and_trajectory_mag_are_fresh": summary.get("output_roles")
        == {".mao": "run_log", ".mag": "trajectory_result"}
        and summary.get("all_outputs_fresh") is True,
        "run_generation_identity_closes": bool(run_id)
        and summary.get("field_generation_id") == run_id
        and summary.get("trajectory_generation_id") == run_id,
        "trajectory_count_closes": particle_count > 0
        and trajectory_count == particle_count,
        "trajectory_ids_unique": summary.get("trajectory_ids_unique") is True,
        "units_explicit": summary.get("position_unit") == "m"
        and summary.get("speed_unit") == "m/s"
        and summary.get("energy_unit") == "eV",
        "current_accounting_closes": current_error <= 1.0e-12,
        "boundary_accounting_matches_mode": hit_count
        == (0 if mode == "transit" else particle_count),
        "collision_power_matches_mode": collision_power
        == 0.0
        if mode == "transit"
        else collision_power > 0.0,
        "magnetic_field_does_no_work": field_mode != "magnetic_only"
        or energy_drift <= 1.0e-6,
        "solver_neutral_gate_passed": summary.get("public_gate_status") == "ok",
    }
    return {
        "schema": "elf-beam-trajectory-run-contract/v1",
        "status": "ok" if all(checks.values()) else "needs_attention",
        "interaction_mode": mode,
        "field_mode": field_mode,
        "checks": checks,
        "issues": [name for name, ok in checks.items() if not ok],
        "metrics": {
            "particle_count": particle_count,
            "trajectory_count": trajectory_count,
            "boundary_hit_count": hit_count,
            "current_closure_relative_error": current_error,
            "maximum_relative_energy_drift": energy_drift,
        },
        "notes": [
            "The primary execution record is .mao; bind the trajectory .mag to the same run generation.",
            "Transit runs require zero hit count and zero collision power; collision runs require one terminal hit per trajectory.",
            "Magnetic-only runs must preserve particle energy. Electromagnetic runs need a separate field-work balance.",
        ],
    }

