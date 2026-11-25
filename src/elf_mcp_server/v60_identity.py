"""Public-safe ACA and BEM matrix replay checks."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

from .v59_identity import validate_source_v59_identity


ACA = "aca_pivot_residual_rank_block_cluster_matrix_owner_identity"
BEM_MATRIX = (
    "bem_matrix_symmetry_positiveenergy_panelnormal_quadrature_mesh_owner_identity"
)


def _number(value: object, *, positive: bool = False, nonnegative: bool = False) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    number = float(value)
    return (
        math.isfinite(number)
        and (not positive or number > 0.0)
        and (not nonnegative or number >= 0.0)
    )


def _close(left: object, right: object, tolerance: float = 1.0e-10) -> bool:
    return _number(left) and _number(right) and math.isclose(
        float(left), float(right), rel_tol=1.0e-9, abs_tol=tolerance
    )


def _vector(value: object, length: int | None = None) -> list[float]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or not value
        or not all(_number(item) for item in value)
        or (length is not None and len(value) != length)
    ):
        return []
    return [float(item) for item in value]


def _matrix(value: object) -> list[list[float]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or not value:
        return []
    rows = [_vector(row) for row in value]
    size = len(rows)
    return rows if size and all(len(row) == size for row in rows) else []


def _digest(value: object) -> bool:
    text = str(value or "").lower()
    return len(text) == 64 and all(character in "0123456789abcdef" for character in text)


def _generations(row: Mapping[str, object], *fields: str) -> bool:
    generation = str(row.get("generation") or "")
    return bool(generation) and all(row.get(field) == generation for field in fields)


def _result(row: Mapping[str, object]) -> bool:
    return _digest(row.get("result_sha256")) and row.get(
        "accepted_result_sha256"
    ) == row.get("result_sha256")


def _replay_copies(row: Mapping[str, object], fields: tuple[str, ...]) -> bool:
    return all(row.get(f"replayed_{field}") == row.get(field) for field in fields)


def _aca_ok(row: Mapping[str, object]) -> bool:
    pivots = row.get("pivot_sequence")
    residual = _vector(row.get("residual_estimate"))
    rank = row.get("rank")
    tolerance = row.get("relative_tolerance")
    if (
        not isinstance(pivots, Sequence)
        or isinstance(pivots, (str, bytes))
        or not pivots
        or not isinstance(rank, int)
        or isinstance(rank, bool)
        or rank != len(pivots)
        or len(residual) != rank + 1
        or not _number(tolerance, positive=True)
    ):
        return False
    locations: set[tuple[int, int]] = set()
    magnitudes: list[float] = []
    for pivot in pivots:
        if (
            not isinstance(pivot, Mapping)
            or set(pivot) != {"row", "column", "magnitude"}
            or not isinstance(pivot.get("row"), int)
            or isinstance(pivot.get("row"), bool)
            or int(pivot["row"]) < 0
            or not isinstance(pivot.get("column"), int)
            or isinstance(pivot.get("column"), bool)
            or int(pivot["column"]) < 0
            or not _number(pivot.get("magnitude"), positive=True)
        ):
            return False
        locations.add((int(pivot["row"]), int(pivot["column"])))
        magnitudes.append(float(pivot["magnitude"]))
    fields = (
        "pivot_sequence",
        "residual_estimate",
        "relative_tolerance",
        "rank",
        "block_owner",
        "row_cluster_owner",
        "column_cluster_owner",
        "matrix_revision_sha256",
        "matrix_owner",
    )
    return (
        _generations(
            row,
            "pivot_generation",
            "residual_generation",
            "rank_generation",
            "block_generation",
            "cluster_generation",
            "matrix_generation",
            "owner_generation",
            "result_generation",
        )
        and len(locations) == rank
        and all(left > right > 0.0 for left, right in zip(residual, residual[1:]))
        and all(_close(value, residual[index]) for index, value in enumerate(magnitudes))
        and residual[-1] <= float(tolerance)
        and str(row.get("block_owner") or "").startswith("block:")
        and str(row.get("row_cluster_owner") or "").startswith("cluster:")
        and str(row.get("column_cluster_owner") or "").startswith("cluster:")
        and row.get("row_cluster_owner") != row.get("column_cluster_owner")
        and _digest(row.get("matrix_revision_sha256"))
        and str(row.get("matrix_owner") or "").startswith("matrix:")
        and _replay_copies(row, fields)
        and _result(row)
    )


def _positive_definite(matrix: list[list[float]], tolerance: float) -> bool:
    size = len(matrix)
    lower = [[0.0] * size for _ in range(size)]
    for row in range(size):
        for column in range(row + 1):
            remainder = matrix[row][column] - sum(
                lower[row][index] * lower[column][index] for index in range(column)
            )
            if row == column:
                if remainder <= tolerance:
                    return False
                lower[row][column] = math.sqrt(remainder)
            else:
                lower[row][column] = remainder / lower[column][column]
    return True


def _bem_matrix_ok(row: Mapping[str, object]) -> bool:
    matrix = _matrix(row.get("bem_matrix"))
    tolerance = row.get("symmetry_tolerance")
    probe = _vector(row.get("energy_probe"))
    normals = row.get("panel_normals")
    order = row.get("quadrature_order")
    if (
        not matrix
        or not _number(tolerance, positive=True)
        or len(probe) != len(matrix)
        or not isinstance(normals, Sequence)
        or isinstance(normals, (str, bytes))
        or len(normals) != len(matrix)
        or not isinstance(order, int)
        or isinstance(order, bool)
        or order <= 0
    ):
        return False
    parsed_normals = [_vector(normal, 3) for normal in normals]
    if not all(parsed_normals):
        return False
    energy = sum(
        probe[row_index] * matrix[row_index][column_index] * probe[column_index]
        for row_index in range(len(matrix))
        for column_index in range(len(matrix))
    )
    fields = (
        "bem_matrix",
        "symmetry_tolerance",
        "energy_probe",
        "positive_energy",
        "panel_normals",
        "quadrature_identity",
        "quadrature_order",
        "boundary_mesh_revision_sha256",
        "boundary_mesh_owner",
    )
    return (
        _generations(
            row,
            "matrix_generation",
            "symmetry_generation",
            "energy_generation",
            "normal_generation",
            "quadrature_generation",
            "mesh_generation",
            "owner_generation",
            "result_generation",
        )
        and all(
            abs(matrix[i][j] - matrix[j][i]) <= float(tolerance)
            for i in range(len(matrix))
            for j in range(len(matrix))
        )
        and _positive_definite(matrix, float(tolerance))
        and _number(row.get("positive_energy"), positive=True)
        and _close(row.get("positive_energy"), energy)
        and all(_close(sum(value * value for value in normal), 1.0) for normal in parsed_normals)
        and row.get("quadrature_identity") == f"triangle-gauss-order-{order}"
        and _digest(row.get("boundary_mesh_revision_sha256"))
        and str(row.get("boundary_mesh_owner") or "").startswith("mesh-owner:")
        and _replay_copies(row, fields)
        and _result(row)
    )


def validate_source_v60_identity(identities: list[object]) -> dict[str, bool]:
    rows = [row for row in identities if isinstance(row, Mapping)]
    if not rows:
        return {}
    checks = validate_source_v59_identity(identities)
    aca_rows = [row[ACA] for row in rows if ACA in row]
    matrix_rows = [row[BEM_MATRIX] for row in rows if BEM_MATRIX in row]
    if aca_rows:
        checks["source_v60_aca_pivot_residual_rank_cluster_matrix_owner"] = (
            len(aca_rows) == len(rows)
            and all(isinstance(item, Mapping) and _aca_ok(item) for item in aca_rows)
        )
    if matrix_rows:
        checks["source_v60_bem_matrix_symmetry_energy_normal_quadrature_owner"] = (
            len(matrix_rows) == len(rows)
            and all(
                isinstance(item, Mapping) and _bem_matrix_ok(item)
                for item in matrix_rows
            )
        )
    return checks
