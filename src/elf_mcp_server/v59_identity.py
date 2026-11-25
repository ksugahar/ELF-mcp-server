"""Public-safe near-singular BEM and conductor-current replay checks for v59."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence


NEAR = "bem_nearsingular_distance_quadrature_order_tolerance_mesh_owner_identity"
CURRENT = "conductor_current_incidence_divergence_continuity_source_owner_identity"


def _number(value: object, *, positive: bool = False) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)) and (not positive or float(value) > 0.0)


def _close(left: object, right: object) -> bool:
    return _number(left) and _number(right) and math.isclose(float(left), float(right), rel_tol=1.0e-9, abs_tol=1.0e-10)


def _series(value: object) -> list[float] | None:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or not value or not all(_number(item) for item in value):
        return None
    return [float(item) for item in value]


def _generations(row: Mapping[str, object], *fields: str) -> bool:
    generation = str(row.get("generation") or "")
    return bool(generation) and all(row.get(field) == generation for field in fields)


def _result(row: Mapping[str, object]) -> bool:
    digest = str(row.get("result_sha256") or "").lower()
    return len(digest) == 64 and all(character in "0123456789abcdef" for character in digest) and row.get("accepted_result_sha256") == digest


def _near_ok(row: Mapping[str, object]) -> bool:
    distance, diameter, ratio = row.get("source_target_distance_m"), row.get("panel_diameter_m"), row.get("distance_ratio")
    order, required = row.get("quadrature_order"), row.get("required_quadrature_order")
    error, tolerance = row.get("estimated_relative_error"), row.get("relative_tolerance")
    if not all(_number(value, positive=True) for value in (distance, diameter, ratio, error, tolerance)) or not all(isinstance(value, int) and not isinstance(value, bool) for value in (order, required)):
        return False
    expected_required = math.ceil(4.0 + 2.0 * max(0.0, -math.log10(float(ratio))))
    names = ("source_target_distance_m", "panel_diameter_m", "distance_ratio", "quadrature_order", "required_quadrature_order", "estimated_relative_error", "relative_tolerance", "near_singular_class", "mesh_revision", "mesh_owner")
    return (
        _generations(row, "distance_generation", "quadrature_generation", "tolerance_generation", "mesh_generation", "owner_generation", "result_generation")
        and _close(ratio, float(distance) / float(diameter)) and float(ratio) < 0.25
        and required == expected_required and order >= required and float(error) <= float(tolerance)
        and row.get("near_singular_class") == "near"
        and str(row.get("mesh_revision") or "").startswith("mesh:") and str(row.get("mesh_owner") or "").startswith("mesh-owner:")
        and all(row.get("replayed_" + name) == row.get(name) for name in names) and _result(row)
    )


def _current_ok(row: Mapping[str, object]) -> bool:
    matrix = row.get("incidence_matrix")
    currents = _series(row.get("branch_currents_a"))
    divergence = _series(row.get("nodal_divergence_a"))
    sources = _series(row.get("source_injection_a"))
    residual = _series(row.get("continuity_residual_a"))
    if not isinstance(matrix, Sequence) or isinstance(matrix, (str, bytes)) or currents is None or divergence is None or sources is None or residual is None:
        return False
    rows = [_series(item) for item in matrix]
    if not rows or any(item is None or len(item) != len(currents) for item in rows) or not (len(rows) == len(divergence) == len(sources) == len(residual)):
        return False
    incidence = [item for item in rows if item is not None]
    expected_divergence = [sum(item[j] * currents[j] for j in range(len(currents))) for item in incidence]
    expected_residual = [expected_divergence[i] - sources[i] for i in range(len(sources))]
    names = ("incidence_matrix", "branch_currents_a", "nodal_divergence_a", "source_injection_a", "continuity_residual_a", "source_revision", "topology_owner")
    return (
        _generations(row, "incidence_generation", "current_generation", "divergence_generation", "continuity_generation", "source_generation", "owner_generation", "result_generation")
        and all(_close(sum(item[j] for item in incidence), 0.0) for j in range(len(currents)))
        and all(_close(actual, expected) for actual, expected in zip(divergence, expected_divergence))
        and all(_close(actual, expected) for actual, expected in zip(residual, expected_residual))
        and all(_close(value, 0.0) for value in residual) and _close(sum(sources), 0.0)
        and str(row.get("source_revision") or "").startswith("source:") and str(row.get("topology_owner") or "").startswith("topology-owner:")
        and all(row.get("replayed_" + name) == row.get(name) for name in names) and _result(row)
    )


def validate_source_v59_identity(identities: list[object]) -> dict[str, bool]:
    rows = [row for row in identities if isinstance(row, Mapping)]
    if not rows:
        return {}
    checks: dict[str, bool] = {}
    near_rows = [row[NEAR] for row in rows if NEAR in row]
    current_rows = [row[CURRENT] for row in rows if CURRENT in row]
    if near_rows:
        checks["source_v59_bem_nearsingular_quadrature_tolerance_mesh_owner"] = len(near_rows) == len(rows) and all(isinstance(item, Mapping) and _near_ok(item) for item in near_rows)
    if current_rows:
        checks["source_v59_conductor_current_incidence_continuity_owner"] = len(current_rows) == len(rows) and all(isinstance(item, Mapping) and _current_ok(item) for item in current_rows)
    return checks
