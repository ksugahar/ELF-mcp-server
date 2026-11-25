"""Public-safe complex-harmonic and sector-replication replay checks."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence


MAO_HARMONIC = "mao_complexharmonic_realimag_phase_frequency_component_body_owner_identity"
SECTOR = "bem_sectorreplication_transform_magnetization_bodymap_result_owner_identity"


def _number(value: object, *, positive: bool = False) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    number = float(value)
    return math.isfinite(number) and (not positive or number > 0.0)


def _close(left: object, right: object) -> bool:
    return _number(left) and _number(right) and math.isclose(
        float(left), float(right), rel_tol=1.0e-9, abs_tol=1.0e-12
    )


def _vector(value: object, *, length: int | None = None) -> list[float]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or not value
        or not all(_number(item) for item in value)
        or (length is not None and len(value) != length)
    ):
        return []
    return [float(item) for item in value]


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


def _harmonic_ok(row: Mapping[str, object]) -> bool:
    order = row.get("component_order")
    real = row.get("real_components_t")
    imaginary = row.get("imaginary_components_t")
    amplitude = _vector(row.get("amplitude_components_t"))
    phase = _vector(row.get("phase_components_deg"))
    if (
        not _number(row.get("frequency_hz"), positive=True)
        or row.get("phase_convention") != "real_part_of_phasor_exp_plus_j_omega_t"
        or not isinstance(order, Sequence)
        or isinstance(order, (str, bytes))
        or not order
        or len(set(order)) != len(order)
        or not all(isinstance(name, str) and name in {"Bx", "By", "Bz", "Hx", "Hy", "Hz"} for name in order)
        or not isinstance(real, Mapping)
        or set(real) != set(order)
        or not isinstance(imaginary, Mapping)
        or set(imaginary) != set(order)
        or not all(_number(value) for value in real.values())
        or not all(_number(value) for value in imaginary.values())
        or len(amplitude) != len(order)
        or len(phase) != len(order)
    ):
        return False
    expected_amplitude = [math.hypot(float(real[name]), float(imaginary[name])) for name in order]
    expected_phase = [math.degrees(math.atan2(float(imaginary[name]), float(real[name]))) for name in order]
    fields = (
        "frequency_hz", "phase_convention", "component_order", "real_components_t",
        "imaginary_components_t", "amplitude_components_t", "phase_components_deg",
        "body_identity", "result_owner",
    )
    return (
        _generations(
            row, "harmonic_generation", "complex_generation", "phase_generation",
            "frequency_generation", "component_generation", "body_generation",
            "owner_generation", "result_generation",
        )
        and all(_close(actual, expected) for actual, expected in zip(amplitude, expected_amplitude))
        and all(_close(actual, expected) for actual, expected in zip(phase, expected_phase))
        and str(row.get("body_identity") or "").startswith("body:")
        and str(row.get("result_owner") or "").startswith("result:")
        and _replay_copies(row, fields)
        and _result(row)
    )


def _sector_ok(row: Mapping[str, object]) -> bool:
    count = row.get("sector_count")
    angles = _vector(row.get("replication_transform_angles_deg"))
    base = _vector(row.get("base_magnetization_vector"), length=3)
    replicated = row.get("replicated_magnetization_vectors")
    body_map = row.get("replicated_body_map")
    if (
        not isinstance(count, int)
        or isinstance(count, bool)
        or count < 2
        or not _number(row.get("base_sector_angle_deg"), positive=True)
        or len(angles) != count
        or len(base) != 3
        or not _close(sum(value * value for value in base), 1.0)
        or not isinstance(replicated, Sequence)
        or isinstance(replicated, (str, bytes))
        or len(replicated) != count
        or not isinstance(body_map, Mapping)
        or set(body_map) != {str(index) for index in range(count)}
        or len(set(body_map.values())) != count
        or not all(isinstance(owner, str) and owner.startswith("body:") for owner in body_map.values())
    ):
        return False
    step = 360.0 / count
    expected_angles = [step * index for index in range(count)]
    if not _close(row.get("base_sector_angle_deg"), step) or not all(
        _close(actual, expected) for actual, expected in zip(angles, expected_angles)
    ):
        return False
    vectors = [_vector(vector, length=3) for vector in replicated]
    if not all(vectors):
        return False
    expected_vectors = [
        [
            math.cos(math.radians(angle)) * base[0] - math.sin(math.radians(angle)) * base[1],
            math.sin(math.radians(angle)) * base[0] + math.cos(math.radians(angle)) * base[1],
            base[2],
        ]
        for angle in expected_angles
    ]
    fields = (
        "sector_count", "base_sector_angle_deg", "replication_transform_angles_deg",
        "base_magnetization_vector", "replicated_magnetization_vectors", "replicated_body_map",
        "source_sector_owner", "result_generation_id", "result_owner",
    )
    return (
        _generations(
            row, "sector_generation", "transform_generation", "magnetization_generation",
            "bodymap_generation", "result_generation", "owner_generation",
        )
        and all(
            all(_close(actual, expected) for actual, expected in zip(vector, expected))
            for vector, expected in zip(vectors, expected_vectors)
        )
        and str(row.get("source_sector_owner") or "").startswith("body:")
        and str(row.get("result_generation_id") or "").startswith("result-generation:")
        and str(row.get("result_owner") or "").startswith("result:")
        and _replay_copies(row, fields)
        and _result(row)
    )


def validate_source_v62_identity(identities: list[object]) -> dict[str, bool]:
    rows = [row for row in identities if isinstance(row, Mapping)]
    if not rows:
        return {}
    checks: dict[str, bool] = {}
    harmonic_rows = [row[MAO_HARMONIC] for row in rows if MAO_HARMONIC in row]
    sector_rows = [row[SECTOR] for row in rows if SECTOR in row]
    if harmonic_rows:
        checks["source_v62_mao_complex_harmonic_component_phase_body_owner"] = (
            len(harmonic_rows) == len(rows)
            and all(isinstance(item, Mapping) and _harmonic_ok(item) for item in harmonic_rows)
        )
    if sector_rows:
        checks["source_v62_bem_sector_transform_magnetization_bodymap_owner"] = (
            len(sector_rows) == len(rows)
            and all(isinstance(item, Mapping) and _sector_ok(item) for item in sector_rows)
        )
    return checks
