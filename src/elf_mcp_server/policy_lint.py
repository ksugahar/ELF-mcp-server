"""Public-package policy lint for ELF-mcp-server.

The public ELF MCP package is a documentation/input-deck server. This lint
guards the publish boundary that matters most for the public repository:
no private validation provenance, no machine-local paths, no unrelated
commercial-tool promotion, and no bundled solver outputs in public samples.
"""
from __future__ import annotations

import json
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
MANIFEST_NAME = "VALIDATED_MANIFEST.json"


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


def _sample_families(samples: Path) -> dict[str, list[Path]]:
    """Return public sample family -> case directories for bundled decks."""
    families: dict[str, list[Path]] = {}
    if not samples.exists():
        return families
    for domain in sorted(p for p in samples.iterdir() if p.is_dir()):
        for family_dir in sorted(p for p in domain.iterdir() if p.is_dir()):
            cases = sorted(p for p in family_dir.iterdir() if p.is_dir())
            if cases:
                families[f"{domain.name}/{family_dir.name}"] = cases
    return families


def _validate_public_sample_manifest(repo: Path, samples: Path) -> list[str]:
    """Ensure bundled sample decks are exactly the validation-passed manifest."""
    issues: list[str] = []
    actual = _sample_families(samples)
    manifest_path = samples / MANIFEST_NAME
    rel_manifest = manifest_path.relative_to(repo).as_posix()
    if not manifest_path.exists():
        return [f"{rel_manifest}: missing validated sample manifest"]

    manifest_text = _read_text(manifest_path)
    for marker in PRIVATE_MARKERS:
        if marker in manifest_text:
            issues.append(f"{rel_manifest}: contains private marker {marker!r}")

    try:
        manifest = json.loads(manifest_text)
    except json.JSONDecodeError as exc:
        return [f"{rel_manifest}: invalid JSON ({exc})"]

    manifest_families = manifest.get("families")
    if not isinstance(manifest_families, dict):
        return [f"{rel_manifest}: missing families object"]

    actual_names = set(actual)
    manifest_names = set(manifest_families)
    for family in sorted(actual_names - manifest_names):
        issues.append(f"{rel_manifest}: sample family {family!r} is not listed as validated")
    for family in sorted(manifest_names - actual_names):
        issues.append(f"{rel_manifest}: listed family {family!r} is not present in public_samples")

    total_cases = 0
    total_input_files = 0
    for family in sorted(actual_names & manifest_names):
        entry = manifest_families[family]
        if not isinstance(entry, dict):
            issues.append(f"{rel_manifest}: family {family!r} entry must be an object")
            continue
        if entry.get("validation") != "passed":
            issues.append(f"{rel_manifest}: family {family!r} is not marked validation='passed'")
        cases = actual[family]
        actual_count = len(cases)
        total_cases += actual_count
        total_input_files += actual_count * 2
        if entry.get("cases") != actual_count:
            issues.append(
                f"{rel_manifest}: family {family!r} cases={entry.get('cases')!r} "
                f"does not match actual {actual_count}"
            )
        if entry.get("input_files") != actual_count * 2:
            issues.append(
                f"{rel_manifest}: family {family!r} input_files={entry.get('input_files')!r} "
                f"does not match actual {actual_count * 2}"
            )
        for case_dir in cases:
            case = case_dir.name
            for suffix in (".mai", ".meg"):
                expected = case_dir / f"{case}{suffix}"
                if not expected.exists():
                    rel = expected.relative_to(repo).as_posix()
                    issues.append(f"{rel}: missing required public input-deck pair file")

    if manifest.get("total_cases") != total_cases:
        issues.append(
            f"{rel_manifest}: total_cases={manifest.get('total_cases')!r} "
            f"does not match actual {total_cases}"
        )
    if manifest.get("total_input_files") != total_input_files:
        issues.append(
            f"{rel_manifest}: total_input_files={manifest.get('total_input_files')!r} "
            f"does not match actual {total_input_files}"
        )

    return issues


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

    samples = repo / "src" / "elf_mcp_server" / "public_samples"
    if samples.exists():
        issues.extend(_validate_public_sample_manifest(repo, samples))
        for path in sorted(p for p in samples.rglob("*") if p.is_file()):
            rel = path.relative_to(repo).as_posix()
            suffix = path.suffix.lower()
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
