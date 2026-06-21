# -*- coding: utf-8 -*-
"""Smoke tests for the public ELF doc-server (elf-mcp-server).

Minimal guards for a public package: the server imports, the four bundled
vendor-doc dumps load, the tool surface is the expected size, and the removed
work-examples family stays OUT (publish-boundary regression guard).
"""
import os
import sys
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_server_imports():
    from elf_mcp_server import server
    assert server.mcp is not None


def test_doc_dumps_load():
    from elf_mcp_server.help_access import list_help_files
    from elf_mcp_server.examples_access import list_examples
    from elf_mcp_server.wiki_access import list_wiki_pages
    from elf_mcp_server.python_access import list_python_files
    assert len(list_help_files()) > 1000
    assert len(list_examples()) > 300
    assert len(list_wiki_pages()) > 50
    assert len(list_python_files()) > 5


def test_100_example_playbook_cards_public_safe():
    from elf_mcp_server.example_playbook import build_example_cards, format_example_cards
    cards = build_example_cards(limit=100)
    assert len(cards) == 100
    assert sum(1 for c in cards if c["solver"] == "MAGIC") == 97
    text = format_example_cards(cards)
    assert "magic/IPM/Motor1.mai" in text
    assert "flux-linkage" in text
    assert "maxwell-force" in text
    assert "C:\\" not in text
    assert "_crossval" not in text


def test_tool_surface_and_no_work_family():
    from elf_mcp_server.server import mcp
    tools = asyncio.run(mcp.list_tools())
    names = [t.name for t in tools]
    assert len(names) >= 15
    assert "elf_examples_playbook" in names
    # publish boundary: the private work-examples corpus tools were removed and
    # must never come back into the public package.
    assert not any("work" in n for n in names), names


def test_usage_topic_nonempty():
    from elf_mcp_server.elf_knowledge import get_elf_documentation
    assert len(get_elf_documentation("overview")) > 100


def test_motor_radia_bridge_topic_public_safe():
    from elf_mcp_server.elf_knowledge import get_elf_documentation
    doc = get_elf_documentation("motor_radia_bridge")
    assert "air-gap field" in doc
    assert "MCL8T" in doc
    assert "MCM4T" in doc
    assert "M1MF" in doc
    assert "SOL FORT" in doc
    assert "SOL FIXA" in doc
    assert "passive pickup coil" in doc
    assert "FLUM <pickup_mid>" in doc
    assert "PM-only pickup examples" in doc
    assert "S:\\" not in doc
    assert "C:\\temp" not in doc
    assert "_crossval" not in doc
