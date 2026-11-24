from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from elf_mcp_server import ElfClient, ElfRunResult, doctor


def test_doctor_reports_missing_home(tmp_path: Path) -> None:
    report = doctor(str(tmp_path / "missing"))
    assert report["ok"] is False
    assert report["python_bits"] in (32, 64)
    assert any("ELF product home not found" in msg for msg in report["issues"])


def test_elf_run_result_output_helpers(tmp_path: Path) -> None:
    flx = tmp_path / "demo.flx"
    flx.write_text("# header\n1  0.125\n2  0.250\nnot a number\n", encoding="utf-8")

    res = ElfRunResult(
        ok=True,
        solver="MAGIC",
        case_name="demo",
        work_dir=tmp_path,
        returncode=0,
        elapsed_s=0.5,
        outputs=("demo.flx",),
    )

    assert res.output_path("flx") == flx
    assert res.output_path(".flx") == flx
    assert "0.125" in (res.read_output(".flx") or "")
    assert res.parse_numeric_table(".flx") == [[1.0, 0.125], [2.0, 0.25]]


def test_elf_client_run_mai_and_sweep(tmp_path: Path) -> None:
    meg = tmp_path / "mesh.meg"
    meg.write_text("MEG_DATA\n", encoding="utf-8")

    dll_dir = tmp_path / "product" / "bin"
    dll_dir.mkdir(parents=True)
    (dll_dir / "magh1600.dll").write_bytes(b"MZ-fake-magic")
    client = ElfClient(product_home=str(dll_dir.parent), timeout_s=60)

    def fake_worker(request, directory, timeout_seconds, *, include_native_diagnostics):
        assert timeout_seconds == 60
        case_name = request["case_name"]
        (directory / f"{case_name}.flx").write_text("1 0.125", encoding="utf-8")
        return {
            "exit_code": 0, "elapsed_seconds": 0.1, "timed_out": False,
            "worker_result": {"ok": True},
        }

    with patch("elf_mcp_server.product_runner._run_worker", side_effect=fake_worker) as worker:
        rows = client.sweep(
            "FILE MESH {case_name}.meg\nCURR {current}\n",
            [{"current": 100}, {"current": 200}],
            tmp_path / "sweep",
            meg_path=meg,
            confirm_product_execution=True,
        )
        directory = tmp_path / "sweep" / "case_000"
        assert client.check_case(directory, "case_000")["ready"] is True
        pending = client.run_case(directory, "case_000")
        assert pending.error == "confirmation_required; confirm_product_execution=true"
        assert worker.call_count == 2

    assert len(rows) == 2
    assert (directory / "case_000.mai").read_text(encoding="utf-8") == (
        "FILE MESH case_000.meg\nCURR 100\n"
    )
    assert (directory / "case_000.meg").read_text(encoding="utf-8") == "MEG_DATA\n"
    assert rows[1]["params"] == {"current": 200}
    result = rows[1]["result"]
    assert result.ok is True
    assert result.returncode == 0
    assert result.elapsed_s == 0.1
    assert result.error is None
    assert result.outputs == ("case_001.flx",)

    failed_stage = {
        "exit_code": 2, "elapsed_seconds": 0.2, "timed_out": False,
        "worker_result": {"ok": False, "error_type": "OSError"},
    }
    with patch("elf_mcp_server.product_runner._run_worker", return_value=failed_stage):
        failed = client.run_case(directory, "case_000", confirm_product_execution=True)
    assert failed.ok is False
    assert failed.returncode == 2
    assert failed.elapsed_s == 0.2
    assert failed.error == "failed; worker exit code 2; OSError; no fresh outputs"


def test_elf_usage_python_client_topic() -> None:
    from elf_mcp_server.elf_knowledge import get_elf_documentation

    doc = get_elf_documentation("python_client")
    assert "ElfClient" in doc
    assert all(example in doc for example in ("doctor(", ".run_case(", ".run_mai(", ".sweep("))

@pytest.mark.parametrize("confirm", [False, True])
def test_elf_client_reports_case_blocking_reasons(tmp_path: Path, confirm: bool) -> None:
    product_home = tmp_path / "product"
    case_dir = tmp_path / "case"
    case_dir.mkdir()
    (case_dir / "demo.mai").touch()
    client = ElfClient(product_home=str(product_home))
    missing_home = client.run_case(case_dir, "demo", confirm_product_execution=confirm)
    assert "ELF product home not found" in missing_home.error

    (product_home / "bin").mkdir(parents=True)
    result = client.run_case(case_dir, "demo", confirm_product_execution=confirm)
    assert not result.ok
    assert "demo.meg" in result.error
    assert "magh1600.dll" in result.error
    assert str(tmp_path) not in result.error


def test_elf_client_sweep_runs_all_generator_cases(tmp_path: Path) -> None:
    mesh = tmp_path / "source.meg"
    mesh.write_bytes(b"mesh")
    base_dir = tmp_path / "sweep"
    client = ElfClient(product_home=str(tmp_path / "missing"))
    params = ({"current": current} for current in (100, 200))

    rows = client.sweep("CURR {current}", params, base_dir, meg_path=mesh)

    assert [row["case_name"] for row in rows] == ["case_000", "case_001"]
    assert [row["result"].raw["status"] for row in rows] == ["confirmation_required"] * 2
    for row, current in zip(rows, (100, 200)):
        name = row["case_name"]
        assert (base_dir / name / f"{name}.mai").read_text(encoding="utf-8") == f"CURR {current}"


def test_elf_client_sweep_rejects_case_name_before_writing(tmp_path: Path) -> None:
    base_dir = tmp_path / "sweep"
    with pytest.raises(ValueError, match="case_name is generated from case_prefix"):
        ElfClient().sweep("{case_name}", [{}, {"case_name": "reserved"}], base_dir)
    assert not base_dir.exists()


def test_elf_client_run_mai_prepares_unconfirmed_case(tmp_path: Path) -> None:
    mesh = tmp_path / "source.meg"
    mesh.write_bytes(b"mesh")
    work_dir = tmp_path / "case"
    client = ElfClient(product_home=str(tmp_path / "missing"))
    result = client.run_mai("PRE", work_dir, "demo", meg_path=mesh)
    assert result.raw["status"] == "confirmation_required"
    assert (work_dir / "demo.mai").read_text(encoding="utf-8") == "PRE"
    assert (work_dir / "demo.meg").read_bytes() == b"mesh"


def test_elf_usage_room_runner_topic() -> None:
    from elf_mcp_server.elf_knowledge import get_elf_documentation

    doc = get_elf_documentation("room_runner")
    assert "ルームランナー" in doc
    assert "LU" in doc


def test_elf_client_compile_iemesh_missing_home(tmp_path: Path) -> None:
    client = ElfClient(product_home=str(tmp_path / "missing"))
    res = client.compile_iemesh("BOX 0 1 0 1 0 1\n", tmp_path / "mesh_run", case_name="motor")
    assert res["ok"] is False
    assert "mesh750.exe" in (res["error"] or "")


def test_elf_run_result_parse_summary_and_axial_template(tmp_path: Path) -> None:
    (tmp_path / "ax.flx").write_text("1 0.15\n2 0.30\n", encoding="utf-8")
    (tmp_path / "ax.frc").write_text("1 12.5\n", encoding="utf-8")
    (tmp_path / "ax.log").write_text("Solver converged in 5 iterations.\n", encoding="utf-8")

    res = ElfRunResult(
        ok=True,
        solver="MAGIC",
        case_name="ax",
        work_dir=tmp_path,
        returncode=0,
        elapsed_s=0.2,
        outputs=("ax.flx", "ax.frc", "ax.log"),
    )
    summary = res.parse_summary()
    assert summary["flx_rows"] == 2
    assert summary["flx_last"] == [2.0, 0.3]
    assert summary["frc_last"] == [1.0, 12.5]
    assert summary["converged"] is True

    mai = ElfClient.build_axial_motor_mai(voltage_v=100.0, rpm=3000.0, pole_pairs=4, steps=36)
    assert "VOLT  1  100.0" in mai
    assert "N=3000.0 rpm" in mai
    assert "Room-Runner" in mai


def test_elf_client_run_mei_and_mai_short_circuits_on_mesh_failure(tmp_path: Path) -> None:
    client = ElfClient(product_home=str(tmp_path / "missing"))
    res = client.run_mei_and_mai("BOX 0 1 0 1 0 1\n", "USE MAGIC 3.50\nEND\n", tmp_path / "e2e")
    assert res.ok is False
    assert "mesh750.exe" in (res.error or "")


def test_elf_client_mei_geometry_helpers() -> None:
    box = ElfClient.mei_box(-1, 1, -1, 1, 0, 2, nx=2, ny=2, nz=2, mat=1)
    cyl = ElfClient.mei_cylinder(0.05, 0.0, 0.01, nr=4, ntheta=24, nz=2, mat=2)
    ring = ElfClient.mei_ring(0.02, 0.05, 0.0, 0.01, nr=4, ntheta=24, nz=2, mat=3)
    assert box.startswith("BOX ")
    assert cyl.startswith("CYL ")
    assert ring.startswith("RING ")


def test_elf_client_build_mai() -> None:
    mai = ElfClient.build_mai(
        mesh_file="motor.meg",
        currents={1: 10.0, 2: -5.0},
        sol_command="FIXB",
        outputs=("FLUM", "FORC"),
    )
    assert "FILE  MESH  motor.meg" in mai
    assert "CURR  1  10.0" in mai
    assert "SOL  FIXB" in mai


def test_iemesh_builder_fluent_api() -> None:
    from elf_mcp_server import IEmeshBuilder

    mei = (
        IEmeshBuilder("axial_motor")
        .ring(0.02, 0.05, 0.0, 0.01, nr=4, ntheta=24, nz=2, mat=1)
        .translate(dz=0.002)
        .rotate(15.0, axis="z")
        .build()
    )
    assert "! axial_motor" in mei
    assert "RING " in mei
    assert "MOV  0.0  0.0  0.002" in mei
    assert "ROT  Z  15.0" in mei


def test_elf_usage_analysis_methods_topic() -> None:
    from elf_mcp_server.elf_knowledge import get_elf_documentation

    doc = get_elf_documentation("analysis_methods")
    assert "FIXA" in doc
    assert "STEP" in doc


def test_mai_builder_fluent_api() -> None:
    from elf_mcp_server import MaiBuilder

    mai = (
        MaiBuilder("MAGIC")
        .mesh("motor.meg")
        .material(1, mu_r=2000.0)
        .voltage(1, 48.0)
        .sol_step(36, 1e-4)
        .output("FLUM", "FORC")
        .build()
    )
    assert "USE  MAGIC  3.50" in mai
    assert "FILE  MESH  motor.meg" in mai
    assert "MATE  1  2000.0" in mai
    assert "VOLT  1  48.0" in mai
    assert "SOL  STEP  36  1.000000e-04" in mai
    assert "FLUM" in mai


def test_suggest_mei_mai_example() -> None:
    from elf_mcp_server import suggest_mei_mai_example

    ax = suggest_mei_mai_example("アキシャルモータを電圧と回転数を指定して解析したい")
    assert ax["kind"] == "axial_motor"
    assert "RING " in ax["mei_text"]
    assert "VOLT  1" in ax["mai_text"]

    es = suggest_mei_mai_example("ELFIN 静電場")
    assert es["kind"] == "electrostatic"
    assert "USE  ELFIN" in es["mai_text"]

    bm = suggest_mei_mai_example("電子顕微鏡の電子線軌道解析")
    assert bm["kind"] == "beam"
    assert "USE  BEAM" in bm["mai_text"]
    assert "-1.602E-19" in bm["mai_text"]
