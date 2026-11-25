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


def test_tetrahedra_are_refused_for_hex_wedge_only_labels():
    """MAGIC rejects MMB4T (ELF-Q(540)) and degenerate-hex tets (ELF-Q(692)); MMB6T wedges are fine."""
    tet = {1: (0, 0, 0), 2: (1, 0, 0), 3: (0, 1, 0), 4: (0, 0, 1)}
    with pytest.raises(mw.MegError, match="MMB has no tetrahedral element"):
        mw.blocks_to_mesh(tet, [mw.MegBlock("MMB", "tet4", [(1, 2, 3, 4)])], "T")
    mw.blocks_to_mesh(tet, [mw.MegBlock("MCO", "tet4", [(1, 2, 3, 4)])], "T")   # MCO4T exists
    wedge = dict(tet) | {5: (1, 0, 1), 6: (0, 1, 1)}
    mw.blocks_to_mesh(wedge, [mw.MegBlock("MMB", "wedge6", [(1, 2, 3, 4, 5, 6)])], "T")


def test_plane_noise_is_snapped_to_exact_zero():
    """MAGIC refuses axisymmetric elements off X-Z by even 3e-16 (ELF-Q(661)); write exact zeros."""
    rz = {1: (1.0, 3.06e-16, 0.0), 2: (-1e-14, -3e-16, 1.0), 3: (2.0, 0.0, 1.0)}
    mesh = mw.blocks_to_mesh(rz, [mw.MegBlock("MMB", "tri3", [(1, 2, 3)])], "R")
    assert all(p[1] == 0.0 and p[0] >= 0.0 for p in mesh.nodes.values())
    flat = {1: (0.0, 0.0, 1e-15), 2: (1.0, 0.0, -1e-15), 3: (0.0, 1.0, 0.0)}
    mesh = mw.blocks_to_mesh(flat, [mw.MegBlock("MMB", "tri3", [(1, 2, 3)])], "K")
    assert all(p[2] == 0.0 for p in mesh.nodes.values())


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


# ----------------------------------------------------------------------
# MCL8T current direction = node 1 -> node 5
# ----------------------------------------------------------------------
_PUBLIC_ORDER = (1, 2, 3, 4, 5, 6, 7, 8)      # nft001: node 1 -> 5 is +z
_CUBIT_ORDER = (4, 7, 8, 3, 1, 6, 5, 2)       # Cubit export of the same cube: 1 -> 5 is +x


# Node numbering as exported by Cubit for the same cube (mm, centred).
_CUBIT_NODES = {1: (1, -1, 1), 2: (1, 1, 1), 3: (-1, 1, 1), 4: (-1, -1, 1),
                5: (1, 1, -1), 6: (1, -1, -1), 7: (-1, -1, -1), 8: (-1, 1, -1)}
_PUBLIC_NODES = {k: tuple(2.0 * (float(x) - 0.5) for x in v) for k, v in CUBE.items() if k <= 8}


def _coil_mesh(order, mid=10):
    nodes = _CUBIT_NODES if tuple(order) == _CUBIT_ORDER else _PUBLIC_NODES
    blk = mw.MegBlock("MCL", "hex8", [list(order)], mid)
    return mw.blocks_to_mesh({k: tuple(map(float, v)) for k, v in nodes.items()}, [blk], "T")


def _corners(mesh):
    return [mesh.nodes[n] for n in mesh.elements[0].nodes]


def _triple(mesh):
    e = mesh.elements[0]
    a, b, c = mw._hex_axes(mesh, e)
    return mw._dot(mw._cross(a, b), c) if hasattr(mw, "_cross") else (
        a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0])
        + a[2] * (b[0] * c[1] - b[1] * c[0]))


def test_public_nft001_coils_run_along_z():
    rep = mw.coil_report(mw.read_meg(
        SAMPLES / "application" / "numeric_force_torque_100" / "nft001" / "nft001.meg"))
    for mid in (10, 11):
        assert rep[mid]["direction"] == pytest.approx((0, 0, 1), abs=1e-12)


def test_coil_direction_follows_node_order():
    z = mw.coil_report(_coil_mesh(_PUBLIC_ORDER))[10]["direction"]
    x = mw.coil_report(_coil_mesh(_CUBIT_ORDER))[10]["direction"]
    assert z == pytest.approx((0, 0, 1)) and x == pytest.approx((1, 0, 0))


def test_check_coil_directions_names_the_mismatch():
    m = _coil_mesh(_CUBIT_ORDER)
    mw.check_coil_directions(m, {10: (1, 0, 0)})
    with pytest.raises(mw.MegError, match="not along the requested axis"):
        mw.check_coil_directions(m, {10: (0, 0, 1)})
    with pytest.raises(mw.MegError, match="reversed"):
        mw.check_coil_directions(m, {10: (-1, 0, 0)})
    with pytest.raises(mw.MegError, match="no MCL8T elements with MID"):
        mw.check_coil_directions(m, {99: (1, 0, 0)})


def test_twisted_coil_is_rejected():
    nodes = {k: tuple(float(x) for x in v) for k, v in CUBE.items() if k <= 8}
    mesh = mw.blocks_to_mesh(nodes, [mw.MegBlock("MCL", "hex8", [[1, 2, 3, 4, 7, 8, 5, 6]], 1)], "T")
    with pytest.raises(mw.MegError, match="twisted"):
        mw.check_coil_directions(mesh)


@pytest.mark.parametrize("order", [_PUBLIC_ORDER, _CUBIT_ORDER])
@pytest.mark.parametrize("axis", [(0, 0, 1), (1, 0, 0), (0, 1, 0), (0, 0, -1), (-1, 0, 0), (0, -1, 0)])
def test_orient_coil_current_reaches_every_axis_without_mirroring(order, axis):
    src = _coil_mesh(order)
    out = mw.orient_coil_current(src, {10: axis})
    mw.check_coil_directions(out, {10: axis})
    assert sorted(out.elements[0].nodes) == sorted(src.elements[0].nodes)
    assert out.nodes == src.nodes
    assert _triple(out) * _triple(src) > 0          # same handedness, element not inside out
    assert src.elements[0].nodes == tuple(order)    # input untouched


def test_orient_to_z_matches_public_direction_and_corners():
    # The spin about the current axis is free (square cross-section); only
    # node 1 -> 5 and the corner set are fixed.
    out = mw.orient_coil_current(_coil_mesh(_CUBIT_ORDER), {10: (0, 0, 1)})
    assert sorted(_corners(out)) == sorted(_corners(_coil_mesh(_PUBLIC_ORDER)))
    assert _corners(out)[4][2] > _corners(out)[0][2]


def test_mcp_tool_reports_and_orients_coils(tmp_path):
    import json
    from elf_mcp_server.handlers import elf_meg_write

    nodes = {str(k): list(map(float, v)) for k, v in _CUBIT_NODES.items()}
    blocks = [{"prefix": "MCL", "shape": "hex8", "connectivity": [list(_CUBIT_ORDER)], "group_id": 10}]
    r = json.loads(elf_meg_write(nodes, blocks))
    assert r["ok"] and r["coil_directions"]["10"]["direction"] == pytest.approx([1, 0, 0])
    bad = json.loads(elf_meg_write(nodes, blocks, coil_axes={"10": [0, 0, 1]}))
    assert not bad["ok"] and "not along the requested axis" in bad["error"]
    out = tmp_path / "c.meg"
    ok = json.loads(elf_meg_write(nodes, blocks, out_path=str(out),
                                  coil_axes={"10": [0, 0, 1]}, orient_coils=True))
    assert ok["ok"] and ok["coil_directions"]["10"]["direction"] == pytest.approx([0, 0, 1])
    assert sorted(_corners(mw.read_meg(out))) == sorted(_corners(_coil_mesh(_PUBLIC_ORDER)))


def test_cubit_coil_axis_preserves_connectivity_and_rejects_wrong_direction(tmp_path):
    from elf_mcp_server import cubit_to_meg as c2m

    labels = {1: "MCL", 2: None}
    mesh = c2m.mesh_from_cubit(_StubCubit(), labels=labels)
    assert c2m.mesh_from_cubit(_StubCubit(), labels=labels, coil_axes={1: "+z"}) == mesh

    target = tmp_path / "wrong-axis.meg"
    for axis in ("+x", "-z"):
        with pytest.raises(mw.MegError, match=r"block 1: MCL8T nodes 1 -> 5"):
            c2m.export_meg_from_cubit(
                _StubCubit(), target, labels=labels, coil_axes={1: axis}
            )
    assert not target.exists()
    with pytest.raises(mw.MegError, match="signed coil axis"):
        c2m.mesh_from_cubit(_StubCubit(), labels=labels, coil_axes={1: "up"})


class _VolumeBlockCubit(_StubCubit):
    """Blocks made from volumes: get_block_hexes is empty, the volume holds them."""

    def get_block_hexes(self, b): return []
    def get_block_volumes(self, b): return [5] if b == 1 else []
    def get_volume_hexes(self, v): return [1] if v == 5 else []


def test_volume_defined_block_falls_back_to_volume_elements():
    from elf_mcp_server import cubit_to_meg as c2m

    mesh = c2m.mesh_from_cubit(_VolumeBlockCubit(), labels={2: None, 3: None})
    assert [e.label for e in mesh.elements] == ["MMB8T"] and mesh.elements[0].mid == 1


def test_labeled_block_without_elements_is_an_error_not_a_silent_drop():
    from elf_mcp_server import cubit_to_meg as c2m

    with pytest.raises(mw.MegError, match="block 1 .*returned no elements"):
        c2m.mesh_from_cubit(_VolumeBlockCubit_NoOwner(), labels={2: None, 3: None})


class _VolumeBlockCubit_NoOwner(_StubCubit):
    def get_block_hexes(self, b): return []


class _Cubit2026Names:
    """Cubit 2026.8 view of the stub: no get_nodeset_name; names via get_exodus_entity_name."""

    def __init__(self):
        self._base = _StubCubit()

    def __getattr__(self, name):
        if name == "get_nodeset_name":
            raise AttributeError(name)
        return getattr(self._base, name)

    def get_nodeset_id_list(self): return [20, 21, 22]
    def get_exodus_entity_name(self, kind, i):
        assert kind == "nodeset"
        return {20: "SPACE_PROBE", 21: "CONTROL", 22: "space_empty"}[i]
    def get_nodeset_nodes_inclusive(self, n): return {20: (10,), 21: (3,), 22: ()}[n]


def test_space_nodeset_uses_exodus_entity_name_on_cubit_2026():
    from elf_mcp_server import cubit_to_meg as c2m

    stub = _Cubit2026Names()
    assert not hasattr(stub, "get_nodeset_name")
    mesh = c2m.mesh_from_cubit(stub, labels={2: None})
    assert mesh.space_nodes == {1: (5.0, 5.0, 5.0)}    # only SPACE_PROBE; CONTROL and the empty set excluded


class _SurfBlocks(_StubCubit):
    """Block 1 owns surfaces 1..3 (one quad each); block 2/3 skipped."""

    def __init__(self, fail_on=None, direct=()):
        super().__init__()
        self.fail_on, self.direct = fail_on, direct

    def get_nodeset_id_list(self): return []
    def get_block_hexes(self, b): return []
    def get_block_pyramids(self, b): return []
    def get_block_quads(self, b): return list(self.direct) if b == 1 else []
    def get_block_surfaces(self, b): return [1, 2, 3] if b == 1 else []
    def get_surface_quads(self, s):
        if s == self.fail_on:
            raise RuntimeError("surface query failed")
        return [s]
    def get_connectivity(self, t, i): return (1, 2, 3, 4)
    def get_nodal_coordinates(self, n): return (float(n), 0.0, 0.0)


def test_failing_per_surface_query_refuses_a_partial_block():
    from elf_mcp_server import cubit_to_meg as c2m

    ok = c2m.mesh_from_cubit(_SurfBlocks(), "K", labels={2: None, 3: None})
    assert len(ok.elements) == 3
    with pytest.raises(mw.MegError, match=r"block 1: get_surface_quads\(2\) failed"):
        c2m.mesh_from_cubit(_SurfBlocks(fail_on=2), "K", labels={2: None, 3: None})


def test_direct_and_geometry_members_are_united():
    from elf_mcp_server import cubit_to_meg as c2m

    mesh = c2m.mesh_from_cubit(_SurfBlocks(direct=(1, 9)), "K", labels={2: None, 3: None})
    assert len(mesh.elements) == 4          # direct 1 and 9, surface 1 deduplicated, 2, 3


def test_element_shared_by_two_blocks_is_rejected():
    from elf_mcp_server import cubit_to_meg as c2m

    class Shared(_SurfBlocks):
        def get_block_id_list(self): return [1, 2]
        def get_block_surfaces(self, b): return [1] if b in (1, 2) else []

    with pytest.raises(mw.MegError, match="belongs to blocks 1 and 2"):
        c2m.mesh_from_cubit(Shared(), "K", labels={1: "MMB", 2: "MMB"})


def test_explicit_faces_are_quads_and_tris_keep_their_own_id_space():
    from elf_mcp_server import cubit_to_meg as c2m

    class Mixed(_SurfBlocks):
        """Real 2026.8 shape: no get_block_quads; 'add face 5' -> get_block_faces; id 5 also exists as a tri."""
        def __getattribute__(self, n):
            if n == "get_block_quads":
                raise AttributeError(n)
            return super().__getattribute__(n)
        def get_block_faces(self, b): return [5] if b == 1 else []
        def get_block_tris(self, b): return [5] if b == 1 else []
        def get_connectivity(self, t, i):
            return {"quad": (1, 2, 3, 4), "tri": (4, 5, 6)}[t]

    mesh = c2m.mesh_from_cubit(Mixed(), "K", labels={2: None, 3: None})
    kinds = sorted(len(e.nodes) for e in mesh.elements)
    assert kinds == [3, 4, 4, 4, 4]          # surfaces 1..3 quads + explicit quad 5 + tri 5 (same number, two elements)
