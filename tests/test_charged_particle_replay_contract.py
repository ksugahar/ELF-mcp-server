from __future__ import annotations

import json

from elf_mcp_server.charged_particle_replay_contract import (
    charged_particle_replay_contract_gate,
)
from elf_mcp_server.server import elf_charged_particle_replay_contract_gate


def _fixture() -> dict[str, object]:
    return {
        "schema": "elf-charged-particle-replay-metadata/v1",
        "physics_identity_digest": "a" * 64,
        "source_values_embedded": False,
        "local_paths_embedded": False,
        "source_baseline": {
            "executed": True,
            "current_field_solver_version_recorded": True,
            "current_trajectory_solver_version_recorded": True,
            "execution_route": "direct_solver_no_gui",
            "gui_visible": False,
            "completion_dialog": False,
            "field_and_trajectory_generation_closed": True,
            "input_manifest_sha256": "b" * 64,
            "field_artifact_sha256": "c" * 64,
            "trajectory_artifact_sha256": "d" * 64,
            "charge_mass_energy_identity_bound": True,
            "kinetic_voltage_semantics_verified": True,
            "relativistic_policy_recorded": True,
            "coordinate_and_field_units_explicit": True,
            "all_particle_states_accounted": True,
            "unwritten_allocation_rows_rejected": True,
            "stop_policy": "first_physical_event",
        },
        "replacement_superset": {
            "executed": True,
            "converged": True,
            "identity_digest": "a" * 64,
            "artifact_sha256": "e" * 64,
            "physical_time_backend": "scipy.integrate.solve_ivp:DOP853",
            "beamline_backend": "xtrack.BorisSpatialIntegrator",
            "kinetic_voltage_conversion_verified": True,
            "magnetic_tracking_verified": True,
            "electrostatic_acceleration_verified": True,
            "relativistic_policy_verified": True,
            "first_stop_event_verified": True,
        },
        "public_gate": {
            "policy": "charged_particle_same_identity_gate_v1",
            "status": "ok",
        },
        "research_lab_retirement_ready": False,
        "product_or_market_retirement_ready": False,
    }


def _gate(payload: dict[str, object]) -> dict[str, object]:
    return charged_particle_replay_contract_gate(json.dumps(payload))


def test_accepts_public_safe_charged_particle_metadata_and_dispatches() -> None:
    fixture = _fixture()
    assert _gate(fixture)["status"] == "verified_partial"
    assert json.loads(elf_charged_particle_replay_contract_gate(json.dumps(fixture)))[
        "status"
    ] == "verified_partial"


def test_rejects_embedded_product_values_or_local_paths() -> None:
    fixture = _fixture()
    fixture["charge_c"] = [-1.0]
    fixture["source_note"] = "C:\\licensed\\example"
    assert _gate(fixture)["status"] == "needs_attention"


def test_rejects_stale_field_trajectory_generation() -> None:
    fixture = _fixture()
    fixture["source_baseline"]["field_and_trajectory_generation_closed"] = False
    assert _gate(fixture)["status"] == "needs_attention"


def test_rejects_unbound_charge_mass_or_voltage_semantics() -> None:
    fixture = _fixture()
    fixture["source_baseline"]["charge_mass_energy_identity_bound"] = False
    fixture["source_baseline"]["kinetic_voltage_semantics_verified"] = False
    assert _gate(fixture)["status"] == "needs_attention"


def test_rejects_implicit_coordinate_or_field_units() -> None:
    fixture = _fixture()
    fixture["source_baseline"]["coordinate_and_field_units_explicit"] = False
    assert _gate(fixture)["status"] == "needs_attention"


def test_rejects_allocation_tail_or_wrong_stop_policy() -> None:
    fixture = _fixture()
    fixture["source_baseline"]["unwritten_allocation_rows_rejected"] = False
    fixture["source_baseline"]["stop_policy"] = "last_allocated_row"
    assert _gate(fixture)["status"] == "needs_attention"


def test_rejects_missing_relativistic_or_electric_replacement_modes() -> None:
    fixture = _fixture()
    fixture["replacement_superset"]["relativistic_policy_verified"] = False
    fixture["replacement_superset"]["electrostatic_acceleration_verified"] = False
    assert _gate(fixture)["status"] == "needs_attention"


def test_rejects_missing_solver_neutral_gate() -> None:
    fixture = _fixture()
    fixture["public_gate"]["status"] = "needs_attention"
    assert _gate(fixture)["status"] == "needs_attention"
