"""Read user-local material and particle definitions, never bundled data."""
import json
from pathlib import Path


def read_local_definitions() -> str:
    """Return the locally imported definitions without executing product code."""
    path = Path.home() / ".elf_mcp" / "definitions.json"
    if not path.is_file():
        return "No user-local material/particle definitions have been imported."
    if path.stat().st_size > 1_000_000:
        raise ValueError("Local definitions exceed the 1 MB limit")
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    return json.dumps(data, ensure_ascii=False, indent=2)
