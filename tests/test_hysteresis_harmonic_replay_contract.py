from __future__ import annotations

import json

from elf_mcp_server.hysteresis_harmonic_replay_contract import (
    history_harmonic_replay_contract_gate,
    hysteresis_harmonic_replay_contract_gate,
)
from elf_mcp_server.server import (
    elf_history_harmonic_replay_contract_gate,
    elf_hysteresis_harmonic_replay_contract_gate,
)


def _fixture() -> dict[str, object]:
    digest = "a" * 64
    return {
        "schema": "elf-history-harmonic-replay-metadata/v2",
        "source_values_embedded": False,
        "local_paths_embedded": False,
        "physics_identity_digest": digest,
        "source_baseline": {
            "executed": True,
            "current_version_recorded": True,
            "history_provenance": "imported_or_archived_field_history",
            "source_solver_hysteresis_capability": False,
            "source_solver_harmonic_capability": True,
            "history_dependent_data": True,
            "contiguous_history_band": "at_least_one_hundred_samples",
            "missing_sequence_detected": True,
            "orphaned_sample_rejected": True,
            "same_identity_state_and_flux_match": True,
            "fundamental_projection_error_band": "below_five_e_minus_four",
            "historical_fundamental_only_gap_detected": True,
            "historical_third_harmonic_field_zero": True,
            "history_artifact_sha256": "b" * 64,
            "harmonic_artifact_sha256": "c" * 64,
        },
        "replacement_superset": {
            "executed": True,
            "converged": True,
            "identity_digest": digest,
            "committed_state_external": True,
            "rollback_verified": True,
            "signed_passive_cycle_verified": True,
            "odd_harmonics": [1, 3, 5, 7],
            "integer_period_projection": True,
            "endpoint_duplicated": False,
            "phase_convention": "real_sine_positive",
            "coefficient_residual_closed": True,
            "waveform_residual_closed": True,
            "fundamental_only_reconstruction_rejected": True,
            "vector_constitutive_lane": "b_input_energy_stop",
            "three_dimensional_vector_path_executed": True,
            "vector_isotropy_verified": True,
            "vector_passivity_verified": True,
            "artifact_sha256": "d" * 64,
        },
        "public_gate": {
            "policy": "history_harmonic_same_identity_gate_v1",
            "status": "ok",
        },
        "research_lab_retirement_ready": False,
        "product_or_market_retirement_ready": False,
    }


def test_accepts_public_safe_history_and_harmonic_superset_metadata() -> None:
    fixture = _fixture()
    result = hysteresis_harmonic_replay_contract_gate(json.dumps(fixture))
    assert result["status"] == "verified_partial"
    assert result["elf_solver_hysteresis_capability_verified"] is False
    assert history_harmonic_replay_contract_gate(json.dumps(fixture)) == result
    assert json.loads(elf_history_harmonic_replay_contract_gate(json.dumps(fixture)))["status"] == "verified_partial"
    assert json.loads(elf_hysteresis_harmonic_replay_contract_gate(json.dumps(fixture)))["status"] == "verified_partial"


def test_rejects_imported_history_relabelled_as_elf_hysteresis_capability() -> None:
    fixture = _fixture()
    fixture["source_baseline"]["source_solver_hysteresis_capability"] = True
    assert hysteresis_harmonic_replay_contract_gate(json.dumps(fixture))["status"] == "needs_attention"


def test_rejects_trial_state_committed_before_acceptance() -> None:
    fixture = _fixture()
    fixture["replacement_superset"]["rollback_verified"] = False
    assert hysteresis_harmonic_replay_contract_gate(json.dumps(fixture))["status"] == "needs_attention"


def test_rejects_ambiguous_cycle_energy_sign() -> None:
    fixture = _fixture()
    fixture["replacement_superset"]["signed_passive_cycle_verified"] = False
    assert hysteresis_harmonic_replay_contract_gate(json.dumps(fixture))["status"] == "needs_attention"


def test_rejects_fundamental_only_reconstruction() -> None:
    fixture = _fixture()
    fixture["replacement_superset"]["odd_harmonics"] = [1]
    assert hysteresis_harmonic_replay_contract_gate(json.dumps(fixture))["status"] == "needs_attention"


def test_rejects_endpoint_duplicated_fourier_window() -> None:
    fixture = _fixture()
    fixture["replacement_superset"]["endpoint_duplicated"] = True
    assert hysteresis_harmonic_replay_contract_gate(json.dumps(fixture))["status"] == "needs_attention"


def test_rejects_nominal_modes_without_coefficient_residual() -> None:
    fixture = _fixture()
    fixture["replacement_superset"]["coefficient_residual_closed"] = False
    assert hysteresis_harmonic_replay_contract_gate(json.dumps(fixture))["status"] == "needs_attention"


def test_rejects_embedded_values_or_paths() -> None:
    fixture = _fixture()
    fixture["source_baseline"]["field_values"] = [1.0]
    assert hysteresis_harmonic_replay_contract_gate(json.dumps(fixture))["status"] == "needs_attention"
