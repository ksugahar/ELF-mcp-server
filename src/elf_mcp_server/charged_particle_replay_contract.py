"""Public-safe metadata contract for charged-particle replacement evidence."""
from __future__ import annotations

import json
import re
from collections.abc import Mapping


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_LOCAL_PATH = re.compile(r"(?:^[A-Za-z]:[\\/]|\\\\[^\\]+\\)")
_FORBIDDEN = {
    "charge_c",
    "mass_kg",
    "kinetic_voltage_v",
    "trajectory_values",
    "position_values",
    "velocity_values",
    "field_values",
    "commercial_metrics",
}


def _digest(value: object) -> bool:
    return bool(_SHA256.fullmatch(str(value or "").lower()))


def _private(value: object, key: str = "") -> bool:
    if str(key).lower() in _FORBIDDEN:
        return True
    if isinstance(value, Mapping):
        return any(_private(item, str(name)) for name, item in value.items())
    if isinstance(value, list):
        return any(_private(item, key) for item in value)
    return isinstance(value, str) and bool(_LOCAL_PATH.search(value))


def charged_particle_replay_contract_gate(summary_json: str) -> dict[str, object]:
    """Validate source-run metadata without exposing product trajectories."""
    try:
        summary = json.loads(summary_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"summary_json must be valid JSON: {exc.msg}") from exc
    if not isinstance(summary, dict):
        raise ValueError("summary_json must decode to an object")
    source = summary.get("source_baseline")
    source = source if isinstance(source, Mapping) else {}
    replacement = summary.get("replacement_superset")
    replacement = replacement if isinstance(replacement, Mapping) else {}
    gate = summary.get("public_gate")
    gate = gate if isinstance(gate, Mapping) else {}
    identity = str(summary.get("physics_identity_digest") or "")
    checks = {
        "schema_is_charged_particle_replay_metadata": summary.get("schema")
        == "elf-charged-particle-replay-metadata/v1",
        "metadata_has_no_product_values_or_local_paths": summary.get(
            "source_values_embedded"
        )
        is False
        and summary.get("local_paths_embedded") is False
        and not _private(summary),
        "identity_and_artifacts_are_content_addressed": _digest(identity)
        and _digest(source.get("input_manifest_sha256"))
        and _digest(source.get("field_artifact_sha256"))
        and _digest(source.get("trajectory_artifact_sha256"))
        and _digest(replacement.get("artifact_sha256")),
        "source_run_is_current_gui_free_and_generation_closed": source.get(
            "executed"
        )
        is True
        and source.get("current_field_solver_version_recorded") is True
        and source.get("current_trajectory_solver_version_recorded") is True
        and source.get("execution_route") == "direct_solver_no_gui"
        and source.get("gui_visible") is False
        and source.get("completion_dialog") is False
        and source.get("field_and_trajectory_generation_closed") is True,
        "source_identity_binds_particle_launch_and_units": source.get(
            "charge_mass_energy_identity_bound"
        )
        is True
        and source.get("kinetic_voltage_semantics_verified") is True
        and source.get("relativistic_policy_recorded") is True
        and source.get("coordinate_and_field_units_explicit") is True,
        "source_state_and_stop_accounting_fail_closed": source.get(
            "all_particle_states_accounted"
        )
        is True
        and source.get("unwritten_allocation_rows_rejected") is True
        and source.get("stop_policy") == "first_physical_event",
        "replacement_superset_covers_both_coordinate_modes": replacement.get(
            "executed"
        )
        is True
        and replacement.get("converged") is True
        and replacement.get("identity_digest") == identity
        and replacement.get("physical_time_backend")
        == "scipy.integrate.solve_ivp:DOP853"
        and replacement.get("beamline_backend") == "xtrack.BorisSpatialIntegrator",
        "replacement_superset_covers_e_b_relativity_and_stop_events": replacement.get(
            "kinetic_voltage_conversion_verified"
        )
        is True
        and replacement.get("magnetic_tracking_verified") is True
        and replacement.get("electrostatic_acceleration_verified") is True
        and replacement.get("relativistic_policy_verified") is True
        and replacement.get("first_stop_event_verified") is True,
        "solver_neutral_public_gate_closed": gate.get("policy")
        == "charged_particle_same_identity_gate_v1"
        and gate.get("status") == "ok",
        "scope_does_not_overclaim_overall_retirement": summary.get(
            "research_lab_retirement_ready"
        )
        is False
        and summary.get("product_or_market_retirement_ready") is False,
    }
    ok = all(checks.values())
    return {
        "schema": "elf-charged-particle-replay-contract/v1",
        "status": "verified_partial" if ok else "needs_attention",
        "checks": checks,
        "issues": [name for name, passed in checks.items() if not passed],
        "charged_particle_replacement_superset_verified": ok,
        "research_lab_retirement_ready": False,
        "product_or_market_retirement_ready": False,
        "notes": [
            "Bind charge, mass, kinetic-voltage semantics, relativity, and SI units before trajectory comparison.",
            "A trajectory result ends at the first physical stop event, not the last allocated output row.",
            "Use physical-time integration for closed paths and beamline-coordinate integration for monotone accelerator paths.",
        ],
    }
