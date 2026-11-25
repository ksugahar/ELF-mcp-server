import copy
import json

from elf_mcp_server.electrostatic_replay_contract import (
    electrostatic_replay_contract_gate,
)
from elf_mcp_server.server import elf_electrostatic_replay_contract_gate


def _summary() -> dict:
    identity = "a" * 64
    return {
        "schema": "elf-electrostatic-replay-metadata/v1",
        "source_values_embedded": False,
        "local_paths_embedded": False,
        "physics_identity_digest": identity,
        "source_replay": {
            "physics_role": "electrostatic_charge_and_field",
            "execution_mode": "headless_direct_cli",
            "input_sha256": {"analysis": "b" * 64, "geometry": "c" * 64},
            "surface_dof_levels": [8, 32, 128, 512],
            "timeout_count": 0,
            "stale_count": 0,
            "charge_conservation_verified": True,
            "refinement_converged": True,
            "solver_version": "13.0.0",
            "executed_at_utc": "2026-07-31T11:00:00+00:00",
        },
        "replacement_route": {
            "lane_id": "ngsolve_electrostatics_bem",
            "solver_ready": True,
            "executed": True,
            "verification_count": 3,
            "artifact_sha256": "d" * 64,
            "solver_version": "revision-123",
            "executed_at_utc": "2026-07-31T11:01:00+00:00",
            "identity_digest": identity,
        },
        "same_identity_tolerance_met": True,
        "research_lab_retirement_ready": False,
        "product_or_market_retirement_ready": False,
    }


def test_electrostatic_contract_accepts_converged_same_identity_replay():
    payload = _summary()
    direct = electrostatic_replay_contract_gate(json.dumps(payload))
    dispatched = json.loads(elf_electrostatic_replay_contract_gate(json.dumps(payload)))
    assert direct["status"] == "verified_partial"
    assert direct["electrostatic_replacement_route_verified"] is True
    assert dispatched["status"] == "verified_partial"


def test_electrostatic_contract_rejects_eddy_current_misrouting():
    payload = _summary()
    payload["replacement_route"]["lane_id"] = "unlisted_replacement_lane"
    result = electrostatic_replay_contract_gate(json.dumps(payload))
    assert result["status"] == "needs_attention"
    assert result["checks"]["replacement_is_executed_same_identity"] is False


def test_electrostatic_contract_rejects_identity_or_freshness_mismatch():
    payload = copy.deepcopy(_summary())
    payload["replacement_route"]["identity_digest"] = "e" * 64
    payload["source_replay"]["stale_count"] = 1
    result = electrostatic_replay_contract_gate(json.dumps(payload))
    assert result["status"] == "needs_attention"
    assert result["checks"]["source_outputs_are_fresh_and_bounded"] is False
    assert result["checks"]["replacement_is_executed_same_identity"] is False


def test_electrostatic_contract_rejects_values_or_retirement_overclaim():
    payload = _summary()
    payload["source_values_embedded"] = True
    payload["research_lab_retirement_ready"] = True
    result = electrostatic_replay_contract_gate(json.dumps(payload))
    assert result["status"] == "needs_attention"
    assert result["checks"]["metadata_has_no_source_values_or_paths"] is False
    assert result["checks"]["scope_does_not_overclaim_retirement"] is False
