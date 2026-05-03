"""Crawl C:/ELF600/help/ HTM files, decode Shift_JIS, strip HTML, dump as JSON.

Output:
  scripts/help_dump.json
    {
      "subdir/file.htm": {
        "title": "...",
        "text": "...",
        "byte_size": int,
        "char_count": int
      },
      ...
    }

Usage:
    python scripts/crawl_help.py [--out PATH] [--root C:/ELF600/help]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from html.parser import HTMLParser


class TextExtractor(HTMLParser):
    """Strip HTML and capture title + body text."""

    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []
        self._in_script = False
        self._in_style = False
        self._in_title = False
        self.title = ""

    def handle_starttag(self, tag, attrs):
        t = tag.lower()
        if t == "script":
            self._in_script = True
        elif t == "style":
            self._in_style = True
        elif t == "title":
            self._in_title = True
        elif t in ("br", "p", "div", "li", "tr", "h1", "h2", "h3", "h4"):
            self._chunks.append("\n")

    def handle_endtag(self, tag):
        t = tag.lower()
        if t == "script":
            self._in_script = False
        elif t == "style":
            self._in_style = False
        elif t == "title":
            self._in_title = False
        elif t in ("p", "div", "li", "tr", "h1", "h2", "h3", "h4", "td"):
            self._chunks.append("\n")

    def handle_data(self, data):
        if self._in_script or self._in_style:
            return
        if self._in_title:
            self.title += data
        self._chunks.append(data)

    def text(self) -> str:
        out = "".join(self._chunks)
        # Collapse runs of whitespace; keep newlines (single) as paragraph sep
        out = re.sub(r"[ \t]+", " ", out)
        out = re.sub(r"\n[ \t]+", "\n", out)
        out = re.sub(r"\n{3,}", "\n\n", out)
        return out.strip()


def decode_html(raw: bytes) -> str:
    """Decode HTML bytes — try Shift_JIS first (most ELF600 help), fallback UTF-8/CP932."""
    for enc in ("shift_jis", "cp932", "utf-8"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("shift_jis", errors="replace")


def extract_one(path: Path) -> dict:
    raw = path.read_bytes()
    html = decode_html(raw)
    parser = TextExtractor()
    try:
        parser.feed(html)
    except Exception as e:
        return {"title": "", "text": f"[parse error: {e}]", "byte_size": len(raw), "char_count": 0}
    text = parser.text()
    title = parser.title.strip()
    return {
        "title": title,
        "text": text,
        "byte_size": len(raw),
        "char_count": len(text),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=r"C:/ELF600/help")
    ap.add_argument("--out", default=str(Path(__file__).parent / "help_dump.json"))
    args = ap.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f"[ERR] {root} not found", file=sys.stderr)
        return 1

    files = sorted(root.rglob("*.htm")) + sorted(root.rglob("*.html"))
    print(f"Crawling {len(files)} HTM files under {root}")

    dump: dict[str, dict] = {}
    for f in files:
        rel = str(f.relative_to(root)).replace("\\", "/")
        try:
            dump[rel] = extract_one(f)
        except Exception as e:
            dump[rel] = {"title": "", "text": f"[error: {e}]", "byte_size": 0, "char_count": 0}

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dump, ensure_ascii=False, indent=2), encoding="utf-8")

    total_chars = sum(v["char_count"] for v in dump.values())
    total_bytes = out.stat().st_size
    print(f"Wrote {out} ({total_bytes/1024:.0f} KB)")
    print(f"Total: {len(dump)} files, {total_chars/1000:.0f}k characters extracted")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
