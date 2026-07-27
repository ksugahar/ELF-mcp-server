from copy import deepcopy

from elf_mcp_server.v59_identity import CURRENT, NEAR, validate_source_v59_identity


CASE_IDS = {"v59_source_tool_bem_nearsingular_distance_quadrature_order_tolerance_mesh_owner_mismatch", "v59_source_tool_conductor_current_incidence_divergence_continuity_source_owner_mismatch"}


def _row(name: str, fields: tuple[str, ...], values: dict[str, object], digit: str) -> dict[str, object]:
    return {"generation": name, **{field: name for field in fields}, **values, **{"replayed_" + key: value for key, value in values.items()}, "result_sha256": digit * 64, "accepted_result_sha256": digit * 64}


def _identities() -> list[dict[str, object]]:
    near = {"source_target_distance_m": 5.0e-4, "panel_diameter_m": 1.0e-2, "distance_ratio": 0.05, "quadrature_order": 8, "required_quadrature_order": 7, "estimated_relative_error": 2.0e-7, "relative_tolerance": 1.0e-6, "near_singular_class": "near", "mesh_revision": "mesh:near-v59", "mesh_owner": "mesh-owner:near-v59"}
    current = {"incidence_matrix": [[-1, 0], [1, -1], [0, 1]], "branch_currents_a": [2.0, 2.0], "nodal_divergence_a": [-2.0, 0.0, 2.0], "source_injection_a": [-2.0, 0.0, 2.0], "continuity_residual_a": [0.0, 0.0, 0.0], "source_revision": "source:current-v59", "topology_owner": "topology-owner:current-v59"}
    fields_near = ("distance_generation", "quadrature_generation", "tolerance_generation", "mesh_generation", "owner_generation", "result_generation")
    fields_current = ("incidence_generation", "current_generation", "divergence_generation", "continuity_generation", "source_generation", "owner_generation", "result_generation")
    return [{NEAR: _row("near-v59", fields_near, near, "3"), CURRENT: _row("current-v59", fields_current, current, "4")} for _ in range(2)]


def test_v59_case_ids_are_frozen() -> None:
    assert len(CASE_IDS) == 2


def test_v59_positive_identities_are_accepted() -> None:
    assert all(validate_source_v59_identity(_identities()).values())


def test_v59_replay_mutations_are_rejected() -> None:
    values = deepcopy(_identities()); values[0][NEAR]["replayed_mesh_owner"] = "mesh-owner:stale"; values[0][CURRENT]["replayed_source_revision"] = "source:stale"
    assert not all(validate_source_v59_identity(values).values())


def test_v59_self_consistent_physics_contradictions_are_rejected() -> None:
    values = deepcopy(_identities())
    for value in values:
        value[NEAR]["quadrature_order"] = value[NEAR]["replayed_quadrature_order"] = 1
        value[CURRENT]["continuity_residual_a"] = value[CURRENT]["replayed_continuity_residual_a"] = [1.0, 0.0, 0.0]
    assert not all(validate_source_v59_identity(values).values())
