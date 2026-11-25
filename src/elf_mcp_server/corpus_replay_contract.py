"""Public-safe metadata contract for a complete headless example replay."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_KNOWN_REPAIRS = {
    "ELF-Q(718): insert EMGO in isolated replay copy",
    "ELF-Q(719): insert CLGO in isolated replay copy",
}


def _is_sha256(value: object) -> bool:
    return bool(_SHA256.fullmatch(str(value or "").strip().lower()))


def corpus_replay_contract_gate(summary_json: str) -> dict:
    """Validate metadata only; never open product files or return solved values."""
    try:
        summary = json.loads(summary_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"summary_json must be valid JSON: {exc.msg}") from exc
    if not isinstance(summary, dict):
        raise ValueError("summary_json must decode to an object")

    execution = summary.get("execution_version")
    execution = execution if isinstance(execution, Mapping) else {}
    fingerprints = execution.get("executable_fingerprints")
    fingerprints = fingerprints if isinstance(fingerprints, Mapping) else {}
    inventory = summary.get("inventory")
    inventory = inventory if isinstance(inventory, Mapping) else {}
    replay = summary.get("live_replay")
    replay = replay if isinstance(replay, Mapping) else {}
    expected_reject = summary.get("expected_reject")
    expected_reject = expected_reject if isinstance(expected_reject, Mapping) else {}
    boundary = summary.get("public_boundary")
    boundary = boundary if isinstance(boundary, Mapping) else {}
    replacement = summary.get("replacement_scope")
    replacement = replacement if isinstance(replacement, Mapping) else {}

    case_count = int(inventory.get("case_count") or 0)
    runnable_count = int(inventory.get("runnable_case_count") or 0)
    reject_count = int(inventory.get("expected_reject_count") or 0)
    role_counts = inventory.get("source_physics_role_counts")
    role_counts = role_counts if isinstance(role_counts, Mapping) else {}
    route_counts = inventory.get("successor_route_counts")
    route_counts = route_counts if isinstance(route_counts, Mapping) else {}
    pass_count = int(replay.get("runnable_pass_count") or 0)
    fail_count = int(replay.get("runnable_fail_count") or 0)
    repairs_raw = replay.get("known_interaction_repairs")
    repairs = repairs_raw if isinstance(repairs_raw, list) else []
    repair_names = {
        str(name)
        for row in repairs
        if isinstance(row, Mapping)
        for name in (row.get("repairs") or [])
    }
    versions = execution.get("observed_solver_versions")
    versions = versions if isinstance(versions, list) else []

    checks = {
        "schema_is_corpus_adjudication": summary.get("schema")
        == "cae-ai-lab.elf-magic-product-corpus-adjudication.v1",
        "artifact_is_private_metadata": summary.get("private") is True,
        "public_boundary_is_value_text_and_path_free": boundary
        == {
            "contains_solved_values": False,
            "contains_source_text": False,
            "contains_local_paths": False,
        },
        "runner_is_content_addressed": _is_sha256(execution.get("runner_sha256")),
        "all_solver_families_have_versions": all(
            str(version).strip() for version in versions
        )
        and len(set(versions)) >= 3,
        "all_executables_are_content_addressed": set(fingerprints)
        == {"BEAM", "ELFIN", "MAGIC", "MESH"}
        and all(
            isinstance(row, Mapping)
            and _is_sha256(row.get("sha256"))
            and int(row.get("size_bytes") or 0) > 0
            for row in fingerprints.values()
        ),
        "inventory_partitions_cleanly": case_count > 0
        and case_count == runnable_count + reject_count,
        "source_physics_roles_are_complete": set(role_counts)
        == {
            "charged_particle_trajectory",
            "electrostatic_charge_and_field",
            "magnetic_field_induction_and_force",
        }
        and sum(int(value) for value in role_counts.values()) == case_count,
        "electrostatic_successor_route_is_not_eddy_current": int(
            route_counts.get("ngsolve_electrostatics_bem") or 0
        )
        == int(role_counts.get("electrostatic_charge_and_field") or -1)
        and "hcurl_eddy_bubble_cln" not in route_counts,
        "all_runnable_cases_pass": runnable_count > 0
        and pass_count == runnable_count
        and fail_count == 0
        and replay.get("unexpected_failures") == [],
        "outputs_are_fresh_and_bounded": replay.get("timeout_cases") == []
        and replay.get("stale_output_cases") == [],
        "known_interactive_repairs_are_allowlisted": repair_names
        <= _KNOWN_REPAIRS,
        "non_runnable_intermediate_is_fail_closed": reject_count > 0
        and expected_reject.get("classification")
        == "non_runnable_pipeline_intermediate"
        and expected_reject.get("pass") is True,
        "source_replay_does_not_overclaim_replacement": replacement.get(
            "source_product_corpus_replay_complete"
        )
        is True
        and replacement.get("same_identity_radia_replay_complete") is False
        and replacement.get("research_lab_retirement_ready") is False
        and replacement.get("product_or_market_retirement_claim") is False,
    }
    status = "ok" if all(checks.values()) else "needs_attention"
    return {
        "schema": "elf-product-corpus-replay-contract/v1",
        "status": status,
        "checks": checks,
        "issues": [name for name, passed in checks.items() if not passed],
        "metrics": {
            "case_count": case_count,
            "runnable_case_count": runnable_count,
            "expected_reject_count": reject_count,
            "known_interaction_repair_count": len(repair_names),
            "source_physics_role_count": len(role_counts),
        },
        "source_product_corpus_replay_complete": status == "ok",
        "research_lab_retirement_ready": False,
        "notes": [
            "Q718 may be replayed headlessly with an isolated-copy EMGO continuation.",
            "Q719 may be replayed headlessly with an isolated-copy CLGO continuation.",
            "A provisional control deck without its generated mesh is an expected reject, not a solved case.",
            "Source replay does not replace same-identity execution in the successor solver.",
        ],
    }
