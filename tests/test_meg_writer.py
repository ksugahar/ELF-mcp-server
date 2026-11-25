from __future__ import annotations

from pathlib import Path

import pytest

from elf_mcp_server import meg_writer as mw

SAMPLES = Path(mw.__file__).parent / "public_samples"

CUBE = {
    1: (0, 0, 0), 2: (1, 0, 0), 3: (1, 1, 0), 4: (0, 1, 0),
    5: (0, 0, 1), 6: (1, 0, 1), 7: (1, 1, 1), 8: (0, 1, 1), 9: (0.5, 0.5, 2),
}


def test_hex_and_pyramid_3d():
    mesh = mw.blocks_to_mesh(CUBE, [
        mw.MegBlock("MMB", "hex8", [(1, 2, 3, 4, 5, 6, 7, 8)], 1),
        mw.MegBlock("MCO", "pyramid5", [(5, 6, 7, 8, 9)], 2),
    ])
    assert [e.label for e in mesh.elements] == ["MMB8T", "MCO8T"]
    assert mesh.elements[1].nodes == (5, 6, 7, 8, 9, 9, 9, 9)
    text = mw.format_meg(mesh)
    assert "* ELEMENT T" in text and text.startswith("BOOK  MEP  3.50\n")
    assert "0.0000000000000E+00" in text            # 14-digit coordinates
    assert mw.parse_meg(text) == mesh


def test_2d_and_axisymmetric_planes():
    plane = {1: (0, 0, 0), 2: (1, 0, 0), 3: (0, 1, 0)}
    mesh = mw.blocks_to_mesh(plane, [mw.MegBlock("MMB", "tri3", [(1, 2, 3)])], "K")
    assert mesh.elements[0].label == "MMB3K"
    assert "* ELEMENT K" in mw.format_meg(mesh)
    rz = {1: (1, 0, 0), 2: (2, 0, 0), 3: (1, 0, 1)}
    mesh = mw.blocks_to_mesh(rz, [mw.MegBlock("MMB", "tri3", [(1, 2, 3)])], "R")
    assert mesh.elements[0].label == "MMB3R"
    with pytest.raises(mw.MegError, match="z = 0"):
        mw.blocks_to_mesh(CUBE, [], "K")
    with pytest.raises(mw.MegError, match="y = 0"):
        mw.blocks_to_mesh(plane | {4: (0, 1, 0)}, [], "R")


@pytest.mark.parametrize("blocks,dim,msg", [
    ([mw.MegBlock("XYZ", "hex8", [(1, 2, 3, 4, 5, 6, 7, 8)])], "T", "not valid"),
    ([mw.MegBlock("MMS", "tri3", [(1, 2, 3)])], "K", "not valid"),
    ([mw.MegBlock("MMB", "hex8", [(1, 2, 3)])], "T", "needs 8"),
    ([mw.MegBlock("MMB", "tri3", [(1, 2, 99)])], "T", "missing nodes"),
])
def test_rejects_bad_input(blocks, dim, msg):
    nodes = CUBE if dim == "T" else {1: (0, 0, 0), 2: (1, 0, 0), 3: (0, 1, 0)}
    with pytest.raises(mw.MegError, match=msg):
        mw.blocks_to_mesh(nodes, blocks, dim)


def test_pyramid_rejected_in_2d():
    plane = {i: (i, 0, 0) for i in range(1, 6)}
    with pytest.raises(mw.MegError, match="only in 3D"):
        mw.blocks_to_mesh(plane, [mw.MegBlock("MMB", "pyramid5", [(1, 2, 3, 4, 5)])], "K")


def test_prefix_from_block_name_has_no_default():
    assert mw.prefix_from_block_name("mmb_core") == "MMB"
    assert mw.prefix_from_block_name("air") is None


def test_write_refuses_overwrite(tmp_path):
    mesh = mw.blocks_to_mesh(CUBE, [mw.MegBlock("MMB", "hex8", [(1, 2, 3, 4, 5, 6, 7, 8)])])
    path = mw.write_meg(mesh, tmp_path / "a.meg")
    with pytest.raises(mw.MegError, match="exists"):
        mw.write_meg(mesh, path)
    mw.write_meg(mesh, path, overwrite=True)
    assert mw.read_meg(path) == mesh


def test_space_nodes_become_mgr2():
    mesh = mw.blocks_to_mesh(CUBE, [], space_nodes=[(0, 0, 0), (1, 2, 3)])
    text = mw.format_meg(mesh)
    assert text.count("MGR2") == 2
    assert mw.parse_meg(text).space_nodes == mesh.space_nodes


def test_public_sample_decks_round_trip():
    files = sorted(SAMPLES.rglob("*.meg"))
    assert files, "public sample decks are missing"
    for f in files:
        mesh = mw.read_meg(f)
        assert mw.parse_meg(mw.format_meg(mesh)) == mesh, f


def test_mcp_tool_writes_and_reports_errors(tmp_path):
    import json

    from elf_mcp_server.handlers import elf_meg_write

    nodes = {str(k): list(v) for k, v in CUBE.items()}
    blocks = [{"prefix": "mmb", "shape": "hex8",
               "connectivity": [[1, 2, 3, 4, 5, 6, 7, 8]]}]
    dry = json.loads(elf_meg_write(nodes, blocks))
    assert dry["ok"] and dry["labels"] == ["MMB8T"] and dry["written"] is None
    out = tmp_path / "m.meg"
    res = json.loads(elf_meg_write(nodes, blocks, out_path=str(out)))
    assert res["written"] and out.is_file()
    again = json.loads(elf_meg_write(nodes, blocks, out_path=str(out)))
    assert not again["ok"] and "exists" in again["error"]
    bad = json.loads(elf_meg_write(nodes, [{"prefix": "ZZZ", "shape": "hex8",
                                            "connectivity": []}]))
    assert not bad["ok"]
    assert not json.loads(elf_meg_write(nodes, blocks, out_path=str(tmp_path / "x.txt")))["ok"]


class _StubCubit:
    """Minimal stand-in for the cubit module (no licensed Cubit needed)."""

    def __init__(self):
        self.names = {1: "MMB_core", 2: "air", 3: "MCO_coil"}
        self.xyz = {k: tuple(map(float, v)) for k, v in CUBE.items()}
        self.xyz[10] = (5.0, 5.0, 5.0)

    def get_block_id_list(self): return [1, 2, 3]
    def get_block_name(self, b): return self.names[b]
    def get_block_hexes(self, b): return [1] if b == 1 else []
    def get_block_pyramids(self, b): return [7] if b == 3 else []
    def get_connectivity(self, t, i):
        return (1, 2, 3, 4, 5, 6, 7, 8) if t == "hex" else (5, 6, 7, 8, 9)
    def get_nodal_coordinates(self, n): return self.xyz[n]
    def get_nodeset_id_list(self): return [1]
    def get_nodeset_name(self, n): return "space_pts"
    def get_nodeset_nodes_inclusive(self, n): return [10]


def test_cubit_adapter_with_stub(tmp_path):
    from elf_mcp_server import cubit_to_meg as c2m

    with pytest.raises(mw.MegError, match="2:'air'"):
        c2m.mesh_from_cubit(_StubCubit())
    mesh = c2m.mesh_from_cubit(_StubCubit(), labels={2: None})
    assert [e.label for e in mesh.elements] == ["MMB8T", "MCO8T"]
    assert [e.mid for e in mesh.elements] == [1, 3]
    assert mesh.space_nodes == {1: (5.0, 5.0, 5.0)}
    out = c2m.export_meg_from_cubit(_StubCubit(), tmp_path / "c.meg", labels={2: None})
    assert mw.read_meg(out) == mesh


def test_export_from_file_uses_injected_cubit(tmp_path):
    from elf_mcp_server import cubit_to_meg as c2m

    stub = _StubCubit()
    cmds = []
    stub.cmd = cmds.append
    out = c2m.export_meg_from_file("m.cub5", tmp_path / "f.meg", labels={2: None}, cubit=stub)
    assert cmds == ['open "m.cub5"'] and out.is_file()
    assert c2m._parse_labels("1:mmb,2:none") == {1: "MMB", 2: None}
    with pytest.raises(mw.MegError, match="not found"):
        c2m.load_cubit(str(tmp_path / "nope"))
