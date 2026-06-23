# -*- coding: utf-8 -*-
"""Smoke tests for the public ELF doc-server (ELF-mcp-server).

Minimal guards for a public package: the server imports, the four bundled
vendor-doc dumps load, the tool surface is the expected size, and the removed
work-examples family stays OUT (publish-boundary regression guard).
"""
import os
import sys
import asyncio
import tomllib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_server_imports():
    import elf_mcp_server
    from elf_mcp_server import server

    assert server.mcp is not None
    pyproject = os.path.join(os.path.dirname(__file__), "..", "pyproject.toml")
    with open(pyproject, "rb") as f:
        project = tomllib.load(f)["project"]
    assert elf_mcp_server.__version__ == project["version"]


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
    assert "_cross" + "val" not in text


def test_tool_surface_and_no_work_family():
    from elf_mcp_server.server import mcp, elf_overview
    tools = asyncio.run(mcp.list_tools())
    names = [t.name for t in tools]
    assert len(names) >= 24
    assert "elf_examples_playbook" in names
    assert "elf_recipe_search" in names
    assert "elf_recipe_get" in names
    assert "elf_plan_workflow" in names
    assert "elf_sample_decks_index" in names
    assert "elf_sample_decks_get" in names
    assert "elf_sample_decks_playbook" in names
    assert "elf_python_team28" in names
    overview = elf_overview()
    overview_text = str(overview)
    assert overview["n_tools"] == 24
    assert "public_boundary" in overview
    assert "recommended_calls" in overview
    assert "COMSOL" not in overview_text
    assert "internal:" not in overview_text
    assert "S:" + "\\" not in overview_text
    # publish boundary: the private work-examples corpus tools were removed and
    # must never come back into the public package. Public workflow planning is
    # allowed; private work-example corpus tools are not.
    forbidden = ("elf_work", "work_examples", "work_examples_", "elf_examples_work")
    assert not any(any(token in n for token in forbidden) for n in names), names


def test_public_sample_decks_are_runnable_inputs_only():
    from elf_mcp_server.sample_decks import (
        build_sample_deck_cards,
        build_team28_cards,
        format_team28_cards,
        list_sample_decks,
        search_sample_decks,
        get_sample_deck,
    )
    decks = list_sample_decks()
    assert len(decks) == 972
    assert sum(1 for d in decks if d["ext"] == "mai") == 486
    assert sum(1 for d in decks if d["ext"] == "meg") == 486
    assert any(d["path"] == "motor/pm_cosine_pickup_72/pm001/pm001.mai" for d in decks)
    assert any(d["path"] == "motor/spm_surface_pm_10/spm001/spm001.mai" for d in decks)
    assert any(d["path"] == "motor/srm_switched_reluctance_10/srm001/srm001.mai" for d in decks)
    assert any(d["path"] == "motor/induction_cage_10/im001/im001.mai" for d in decks)
    assert any(d["path"] == "application/wpt_loop_10/wpl001/wpl001.mai" for d in decks)
    assert any(d["path"] == "application/mri_loop_10/mrl001/mrl001.mai" for d in decks)
    assert any(d["path"] == "motor/sr_motor_loop_10/srl001/srl001.mai" for d in decks)
    assert any(d["path"] == "motor/spm_loop_10/spl001/spl001.mai" for d in decks)
    assert any(
        d["path"] == "application/ih_induction_heating_10/ihl001/ihl001.mai"
        for d in decks
    )
    assert any(d["path"] == "motor/reluctance_motor_10/ryl001/ryl001.mai" for d in decks)
    assert any(d["path"] == "motor/hysteresis_motor_10/hyl001/hyl001.mai" for d in decks)
    assert any(
        d["path"] == "application/transformer_loop_10/tfl001/tfl001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/accelerator_magnet_10/acl001/acl001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/transformer_core_pickup_12/tf001/tf001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/mri_gradient_shield_12/mri001/mri001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/wpt_coupled_coils_10/wpt001/wpt001.mai"
        for d in decks
    )
    hits = search_sample_decks("HBCN FLUM", ext="mai")
    assert hits
    assert hits[0]["path"].endswith(".mai")
    transformer_hits = search_sample_decks("transformer FLUM", ext="mai")
    assert transformer_hits
    assert transformer_hits[0]["path"].startswith("application/transformer")
    mri_hits = search_sample_decks("MRI OHM2 FREQ", ext="mai")
    assert mri_hits
    assert mri_hits[0]["path"].startswith("application/mri")
    im_hits = search_sample_decks("induction motor cage OHM2 FLUM", ext="mai")
    assert im_hits
    assert im_hits[0]["path"].startswith("motor/induction_cage_10")
    spm_hits = search_sample_decks("SPM HBRM FLUM", ext="mai")
    assert spm_hits
    assert spm_hits[0]["path"].startswith("motor/spm_surface_pm_10")
    srm_hits = search_sample_decks("SRM reluctance FLUM", ext="mai")
    assert srm_hits
    assert srm_hits[0]["path"].startswith("motor/srm_switched_reluctance_10")
    wpt_hits = search_sample_decks("WPT MOMC FLUM", ext="mai")
    assert wpt_hits
    assert wpt_hits[0]["path"].startswith("application/wpt_coupled_coils_10")
    wpt_loop_hits = search_sample_decks("Loop10 WPT MOMC FLUM", ext="mai")
    assert wpt_loop_hits
    assert wpt_loop_hits[0]["path"].startswith("application/wpt_loop_10")
    mri_loop_hits = search_sample_decks("Loop10 MRI OHM2 FREQ", ext="mai")
    assert mri_loop_hits
    assert mri_loop_hits[0]["path"].startswith("application/mri_loop_10")
    sr_loop_hits = search_sample_decks("SR-motor reluctance FLUM", ext="mai")
    assert sr_loop_hits
    assert sr_loop_hits[0]["path"].startswith("motor/sr_motor_loop_10")
    spm_loop_hits = search_sample_decks("Loop10 SPM HBRM FLUM", ext="mai")
    assert spm_loop_hits
    assert spm_loop_hits[0]["path"].startswith("motor/spm_loop_10")
    ih_hits = search_sample_decks("IH induction-heating MOMC", ext="mai")
    assert ih_hits
    assert ih_hits[0]["path"].startswith("application/ih_induction_heating_10")
    reluctance_hits = search_sample_decks("reluctance motor synchronous saliency", ext="mai")
    assert reluctance_hits
    assert reluctance_hits[0]["path"].startswith("motor/reluctance_motor_10")
    hysteresis_hits = search_sample_decks("hysteresis motor high-coercivity", ext="mai")
    assert hysteresis_hits
    assert hysteresis_hits[0]["path"].startswith("motor/hysteresis_motor_10")
    transformer_loop_hits = search_sample_decks("Loop10 transformer FLUM", ext="mai")
    assert transformer_loop_hits
    assert transformer_loop_hits[0]["path"].startswith("application/transformer_loop_10")
    accelerator_hits = search_sample_decks("accelerator electromagnet FLUM", ext="mai")
    assert accelerator_hits
    assert accelerator_hits[0]["path"].startswith("application/accelerator_magnet_10")
    pm001 = get_sample_deck("motor/pm_cosine_pickup_72/pm001/pm001.mai")
    text = pm001["text"]
    assert "USE  MAGIC" in text
    assert "HBCN 1 0 1" in text
    assert "HBCN 2 0 2" in text
    assert "FLUM  49" in text
    cards = build_sample_deck_cards(limit=486)
    assert len(cards) == 486
    spm_cards = build_sample_deck_cards(limit=20, family="spm_surface_pm_10")
    assert len(spm_cards) == 10
    assert "spm" in spm_cards[0]["tags"]
    assert "MWL8T" in spm_cards[0]["elements"]
    srm_cards = build_sample_deck_cards(limit=20, family="srm_switched_reluctance_10")
    assert len(srm_cards) == 10
    assert "srm" in srm_cards[0]["tags"]
    assert "MMB8T" in srm_cards[0]["elements"]
    induction_cards = build_sample_deck_cards(limit=20, family="induction_cage_10")
    assert len(induction_cards) == 10
    assert "induction" in induction_cards[0]["tags"]
    assert "MAB8T" in induction_cards[0]["elements"]
    transformer_cards = build_sample_deck_cards(limit=20, family="transformer_core_pickup_12")
    assert len(transformer_cards) == 12
    assert "transformer" in transformer_cards[0]["tags"]
    mri_cards = build_sample_deck_cards(limit=20, family="mri_gradient_shield_12")
    assert len(mri_cards) == 12
    assert "MAB8T" in mri_cards[0]["elements"]
    wpt_cards = build_sample_deck_cards(limit=20, family="wpt_coupled_coils_10")
    assert len(wpt_cards) == 10
    assert "wpt" in wpt_cards[0]["tags"]
    assert "MCL8T" in wpt_cards[0]["elements"]
    loop_family_checks = [
        ("application/wpt_loop_10", "wpt", "MCL8T"),
        ("application/mri_loop_10", "mri", "MAB8T"),
        ("motor/sr_motor_loop_10", "sr-motor", "MMB8T"),
        ("motor/spm_loop_10", "spm", "MWL8T"),
        ("application/ih_induction_heating_10", "ih", "MAB8T"),
        ("motor/reluctance_motor_10", "reluctance", "MMB8T"),
        ("motor/hysteresis_motor_10", "hysteresis", "MMB8T"),
        ("application/transformer_loop_10", "transformer", "MCL8T"),
        ("application/accelerator_magnet_10", "accelerator", "MMB8T"),
    ]
    for family, tag, element in loop_family_checks:
        family_cards = build_sample_deck_cards(limit=20, family=family)
        assert len(family_cards) == 10
        assert tag in family_cards[0]["tags"]
        assert element in family_cards[0]["elements"]
    team28 = build_team28_cards()
    assert len(team28) == 28
    team28_text = format_team28_cards(team28)
    assert "Python-interface seed manifest" in team28_text
    assert "normal ELF GUI/CLI" in team28_text
    assert "outside this documentation MCP server" in team28_text
    assert "pm_square_2pole_pickup_100" in team28_text
    combined = "\n".join(get_sample_deck(d["path"])["text"] for d in decks)
    forbidden = ("C:" + "\\temp", "S:" + "\\", "_cross" + "val", ".mag", ".mao", ".mat", ".mac")
    assert not any(token in combined for token in forbidden)


def test_public_policy_lint_passes():
    from pathlib import Path

    from elf_mcp_server.policy_lint import run_policy_lint

    repo = Path(__file__).resolve().parents[1]
    assert run_policy_lint(repo) == []


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
    assert "S:" + "\\" not in doc
    assert "C:" + "\\temp" not in doc
    assert "_cross" + "val" not in doc


def test_recipe_tools_public_safe():
    from elf_mcp_server.recipes import (
        list_recipes,
        search_recipes,
        get_recipe,
        format_recipe,
        plan_workflow,
    )
    recipes = list_recipes(tag="motor")
    assert any(r.name == "passive_flum_pickup" for r in recipes)
    assert any(r.name == "maxwell_torque_surface" for r in recipes)
    matches = search_recipes("back EMF pickup", top_k=3)
    assert matches
    assert matches[0][1].name == "passive_flum_pickup"
    recipe = get_recipe("mutual_flux_current_pickup")
    text = format_recipe(recipe)
    plan = plan_workflow("cogging torque sweep")
    combined = text + plan
    assert "FLUM <pickup_mid>" in combined
    assert "maxwell_torque_surface" in combined
    assert "C:\\" not in combined
    assert "_cross" + "val" not in combined
