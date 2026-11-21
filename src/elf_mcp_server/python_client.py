"""High-level Python client for driving a user-local ELF/MAGIC installation.

Builds on ``product_runner`` (isolated ctypes worker) to provide:
- ``doctor()``: environment and DLL diagnostics
- ``ElfClient``: ergonomic case execution, ``.mai`` text execution,
  parametric sweeps, and output file reading/parsing.

This module contains no product binaries, vendor wrappers, or licenses.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import shutil
import struct
from typing import Any, Mapping, Sequence

from .product_runner import check_product_case, discover_product, run_product_case


def doctor(product_home: str = "") -> dict[str, Any]:
    """Diagnose local ELF/MAGIC product installation and Python compatibility."""
    discovery = discover_product(product_home, include_paths=True)
    pointer_bits = struct.calcsize("P") * 8
    issues: list[str] = []

    if pointer_bits != 64:
        issues.append(f"64-bit Python is recommended for ELF600 DLLs (detected {pointer_bits}-bit).")
    if not discovery.get("found"):
        issues.append(
            "ELF product home not found. Set ELF_PRODUCT_HOME, ELF600_HOME, or ELF_HOME "
            "to the directory containing bin/."
        )
    solvers = discovery.get("solvers", {})
    for solver_name in ("MAGIC", "ELFIN"):
        info = solvers.get(solver_name, {})
        if not info.get("available"):
            issues.append(f"{solver_name} DLL not found under product bin/.")

    return {
        "ok": len(issues) == 0,
        "python_bits": pointer_bits,
        "discovery": discovery,
        "issues": issues,
    }


@dataclass(frozen=True)
class ElfRunResult:
    """Structured result from an ``ElfClient`` solver run."""

    ok: bool
    solver: str
    case_name: str
    work_dir: Path
    returncode: int | None
    elapsed_s: float | None
    outputs: tuple[str, ...] = field(default_factory=tuple)
    raw: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def output_path(self, suffix: str) -> Path | None:
        """Return the path to a generated output file matching ``suffix`` (e.g. '.flx')."""
        norm = suffix if suffix.startswith(".") else f".{suffix}"
        norm_lower = norm.lower()
        for name in self.outputs:
            if name.lower().endswith(norm_lower):
                candidate = self.work_dir / name
                if candidate.is_file():
                    return candidate
        fallback = self.work_dir / f"{self.case_name}{norm}"
        return fallback if fallback.is_file() else None

    def read_output(self, suffix: str, encoding: str = "utf-8") -> str | None:
        """Read a generated text output file, returning None if not present."""
        path = self.output_path(suffix)
        if path is None:
            return None
        return path.read_text(encoding=encoding, errors="replace")

    def parse_numeric_table(self, suffix: str) -> list[list[float]]:
        """Parse whitespace-separated numeric rows from an output file, skipping non-numeric lines."""
        text = self.read_output(suffix)
        if text is None:
            return []
        rows: list[list[float]] = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith(("#", "!", "*")):
                continue
            parts = stripped.split()
            try:
                rows.append([float(p) for p in parts])
            except ValueError:
                continue
        return rows


class ElfClient:
    """High-level Python client for running ELF/MAGIC cases and parametric sweeps."""

    def __init__(
        self,
        product_home: str = "",
        solver: str = "MAGIC",
        timeout_s: int = 300,
    ) -> None:
        self.product_home = product_home
        self.solver = solver
        self.timeout_s = timeout_s

    def doctor(self) -> dict[str, Any]:
        """Run environment diagnostics for this client's configured ``product_home``."""
        return doctor(self.product_home)

    def check_case(
        self,
        work_dir: str | Path,
        case_name: str,
        *,
        solver: str | None = None,
    ) -> dict[str, Any]:
        """Validate inputs and solver availability for an existing case directory."""
        return check_product_case(
            case_dir=str(work_dir),
            case_name=case_name,
            solver=solver or self.solver,
            product_home=self.product_home,
        )

    def run_case(
        self,
        work_dir: str | Path,
        case_name: str,
        *,
        solver: str | None = None,
        timeout_s: int | None = None,
    ) -> ElfRunResult:
        """Execute an existing ``<case_name>.mai`` / ``.meg`` in ``work_dir``."""
        resolved_dir = Path(work_dir).resolve()
        chosen_solver = (solver or self.solver).strip().upper()
        raw = run_product_case(
            case_dir=str(resolved_dir),
            case_name=case_name,
            solver=chosen_solver,
            product_home=self.product_home,
            timeout_s=self.timeout_s if timeout_s is None else timeout_s,
        )
        outputs = tuple(
            item["name"]
            for item in raw.get("fresh_outputs", [])
            if isinstance(item, Mapping) and "name" in item
        )
        return ElfRunResult(
            ok=bool(raw.get("ok")),
            solver=chosen_solver,
            case_name=case_name,
            work_dir=resolved_dir,
            returncode=raw.get("returncode"),
            elapsed_s=raw.get("elapsed_s"),
            outputs=outputs,
            raw=raw,
            error=raw.get("error"),
        )

    def run_mai(
        self,
        mai_text: str,
        work_dir: str | Path,
        case_name: str = "case",
        *,
        meg_path: str | Path | None = None,
        solver: str | None = None,
        timeout_s: int | None = None,
    ) -> ElfRunResult:
        """Write ``mai_text`` (and optional ``meg_path``) into ``work_dir`` and run the solver."""
        resolved_dir = Path(work_dir).resolve()
        resolved_dir.mkdir(parents=True, exist_ok=True)
        (resolved_dir / f"{case_name}.mai").write_text(mai_text, encoding="utf-8")
        if meg_path is not None:
            src_meg = Path(meg_path).resolve(strict=True)
            dst_meg = resolved_dir / f"{case_name}.meg"
            if src_meg != dst_meg:
                shutil.copy2(src_meg, dst_meg)
        return self.run_case(
            resolved_dir,
            case_name,
            solver=solver,
            timeout_s=timeout_s,
        )

    def sweep(
        self,
        template_mai: str,
        params_list: Sequence[Mapping[str, Any]],
        base_dir: str | Path,
        *,
        meg_path: str | Path | None = None,
        solver: str | None = None,
        timeout_s: int | None = None,
        case_prefix: str = "case",
    ) -> list[dict[str, Any]]:
        """Run a parametric sweep by formatting ``template_mai`` for each parameter dict."""
        root = Path(base_dir).resolve()
        root.mkdir(parents=True, exist_ok=True)
        results: list[dict[str, Any]] = []
        for idx, params in enumerate(params_list):
            case_name = f"{case_prefix}_{idx:03d}"
            case_dir = root / case_name
            mai_text = template_mai.format(**params)
            run_res = self.run_mai(
                mai_text,
                case_dir,
                case_name=case_name,
                meg_path=meg_path,
                solver=solver,
                timeout_s=timeout_s,
            )
            results.append(
                {
                    "index": idx,
                    "case_name": case_name,
                    "params": dict(params),
                    "result": run_res,
                }
            )
        return results
