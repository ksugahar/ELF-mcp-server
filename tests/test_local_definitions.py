import json
from pathlib import Path

from elf_mcp_server.elf_knowledge import get_elf_documentation


def test_local_data_is_only_read_when_requested(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    assert "No user-local" in get_elf_documentation("local_definitions")
    directory = tmp_path / ".elf_mcp"
    directory.mkdir()
    payload = {"particles": [{"name": "local-test-particle", "charge_C": -1.0}]}
    (directory / "definitions.json").write_text(json.dumps(payload), encoding="utf-8")
    assert json.loads(get_elf_documentation("local_definitions")) == payload
    assert "local-test-particle" not in get_elf_documentation("all")
