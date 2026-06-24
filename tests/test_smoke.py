# -*- coding: utf-8 -*-
"""Smoke tests for the public ELF doc-server (ELF-mcp-server).

Minimal guards for a public package: the server imports, the four bundled
vendor-doc dumps load, the tool surface is the expected size, and the removed
work-examples family stays OUT (publish-boundary regression guard).
"""
import os
import sys
import asyncio
import json
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
    assert len(names) >= 25
    assert "elf_examples_playbook" in names
    assert "elf_recipe_search" in names
    assert "elf_recipe_get" in names
    assert "elf_plan_workflow" in names
    assert "elf_sample_decks_index" in names
    assert "elf_sample_decks_get" in names
    assert "elf_sample_decks_route" in names
    assert "elf_sample_decks_playbook" in names
    assert "elf_sample_decks_validation" in names
    assert "elf_sample_decks_representatives" in names
    assert "elf_sample_decks_quality" in names
    assert "elf_sample_decks_physics" in names
    assert "elf_sample_decks_validation_matrix" in names
    assert "elf_sample_decks_observable_contracts" in names
    assert "elf_sample_decks_cross_validation" in names
    assert "elf_public_promotion" in names
    assert "elf_python_team28" in names
    overview = elf_overview()
    overview_text = str(overview)
    assert overview["n_tools"] == 33
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
        build_publication_batch_summary,
        build_cross_validation_summary,
        build_quality_summary,
        build_observable_contract_summary,
        build_physical_quantity_summary,
        build_validation_matrix,
        build_representative_cards,
        build_team28_cards,
        build_validation_summary,
        format_public_promotion,
        format_cross_validation_summary,
        format_observable_contract_summary,
        format_physical_quantity_summary,
        format_quality_summary,
        format_validation_matrix,
        format_representative_cards,
        format_validation_summary,
        format_team28_cards,
        list_sample_decks,
        route_sample_decks,
        format_sample_deck_routes,
        search_sample_decks,
        get_sample_deck,
    )
    decks = list_sample_decks()
    assert len(decks) == 3200
    assert sum(1 for d in decks if d["ext"] == "mai") == 1600
    assert sum(1 for d in decks if d["ext"] == "meg") == 1600
    assert any(d["path"] == "application/motor/pm_cosine_pickup_72/pm001/pm001.mai" for d in decks)
    assert any(d["path"] == "application/motor/spm_surface_pm_10/spm001/spm001.mai" for d in decks)
    assert any(d["path"] == "application/motor/srm_switched_reluctance_10/srm001/srm001.mai" for d in decks)
    assert any(d["path"] == "application/motor/induction_cage_10/im001/im001.mai" for d in decks)
    assert any(d["path"] == "application/motor/emdlab_bldc_spm_10/ebl001/ebl001.mai" for d in decks)
    assert any(d["path"] == "application/motor/emdlab_ipm_hairpin_10/eip001/eip001.mai" for d in decks)
    assert any(d["path"] == "application/motor/emdlab_induction_bar_10/eim001/eim001.mai" for d in decks)
    assert any(d["path"] == "application/motor/emdlab_synrm_flux_barrier_10/esr001/esr001.mai" for d in decks)
    assert any(d["path"] == "application/motor/emdlab_srm_pole_variants_10/esm001/esm001.mai" for d in decks)
    assert any(d["path"] == "application/motor/emdlab_afpm_linearized_10/eaf001/eaf001.mai" for d in decks)
    assert any(d["path"] == "application/motor/emdlab_bldc_outer_rotor_10/ebo001/ebo001.mai" for d in decks)
    assert any(d["path"] == "application/motor/emdlab_induction_fraction_10/eif001/eif001.mai" for d in decks)
    assert any(d["path"] == "application/motor/emdlab_spmsm_static_torque_10/eptq001/eptq001.mai" for d in decks)
    assert any(d["path"] == "application/motor/emdlab_srm1216_outer_rotor_10/ero001/ero001.mai" for d in decks)
    assert any(d["path"] == "application/motor/emdlab_synrm_fraction_static_torque_10/eyf001/eyf001.mai" for d in decks)
    assert any(
        d["path"] == "application/emdlab_1ph_transformer_static_10/ept001/ept001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/emdlab_benchmark_ccore_10/ecc001/ecc001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/numeric_validation_anchors_10/nva001/nva001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/numeric_flum_law_64/nfl001/nfl001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/numeric_inductance_energy_100/nie001/nie001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/numeric_force_torque_100/nft001/nft001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/numeric_ac_loss_100/nal001/nal001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/numeric_magnetic_circuit_100/nmc001/nmc001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/numeric_permanent_magnet_100/npm001/npm001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/numeric_transformer_coupling_100/ntc001/ntc001.mai"
        for d in decks
    )
    assert any(d["path"] == "application/motor/ipm_interior_pm_10/ipm001/ipm001.mai" for d in decks)
    assert any(d["path"] == "application/motor/wound_field_sync_10/wfs001/wfs001.mai" for d in decks)
    assert any(d["path"] == "application/motor/axial_flux_pm_10/afm001/afm001.mai" for d in decks)
    assert any(d["path"] == "application/motor/linear_pm_motor_10/lpm001/lpm001.mai" for d in decks)
    assert any(d["path"] == "application/motor/stepper_motor_10/stm001/stm001.mai" for d in decks)
    assert any(d["path"] == "application/wpt_loop_10/wpl001/wpl001.mai" for d in decks)
    assert any(d["path"] == "application/mri_loop_10/mrl001/mrl001.mai" for d in decks)
    assert any(d["path"] == "application/motor/sr_motor_loop_10/srl001/srl001.mai" for d in decks)
    assert any(d["path"] == "application/motor/spm_loop_10/spl001/spl001.mai" for d in decks)
    assert any(
        d["path"] == "application/ih_induction_heating_10/ihl001/ihl001.mai"
        for d in decks
    )
    assert any(d["path"] == "application/motor/reluctance_motor_10/ryl001/ryl001.mai" for d in decks)
    assert any(d["path"] == "application/motor/hysteresis_motor_10/hyl001/hyl001.mai" for d in decks)
    assert any(
        d["path"] == "application/transformer_loop_10/tfl001/tfl001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/accelerator_magnet_10/acl001/acl001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/actuator_plunger_10/atl001/atl001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/maglev_bearing_10/mvl001/mvl001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/magnetic_separator_10/msl001/msl001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/eddy_current_brake_10/ebl001/ebl001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/ndt_eddy_probe_10/ndl001/ndl001.mai"
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
    assert any(
        d["path"] == "application/magnetic_gear_10/mgl001/mgl001.mai"
        for d in decks
    )
    assert any(d["path"] == "application/voice_coil_10/vcl001/vcl001.mai" for d in decks)
    assert any(
        d["path"] == "application/relay_solenoid_10/rsl001/rsl001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/hall_sensor_fixture_10/hsl001/hsl001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/electromagnetic_clutch_10/ecl001/ecl001.mai"
        for d in decks
    )
    assert any(d["path"] == "application/wpt_misalignment_10/wpm001/wpm001.mai" for d in decks)
    assert any(
        d["path"] == "application/mri_gradient_sequence_10/mgs001/mgs001.mai"
        for d in decks
    )
    assert any(
        d["path"] == "application/transformer_leakage_10/tlg001/tlg001.mai"
        for d in decks
    )
    assert any(d["path"] == "application/ih_susceptor_ring_10/ihr001/ihr001.mai" for d in decks)
    assert any(
        d["path"] == "application/accelerator_corrector_10/acm001/acm001.mai"
        for d in decks
    )
    manifest_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "src",
        "elf_mcp_server",
        "public_samples",
        "VALIDATED_MANIFEST.json",
    )
    with open(manifest_path, encoding="ascii") as f:
        manifest = json.load(f)
    assert manifest["total_cases"] == 1600
    assert manifest["total_input_files"] == 3200
    assert len(manifest["families"]) == 72
    assert all(v["validation"] == "passed" for v in manifest["families"].values())
    assert all(v["validation_level"] for v in manifest["families"].values())
    levels = {v["validation_level"] for v in manifest["families"].values()}
    assert levels == {"ngsolve_proxy_energy", "ngsolve_numeric_invariant"}
    assert "ngsolve_proxy_energy_positive" in manifest["families"][
        "application/motor/emdlab_ipm_hairpin_10"
    ]["checks"]
    assert "ngsolve_proxy_energy_positive" in manifest["families"][
        "application/emdlab_benchmark_ccore_10"
    ]["checks"]
    assert "ngsolve_proxy_energy_positive" in manifest["families"][
        "application/motor/wound_field_sync_10"
    ]["checks"]
    numeric_manifest = manifest["families"]["application/numeric_validation_anchors_10"]
    assert numeric_manifest["validation_level"] == "ngsolve_numeric_invariant"
    assert "elf_flux_invariants_passed" in numeric_manifest["checks"]
    assert "ngsolve_numeric_invariants_passed" in numeric_manifest["checks"]
    flum_law_manifest = manifest["families"]["application/numeric_flum_law_64"]
    assert flum_law_manifest["cases"] == 64
    assert flum_law_manifest["validation_level"] == "ngsolve_numeric_invariant"
    assert "elf_flux_invariants_passed" in flum_law_manifest["checks"]
    assert "ngsolve_numeric_invariants_passed" in flum_law_manifest["checks"]
    inductance_manifest = manifest["families"]["application/numeric_inductance_energy_100"]
    assert inductance_manifest["cases"] == 100
    assert inductance_manifest["validation_level"] == "ngsolve_numeric_invariant"
    assert "elf_flux_invariants_passed" in inductance_manifest["checks"]
    assert "ngsolve_numeric_invariants_passed" in inductance_manifest["checks"]
    force_manifest = manifest["families"]["application/numeric_force_torque_100"]
    assert force_manifest["cases"] == 100
    assert force_manifest["validation_level"] == "ngsolve_numeric_invariant"
    assert "elf_flux_invariants_passed" in force_manifest["checks"]
    assert "ngsolve_numeric_invariants_passed" in force_manifest["checks"]
    ac_loss_manifest = manifest["families"]["application/numeric_ac_loss_100"]
    assert ac_loss_manifest["cases"] == 100
    assert ac_loss_manifest["validation_level"] == "ngsolve_numeric_invariant"
    assert "elf_flux_invariants_passed" in ac_loss_manifest["checks"]
    assert "ngsolve_numeric_invariants_passed" in ac_loss_manifest["checks"]
    magnetic_circuit_manifest = manifest["families"]["application/numeric_magnetic_circuit_100"]
    assert magnetic_circuit_manifest["cases"] == 100
    assert magnetic_circuit_manifest["validation_level"] == "ngsolve_numeric_invariant"
    assert "elf_flux_invariants_passed" in magnetic_circuit_manifest["checks"]
    assert "ngsolve_numeric_invariants_passed" in magnetic_circuit_manifest["checks"]
    permanent_magnet_manifest = manifest["families"]["application/numeric_permanent_magnet_100"]
    assert permanent_magnet_manifest["cases"] == 100
    assert permanent_magnet_manifest["validation_level"] == "ngsolve_numeric_invariant"
    assert "elf_flux_invariants_passed" in permanent_magnet_manifest["checks"]
    assert "ngsolve_numeric_invariants_passed" in permanent_magnet_manifest["checks"]
    transformer_coupling_manifest = manifest["families"]["application/numeric_transformer_coupling_100"]
    assert transformer_coupling_manifest["cases"] == 100
    assert transformer_coupling_manifest["validation_level"] == "ngsolve_numeric_invariant"
    assert "elf_flux_invariants_passed" in transformer_coupling_manifest["checks"]
    assert "ngsolve_numeric_invariants_passed" in transformer_coupling_manifest["checks"]
    validation_summary = build_validation_summary()
    assert validation_summary["total_cases"] == 1600
    assert validation_summary["total_input_files"] == 3200
    assert validation_summary["total_families"] == 72
    assert validation_summary["level_counts"]["ngsolve_proxy_energy"]["families"] == 64
    assert validation_summary["level_counts"]["ngsolve_proxy_energy"]["cases"] == 926
    assert validation_summary["level_counts"]["ngsolve_numeric_invariant"]["families"] == 8
    assert validation_summary["level_counts"]["ngsolve_numeric_invariant"]["cases"] == 674
    publication_batches = build_publication_batch_summary()
    assert publication_batches["checkpoint_size"] == 100
    assert publication_batches["total_cases"] == 1600
    assert publication_batches["total_batches"] == 16
    assert publication_batches["full_100_case_batches"] == 16
    assert publication_batches["remainder_cases"] == 0
    assert publication_batches["next_checkpoint_cases"] == 1700
    assert publication_batches["additional_cases_needed_for_next_100_case_checkpoint"] == 100
    validation_text = format_validation_summary(validation_summary)
    assert "1600 cases" in validation_text
    assert "ngsolve_proxy_energy" in validation_text
    assert "not a full absolute field/force/torque/loss agreement suite" in validation_text
    assert "100-case publication checkpoints" in validation_text
    assert "100 additional validated cases would make the next optional increment" in validation_text
    quality_summary = build_quality_summary()
    assert quality_summary["label_counts"]["gold_numeric_invariant"]["cases"] == 674
    assert quality_summary["label_counts"]["silver_observable_contract"]["cases"] == 500
    assert quality_summary["label_counts"]["silver_proxy_energy"]["cases"] == 426
    assert quality_summary["quality_gate_status"] == "PASS"
    assert all(gate["status"] == "PASS" for gate in quality_summary["quality_gates"])
    assert {gate["gate"] for gate in quality_summary["quality_gates"]} >= {
        "paired_mai_meg",
        "manifest_matches_files",
        "publication_batches_cover_cases",
        "public_boundary_text",
        "no_solver_output_files",
        "application_hierarchy",
        "observable_contract_target_is_500_cases",
        "observable_contract_markers_pass",
    }
    quality_text = format_quality_summary(quality_summary)
    assert "Publication Quality Gates (PASS)" in quality_text
    assert "paired_mai_meg" in quality_text
    assert "manifest_matches_files" in quality_text
    assert "physical_quantity_case_coverage" in quality_text
    assert "gold_physics_anchor_coverage" in quality_text
    assert "gold_numeric_invariant" in quality_text
    assert "silver_observable_contract" in quality_text
    assert "silver_proxy_energy" in quality_text
    gold_quality_text = format_quality_summary(build_quality_summary(label="gold"))
    assert "application/numeric_transformer_coupling_100" in gold_quality_text
    enhanced_quality_text = format_quality_summary(build_quality_summary(label="observable"))
    assert "500 cases" in enhanced_quality_text
    assert "application/motor/pm_square_2pole_pickup_100" in enhanced_quality_text
    observable_contract_summary = build_observable_contract_summary()
    assert observable_contract_summary["observable_contract_gate_status"] == "PASS"
    assert observable_contract_summary["enhanced_cases"] == 500
    assert observable_contract_summary["enhanced_family_count"] == 28
    assert observable_contract_summary["failed_case_count"] == 0
    observable_contract_text = format_observable_contract_summary(observable_contract_summary)
    assert "Observable Contract Gates (PASS)" in observable_contract_text
    assert "public_observable_contract_passed" in observable_contract_text
    assert "application/wpt_misalignment_10" in observable_contract_text
    physics_summary = build_physical_quantity_summary()
    assert physics_summary["physical_gate_status"] == "PASS"
    assert all(gate["status"] == "PASS" for gate in physics_summary["physical_gates"])
    assert physics_summary["quantity_counts"]["flux_linkage"]["cases"] == 1600
    assert physics_summary["quantity_counts"]["flux_linkage"]["gold_cases"] == 674
    assert physics_summary["quantity_counts"]["motor_flux_linkage"]["cases"] == 652
    assert physics_summary["quantity_counts"]["force_torque_gradient"]["gold_cases"] == 100
    assert physics_summary["quantity_counts"]["ac_loss"]["gold_cases"] == 100
    assert physics_summary["quantity_counts"]["permanent_magnet_flux"]["gold_cases"] == 100
    assert physics_summary["quantity_counts"]["transformer_coupling"]["gold_cases"] == 100
    physics_text = format_physical_quantity_summary(physics_summary)
    assert "Physical Quantity Gates (PASS)" in physics_text
    assert "flux_linkage" in physics_text
    assert "transformer_coupling" in physics_text
    force_physics = build_physical_quantity_summary(quantity="force")
    assert force_physics["quantity_counts"]["force_torque_gradient"]["gold_cases"] == 100
    assert any(
        row["family"] == "application/numeric_force_torque_100"
        for row in force_physics["families"]
    )
    cross_validation_summary = build_cross_validation_summary()
    assert cross_validation_summary["cross_validation_gate_status"] == "PASS"
    assert all(
        gate["status"] == "PASS"
        for gate in cross_validation_summary["cross_validation_gates"]
    )
    assert cross_validation_summary["gaps"]["families_without_independent_cross_validation"] == 0
    assert cross_validation_summary["gaps"]["cases_without_independent_cross_validation"] == 0
    assert cross_validation_summary["method_counts"]["ngsolve_proxy_energy_positive"]["cases"] == 926
    assert cross_validation_summary["method_counts"]["ngsolve_numeric_invariants_passed"]["cases"] == 674
    assert cross_validation_summary["method_counts"]["elf_flux_invariants_passed"]["cases"] == 674
    cross_validation_text = format_cross_validation_summary(cross_validation_summary)
    assert "Cross-Validation Gates (PASS)" in cross_validation_text
    assert "No family is missing independent NGSolve cross-validation" in cross_validation_text
    assert "Silver-To-Gold Upgrade Candidates" in cross_validation_text
    matrix_summary = build_validation_matrix()
    assert matrix_summary["validation_matrix_gate_status"] == "PASS"
    assert all(
        gate["status"] == "PASS"
        for gate in matrix_summary["validation_matrix_gates"]
    )
    assert matrix_summary["selected_family_count"] == matrix_summary["total_families"]
    assert matrix_summary["quantities"]["transformer_coupling"]["gold_cases"] == 100
    assert "ngsolve_numeric_invariants_passed" in matrix_summary["quantities"]["transformer_coupling"]["validation_methods"]
    matrix_text = format_validation_matrix(matrix_summary)
    assert "Validation Matrix Gates (PASS)" in matrix_text
    assert "transformer_coupling" in matrix_text
    assert "application/numeric_transformer_coupling_100/ntc001/ntc001.mai" in matrix_text
    transformer_matrix = build_validation_matrix(quantity="transformer", label="gold")
    assert transformer_matrix["selected_family_count"] >= 1
    assert any(
        row["family"] == "application/numeric_transformer_coupling_100"
        for row in transformer_matrix["families"]
    )
    representatives = build_representative_cards()
    assert len(representatives) >= 32
    assert representatives[0]["quality_label"] == "silver_observable_contract"
    representative_text = format_representative_cards(representatives)
    assert "why representative" in representative_text
    assert "application/motor/emdlab_ipm_hairpin_10/eip001/eip001.mai" in representative_text
    assert "application/numeric_transformer_coupling_100/ntc001/ntc001.mai" in representative_text
    motor_representatives = build_representative_cards(area="motor")
    assert any(card["family"] == "application/motor/emdlab_ipm_hairpin_10" for card in motor_representatives)
    promotion_ja = format_public_promotion("ja")
    assert "1600" in promotion_ja
    assert "品質ラベル" in promotion_ja
    assert "solver 出力" in promotion_ja
    promotion_en = format_public_promotion("en")
    assert "1600 public runnable" in promotion_en
    numeric_summary = build_validation_summary(family="numeric_validation")
    assert numeric_summary["selected_family_count"] == 1
    assert numeric_summary["families"][0]["family"] == "application/numeric_validation_anchors_10"
    numeric_text = format_validation_summary(numeric_summary)
    assert "elf_flux_invariants_passed" in numeric_text
    flum_law_summary = build_validation_summary(family="numeric_flum_law")
    assert flum_law_summary["selected_family_count"] == 1
    assert flum_law_summary["families"][0]["family"] == "application/numeric_flum_law_64"
    assert flum_law_summary["families"][0]["cases"] == 64
    inductance_summary = build_validation_summary(family="numeric_inductance_energy")
    assert inductance_summary["selected_family_count"] == 1
    assert inductance_summary["families"][0]["family"] == "application/numeric_inductance_energy_100"
    assert inductance_summary["families"][0]["cases"] == 100
    force_summary = build_validation_summary(family="numeric_force_torque")
    assert force_summary["selected_family_count"] == 1
    assert force_summary["families"][0]["family"] == "application/numeric_force_torque_100"
    assert force_summary["families"][0]["cases"] == 100
    ac_loss_summary = build_validation_summary(family="numeric_ac_loss")
    assert ac_loss_summary["selected_family_count"] == 1
    assert ac_loss_summary["families"][0]["family"] == "application/numeric_ac_loss_100"
    assert ac_loss_summary["families"][0]["cases"] == 100
    magnetic_circuit_summary = build_validation_summary(family="numeric_magnetic_circuit")
    assert magnetic_circuit_summary["selected_family_count"] == 1
    assert magnetic_circuit_summary["families"][0]["family"] == "application/numeric_magnetic_circuit_100"
    assert magnetic_circuit_summary["families"][0]["cases"] == 100
    permanent_magnet_summary = build_validation_summary(family="numeric_permanent_magnet")
    assert permanent_magnet_summary["selected_family_count"] == 1
    assert permanent_magnet_summary["families"][0]["family"] == "application/numeric_permanent_magnet_100"
    assert permanent_magnet_summary["families"][0]["cases"] == 100
    transformer_coupling_summary = build_validation_summary(family="numeric_transformer_coupling")
    assert transformer_coupling_summary["selected_family_count"] == 1
    assert transformer_coupling_summary["families"][0]["family"] == "application/numeric_transformer_coupling_100"
    assert transformer_coupling_summary["families"][0]["cases"] == 100
    hits = search_sample_decks("HBCN FLUM", ext="mai")
    assert hits
    assert hits[0]["path"].endswith(".mai")
    transformer_hits = search_sample_decks("transformer FLUM", ext="mai")
    assert transformer_hits
    assert transformer_hits[0]["path"].startswith(
        (
            "application/transformer",
            "application/emdlab_1ph_transformer_static_10",
            "application/numeric_transformer_coupling_100",
        )
    )
    transformer_coupling_hits = search_sample_decks("transformer coupling turns ratio HBCU FLUM", ext="mai")
    assert transformer_coupling_hits
    assert transformer_coupling_hits[0]["path"].startswith("application/numeric_transformer_coupling_100")
    mri_hits = search_sample_decks("MRI OHM2 FREQ", ext="mai")
    assert mri_hits
    assert mri_hits[0]["path"].startswith("application/mri")
    im_hits = search_sample_decks("induction motor cage OHM2 FLUM", top_k=20, ext="mai")
    assert im_hits
    assert any(h["path"].startswith("application/motor/induction_cage_10") for h in im_hits)
    spm_hits = search_sample_decks("SPM HBRM FLUM", top_k=20, ext="mai")
    assert spm_hits
    assert any(h["path"].startswith("application/motor/spm_surface_pm_10") for h in spm_hits)
    srm_hits = search_sample_decks("SRM reluctance FLUM", top_k=20, ext="mai")
    assert srm_hits
    assert any(h["path"].startswith("application/motor/srm_switched_reluctance_10") for h in srm_hits)
    emdlab_ipm_hits = search_sample_decks("EMDLAB-style IPM hairpin FLUM", ext="mai")
    assert emdlab_ipm_hits
    assert emdlab_ipm_hits[0]["path"].startswith("application/motor/emdlab_ipm_hairpin_10")
    emdlab_im_hits = search_sample_decks("induction-machine bar OHM2 FLUM", ext="mai")
    assert emdlab_im_hits
    assert emdlab_im_hits[0]["path"].startswith("application/motor/emdlab_induction_bar_10")
    emdlab_synrm_hits = search_sample_decks("EMDLAB-style SynRM flux-barrier FLUM", ext="mai")
    assert emdlab_synrm_hits
    assert emdlab_synrm_hits[0]["path"].startswith("application/motor/emdlab_synrm_flux_barrier_10")
    emdlab_srm_hits = search_sample_decks("EMDLAB-style SRM pole-variant FLUM", ext="mai")
    assert emdlab_srm_hits
    assert emdlab_srm_hits[0]["path"].startswith("application/motor/emdlab_srm_pole_variants_10")
    emdlab_afpm_hits = search_sample_decks("EMDLAB-style AFPM linearized-airgap FLUM", ext="mai")
    assert emdlab_afpm_hits
    assert emdlab_afpm_hits[0]["path"].startswith("application/motor/emdlab_afpm_linearized_10")
    emdlab_spmsm_static_hits = search_sample_decks("EMDLAB-style SPM static-torque FLUM", ext="mai")
    assert emdlab_spmsm_static_hits
    assert emdlab_spmsm_static_hits[0]["path"].startswith("application/motor/emdlab_spmsm_static_torque_10")
    emdlab_transformer_hits = search_sample_decks("EMDLAB-style single-phase transformer static FLUM", ext="mai")
    assert emdlab_transformer_hits
    assert emdlab_transformer_hits[0]["path"].startswith("application/emdlab_1ph_transformer_static_10")
    emdlab_ccore_hits = search_sample_decks("EMDLAB-style benchmark C-core FLUM", ext="mai")
    assert emdlab_ccore_hits
    assert emdlab_ccore_hits[0]["path"].startswith("application/emdlab_benchmark_ccore_10")
    numeric_hits = search_sample_decks("numeric validation anchor current scaling FLUM", ext="mai")
    assert numeric_hits
    assert numeric_hits[0]["path"].startswith("application/numeric_validation_anchors_10")
    flum_law_hits = search_sample_decks("FLUM law superposition", ext="mai")
    assert flum_law_hits
    assert flum_law_hits[0]["path"].startswith("application/numeric_flum_law_64")
    inductance_hits = search_sample_decks("inductance co-energy FLUM turn scaling", ext="mai")
    assert inductance_hits
    assert inductance_hits[0]["path"].startswith("application/numeric_inductance_energy_100")
    force_hits = search_sample_decks("force torque co-energy gradient", ext="mai")
    assert force_hits
    assert force_hits[0]["path"].startswith("application/numeric_force_torque_100")
    ac_loss_hits = search_sample_decks("AC loss frequency square OHM2", ext="mai")
    assert ac_loss_hits
    assert ac_loss_hits[0]["path"].startswith("application/numeric_ac_loss_100")
    magnetic_circuit_hits = search_sample_decks("magnetic circuit air gap HBCU", ext="mai")
    assert magnetic_circuit_hits
    assert magnetic_circuit_hits[0]["path"].startswith("application/numeric_magnetic_circuit_100")
    permanent_magnet_hits = search_sample_decks("permanent magnet HBRM polarity FLUM", ext="mai")
    assert permanent_magnet_hits
    assert permanent_magnet_hits[0]["path"].startswith("application/numeric_permanent_magnet_100")
    route = route_sample_decks("I want an IPM hairpin motor flux linkage deck", limit=3)
    assert route
    assert route[0]["family"] == "application/motor/emdlab_ipm_hairpin_10"
    route_text = format_sample_deck_routes(route, "IPM hairpin motor flux linkage")
    assert "elf_sample_decks_playbook" in route_text
    assert "application/motor/emdlab_ipm_hairpin_10/eip001/eip001.mai" in route_text
    wpt_route = route_sample_decks("WPT misalignment with a conducting shield", limit=2)
    assert wpt_route[0]["family"] == "application/wpt_misalignment_10"
    outer_route = route_sample_decks("BLDC outer rotor motor", limit=2)
    assert outer_route[0]["family"] == "application/motor/emdlab_bldc_outer_rotor_10"
    transformer_static_route = route_sample_decks("single phase transformer static", limit=2)
    assert transformer_static_route[0]["family"] == "application/emdlab_1ph_transformer_static_10"
    ccore_route = route_sample_decks("benchmark C-core magnet", limit=2)
    assert ccore_route[0]["family"] == "application/emdlab_benchmark_ccore_10"
    numeric_route = route_sample_decks("numeric validation anchor FLUM invariant", limit=2)
    assert numeric_route[0]["family"] == "application/numeric_validation_anchors_10"
    flum_law_route = route_sample_decks("FLUM law current linearity superposition", limit=2)
    assert flum_law_route[0]["family"] == "application/numeric_flum_law_64"
    inductance_route = route_sample_decks("inductance co-energy FLUM turn scaling", limit=2)
    assert inductance_route[0]["family"] == "application/numeric_inductance_energy_100"
    force_route = route_sample_decks("force torque co-energy gradient", limit=2)
    assert force_route[0]["family"] == "application/numeric_force_torque_100"
    ac_loss_route = route_sample_decks("AC loss frequency square OHM2", limit=2)
    assert ac_loss_route[0]["family"] == "application/numeric_ac_loss_100"
    magnetic_circuit_route = route_sample_decks("magnetic circuit air gap HBCU", limit=2)
    assert magnetic_circuit_route[0]["family"] == "application/numeric_magnetic_circuit_100"
    permanent_magnet_route = route_sample_decks("permanent magnet HBRM polarity FLUM", limit=2)
    assert permanent_magnet_route[0]["family"] == "application/numeric_permanent_magnet_100"
    transformer_coupling_route = route_sample_decks("transformer coupling turns ratio HBCU FLUM", limit=2)
    assert transformer_coupling_route[0]["family"] == "application/numeric_transformer_coupling_100"
    wound_route = route_sample_decks("wound-field synchronous motor rotor field", limit=2)
    assert wound_route[0]["family"] == "application/motor/wound_field_sync_10"
    stepper_route = route_sample_decks("stepper motor detent angle", limit=2)
    assert stepper_route[0]["family"] == "application/motor/stepper_motor_10"
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
    assert sr_loop_hits[0]["path"].startswith("application/motor/sr_motor_loop_10")
    spm_loop_hits = search_sample_decks("Loop10 SPM HBRM FLUM", ext="mai")
    assert spm_loop_hits
    assert spm_loop_hits[0]["path"].startswith("application/motor/spm_loop_10")
    ih_hits = search_sample_decks("IH induction-heating MOMC", ext="mai")
    assert ih_hits
    assert ih_hits[0]["path"].startswith("application/ih_induction_heating_10")
    reluctance_hits = search_sample_decks("reluctance motor synchronous saliency", ext="mai")
    assert reluctance_hits
    assert reluctance_hits[0]["path"].startswith("application/motor/reluctance_motor_10")
    hysteresis_hits = search_sample_decks("hysteresis motor high-coercivity", ext="mai")
    assert hysteresis_hits
    assert hysteresis_hits[0]["path"].startswith("application/motor/hysteresis_motor_10")
    transformer_loop_hits = search_sample_decks("Loop10 transformer FLUM", ext="mai")
    assert transformer_loop_hits
    assert transformer_loop_hits[0]["path"].startswith("application/transformer_loop_10")
    accelerator_hits = search_sample_decks("accelerator electromagnet FLUM", ext="mai")
    assert accelerator_hits
    assert accelerator_hits[0]["path"].startswith("application/accelerator_magnet_10")
    actuator_hits = search_sample_decks("Loop11 actuator plunger FLUM", ext="mai")
    assert actuator_hits
    assert actuator_hits[0]["path"].startswith("application/actuator_plunger_10")
    maglev_hits = search_sample_decks("Loop11 maglev bearing FLUM", ext="mai")
    assert maglev_hits
    assert maglev_hits[0]["path"].startswith("application/maglev_bearing_10")
    separator_hits = search_sample_decks("Loop11 magnetic separator FLUM", ext="mai")
    assert separator_hits
    assert separator_hits[0]["path"].startswith("application/magnetic_separator_10")
    brake_hits = search_sample_decks("Loop11 eddy-current brake OHM2", ext="mai")
    assert brake_hits
    assert brake_hits[0]["path"].startswith("application/eddy_current_brake_10")
    ndt_hits = search_sample_decks("Loop11 NDT eddy-current probe OHM2", ext="mai")
    assert ndt_hits
    assert ndt_hits[0]["path"].startswith("application/ndt_eddy_probe_10")
    gear_hits = search_sample_decks("Loop12 magnetic gear HBCN FLUM", ext="mai")
    assert gear_hits
    assert gear_hits[0]["path"].startswith("application/magnetic_gear_10")
    voice_hits = search_sample_decks("Loop12 voice-coil actuator FLUM", ext="mai")
    assert voice_hits
    assert voice_hits[0]["path"].startswith("application/voice_coil_10")
    relay_hits = search_sample_decks("Loop12 relay solenoid FLUM", ext="mai")
    assert relay_hits
    assert relay_hits[0]["path"].startswith("application/relay_solenoid_10")
    hall_hits = search_sample_decks("Loop12 Hall-sensor fixture FLUM", ext="mai")
    assert hall_hits
    assert hall_hits[0]["path"].startswith("application/hall_sensor_fixture_10")
    clutch_hits = search_sample_decks("Loop12 electromagnetic clutch OHM2", ext="mai")
    assert clutch_hits
    assert clutch_hits[0]["path"].startswith("application/electromagnetic_clutch_10")
    pm001 = get_sample_deck("application/motor/pm_cosine_pickup_72/pm001/pm001.mai")
    pm001_legacy = get_sample_deck("motor/pm_cosine_pickup_72/pm001/pm001.mai")
    assert pm001_legacy["path"] == "application/motor/pm_cosine_pickup_72/pm001/pm001.mai"
    text = pm001["text"]
    assert "USE  MAGIC" in text
    assert "HBCN 1 0 1" in text
    assert "HBCN 2 0 2" in text
    assert "FLUM  49" in text
    cards = build_sample_deck_cards(limit=1600)
    assert len(cards) == 1600
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
        ("application/motor/sr_motor_loop_10", "sr-motor", "MMB8T"),
        ("application/motor/spm_loop_10", "spm", "MWL8T"),
        ("application/ih_induction_heating_10", "ih", "MAB8T"),
        ("application/motor/reluctance_motor_10", "reluctance", "MMB8T"),
        ("application/motor/hysteresis_motor_10", "hysteresis", "MMB8T"),
        ("application/transformer_loop_10", "transformer", "MCL8T"),
        ("application/accelerator_magnet_10", "accelerator", "MMB8T"),
        ("application/actuator_plunger_10", "actuator", "MMB8T"),
        ("application/maglev_bearing_10", "maglev", "MMB8T"),
        ("application/magnetic_separator_10", "separator", "MWL8T"),
        ("application/eddy_current_brake_10", "brake", "MAB8T"),
        ("application/ndt_eddy_probe_10", "ndt", "MAB8T"),
        ("application/magnetic_gear_10", "magnetic-gear", "MWL8T"),
        ("application/voice_coil_10", "voice-coil", "MCL8T"),
        ("application/relay_solenoid_10", "relay", "MMB8T"),
        ("application/hall_sensor_fixture_10", "hall-sensor", "MWL8T"),
        ("application/electromagnetic_clutch_10", "clutch", "MAB8T"),
        ("application/motor/emdlab_bldc_spm_10", "bldc", "MWL8T"),
        ("application/motor/emdlab_ipm_hairpin_10", "ipm", "MWL8T"),
        ("application/motor/emdlab_induction_bar_10", "rotor-bar", "MAB8T"),
        ("application/motor/emdlab_synrm_flux_barrier_10", "synrm", "MMB8T"),
        ("application/motor/emdlab_srm_pole_variants_10", "pole-variant", "MMB8T"),
        ("application/motor/emdlab_afpm_linearized_10", "afpm", "MWL8T"),
        ("application/motor/emdlab_bldc_outer_rotor_10", "outer-rotor", "MWL8T"),
        ("application/motor/emdlab_spmsm_static_torque_10", "static-torque", "MWL8T"),
        ("application/motor/emdlab_srm1216_outer_rotor_10", "12-16", "MMB8T"),
        ("application/motor/emdlab_synrm_fraction_static_torque_10", "fractional-sector", "MMB8T"),
        ("application/emdlab_1ph_transformer_static_10", "single-phase", "MMB8T"),
        ("application/emdlab_benchmark_ccore_10", "c-core", "MMB8T"),
        ("application/motor/ipm_interior_pm_10", "ipm", "MWL8T"),
        ("application/motor/wound_field_sync_10", "wound-field", "MCL8T"),
        ("application/motor/axial_flux_pm_10", "afpm", "MWL8T"),
        ("application/motor/linear_pm_motor_10", "linear-pm", "MWL8T"),
        ("application/motor/stepper_motor_10", "stepper", "MWL8T"),
        ("application/wpt_misalignment_10", "misalignment", "MAB8T"),
        ("application/mri_gradient_sequence_10", "gradient-sequence", "MAB8T"),
        ("application/transformer_leakage_10", "leakage", "MMB8T"),
        ("application/ih_susceptor_ring_10", "susceptor", "MAB8T"),
        ("application/accelerator_corrector_10", "corrector", "MMB8T"),
        ("application/numeric_validation_anchors_10", "numeric-validation", "MCL8T"),
        ("application/numeric_flum_law_64", "flum-law", "MCL8T"),
        ("application/numeric_inductance_energy_100", "inductance", "MCL8T"),
        ("application/numeric_force_torque_100", "force", "MCL8T"),
        ("application/numeric_ac_loss_100", "ac-loss", "MAB8T"),
        ("application/numeric_magnetic_circuit_100", "magnetic-circuit", "MMB8T"),
        ("application/numeric_permanent_magnet_100", "permanent-magnet", "MWL8T"),
        ("application/numeric_transformer_coupling_100", "transformer-coupling", "MMB8T"),
    ]
    expected_family_lengths = {
        "application/numeric_flum_law_64": 64,
        "application/numeric_inductance_energy_100": 100,
        "application/numeric_force_torque_100": 100,
        "application/numeric_ac_loss_100": 100,
        "application/numeric_magnetic_circuit_100": 100,
        "application/numeric_permanent_magnet_100": 100,
        "application/numeric_transformer_coupling_100": 100,
    }
    for family, tag, element in loop_family_checks:
        family_cards = build_sample_deck_cards(limit=120, family=family)
        expected_len = expected_family_lengths.get(family, 10)
        assert len(family_cards) == expected_len
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
