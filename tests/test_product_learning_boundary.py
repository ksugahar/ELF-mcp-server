"""Product releases exclude the laboratory's external learning corpus."""
from pathlib import Path

from elf_mcp_server.sample_decks import SAMPLE_ROUTE_RULES, load_sample_decks


def test_product_samples_and_routes_exclude_external_learning_corpus():
    forbidden = "emd" + "lab"
    decks = load_sample_decks()
    assert all(forbidden not in path.lower() for path in decks)
    families = {deck.family for deck in decks.values()}
    assert all(rule['family'] in families for rule in SAMPLE_ROUTE_RULES)
    assert all(forbidden not in str(rule).lower() for rule in SAMPLE_ROUTE_RULES)


def test_public_boundary_check_rejects_external_learning_marker():
    from elf_mcp_server.policy_lint import PRIVATE_MARKERS
    assert "EMD" + "LAB" in PRIVATE_MARKERS
    assert "emd" + "lab" in PRIVATE_MARKERS


def test_public_readme_matches_retained_corpus():
    root = Path(__file__).resolve().parents[1]
    text = (root / 'README.md').read_text(encoding='utf-8')
    assert '1360 cases, 2720 input files' in text
    assert 'emd' + 'lab' not in text.lower()
