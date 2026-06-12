# -*- coding: utf-8 -*-
"""Smoke tests for the public ELF doc-server (mcp-server-elf).

Minimal guards for a public package: the server imports, the four bundled
vendor-doc dumps load, the tool surface is the expected size, and the removed
work-examples family stays OUT (publish-boundary regression guard).
"""
import os
import sys
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_server_imports():
    from mcp_server_elf import server
    assert server.mcp is not None


def test_doc_dumps_load():
    from mcp_server_elf.help_access import list_help_files
    from mcp_server_elf.examples_access import list_examples
    from mcp_server_elf.wiki_access import list_wiki_pages
    from mcp_server_elf.python_access import list_python_files
    assert len(list_help_files()) > 1000
    assert len(list_examples()) > 300
    assert len(list_wiki_pages()) > 50
    assert len(list_python_files()) > 5


def test_tool_surface_and_no_work_family():
    from mcp_server_elf.server import mcp
    tools = asyncio.run(mcp.list_tools())
    names = [t.name for t in tools]
    assert len(names) >= 13
    # publish boundary: the private work-examples corpus tools were removed and
    # must never come back into the public package.
    assert not any("work" in n for n in names), names


def test_usage_topic_nonempty():
    from mcp_server_elf.elf_knowledge import get_elf_documentation
    assert len(get_elf_documentation("overview")) > 100
