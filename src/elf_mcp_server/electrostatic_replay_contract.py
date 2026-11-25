"""Metadata-only contract for electrostatic source/replacement replay."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping


_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _is_sha256(value: object) -> bool:
    return bool(_SHA256.fullmatch(str(value or "").strip().lower()))


def electrostatic_replay_contract_gate(summary_json: str) -> dict:
    """Validate convergence and identity metadata without solved values."""
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
    input_digests = source.get("input_sha256")
    input_digests = input_digests if isinstance(input_digests, Mapping) else {}
    dof_levels = source.get("surface_dof_levels")
    dof_levels = dof_levels if isinstance(dof_levels, list) else []
    identity = str(summary.get("physics_identity_digest") or "")

    checks = {
        "schema_is_electrostatic_replay": summary.get("schema")
        == "elf-electrostatic-replay-metadata/v1",
        "metadata_has_no_source_values_or_paths": summary.get(
            "source_values_embedded"
        )
        is False
        and summary.get("local_paths_embedded") is False,
        "physics_identity_is_content_addressed": _is_sha256(identity),
        "source_inputs_are_content_addressed": set(input_digests)
        == {"analysis", "geometry"}
        and all(_is_sha256(value) for value in input_digests.values()),
        "source_is_headless_electrostatic_surface_replay": source.get(
            "physics_role"
        )
        == "electrostatic_charge_and_field"
        and source.get("execution_mode") == "headless_direct_cli",
        "source_refinement_is_ordered": len(dof_levels) >= 3
        and all(isinstance(value, int) and value > 0 for value in dof_levels)
        and dof_levels == sorted(set(dof_levels)),
        "source_outputs_are_fresh_and_bounded": int(
            source.get("timeout_count") or 0
        )
        == 0
        and int(source.get("stale_count") or 0) == 0,
        "source_charge_conservation_and_convergence_verified": source.get(
            "charge_conservation_verified"
        )
        is True
        and source.get("refinement_converged") is True,
        "source_version_and_date_are_recorded": bool(
            str(source.get("solver_version") or "").strip()
        )
        and bool(str(source.get("executed_at_utc") or "").strip()),
        "replacement_is_executed_same_identity": replacement.get("lane_id")
        == "ngsolve_electrostatics_bem"
        and replacement.get("solver_ready") is True
        and replacement.get("executed") is True
        and int(replacement.get("verification_count") or 0) > 0
        and _is_sha256(replacement.get("artifact_sha256"))
        and replacement.get("identity_digest") == identity
        and bool(str(replacement.get("solver_version") or "").strip())
        and bool(str(replacement.get("executed_at_utc") or "").strip()),
        "same_identity_tolerance_is_verified": summary.get(
            "same_identity_tolerance_met"
        )
        is True,
        "scope_does_not_overclaim_retirement": summary.get(
            "research_lab_retirement_ready"
        )
        is False
        and summary.get("product_or_market_retirement_ready") is False,
    }
    ok = all(checks.values())
    return {
        "schema": "elf-electrostatic-replay-contract/v1",
        "status": "verified_partial" if ok else "needs_attention",
        "checks": checks,
        "issues": [name for name, passed in checks.items() if not passed],
        "electrostatic_replacement_route_verified": ok,
        "research_lab_retirement_ready": False,
        "notes": [
            "Compare converged discretizations, not a coarse source value as ground truth.",
            "The electrostatic lane is distinct from eddy-current formulations.",
        ],
    }
