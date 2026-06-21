"""Public ELF-runnable ELF/MAGIC sample input decks.

This corpus contains lab-authored .mai/.meg decks only. It intentionally
excludes solver outputs, comparison metrics, private paths, and provenance.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
import re
from typing import Any


ROOT = "public_samples"

FAMILY_META = {
    "motor/pm_cosine_pickup_72": {
        "title": "2-pole cosine-amplitude PM pickup",
        "tags": ("motor", "pm", "cosine-remanence", "hbrm", "hbcn", "flum", "pickup"),
        "hint": "Use when spatially varying PM remanence or per-segment HBCN curve assignment matters.",
    },
    "motor/pm_square_2pole_pickup_100": {
        "title": "2-pole square-wave PM pickup",
        "tags": ("motor", "pm", "2-pole", "square-wave", "mwl8t", "flum", "pickup"),
        "hint": "Use as the broadest PM-only passive pickup baseline.",
    },
    "motor/pm_square_4pole_pickup_60": {
        "title": "4-pole square-wave PM pickup",
        "tags": ("motor", "pm", "4-pole", "square-wave", "mwl8t", "flum", "pickup"),
        "hint": "Use for multipole polarity, rotor-angle sign, and passive FLUM checks.",
    },
    "motor/pm_square_6pole_pickup_72": {
        "title": "6-pole square-wave PM pickup",
        "tags": ("motor", "pm", "6-pole", "square-wave", "mwl8t", "flum", "pickup"),
        "hint": "Use for shorter mechanical period PM pickup examples.",
    },
    "motor/pm_square_8pole_pickup_28": {
        "title": "8-pole square-wave PM pickup subset",
        "tags": ("motor", "pm", "8-pole", "square-wave", "mwl8t", "flum", "pickup"),
        "hint": "Use for compact high-pole-count PM pickup examples.",
    },
}

TEAM28_CASES: tuple[tuple[str, str], ...] = (
    ("motor/pm_square_2pole_pickup_100", "pm001"),
    ("motor/pm_square_2pole_pickup_100", "pm006"),
    ("motor/pm_square_2pole_pickup_100", "pm019"),
    ("motor/pm_square_2pole_pickup_100", "pm024"),
    ("motor/pm_square_2pole_pickup_100", "pm049"),
    ("motor/pm_square_2pole_pickup_100", "pm072"),
    ("motor/pm_square_2pole_pickup_100", "pm097"),
    ("motor/pm_square_2pole_pickup_100", "pm100"),
    ("motor/pm_square_4pole_pickup_60", "pm001"),
    ("motor/pm_square_4pole_pickup_60", "pm012"),
    ("motor/pm_square_4pole_pickup_60", "pm025"),
    ("motor/pm_square_4pole_pickup_60", "pm036"),
    ("motor/pm_square_4pole_pickup_60", "pm060"),
    ("motor/pm_square_6pole_pickup_72", "pm001"),
    ("motor/pm_square_6pole_pickup_72", "pm018"),
    ("motor/pm_square_6pole_pickup_72", "pm025"),
    ("motor/pm_square_6pole_pickup_72", "pm042"),
    ("motor/pm_square_6pole_pickup_72", "pm061"),
    ("motor/pm_square_6pole_pickup_72", "pm072"),
    ("motor/pm_square_8pole_pickup_28", "pm001"),
    ("motor/pm_square_8pole_pickup_28", "pm013"),
    ("motor/pm_square_8pole_pickup_28", "pm028"),
    ("motor/pm_cosine_pickup_72", "pm001"),
    ("motor/pm_cosine_pickup_72", "pm004"),
    ("motor/pm_cosine_pickup_72", "pm025"),
    ("motor/pm_cosine_pickup_72", "pm049"),
    ("motor/pm_cosine_pickup_72", "pm071"),
    ("motor/pm_cosine_pickup_72", "pm072"),
)

SOL_RE = re.compile(r"^\s*SOL\s+([A-Z0-9_]+)", re.MULTILINE)
ELEMENT_RE = re.compile(r"\b(MWL8T|MWV8T|MCL8T|MMB8T|MCO[0-9A-Z]*|MCM[0-9A-Z]*|MJH[0-9A-Z]*)\b")
KEYWORDS = (
    "HBUN",
    "HBSC",
    "HBCU",
    "HBRM",
    "HBCN",
    "VEC3",
    "COI1",
    "AMP1",
    "TIME",
    "NONL",
    "DMEG",
    "FLUM",
)


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


def _uniq(items: list[str]) -> list[str]:
    seen = set()
    out = []
    for item in items:
        if item not in seen:
            out.append(item)
            seen.add(item)
    return out


def _family_meta(family: str) -> dict[str, Any]:
    return FAMILY_META.get(
        family,
        {
            "title": family.rsplit("/", 1)[-1] if family else "sample deck",
            "tags": ("sample-deck",),
            "hint": "Use as a public ELF/MAGIC input deck for a local ELF installation.",
        },
    )


def build_sample_deck_cards(
    limit: int = 100,
    family: str | None = None,
    query: str | None = None,
    team28: bool = False,
) -> list[dict[str, Any]]:
    """Build compact cards over public ELF-runnable sample deck cases."""
    decks = load_sample_decks()
    mai_decks = [d for d in decks.values() if d.ext == "mai"]
    if team28:
        wanted = set(TEAM28_CASES)
        mai_decks = [d for d in mai_decks if (d.family, d.case) in wanted]
    if family:
        mai_decks = [d for d in mai_decks if family in d.family]

    cards = []
    for mai in sorted(mai_decks, key=lambda d: d.path):
        meg_path = mai.path[:-4] + ".meg"
        meg = decks.get(meg_path)
        meta = _family_meta(mai.family)
        haystack = " ".join(
            [
                mai.path,
                mai.family,
                mai.case,
                mai.text,
                meg.text if meg else "",
                " ".join(meta["tags"]),
            ]
        ).lower()
        if query:
            keywords = [k.lower() for k in query.split() if k.strip()]
            if not all(k in haystack for k in keywords):
                continue
        sol_blocks = _uniq(SOL_RE.findall(mai.text))
        pre_keywords = [kw for kw in KEYWORDS if re.search(rf"^\s*{kw}\b", mai.text, re.MULTILINE)]
        elements = _uniq(ELEMENT_RE.findall(meg.text if meg else ""))
        tags = list(meta["tags"])
        hint = meta["hint"]
        if team28:
            hint = (
                "Use as a Python-interface seed/inspection deck; team28 is "
                "an orchestration manifest, not a normal ELF GUI/CLI "
                "deck-execution workflow."
            )
        cards.append(
            {
                "family": mai.family,
                "case": mai.case,
                "title": meta["title"],
                "tags": tags,
                "mai_path": mai.path,
                "meg_path": meg_path if meg else "",
                "sol_blocks": sol_blocks,
                "pre_keywords": pre_keywords,
                "elements": elements,
                "char_count": mai.char_count + (meg.char_count if meg else 0),
                "hint": hint,
            }
        )
    if team28:
        order = {key: i for i, key in enumerate(TEAM28_CASES)}
        cards.sort(key=lambda c: order[(c["family"], c["case"])])
    return cards[: max(0, min(limit, 332))]


def build_team28_cards() -> list[dict[str, Any]]:
    """Build the curated 28-card Python-interface representative set."""
    return build_sample_deck_cards(limit=28, team28=True)


def format_sample_deck_cards(cards: list[dict[str, Any]], title: str = "ELF public sample deck playbook") -> str:
    """Format compact sample deck cards as Markdown."""
    if not cards:
        return f"# {title}\n\nNo sample deck cards matched."
    lines = [f"# {title} ({len(cards)} cards)", ""]
    for i, card in enumerate(cards, 1):
        lines.append(f"## {i}. {card['title']} / {card['case']}")
        lines.append(f"- family: `{card['family']}`")
        lines.append(f"- files: `{card['mai_path']}` + `{card['meg_path']}`")
        lines.append(f"- tags: {', '.join(card['tags'])}")
        lines.append(f"- SOL: {', '.join(card['sol_blocks']) if card['sol_blocks'] else '(none)'}")
        lines.append(f"- PRE: {', '.join(card['pre_keywords']) if card['pre_keywords'] else '(none)'}")
        lines.append(f"- elements: {', '.join(card['elements']) if card['elements'] else '(none)'}")
        lines.append(f"- hint: {card['hint']}")
        lines.append("")
    return "\n".join(lines).rstrip()


def format_team28_cards(cards: list[dict[str, Any]]) -> str:
    """Format team28 cards with the required Python-interface manifest note."""
    body = format_sample_deck_cards(cards, title="ELF Python-interface team28")
    note = (
        "# team28 Python-interface seed manifest\n\n"
        "team28 is a Python-interface seed manifest, not a normal ELF GUI/CLI "
        "deck-execution workflow. The public `.mai`/`.meg` paths below are "
        "seed decks and inspection material; runtime orchestration belongs to "
        "the ELF Python interface, outside this documentation MCP server.\n\n"
    )
    return note + body
