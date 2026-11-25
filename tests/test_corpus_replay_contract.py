import copy
import json

from elf_mcp_server.corpus_replay_contract import corpus_replay_contract_gate
from elf_mcp_server.server import elf_product_corpus_replay_contract_gate


def _summary() -> dict:
    return {
        "schema": "cae-ai-lab.elf-magic-product-corpus-adjudication.v1",
        "private": True,
        "public_boundary": {
            "contains_solved_values": False,
            "contains_source_text": False,
            "contains_local_paths": False,
        },
        "execution_version": {
            "runner_sha256": "a" * 64,
            "observed_solver_versions": ["10.0.0", "13.0.0", "16.0.0"],
            "executable_fingerprints": {
                name: {"sha256": str(index) * 64, "size_bytes": 100 + index}
                for index, name in enumerate(
                    ("BEAM", "ELFIN", "MAGIC", "MESH"), start=1
                )
            },
        },
        "inventory": {
            "case_count": 4,
            "runnable_case_count": 3,
            "expected_reject_count": 1,
            "source_physics_role_counts": {
                "charged_particle_trajectory": 1,
                "electrostatic_charge_and_field": 1,
                "magnetic_field_induction_and_force": 2,
            },
            "successor_route_counts": {
                "radia_field_to_xsuite": 1,
                "ngsolve_electrostatics_bem": 1,
                "radia_magnetic_lane": 2,
            },
        },
        "live_replay": {
            "runnable_pass_count": 3,
            "runnable_fail_count": 0,
            "unexpected_failures": [],
            "timeout_cases": [],
            "stale_output_cases": [],
            "known_interaction_repairs": [
                {
                    "case_id": "case-a",
                    "repairs": [
                        "ELF-Q(718): insert EMGO in isolated replay copy"
                    ],
                },
                {
                    "case_id": "case-b",
                    "repairs": [
                        "ELF-Q(719): insert CLGO in isolated replay copy"
                    ],
                },
            ],
        },
        "expected_reject": {
            "classification": "non_runnable_pipeline_intermediate",
            "pass": True,
        },
        "replacement_scope": {
            "source_product_corpus_replay_complete": True,
            "same_identity_radia_replay_complete": False,
            "research_lab_retirement_ready": False,
            "product_or_market_retirement_claim": False,
        },
    }


def test_corpus_contract_accepts_complete_replay_and_expected_reject():
    payload = _summary()
    result = corpus_replay_contract_gate(json.dumps(payload))
    dispatched = json.loads(elf_product_corpus_replay_contract_gate(json.dumps(payload)))

    assert result["status"] == "ok"
    assert result["source_product_corpus_replay_complete"] is True
    assert result["research_lab_retirement_ready"] is False
    assert dispatched["status"] == "ok"


def test_corpus_contract_rejects_stale_or_failed_runs():
    payload = _summary()
    payload["live_replay"]["runnable_pass_count"] = 2
    payload["live_replay"]["runnable_fail_count"] = 1
    payload["live_replay"]["unexpected_failures"] = ["case-c"]
    payload["live_replay"]["stale_output_cases"] = ["case-c"]

    result = corpus_replay_contract_gate(json.dumps(payload))

    assert result["status"] == "needs_attention"
    assert result["checks"]["all_runnable_cases_pass"] is False
    assert result["checks"]["outputs_are_fresh_and_bounded"] is False


def test_corpus_contract_rejects_unknown_automatic_repair():
    payload = copy.deepcopy(_summary())
    payload["live_replay"]["known_interaction_repairs"][0]["repairs"] = [
        "unknown automatic patch"
    ]

    result = corpus_replay_contract_gate(json.dumps(payload))

    assert result["status"] == "needs_attention"
    assert result["checks"]["known_interactive_repairs_are_allowlisted"] is False


def test_corpus_contract_rejects_solved_values_or_retirement_overclaim():
    payload = _summary()
    payload["public_boundary"]["contains_solved_values"] = True
    payload["replacement_scope"]["research_lab_retirement_ready"] = True

    result = corpus_replay_contract_gate(json.dumps(payload))

    assert result["status"] == "needs_attention"
    assert result["checks"]["public_boundary_is_value_text_and_path_free"] is False
    assert result["checks"]["source_replay_does_not_overclaim_replacement"] is False


def test_corpus_contract_rejects_electrostatics_misrouted_as_eddy_current():
    payload = _summary()
    routes = payload["inventory"]["successor_route_counts"]
    routes.pop("ngsolve_electrostatics_bem")
    routes["hcurl_eddy_bubble_cln"] = 1

    result = corpus_replay_contract_gate(json.dumps(payload))

    assert result["status"] == "needs_attention"
    assert result["checks"]["electrostatic_successor_route_is_not_eddy_current"] is False
