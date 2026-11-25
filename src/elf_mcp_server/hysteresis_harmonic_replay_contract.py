"""Public-safe metadata contract for imported history and harmonic evidence.

ELF/MAGIC does not provide a hysteresis material solver.  Archived field
history may be replayed to validate a replacement constitutive model, but that
replay must never be counted as an ELF hysteresis capability.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_LOCAL_PATH = re.compile(r"(?:^[A-Za-z]:[\\/]|\\\\[^\\]+\\)")
_FORBIDDEN = {
    "field_values",
    "flux_values",
    "state_values",
    "source_values",
    "result_values",
    "cycle_energy_density_j_per_m3",
    "harmonic_coefficients",
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


def hysteresis_harmonic_replay_contract_gate(summary_json: str) -> dict[str, object]:
    """Validate imported history scope and a public-safe replacement superset."""

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
        "schema_is_history_harmonic_replay_metadata_v2": summary.get("schema")
        == "elf-history-harmonic-replay-metadata/v2",
        "metadata_has_no_source_values_or_local_paths": summary.get(
            "source_values_embedded"
        )
        is False
        and summary.get("local_paths_embedded") is False
        and not _private(summary),
        "identity_and_artifacts_are_content_addressed": _digest(identity)
        and _digest(source.get("history_artifact_sha256"))
        and _digest(source.get("harmonic_artifact_sha256"))
        and _digest(replacement.get("artifact_sha256")),
        "history_is_imported_not_claimed_as_source_solver_hysteresis": source.get(
            "history_provenance"
        )
        == "imported_or_archived_field_history"
        and source.get("source_solver_hysteresis_capability") is False
        and source.get("history_dependent_data") is True,
        "source_history_is_replayed_contiguous_and_gap_fail_closed": source.get(
            "executed"
        )
        is True
        and source.get("current_version_recorded") is True
        and source.get("contiguous_history_band") == "at_least_one_hundred_samples"
        and source.get("missing_sequence_detected") is True
        and source.get("orphaned_sample_rejected") is True
        and source.get("same_identity_state_and_flux_match") is True,
        "source_harmonic_scope_is_reported_without_overclaim": source.get(
            "source_solver_harmonic_capability"
        )
        is True
        and source.get(
            "fundamental_projection_error_band"
        )
        == "below_five_e_minus_four"
        and source.get("historical_fundamental_only_gap_detected") is True
        and source.get("historical_third_harmonic_field_zero") is True,
        "replacement_commits_only_accepted_history": replacement.get(
            "executed"
        )
        is True
        and replacement.get("converged") is True
        and replacement.get("identity_digest") == identity
        and replacement.get("committed_state_external") is True
        and replacement.get("rollback_verified") is True
        and replacement.get("signed_passive_cycle_verified") is True,
        "replacement_odd_harmonics_have_window_residual_and_closure": replacement.get(
            "odd_harmonics"
        )
        == [1, 3, 5, 7]
        and replacement.get("integer_period_projection") is True
        and replacement.get("endpoint_duplicated") is False
        and replacement.get("phase_convention") == "real_sine_positive"
        and replacement.get("coefficient_residual_closed") is True
        and replacement.get("waveform_residual_closed") is True
        and replacement.get("fundamental_only_reconstruction_rejected") is True,
        "replacement_vector_energy_history_is_verified": replacement.get(
            "vector_constitutive_lane"
        )
        == "b_input_energy_stop"
        and replacement.get("three_dimensional_vector_path_executed") is True
        and replacement.get("vector_isotropy_verified") is True
        and replacement.get("vector_passivity_verified") is True,
        "solver_neutral_public_gate_closed": gate.get("policy")
        == "history_harmonic_same_identity_gate_v1"
        and gate.get("status") == "ok",
        "scope_does_not_overclaim_overall_retirement": summary.get(
            "research_lab_retirement_ready"
        )
        is False
        and summary.get("product_or_market_retirement_ready") is False,
    }
    ok = all(checks.values())
    return {
        "schema": "elf-history-harmonic-replay-contract/v2",
        "status": "verified_partial" if ok else "needs_attention",
        "checks": checks,
        "issues": [name for name, passed in checks.items() if not passed],
        "history_harmonic_replacement_superset_verified": ok,
        "elf_solver_hysteresis_capability_verified": False,
        "elf_solver_harmonic_capability_verified": ok,
        "research_lab_retirement_ready": False,
        "product_or_market_retirement_ready": False,
        "notes": [
            "A missing history sample splits the replay; samples after the gap are not silently stitched.",
            "A fundamental effective slope is not harmonic balance when non-zero odd modes are omitted.",
            "Imported history is replacement test data, not evidence that ELF/MAGIC solves hysteresis.",
        ],
    }


history_harmonic_replay_contract_gate = hysteresis_harmonic_replay_contract_gate
