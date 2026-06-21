"""Public-package policy lint for ELF-mcp-server.

The public ELF MCP package is a documentation/input-deck server. This lint
guards the publish boundary that matters most for the public repository:
no private validation provenance, no machine-local paths, no unrelated
commercial-tool promotion, and no bundled solver outputs in public samples.
"""
from __future__ import annotations

from pathlib import Path
import sys


TEXT_SUFFIXES = {".md", ".py", ".toml", ".txt", ".mai", ".meg"}

CURATED_PATHS = (
    "README.md",
    "pyproject.toml",
    "src/elf_mcp_server",
)

PRIVATE_MARKERS = (
    "S:\\",
    "S:/",
    "W:\\",
    "W:/",
    "C:\\temp",
    "_crossval",
    "internal:",
    "LAB private",
    "COMSOL_Multiphysics_MCP",
    "FEMM",
    "JMAG",
    "elf_converter",
)

SAMPLE_OUTPUT_SUFFIXES = (".mag", ".mao", ".mat", ".mac")
SAMPLE_OUTPUT_MARKERS = SAMPLE_OUTPUT_SUFFIXES + ("summary.csv",)


def _iter_text_files(root: Path, rel_roots: tuple[str, ...]) -> list[Path]:
    files: list[Path] = []
    for rel in rel_roots:
        path = root / rel
        if not path.exists():
            continue
        if path.is_file():
            candidates = [path]
        else:
            candidates = [p for p in path.rglob("*") if p.is_file()]
        for candidate in candidates:
            if candidate.name == "policy_lint.py":
                continue
            if candidate.suffix.lower() in TEXT_SUFFIXES:
                files.append(candidate)
    return sorted(set(files))


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="cp932", errors="replace")


def run_policy_lint(root: Path | str | None = None) -> list[str]:
    """Return policy-lint issue strings for a repository root."""
    repo = Path(root) if root is not None else Path.cwd()
    repo = repo.resolve()
    issues: list[str] = []

    for path in _iter_text_files(repo, CURATED_PATHS):
        rel = path.relative_to(repo).as_posix()
        text = _read_text(path)
        for marker in PRIVATE_MARKERS:
            if marker in text:
                issues.append(f"{rel}: contains private marker {marker!r}")

    samples = repo / "src" / "elf_mcp_server" / "public_samples" / "motor"
    if samples.exists():
        for path in sorted(p for p in samples.rglob("*") if p.is_file()):
            rel = path.relative_to(repo).as_posix()
            suffix = path.suffix.lower()
            if suffix not in {".mai", ".meg"}:
                issues.append(f"{rel}: public motor sample must be .mai or .meg")
            if suffix in SAMPLE_OUTPUT_SUFFIXES or path.name.lower() == "summary.csv":
                issues.append(f"{rel}: solver output file is not allowed")
            if suffix in {".mai", ".meg"}:
                text = _read_text(path)
                for marker in SAMPLE_OUTPUT_MARKERS + PRIVATE_MARKERS:
                    if marker in text:
                        issues.append(f"{rel}: contains forbidden marker {marker!r}")

    return issues


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    root = Path(args[0]) if args else Path.cwd()
    issues = run_policy_lint(root)
    if issues:
        print("ELF MCP policy lint FAILED")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print("ELF MCP policy lint PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
