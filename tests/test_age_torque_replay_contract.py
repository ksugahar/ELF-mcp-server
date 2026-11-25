from __future__ import annotations

import copy
import hashlib
import json

from elf_mcp_server.age_torque_replay_contract import age_torque_replay_contract_gate


def _fixture() -> dict[str, object]:
    identity = hashlib.sha256(b"private-age-torque-identity").hexdigest()
    inputs = [
        {
            "analysis": hashlib.sha256(f"analysis-{index}".encode()).hexdigest(),
            "geometry": hashlib.sha256(f"geometry-{index}".encode()).hexdigest(),
        }
        for index in range(3)
    ]
    return {
        "schema": "elf-age-torque-replay-metadata/v1",
        "physics_identity_digest": identity,
        "source_values_embedded": False,
        "local_paths_embedded": False,
        "source_replay": {
            "input_sha256": inputs,
            "physics_role": "magnetic_force_torque",
            "execution_mode": "headless_direct_cli",
            "magnetic_hex_counts": [40, 320, 1080],
            "mesh_convergence_verified": True,
            "angle_symmetry_verified": True,
            "closed_surface_force_residual_verified": True,
            "fresh_outputs_verified": True,
            "timeout_count": 0,
            "stale_count": 0,
            "solver_version": "recorded",
            "executed_at_utc": "2026-07-31T14:00:00+00:00",
        },
        "replacement_route": {
            "lane_id": "ngsolve_age",
            "solver_ready": True,
            "executed": True,
            "discretization_converged": True,
            "action_reaction_verified": True,
            "gap_radius_invariance_verified": True,
            "verification_count": 4,
            "artifact_sha256": hashlib.sha256(b"replacement").hexdigest(),
            "identity_digest": identity,
            "solver_version": "recorded",
            "executed_at_utc": "2026-07-31T14:00:00+00:00",
        },
        "same_identity_tolerance_met": True,
        "dimensional_scope": "long_extrusion_limit",
        "research_lab_retirement_ready": False,
        "product_or_market_retirement_ready": False,
    }


def test_accepts_metadata_only_age_torque_replay() -> None:
    result = age_torque_replay_contract_gate(json.dumps(_fixture()))
    assert result["status"] == "verified_partial"
    assert result["issues"] == []


def test_rejects_wrong_replacement_lane() -> None:
    summary = _fixture()
    summary["replacement_route"]["lane_id"] = "unlisted_reduced_fem_lane"
    result = age_torque_replay_contract_gate(json.dumps(summary))
    assert "replacement_is_executed_same_identity_ngsolve_age" in result["issues"]


def test_rejects_embedded_values_or_paths() -> None:
    summary = _fixture()
    summary["source_values_embedded"] = True
    result = age_torque_replay_contract_gate(json.dumps(summary))
    assert "metadata_has_no_source_values_or_paths" in result["issues"]


def test_rejects_stale_or_unbalanced_replay() -> None:
    summary = copy.deepcopy(_fixture())
    summary["source_replay"]["stale_count"] = 1
    summary["replacement_route"]["action_reaction_verified"] = False
    result = age_torque_replay_contract_gate(json.dumps(summary))
    assert "source_outputs_are_fresh_and_bounded" in result["issues"]
    assert "replacement_is_executed_same_identity_ngsolve_age" in result["issues"]


def test_rejects_arbitrary_three_dimensional_overclaim() -> None:
    summary = _fixture()
    summary["dimensional_scope"] = "arbitrary_3d_motion"
    result = age_torque_replay_contract_gate(json.dumps(summary))
    assert "same_identity_tolerance_is_verified_in_declared_scope" in result["issues"]
