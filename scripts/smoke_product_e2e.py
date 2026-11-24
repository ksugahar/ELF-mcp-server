"""End-to-end smoke script for a user-local ELF/MAGIC product installation."""
from __future__ import annotations

from pathlib import Path
import tempfile

from elf_mcp_server import ElfClient, doctor


def main() -> int:
    diag = doctor()
    print("doctor:", diag["ok"], "issues:", diag["issues"])
    if not diag["ok"]:
        return 1

    client = ElfClient(solver="MAGIC")
    mei = client.mei_box(-0.05, 0.05, -0.05, 0.05, -0.05, 0.05, nx=2, ny=2, nz=2, mat=1)
    mai = client.build_mai(mesh_file="smoke.meg", currents={1: 100.0})

    with tempfile.TemporaryDirectory(prefix="elf_smoke_") as tmp:
        res = client.run_mei_and_mai(mei, mai, Path(tmp), case_name="smoke")
        print("run ok:", res.ok, "summary:", res.parse_summary())
        return 0 if res.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
