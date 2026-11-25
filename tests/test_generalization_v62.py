from __future__ import annotations

from copy import deepcopy
import json
import math

from elf_mcp_server.server import elf_force_method_profile_contract_gate
from elf_mcp_server.v62_identity import MAO_HARMONIC, SECTOR, validate_source_v62_identity
from test_force_method_profile_contract import _summary


CASE_IDS = {
    "v62_source_tool_mao_complexharmonic_realimag_phase_frequency_component_body_owner_mismatch",
    "v62_source_tool_bem_sectorreplication_transform_magnetization_bodymap_result_owner_mismatch",
}


def _row(generation: str, fields: tuple[str, ...], values: dict, digest: str) -> dict:
    return {
        "generation": generation,
        **{field: generation for field in fields},
        **values,
        **{f"replayed_{key}": value for key, value in values.items()},
        "result_sha256": digest * 64,
        "accepted_result_sha256": digest * 64,
    }


def _identity() -> dict:
    order = ["Bx", "By", "Bz"]
    real = {"Bx": 0.3, "By": -0.4, "Bz": 0.0}
    imaginary = {"Bx": 0.4, "By": 0.3, "Bz": 0.1}
    harmonic = {
        "frequency_hz": 400.0,
        "phase_convention": "real_part_of_phasor_exp_plus_j_omega_t",
        "component_order": order,
        "real_components_t": real,
        "imaginary_components_t": imaginary,
        "amplitude_components_t": [math.hypot(real[name], imaginary[name]) for name in order],
        "phase_components_deg": [math.degrees(math.atan2(imaginary[name], real[name])) for name in order],
        "body_identity": "body:mao-harmonic-v62",
        "result_owner": "result:mao-harmonic-v62",
    }
    count = 8
    angles = [45.0 * index for index in range(count)]
    sector = {
        "sector_count": count,
        "base_sector_angle_deg": 45.0,
        "replication_transform_angles_deg": angles,
        "base_magnetization_vector": [1.0, 0.0, 0.0],
        "replicated_magnetization_vectors": [
            [math.cos(math.radians(angle)), math.sin(math.radians(angle)), 0.0]
            for angle in angles
        ],
        "replicated_body_map": {str(index): f"body:sector-{index}" for index in range(count)},
        "source_sector_owner": "body:sector-source-v62",
        "result_generation_id": "result-generation:sector-v62",
        "result_owner": "result:sector-v62",
    }
    return {
        MAO_HARMONIC: _row(
            "harmonic-v62-test",
            (
                "harmonic_generation", "complex_generation", "phase_generation", "frequency_generation",
                "component_generation", "body_generation", "owner_generation", "result_generation",
            ), harmonic, "e",
        ),
        SECTOR: _row(
            "sector-v62-test",
            (
                "sector_generation", "transform_generation", "magnetization_generation",
                "bodymap_generation", "result_generation", "owner_generation",
            ), sector, "f",
        ),
    }


def test_v62_positive_identities_and_mcp_surface_are_accepted() -> None:
    identities = [_identity(), deepcopy(_identity())]
    assert all(validate_source_v62_identity(identities).values())
    summary = _summary()
    for run in summary["runs"]:
        run.update(deepcopy(_identity()))
    result = json.loads(elf_force_method_profile_contract_gate(json.dumps(summary)))
    assert result["status"] == "ok"
    assert all(result["force_v62_identity_checks"].values())


def test_v62_frozen_replay_mutations_are_rejected() -> None:
    identities = [_identity(), deepcopy(_identity())]
    identities[0][MAO_HARMONIC].update(
        replayed_frequency_hz=-1.0, replayed_phase_convention="stale",
        replayed_component_order=["Bz", "Bx"], replayed_real_components_t={"Bx": 9.0},
        replayed_imaginary_components_t={"Bx": 9.0}, replayed_body_identity="body:stale",
        replayed_result_owner="result:stale",
    )
    identities[0][SECTOR].update(
        replayed_sector_count=3, replayed_replication_transform_angles_deg=[0.0],
        replayed_replicated_magnetization_vectors=[[9.0, 9.0, 9.0]],
        replayed_replicated_body_map={"0": "body:stale"},
        replayed_result_generation_id="result-generation:stale", replayed_result_owner="result:stale",
    )
    assert not all(validate_source_v62_identity(identities).values())


def test_v62_self_consistent_semantic_contradictions_are_rejected() -> None:
    identities = [_identity(), deepcopy(_identity())]
    identities[0][MAO_HARMONIC]["amplitude_components_t"] = [9.0, 9.0, 9.0]
    identities[0][MAO_HARMONIC]["replayed_amplitude_components_t"] = [9.0, 9.0, 9.0]
    identities[0][SECTOR]["base_sector_angle_deg"] = 90.0
    identities[0][SECTOR]["replayed_base_sector_angle_deg"] = 90.0
    assert not all(validate_source_v62_identity(identities).values())


def test_v62_malformed_values_reject_without_raising() -> None:
    identities = [_identity(), deepcopy(_identity())]
    identities[0][MAO_HARMONIC]["component_order"] = "bad"
    identities[0][SECTOR]["replicated_body_map"] = []
    assert not all(validate_source_v62_identity(identities).values())
