from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

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
