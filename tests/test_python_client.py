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

    fake_raw = {
        "ok": True,
        "returncode": 0,
        "elapsed_s": 0.1,
        "fresh_outputs": [{"name": "case_000.flx"}],
    }

    client = ElfClient(product_home=str(tmp_path), solver="MAGIC", timeout_s=60)
    with patch("elf_mcp_server.python_client.run_product_case", return_value=fake_raw) as mock_run:
        rows = client.sweep(
            "CURR {current}\n",
            [{"current": 100}, {"current": 200}],
            tmp_path / "sweep",
            meg_path=meg,
        )

    assert len(rows) == 2
    assert mock_run.call_count == 2
    assert (tmp_path / "sweep" / "case_000" / "case_000.mai").read_text(encoding="utf-8") == "CURR 100\n"
    assert (tmp_path / "sweep" / "case_000" / "case_000.meg").read_text(encoding="utf-8") == "MEG_DATA\n"
    assert rows[1]["params"] == {"current": 200}
    assert rows[1]["result"].ok is True
