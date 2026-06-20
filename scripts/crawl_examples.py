"""Crawl C:/ELF600/examples/ text files (.mai .mei .txt .props .model), dump as JSON.

Skips .meg (binary mesh), .mag (binary results), .pdf, .xls/.xlsx (separate).

Output:
  src/elf_mcp_server/examples_dump.json
    {
      "magic/BASIC/ABCL2.mai": {
        "ext": "mai",
        "solver": "MAGIC",
        "category": "BASIC",
        "char_count": int,
        "byte_size": int,
        "text": "..."
      },
      ...
    }

Usage:
    python scripts/crawl_examples.py [--root C:/ELF600/examples] [--out PATH]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TEXT_EXTS = {".mai", ".mei", ".txt", ".props", ".model"}


def decode(raw: bytes) -> str:
    for enc in ("shift_jis", "cp932", "utf-8"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("shift_jis", errors="replace")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=r"C:/ELF600/examples")
    ap.add_argument("--out", default=str(Path(__file__).parent.parent / "src" / "elf_mcp_server" / "examples_dump.json"))
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
        rel_parts = f.relative_to(root).parts
        rel = "/".join(rel_parts)
        solver = rel_parts[0].upper() if rel_parts else ""
        category = rel_parts[1] if len(rel_parts) >= 2 else ""
        try:
            raw = f.read_bytes()
            text = decode(raw)
        except Exception as e:
            text = f"[error reading: {e}]"
            raw = b""
        dump[rel] = {
            "ext": f.suffix.lower().lstrip("."),
            "solver": solver,
            "category": category,
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
    by_solver = {}
    for v in dump.values():
        s = v["solver"]
        by_solver[s] = by_solver.get(s, 0) + 1
    print(f"By solver: {by_solver}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
