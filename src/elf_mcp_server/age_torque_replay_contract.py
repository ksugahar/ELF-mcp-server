"""Metadata-only contract for a rotating torque replay against NGSolve+AGE."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping


_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _is_sha256(value: object) -> bool:
    return bool(_SHA256.fullmatch(str(value or "").strip().lower()))


def age_torque_replay_contract_gate(summary_json: str) -> dict[str, object]:
    """Validate metadata without exposing solver paths or numeric results."""
    try:
        summary = json.loads(summary_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"summary_json must be valid JSON: {exc.msg}") from exc
    if not isinstance(summary, dict):
        raise ValueError("summary_json must decode to an object")

    source = summary.get("source_replay")
    source = source if isinstance(source, Mapping) else {}
    replacement = summary.get("replacement_route")
    replacement = replacement if isinstance(replacement, Mapping) else {}
    inputs = source.get("input_sha256")
    inputs = inputs if isinstance(inputs, list) else []
    identity = str(summary.get("physics_identity_digest") or "")
    counts = source.get("magnetic_hex_counts")
    counts = counts if isinstance(counts, list) else []

    checks = {
        "schema_is_age_torque_replay": summary.get("schema")
        == "elf-age-torque-replay-metadata/v1",
        "metadata_has_no_source_values_or_paths": summary.get("source_values_embedded")
        is False
        and summary.get("local_paths_embedded") is False,
        "physics_identity_is_content_addressed": _is_sha256(identity),
        "source_inputs_are_content_addressed": len(inputs) >= 3
        and all(
            isinstance(row, Mapping)
            and set(row) == {"analysis", "geometry"}
            and all(_is_sha256(value) for value in row.values())
            for row in inputs
        ),
        "source_is_headless_torque_replay": source.get("physics_role")
        == "magnetic_force_torque"
        and source.get("execution_mode") == "headless_direct_cli",
        "source_refinement_and_angle_controls_are_verified": len(counts) >= 3
        and all(isinstance(value, int) and value > 0 for value in counts)
        and all(left < right for left, right in zip(counts, counts[1:]))
        and source.get("mesh_convergence_verified") is True
        and source.get("angle_symmetry_verified") is True
        and source.get("closed_surface_force_residual_verified") is True,
        "source_outputs_are_fresh_and_bounded": source.get("fresh_outputs_verified")
        is True
        and int(source.get("timeout_count") or 0) == 0
        and int(source.get("stale_count") or 0) == 0,
        "source_version_and_date_are_recorded": bool(
            str(source.get("solver_version") or "").strip()
        )
        and bool(str(source.get("executed_at_utc") or "").strip()),
        "replacement_is_executed_same_identity_ngsolve_age": replacement.get("lane_id")
        == "ngsolve_age"
        and replacement.get("solver_ready") is True
        and replacement.get("executed") is True
        and replacement.get("discretization_converged") is True
        and replacement.get("action_reaction_verified") is True
        and replacement.get("gap_radius_invariance_verified") is True
        and int(replacement.get("verification_count") or 0) >= 3
        and _is_sha256(replacement.get("artifact_sha256"))
        and replacement.get("identity_digest") == identity
        and bool(str(replacement.get("solver_version") or "").strip())
        and bool(str(replacement.get("executed_at_utc") or "").strip()),
        "same_identity_tolerance_is_verified_in_declared_scope": summary.get(
            "same_identity_tolerance_met"
        )
        is True
        and summary.get("dimensional_scope") == "long_extrusion_limit",
        "scope_does_not_overclaim_retirement": summary.get(
            "research_lab_retirement_ready"
        )
        is False
        and summary.get("product_or_market_retirement_ready") is False,
    }
    ok = all(checks.values())
    return {
        "schema": "elf-age-torque-replay-contract/v1",
        "status": "verified_partial" if ok else "needs_attention",
        "checks": checks,
        "issues": [name for name, passed in checks.items() if not passed],
        "ngsolve_age_torque_route_verified": ok,
        "research_lab_retirement_ready": False,
        "notes": [
            "The public contract records hashes, convergence, balance, and scope only.",
            "Long-extrusion evidence does not prove arbitrary three-dimensional motion.",
        ],
    }

