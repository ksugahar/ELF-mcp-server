"""Public runnable ELF/MAGIC sample input decks.

This corpus contains lab-authored .mai/.meg decks only. It intentionally
excludes solver outputs, comparison metrics, private paths, and provenance.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
from typing import Any


ROOT = "public_samples"


@dataclass(frozen=True)
class SampleDeck:
    path: str
    family: str
    case: str
    ext: str
    char_count: int
    text: str


def _sample_root():
    return resources.files("elf_mcp_server").joinpath(ROOT)


def _walk_files(node, prefix: str = "") -> list[tuple[str, Any]]:
    files: list[tuple[str, Any]] = []
    for child in sorted(node.iterdir(), key=lambda p: p.name):
        rel = f"{prefix}/{child.name}" if prefix else child.name
        if child.is_dir():
            files.extend(_walk_files(child, rel))
        elif child.is_file() and child.name.lower().endswith((".mai", ".meg")):
            files.append((rel.replace("\\", "/"), child))
    return files


@lru_cache(maxsize=1)
def load_sample_decks() -> dict[str, SampleDeck]:
    """Load bundled public sample decks once and cache them."""
    decks: dict[str, SampleDeck] = {}
    root = _sample_root()
    for rel_path, file_ref in _walk_files(root):
        text = file_ref.read_text(encoding="ascii")
        parts = rel_path.split("/")
        family = "/".join(parts[:-2]) if len(parts) >= 3 else ""
        case = parts[-2] if len(parts) >= 2 else ""
        ext = parts[-1].rsplit(".", 1)[-1].lower()
        decks[rel_path] = SampleDeck(
            path=rel_path,
            family=family,
            case=case,
            ext=ext,
            char_count=len(text),
            text=text,
        )
    return decks


def list_sample_decks(family: str | None = None, case: str | None = None, ext: str | None = None) -> list[dict[str, Any]]:
    """List public sample input decks, optionally filtered."""
    decks = load_sample_decks()
    e = ext.lower().lstrip(".") if ext else None
    out = []
    for deck in decks.values():
        if family and family not in deck.family:
            continue
        if case and case != deck.case:
            continue
        if e and e != deck.ext:
            continue
        out.append(
            {
                "path": deck.path,
                "family": deck.family,
                "case": deck.case,
                "ext": deck.ext,
                "char_count": deck.char_count,
            }
        )
    return sorted(out, key=lambda d: d["path"])


def search_sample_decks(query: str, top_k: int = 10, ext: str | None = None) -> list[dict[str, Any]]:
    """Substring-search public sample deck text and paths."""
    keywords = [k.strip() for k in query.split() if k.strip()]
    if not keywords:
        return []
    e = ext.lower().lstrip(".") if ext else None
    hits = []
    for deck in load_sample_decks().values():
        if e and deck.ext != e:
            continue
        haystack = f"{deck.path}\n{deck.text}"
        lower = haystack.lower()
        scores = [lower.count(kw.lower()) for kw in keywords]
        if not all(score > 0 for score in scores):
            continue
        first = lower.find(keywords[0].lower())
        start = max(0, first - 80)
        end = min(len(haystack), first + 220)
        snippet = haystack[start:end].replace("\n", " | ").strip()
        if start > 0:
            snippet = "..." + snippet
        if end < len(haystack):
            snippet += "..."
        hits.append(
            {
                "path": deck.path,
                "family": deck.family,
                "case": deck.case,
                "ext": deck.ext,
                "score": sum(scores),
                "snippet": snippet,
            }
        )
    hits.sort(key=lambda h: (-h["score"], h["path"]))
    return hits[:top_k]


def get_sample_deck(rel_path: str, max_chars: int = 60000) -> dict[str, Any]:
    """Get full text of a public sample .mai/.meg deck."""
    decks = load_sample_decks()
    deck = decks.get(rel_path)
    if deck is None:
        candidates = [p for p in decks if p.endswith("/" + rel_path) or p == rel_path]
        if len(candidates) == 1:
            deck = decks[candidates[0]]
        else:
            return {
                "path": rel_path,
                "error": f"not found (try one of: {candidates[:5]})" if candidates
                else "not found in public sample decks",
            }
    text = deck.text
    truncated = len(text) > max_chars
    if truncated:
        text = text[:max_chars] + f"\n\n[... truncated, full length: {deck.char_count} chars]"
    return {
        "path": deck.path,
        "family": deck.family,
        "case": deck.case,
        "ext": deck.ext,
        "text": text,
        "char_count": deck.char_count,
        "truncated": truncated,
    }
