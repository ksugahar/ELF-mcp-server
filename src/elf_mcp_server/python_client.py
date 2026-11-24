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
import subprocess
from typing import Any, Iterable, Mapping

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

    def parse_summary(self) -> dict[str, Any]:
        """Extract a compact structured summary from common ELF output files (.flx, .frc, .mag, .log)."""
        flx_rows = self.parse_numeric_table(".flx")
        frc_rows = self.parse_numeric_table(".frc")
        mag_rows = self.parse_numeric_table(".mag")
        log_text = self.read_output(".log") or ""
        converged = (
            "converg" in log_text.lower() and "not converg" not in log_text.lower()
        ) if log_text else None
        return {
            "ok": self.ok,
            "case_name": self.case_name,
            "flx_rows": len(flx_rows),
            "flx_last": flx_rows[-1] if flx_rows else None,
            "frc_rows": len(frc_rows),
            "frc_last": frc_rows[-1] if frc_rows else None,
            "mag_rows": len(mag_rows),
            "converged": converged,
        }


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
            case_directory=str(work_dir),
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
        confirm_product_execution: bool = False,
    ) -> ElfRunResult:
        """Execute an existing ``<case_name>.mai`` / ``.meg`` in ``work_dir``."""
        resolved_dir = Path(work_dir).resolve()
        chosen_solver = (solver or self.solver).strip().upper()
        raw = run_product_case(
            case_directory=str(resolved_dir),
            case_name=case_name,
            solver=chosen_solver,
            product_home=self.product_home,
            timeout_seconds=self.timeout_s if timeout_s is None else timeout_s,
            confirm_product_execution=confirm_product_execution,
        )
        outputs = tuple(
            item["name"]
            for item in raw.get("fresh_outputs", [])
            if isinstance(item, Mapping) and "name" in item
        )
        stage = raw.get("stage") or {}
        worker = stage.get("worker_result") or {}
        error = None
        if not raw["ok"]:
            reasons = [raw["status"]]
            if raw.get("required_confirmation"):
                reasons.append(raw["required_confirmation"])
            reasons.extend(raw.get("blocking_reasons", ()))
            if stage.get("timed_out"):
                reasons.append("worker timed out")
            if stage.get("exit_code") not in (None, 0):
                reasons.append(f"worker exit code {stage['exit_code']}")
            if worker.get("error_type"):
                reasons.append(worker["error_type"])
            if raw.get("inputs_unchanged") is False:
                reasons.append("case inputs changed")
            if stage and not outputs:
                reasons.append("no fresh outputs")
            error = "; ".join(reasons)
        return ElfRunResult(
            ok=bool(raw.get("ok")),
            solver=chosen_solver,
            case_name=case_name,
            work_dir=resolved_dir,
            returncode=stage.get("exit_code"),
            elapsed_s=stage.get("elapsed_seconds"),
            outputs=outputs,
            raw=raw,
            error=error,
        )

    def compile_iemesh(
        self,
        mei_text: str,
        work_dir: str | Path,
        case_name: str = "case",
        *,
        timeout_s: int | None = None,
    ) -> dict[str, Any]:
        """Write ``mei_text`` to ``<case_name>.mei`` and compile ``<case_name>.meg`` via ``mesh750.exe``."""
        resolved_dir = Path(work_dir).resolve()
        resolved_dir.mkdir(parents=True, exist_ok=True)
        mei_path = resolved_dir / f"{case_name}.mei"
        mei_path.write_text(mei_text, encoding="utf-8")

        discovery = discover_product(self.product_home, include_paths=True)
        home_str = discovery.get("home")
        if not discovery.get("found") or not home_str:
            return {
                "ok": False,
                "meg_path": None,
                "returncode": None,
                "stdout": "",
                "stderr": "",
                "error": "ELF product home not found; cannot locate bin/mesh750.exe.",
            }
        exe_path = Path(home_str) / "bin" / "mesh750.exe"
        if not exe_path.is_file():
            return {
                "ok": False,
                "meg_path": None,
                "returncode": None,
                "stdout": "",
                "stderr": "",
                "error": f"IEmesh executable not found: {exe_path}",
            }

        proc = subprocess.run(
            [str(exe_path), mei_path.name],
            cwd=str(resolved_dir),
            capture_output=True,
            text=True,
            timeout=self.timeout_s if timeout_s is None else timeout_s,
            check=False,
        )
        meg_path = resolved_dir / f"{case_name}.meg"
        ok = proc.returncode == 0 and meg_path.is_file()
        return {
            "ok": ok,
            "meg_path": meg_path if meg_path.is_file() else None,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "error": None if ok else f"mesh750.exe failed (returncode={proc.returncode})",
        }

    def run_mai(
        self,
        mai_text: str,
        work_dir: str | Path,
        case_name: str = "case",
        *,
        meg_path: str | Path | None = None,
        solver: str | None = None,
        timeout_s: int | None = None,
        confirm_product_execution: bool = False,
    ) -> ElfRunResult:
        """Write the .mai and copy the optional .meg into the work directory.

        These writes occur even when confirmation is false. Only solver execution
        requires confirmation.
        """
        resolved_dir = Path(work_dir).resolve()
        resolved_dir.mkdir(parents=True, exist_ok=True)
        (resolved_dir / f"{case_name}.mai").write_text(mai_text, encoding="utf-8", newline="\n")
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
            confirm_product_execution=confirm_product_execution,
        )

    def sweep(
        self,
        template_mai: str,
        params_list: Iterable[Mapping[str, Any]],
        base_dir: str | Path,
        *,
        meg_path: str | Path | None = None,
        solver: str | None = None,
        timeout_s: int | None = None,
        confirm_product_execution: bool = False,
        case_prefix: str = "case",
    ) -> list[dict[str, Any]]:
        """Format and prepare one case per parameter mapping.

        Each .mai is written and each supplied .meg is copied even when confirmation
        is false. Only solver execution requires confirmation.
        """
        params_list = list(params_list)
        if any("case_name" in params for params in params_list):
            raise ValueError("case_name is generated from case_prefix and cannot be supplied in sweep params")
        root = Path(base_dir).resolve()
        root.mkdir(parents=True, exist_ok=True)
        results: list[dict[str, Any]] = []
        for idx, params in enumerate(params_list):
            case_name = f"{case_prefix}_{idx:03d}"
            case_dir = root / case_name
            mai_text = template_mai.format(case_name=case_name, **params)
            run_res = self.run_mai(
                mai_text,
                case_dir,
                case_name=case_name,
                meg_path=meg_path,
                solver=solver,
                timeout_s=timeout_s,
                confirm_product_execution=confirm_product_execution,
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

    @staticmethod
    def build_axial_motor_mai(
        *,
        mesh_file: str = "axial_motor.meg",
        voltage_v: float = 48.0,
        rpm: float = 1500.0,
        pole_pairs: int = 4,
        steps: int = 36,
        room_runner: bool = True,
    ) -> str:
        """Build a starter .mai deck for an axial-flux motor with voltage, RPM, and time-stepping."""
        elec_freq_hz = (rpm / 60.0) * pole_pairs
        dt_s = (60.0 / rpm) / steps if rpm > 0 and steps > 0 else 1e-4
        rr_note = "  ! Room-Runner enabled: reuse matrix/LU across periodic steps\n" if room_runner else ""
        return (
            "USE  MAGIC  3.50\n"
            "PRE\n"
            f"  FILE  MESH  {mesh_file}\n"
            f"  ! Axial-flux motor: V={voltage_v} V, N={rpm} rpm, p={pole_pairs}, f_e={elec_freq_hz:.2f} Hz\n"
            f"  VOLT  1  {voltage_v}\n"
            f"{rr_note}"
            "END\n"
            f"SOL  STEP  {steps}  {dt_s:.6e}\n"
            "END\n"
        )

    def run_mei_and_mai(
        self,
        mei_text: str,
        mai_text: str,
        work_dir: str | Path,
        case_name: str = "case",
        *,
        solver: str | None = None,
        timeout_s: int | None = None,
    ) -> ElfRunResult:
        """End-to-end: compile ``mei_text`` -> ``.meg`` via IEmesh, then run ``mai_text``."""
        mesh_res = self.compile_iemesh(
            mei_text,
            work_dir,
            case_name=case_name,
            timeout_s=timeout_s,
        )
        if not mesh_res["ok"]:
            return ElfRunResult(
                ok=False,
                solver=(solver or self.solver).strip().upper(),
                case_name=case_name,
                work_dir=Path(work_dir).resolve(),
                returncode=mesh_res["returncode"],
                elapsed_s=None,
                raw=mesh_res,
                error=mesh_res["error"],
            )
        return self.run_mai(
            mai_text,
            work_dir,
            case_name=case_name,
            meg_path=mesh_res["meg_path"],
            solver=solver,
            timeout_s=timeout_s,
        )

    @staticmethod
    def mei_box(
        x0: float,
        x1: float,
        y0: float,
        y1: float,
        z0: float,
        z1: float,
        *,
        nx: int = 4,
        ny: int = 4,
        nz: int = 4,
        mat: int = 1,
    ) -> str:
        """Generate a .mei box-mesh snippet."""
        return f"BOX  {x0}  {x1}  {y0}  {y1}  {z0}  {z1}  {nx}  {ny}  {nz}  {mat}\n"

    @staticmethod
    def mei_cylinder(
        r: float,
        z0: float,
        z1: float,
        *,
        nr: int = 4,
        ntheta: int = 16,
        nz: int = 4,
        mat: int = 1,
    ) -> str:
        """Generate a .mei cylinder-mesh snippet."""
        return f"CYL  0.0  0.0  {r}  {z0}  {z1}  {nr}  {ntheta}  {nz}  {mat}\n"

    @staticmethod
    def mei_ring(
        r_in: float,
        r_out: float,
        z0: float,
        z1: float,
        *,
        nr: int = 4,
        ntheta: int = 16,
        nz: int = 4,
        mat: int = 1,
    ) -> str:
        """Generate a .mei annular/ring-mesh snippet (useful for axial-flux motor cores/magnets)."""
        return f"RING  0.0  0.0  {r_in}  {r_out}  {z0}  {z1}  {nr}  {ntheta}  {nz}  {mat}\n"

    @staticmethod
    def build_mai(
        *,
        mesh_file: str = "case.meg",
        solver: str = "MAGIC",
        materials: Sequence[str] = (),
        currents: Mapping[int, float] | None = None,
        sol_command: str = "FIXA",
        outputs: Sequence[str] = ("FLUM", "FORC"),
    ) -> str:
        """Build a clean .mai input deck from structured Python arguments."""
        lines = [f"USE  {solver.strip().upper()}  3.50", "PRE", f"  FILE  MESH  {mesh_file}"]
        lines.extend(f"  {m}" for m in materials)
        if currents:
            for idx, amp in currents.items():
                lines.append(f"  CURR  {idx}  {amp}")
        lines.extend(["END", f"SOL  {sol_command}"])
        lines.extend(f"  {out}" for out in outputs)
        lines.append("END")
        return "\n".join(lines) + "\n"


class IEmeshBuilder:
    """Composable Python API for building .mei mesh scripts and compiling .meg files."""

    def __init__(self, title: str = "model") -> None:
        self.title = title
        self._lines: list[str] = [f"! {title}"]

    def box(
        self,
        x0: float,
        x1: float,
        y0: float,
        y1: float,
        z0: float,
        z1: float,
        *,
        nx: int = 4,
        ny: int = 4,
        nz: int = 4,
        mat: int = 1,
    ) -> "IEmeshBuilder":
        self._lines.append(ElfClient.mei_box(x0, x1, y0, y1, z0, z1, nx=nx, ny=ny, nz=nz, mat=mat).rstrip("\n"))
        return self

    def cylinder(
        self,
        r: float,
        z0: float,
        z1: float,
        *,
        nr: int = 4,
        ntheta: int = 16,
        nz: int = 4,
        mat: int = 1,
    ) -> "IEmeshBuilder":
        self._lines.append(ElfClient.mei_cylinder(r, z0, z1, nr=nr, ntheta=ntheta, nz=nz, mat=mat).rstrip("\n"))
        return self

    def ring(
        self,
        r_in: float,
        r_out: float,
        z0: float,
        z1: float,
        *,
        nr: int = 4,
        ntheta: int = 16,
        nz: int = 4,
        mat: int = 1,
    ) -> "IEmeshBuilder":
        self._lines.append(ElfClient.mei_ring(r_in, r_out, z0, z1, nr=nr, ntheta=ntheta, nz=nz, mat=mat).rstrip("\n"))
        return self

    def rotate(self, angle_deg: float, *, axis: str = "z") -> "IEmeshBuilder":
        self._lines.append(f"ROT  {axis.strip().upper()}  {angle_deg}")
        return self

    def translate(self, dx: float = 0.0, dy: float = 0.0, dz: float = 0.0) -> "IEmeshBuilder":
        self._lines.append(f"MOV  {dx}  {dy}  {dz}")
        return self

    def raw(self, line: str) -> "IEmeshBuilder":
        self._lines.append(line.rstrip("\n"))
        return self

    def build(self) -> str:
        """Render the accumulated .mei script."""
        return "\n".join(self._lines) + "\n"

    def compile(
        self,
        client: ElfClient,
        work_dir: str | Path,
        case_name: str = "case",
        *,
        timeout_s: int | None = None,
    ) -> dict[str, Any]:
        """Compile this .mei script to .meg using ``client.compile_iemesh``."""
        return client.compile_iemesh(self.build(), work_dir, case_name=case_name, timeout_s=timeout_s)


class MaiBuilder:
    """Composable Python API for building .mai solver input decks."""

    def __init__(self, solver: str = "MAGIC", version: str = "3.50") -> None:
        self.solver = solver.strip().upper()
        self.version = version
        self._pre_lines: list[str] = []
        self._sol_header: str = "SOL  FIXA"
        self._sol_lines: list[str] = []

    def mesh(self, mesh_file: str) -> "MaiBuilder":
        self._pre_lines.append(f"  FILE  MESH  {mesh_file}")
        return self

    def material(self, mat_id: int, *, mu_r: float = 1000.0) -> "MaiBuilder":
        self._pre_lines.append(f"  MATE  {mat_id}  {mu_r}")
        return self

    def current(self, coil_id: int, amp: float) -> "MaiBuilder":
        self._pre_lines.append(f"  CURR  {coil_id}  {amp}")
        return self

    def voltage(self, coil_id: int, volt: float) -> "MaiBuilder":
        self._pre_lines.append(f"  VOLT  {coil_id}  {volt}")
        return self

    def pre_raw(self, line: str) -> "MaiBuilder":
        self._pre_lines.append(f"  {line.strip()}")
        return self

    def sol(self, command: str = "FIXA") -> "MaiBuilder":
        self._sol_header = f"SOL  {command.strip()}"
        return self

    def sol_step(self, steps: int, dt_s: float) -> "MaiBuilder":
        self._sol_header = f"SOL  STEP  {steps}  {dt_s:.6e}"
        return self

    def output(self, *names: str) -> "MaiBuilder":
        for name in names:
            self._sol_lines.append(f"  {name.strip()}")
        return self

    def build(self) -> str:
        """Render the complete .mai deck."""
        lines = [f"USE  {self.solver}  {self.version}", "PRE", *self._pre_lines, "END", self._sol_header, *self._sol_lines, "END"]
        return "\n".join(lines) + "\n"


def suggest_mei_mai_example(goal: str) -> dict[str, str]:
    """Return a ready-to-run (.mei, .mai) example pair tailored to a natural-language goal."""
    text = goal.lower()
    if any(k in text for k in ("hysteresis", "ヒステリシス")):
        mei = IEmeshBuilder("hysteresis_motor").ring(0.015, 0.04, 0.0, 0.01, nr=4, ntheta=24, nz=2, mat=1).build()
        mai = MaiBuilder("MAGIC").mesh("hysteresis_motor.meg").sol_step(36, 1e-4).output("FLUM", "FORC").build()
        return {
            "kind": "hysteresis_motor",
            "title": "Hysteresis motor (vector hysteresis / time-stepping)",
            "mei_text": mei,
            "mai_text": mai,
            "notes": "Combine with hysteresis material table and Room-Runner time-stepping.",
        }
    if any(k in text for k in ("sensor", "hall", "磁気センサ", "センサー", "ホール")):
        mei = IEmeshBuilder("magnetic_sensor").box(-0.01, 0.01, -0.01, 0.01, 0.0, 0.005, mat=1).build()
        mai = MaiBuilder("MAGIC").mesh("magnetic_sensor.meg").material(1, mu_r=500.0).sol("FIXA").output("FIEL").build()
        return {
            "kind": "magnetic_sensor",
            "title": "Magnetic sensor / Hall probe field evaluation (MAGIC)",
            "mei_text": mei,
            "mai_text": mai,
            "notes": "Evaluate B-field at probe points with SOL FIXA + FIEL.",
        }
    if any(k in text for k in ("actuator", "solenoid", "アクチュエータ", "ソレノイド", "電磁石")):
        mei = IEmeshBuilder("actuator").cylinder(0.02, 0.0, 0.03, nr=4, ntheta=16, nz=4, mat=1).build()
        mai = MaiBuilder("MAGIC").mesh("actuator.meg").material(1, mu_r=1000.0).current(1, 500.0).sol("FIXB").output("FORC", "FLUM").build()
        return {
            "kind": "actuator",
            "title": "Actuator / solenoid force & flux (MAGIC)",
            "mei_text": mei,
            "mai_text": mai,
            "notes": "Nonlinear force/flux evaluation with SOL FIXB + FORC.",
        }
    if any(k in text for k in ("axial", "アキシャル", "motor", "モータ", "rpm", "回転")):
        mei = (
            IEmeshBuilder("axial_motor")
            .ring(0.02, 0.05, 0.0, 0.01, nr=4, ntheta=24, nz=2, mat=1)
            .ring(0.02, 0.05, 0.012, 0.022, nr=4, ntheta=24, nz=2, mat=2)
            .build()
        )
        mai = ElfClient.build_axial_motor_mai(
            mesh_file="axial_motor.meg",
            voltage_v=48.0,
            rpm=1500.0,
            pole_pairs=4,
            steps=36,
            room_runner=True,
        )
        return {
            "kind": "axial_motor",
            "title": "Axial-flux motor (voltage + RPM + Room-Runner)",
            "mei_text": mei,
            "mai_text": mai,
            "notes": "Compile .mei -> .meg with ElfClient.compile_iemesh, then run with ElfClient.run_mai.",
        }
    if any(k in text for k in ("beam", "顕微鏡", "電子", "粒子", "microscope", "electron", "lens")):
        mei = IEmeshBuilder("electron_lens").ring(0.005, 0.02, 0.0, 0.01, nr=4, ntheta=24, nz=2, mat=1).build()
        mai = (
            "USE  BEAM  3.50\n"
            "PRE\n"
            "  FILE  MAGIC  lens_M\n"
            "  FILE  ELFIN  lens_E\n"
            "  CHAR  1  -1.602E-19\n"
            "  MASS  1  9.109E-31\n"
            "  VOLB  1  10000.0\n"
            "END\n"
            "SOL  BEAM\n"
            "END\n"
        )
        return {
            "kind": "beam",
            "title": "Electron microscope / charged-particle tracking (BEAM)",
            "mei_text": mei,
            "mai_text": mai,
            "notes": "Import MAGIC magnetic field and optional ELFIN electric field; signed CHAR=-1.602E-19 for electrons.",
        }
    if any(k in text for k in ("elfin", "静電", "electrostatic", "volt")):
        mei = IEmeshBuilder("electrostatic_gap").box(-0.02, 0.02, -0.02, 0.02, 0.0, 0.01, mat=1).build()
        mai = MaiBuilder("ELFIN").mesh("electrostatic_gap.meg").voltage(1, 1000.0).sol("FIXA").output("FIEL").build()
        return {
            "kind": "electrostatic",
            "title": "Electrostatic field (ELFIN)",
            "mei_text": mei,
            "mai_text": mai,
            "notes": "Run with ElfClient(solver='ELFIN').run_mei_and_mai(...).",
        }
    mei = IEmeshBuilder("magnetostatic_box").box(-0.05, 0.05, -0.05, 0.05, -0.05, 0.05, mat=1).build()
    mai = MaiBuilder("MAGIC").mesh("magnetostatic_box.meg").material(1, mu_r=1000.0).current(1, 100.0).sol("FIXA").output("FLUM", "FORC").build()
    return {
        "kind": "magnetostatic",
        "title": "Magnetostatic benchmark (MAGIC)",
        "mei_text": mei,
        "mai_text": mai,
        "notes": "Run with ElfClient(solver='MAGIC').run_mei_and_mai(...).",
    }
