"""Crawl C:/ELF600/bin/ Python interface files + config + definitions, dump as JSON.

Bundles:
- elftypes.py / magtypes.py — ctypes wrappers for elfh1300.dll / magh1600.dll
  (~1100 lines each, 83 API functions)
- *.cfg — ELFIN.cfg, MAGIC.cfg
- *.def — ELFERR.def (error codes), MESERR.def (mesh errors), IEmesh.def, etc.
- Wmap2def.txt, etc.

Skips binary .exe / .dll / .sres.

Output:
  src/elf_mcp_server/python_dump.json
    {
      "elftypes.py": {
        "ext": "py",
        "char_count": int,
        "byte_size": int,
        "text": "..."
      },
      ...
    }

Usage:
    python scripts/crawl_python.py [--root C:/ELF600/bin] [--out PATH]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TEXT_EXTS = {".py", ".cfg", ".def", ".txt", ".bat"}


def decode(raw: bytes) -> str:
    for enc in ("utf-8", "shift_jis", "cp932"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=r"C:/ELF600/bin")
    ap.add_argument("--out", default=str(Path(__file__).parent.parent / "src" / "elf_mcp_server" / "python_dump.json"))
    args = ap.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f"[ERR] {root} not found", file=sys.stderr)
        return 1

    files = []
    for ext in TEXT_EXTS:
        files.extend(sorted(root.rglob(f"*{ext}")))
    print(f"Crawling {len(files)} text files under {root}")

    dump: dict[str, dict] = {}
    for f in files:
        rel = str(f.relative_to(root)).replace("\\", "/")
        try:
            raw = f.read_bytes()
            text = decode(raw)
        except Exception as e:
            text = f"[error: {e}]"
            raw = b""
        dump[rel] = {
            "ext": f.suffix.lower().lstrip("."),
            "char_count": len(text),
            "byte_size": len(raw),
            "text": text,
        }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dump, ensure_ascii=False, indent=2), encoding="utf-8")

    total_chars = sum(v["char_count"] for v in dump.values())
    print(f"Wrote {out} ({out.stat().st_size/1024:.0f} KB)")
    print(f"Total: {len(dump)} files, {total_chars/1000:.0f}k characters")
    by_ext = {}
    for v in dump.values():
        e = v["ext"]
        by_ext[e] = by_ext.get(e, 0) + 1
    print(f"By ext: {by_ext}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
