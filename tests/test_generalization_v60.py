from copy import deepcopy

from elf_mcp_server.v60_identity import (
    ACA,
    BEM_MATRIX,
    validate_source_v60_identity,
)


CASE_IDS = {
    "v60_source_tool_aca_pivot_residual_rank_block_cluster_matrix_owner_mismatch",
    "v60_source_tool_bem_matrix_symmetry_positiveenergy_panelnormal_quadrature_mesh_owner_mismatch",
}


def _row(
    generation: str,
    generation_fields: tuple[str, ...],
    values: dict[str, object],
    digest: str,
) -> dict[str, object]:
    return {
        "generation": generation,
        **{field: generation for field in generation_fields},
        **values,
        **{f"replayed_{key}": value for key, value in values.items()},
        "result_sha256": digest * 64,
        "accepted_result_sha256": digest * 64,
    }


def _identity() -> dict[str, object]:
    aca = {
        "pivot_sequence": [
            {"row": 2, "column": 4, "magnitude": 1.0},
            {"row": 5, "column": 1, "magnitude": 0.2},
            {"row": 0, "column": 3, "magnitude": 0.04},
        ],
        "residual_estimate": [1.0, 0.2, 0.04, 0.008],
        "relative_tolerance": 0.01,
        "rank": 3,
        "block_owner": "block:aca-v60",
        "row_cluster_owner": "cluster:row-v60",
        "column_cluster_owner": "cluster:column-v60",
        "matrix_revision_sha256": "3" * 64,
        "matrix_owner": "matrix:aca-v60",
    }
    matrix = [[2.0, -1.0, 0.0], [-1.0, 2.0, -1.0], [0.0, -1.0, 2.0]]
    probe = [1.0, 2.0, 3.0]
    bem = {
        "bem_matrix": matrix,
        "symmetry_tolerance": 1.0e-12,
        "energy_probe": probe,
        "positive_energy": sum(
            probe[row] * matrix[row][column] * probe[column]
            for row in range(3)
            for column in range(3)
        ),
        "panel_normals": [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ],
        "quadrature_identity": "triangle-gauss-order-4",
        "quadrature_order": 4,
        "boundary_mesh_revision_sha256": "5" * 64,
        "boundary_mesh_owner": "mesh-owner:bem-v60",
    }
    return {
        ACA: _row(
            "aca-v60-test",
            (
                "pivot_generation",
                "residual_generation",
                "rank_generation",
                "block_generation",
                "cluster_generation",
                "matrix_generation",
                "owner_generation",
                "result_generation",
            ),
            aca,
            "4",
        ),
        BEM_MATRIX: _row(
            "bem-matrix-v60-test",
            (
                "matrix_generation",
                "symmetry_generation",
                "energy_generation",
                "normal_generation",
                "quadrature_generation",
                "mesh_generation",
                "owner_generation",
                "result_generation",
            ),
            bem,
            "6",
        ),
    }


def test_v60_positive_identities_are_accepted() -> None:
    assert all(validate_source_v60_identity([_identity(), _identity()]).values())


def test_v60_frozen_mutations_are_rejected() -> None:
    identities = [_identity(), _identity()]
    identities[0][ACA]["replayed_rank"] = 99
    identities[0][BEM_MATRIX]["replayed_boundary_mesh_owner"] = "mesh-owner:stale"
    assert not all(validate_source_v60_identity(identities).values())


def test_v60_self_consistent_numerical_contradictions_are_rejected() -> None:
    identities = [_identity(), _identity()]
    bad_residual = [1.0, 2.0, 3.0, 4.0]
    identities[0][ACA]["residual_estimate"] = bad_residual
    identities[0][ACA]["replayed_residual_estimate"] = bad_residual
    bad_matrix = [[0.0, 1.0], [0.0, 0.0]]
    identities[0][BEM_MATRIX]["bem_matrix"] = bad_matrix
    identities[0][BEM_MATRIX]["replayed_bem_matrix"] = bad_matrix
    assert not all(validate_source_v60_identity(identities).values())


def test_v60_malformed_values_reject_without_raising() -> None:
    identities = [_identity(), _identity()]
    identities[0][ACA]["pivot_sequence"] = "bad"
    identities[0][BEM_MATRIX]["panel_normals"] = [[1.0]]
    assert not all(validate_source_v60_identity(identities).values())
