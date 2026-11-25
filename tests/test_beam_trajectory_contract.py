import copy
import json

from elf_mcp_server.beam_trajectory_contract import beam_trajectory_run_contract_gate
from elf_mcp_server.server import elf_beam_trajectory_run_contract_gate


def _summary():
    return {
        "solver_family": "BEAM",
        "execution_route": "direct_beam_solver_no_gui",
        "gui_visible": False,
        "completion_dialog": False,
        "solver_version": "product solver version",
        "run_date_utc": "2026-07-31T00:00:00+00:00",
        "source_digest_count": 3,
        "output_roles": {".mao": "run_log", ".mag": "trajectory_result"},
        "all_outputs_fresh": True,
        "run_id": "beam-generation-1",
        "field_generation_id": "beam-generation-1",
        "trajectory_generation_id": "beam-generation-1",
        "interaction_mode": "transit",
        "field_mode": "magnetic_only",
        "particle_count": 3,
        "trajectory_count": 3,
        "trajectory_ids_unique": True,
        "position_unit": "m",
        "speed_unit": "m/s",
        "energy_unit": "eV",
        "source_current_a": 1.0,
        "terminal_current_a": 1.0,
        "boundary_hit_count": 0,
        "collision_power_w": 0.0,
        "maximum_relative_energy_drift": 1.0e-10,
        "public_gate_status": "ok",
    }


def test_accepts_gui_free_magnetic_transit_and_dispatches():
    result = beam_trajectory_run_contract_gate(json.dumps(_summary()))
    dispatched = json.loads(elf_beam_trajectory_run_contract_gate(json.dumps(_summary())))
    assert result["status"] == "ok"
    assert dispatched["status"] == "ok"


def test_accepts_collision_with_terminal_accounting():
    payload = _summary()
    payload.update(
        interaction_mode="collision",
        boundary_hit_count=3,
        collision_power_w=2.5,
    )
    assert beam_trajectory_run_contract_gate(json.dumps(payload))["status"] == "ok"


def test_rejects_stale_generation_and_magnetic_energy_drift():
    payload = copy.deepcopy(_summary())
    payload["trajectory_generation_id"] = "old-generation"
    payload["maximum_relative_energy_drift"] = 2.0e-3
    result = beam_trajectory_run_contract_gate(json.dumps(payload))
    assert result["status"] == "needs_attention"
    assert result["checks"]["run_generation_identity_closes"] is False
    assert result["checks"]["magnetic_field_does_no_work"] is False


def test_rejects_transit_with_collision_accounting():
    payload = copy.deepcopy(_summary())
    payload["boundary_hit_count"] = 3
    payload["collision_power_w"] = 2.5
    result = beam_trajectory_run_contract_gate(json.dumps(payload))
    assert result["status"] == "needs_attention"
    assert result["checks"]["boundary_accounting_matches_mode"] is False
    assert result["checks"]["collision_power_matches_mode"] is False
