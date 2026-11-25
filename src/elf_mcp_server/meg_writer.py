"""Pure-Python ELF/MAGIC ``.meg`` writer and reader.

The writer takes a neutral mesh (node coordinates plus element blocks that
already carry an ELF label prefix).  It does not need Cubit, a compiled
plugin or any other solver software.  Producing the neutral mesh (for example
from a live Cubit session through ``import cubit``) is the caller's job.

Format facts used here were read from real ELF decks:

* ``T`` = full 3D, ``K`` = 2D planar (XY plane, z = 0),
  ``R`` = axisymmetric (XZ plane, y = 0).
* An element name is ``PREFIX(3) + NODE_COUNT(1) + DIM(1)``, e.g. ``MMB8T``.
* A deck is ``BOOK MEP`` header, ``MGSC`` scale, optional ``MIMA`` lines, then
  two ``* NODE`` / ``* ELEMENT <DIM>`` / ``* FIGURE`` sections: source nodes
  (``MGR1``) with elements, and evaluation nodes (``MGR2``) with elements.
* Coordinates are written as ``%.13E`` so no precision is lost.

Nothing here is silent: unknown labels, missing nodes, off-plane 2D
coordinates and unlabeled blocks raise ``MegError``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping, Sequence

DIMS = ("T", "K", "R")

_COMMON = ("MMB", "MMT", "MMP", "MWL", "MWV", "MCL", "MAB", "MAT", "MBB",
           "MCO", "MCM", "MSH")
VALID_LABELS: dict[str, tuple[str, ...]] = {
    "T": _COMMON + ("MMS", "MJH", "MCB"),
    "K": _COMMON + ("MJH",),
    "R": _COMMON,
}

# Node count of the neutral shapes accepted by ``blocks_to_mesh``.
_SHAPE_NODES = {
    "line2": 2, "tri3": 3, "quad4": 4, "tet4": 4,
    "wedge6": 6, "hex8": 8, "pyramid5": 5,
}
_COORD_TOL = 1.0e-12


class MegError(ValueError):
    """Raised when a mesh cannot be written as a faithful MEG deck."""


@dataclass
class MegElement:
    label: str                  # full name, e.g. "MMB8T"
    id: int
    pid: int                    # second integer field (0 in all samples)
    mid: int                    # material / group id
    nodes: tuple[int, ...]


@dataclass
class MegMesh:
    dim: str = "T"
    scale: float = 0.001
    symmetry: list[str] = field(default_factory=list)   # raw MIMA arguments
    version: str = "7.3.0"
    nodes: dict[int, tuple[float, float, float]] = field(default_factory=dict)
    elements: list[MegElement] = field(default_factory=list)
    space_nodes: dict[int, tuple[float, float, float]] = field(default_factory=dict)
    space_elements: list[MegElement] = field(default_factory=list)


@dataclass
class MegBlock:
    """One group of same-shape elements that share an ELF label prefix."""

    prefix: str                 # "MMB", "MCO", ...
    shape: str                  # key of _SHAPE_NODES
    connectivity: Sequence[Sequence[int]]
    group_id: int = 1


# ----------------------------------------------------------------------
# Validation helpers
# ----------------------------------------------------------------------
def _check_dim(dim: str) -> None:
    if dim not in DIMS:
        raise MegError(f"DIM must be one of {DIMS}, got {dim!r}")


def _plane_point(dim: str, p: Sequence[float], where: str) -> tuple[float, float, float]:
    x, y, z = (float(p[0]), float(p[1]), float(p[2]))
    if dim == "K" and abs(z) > _COORD_TOL:
        raise MegError(f"{where}: 2D (K) deck needs z = 0, got z = {z!r}")
    if dim == "R" and abs(y) > _COORD_TOL:
        raise MegError(f"{where}: axisymmetric (R) deck needs y = 0, got y = {y!r}")
    if dim == "R" and x < -_COORD_TOL:
        raise MegError(f"{where}: axisymmetric (R) deck needs x >= 0, got x = {x!r}")
    return (x, y, z)


def check_label(prefix: str, dim: str) -> None:
    _check_dim(dim)
    if prefix not in VALID_LABELS[dim]:
        raise MegError(
            f"label prefix {prefix!r} is not valid for DIM {dim}; "
            f"valid: {', '.join(VALID_LABELS[dim])}")


def prefix_from_block_name(name: str) -> str | None:
    """Return the 3-letter prefix a block name starts with, or None.

    Matching is case-insensitive.  There is deliberately no default: the
    caller decides what an unlabeled block (for example air) means.
    """
    head = (name or "").strip().upper()[:3]
    return head if head in set(VALID_LABELS["T"]) else None


# ----------------------------------------------------------------------
# Building a mesh from neutral blocks
# ----------------------------------------------------------------------
def blocks_to_mesh(
    nodes: Mapping[int, Sequence[float]],
    blocks: Iterable[MegBlock],
    dim: str = "T",
    *,
    scale: float = 0.001,
    symmetry: Sequence[str] = (),
    space_nodes: Sequence[Sequence[float]] = (),
    version: str = "7.3.0",
) -> MegMesh:
    """Build a ``MegMesh`` from neutral nodes and labeled element blocks.

    Pyramids become 8-node degenerate hexes (apex repeated four times) in 3D
    and are rejected in 2D.  Element ids are assigned sequentially from 1 in
    block order.  ``space_nodes`` become sequential ``MGR2`` records.
    """
    _check_dim(dim)
    mesh = MegMesh(dim=dim, scale=float(scale), symmetry=list(symmetry),
                   version=version)
    for nid, p in nodes.items():
        if int(nid) <= 0:
            raise MegError(f"node id must be positive, got {nid!r}")
        mesh.nodes[int(nid)] = _plane_point(dim, p, f"node {nid}")
    eid = 0
    for blk in blocks:
        check_label(blk.prefix, dim)
        if blk.shape not in _SHAPE_NODES:
            raise MegError(f"unknown element shape {blk.shape!r}")
        n = _SHAPE_NODES[blk.shape]
        for conn in blk.connectivity:
            conn = tuple(int(c) for c in conn)
            if len(conn) != n:
                raise MegError(
                    f"{blk.shape} element needs {n} nodes, got {len(conn)}")
            if blk.shape == "pyramid5":
                if dim != "T":
                    raise MegError("pyramid elements exist only in 3D (T)")
                conn = conn[:4] + (conn[4],) * 4
            eid += 1
            mesh.elements.append(MegElement(
                f"{blk.prefix}{len(conn)}{dim}", eid, 0, int(blk.group_id), conn))
    for i, p in enumerate(space_nodes, start=1):
        mesh.space_nodes[i] = _plane_point(dim, p, f"space node {i}")
    validate(mesh)
    return mesh


def validate(mesh: MegMesh) -> None:
    """Raise ``MegError`` unless the mesh is internally consistent."""
    _check_dim(mesh.dim)
    for section, nodes, elems in (
        ("source", mesh.nodes, mesh.elements),
        ("evaluation", mesh.space_nodes, mesh.space_elements),
    ):
        seen: set[int] = set()
        for e in elems:
            if e.id in seen:
                raise MegError(f"{section}: duplicate element id {e.id}")
            seen.add(e.id)
            if len(e.label) != 5 or e.label[4] != mesh.dim:
                raise MegError(
                    f"{section}: element {e.id} label {e.label!r} does not "
                    f"match DIM {mesh.dim}")
            check_label(e.label[:3], mesh.dim)
            if not e.label[3].isdigit() or int(e.label[3]) != len(e.nodes):
                raise MegError(
                    f"{section}: element {e.id} label {e.label!r} disagrees "
                    f"with its {len(e.nodes)} nodes")
            missing = [n for n in e.nodes if n not in nodes]
            if missing:
                raise MegError(
                    f"{section}: element {e.id} references missing nodes {missing}")


# ----------------------------------------------------------------------
# Coil current direction (MCL8T)
# ----------------------------------------------------------------------
# ELF/MAGIC reference 2.7.1: the positive current of an MCL8T element flows
# from node 1 to node 5 ("the element direction is fixed by the node order").
# Nothing else in the deck carries the direction, so the node order IS the
# current direction.  A mesher's connectivity order is arbitrary, so check it
# (``coil_directions`` / ``check_coil_directions``) or set it
# (``orient_coil_current``).  MCL6T and the 2D coils are not examined here.
_HEX_SIGNS = ((-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
              (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1))


def _sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def _norm(v):
    return sum(x * x for x in v) ** 0.5


def _unit(v, what="vector"):
    n = _norm(v)
    if n <= 0.0:
        raise MegError(f"{what} has zero length")
    return tuple(x / n for x in v)


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _angle_deg(a, b) -> float:
    import math
    c = max(-1.0, min(1.0, _dot(_unit(a), _unit(b))))
    return math.degrees(math.acos(c))


def _hex_axes(mesh: MegMesh, e: MegElement):
    """Mean edge vectors of the hex along its three local axes."""
    p = [mesh.nodes[n] for n in e.nodes]
    def mean(pairs):
        vs = [_sub(p[j], p[i]) for i, j in pairs]
        return tuple(sum(v[k] for v in vs) / len(vs) for k in range(3))
    return (mean(((0, 1), (3, 2), (4, 5), (7, 6))),
            mean(((0, 3), (1, 2), (4, 7), (5, 6))),
            mean(((0, 4), (1, 5), (2, 6), (3, 7))))


def coil_directions(mesh: MegMesh) -> list[dict]:
    """Current direction (node 1 -> node 5) of every MCL8T element.

    Returns one dict per element: ``id``, ``mid``, ``direction`` (unit vector,
    mean of the four edges 1-5, 2-6, 3-7, 4-8) and ``spread_deg`` (largest
    angle between one of those edges and the mean; large means twisted).
    """
    out = []
    for e in mesh.elements:
        if e.label[:4] != "MCL8" or len(e.nodes) != 8:
            continue
        p = [mesh.nodes[n] for n in e.nodes]
        edges = [_sub(p[j], p[i]) for i, j in ((0, 4), (1, 5), (2, 6), (3, 7))]
        mean = tuple(sum(v[k] for v in edges) / 4 for k in range(3))
        d = _unit(mean, f"MCL8T element {e.id} current direction")
        out.append({"id": e.id, "mid": e.mid, "n1": e.nodes[0], "n5": e.nodes[4],
                    "direction": d,
                    "spread_deg": max(_angle_deg(v, mean) for v in edges)})
    return out


def coil_report(mesh: MegMesh) -> dict[int, dict]:
    """Per material id: element count, mean direction, worst element angle."""
    by: dict[int, list[dict]] = {}
    for c in coil_directions(mesh):
        by.setdefault(c["mid"], []).append(c)
    rep = {}
    for mid, items in by.items():
        mean = _unit(tuple(sum(c["direction"][k] for c in items) for k in range(3)),
                     f"coil MID {mid} mean direction")
        rep[mid] = {"elements": len(items), "direction": mean,
                    "max_angle_to_mean_deg": max(_angle_deg(c["direction"], mean)
                                                 for c in items),
                    "max_spread_deg": max(c["spread_deg"] for c in items)}
    return rep


_SIGNED_AXES = {"+x": (1.0, 0.0, 0.0), "-x": (-1.0, 0.0, 0.0),
                "+y": (0.0, 1.0, 0.0), "-y": (0.0, -1.0, 0.0),
                "+z": (0.0, 0.0, 1.0), "-z": (0.0, 0.0, -1.0)}


def _as_axis(mid, v) -> tuple[float, float, float]:
    if isinstance(v, str):
        key = v.strip().lower()
        if key not in _SIGNED_AXES:
            raise MegError(f"block {mid}: expected a signed coil axis such as '+z' "
                           f"or an (x, y, z) vector, got {v!r}")
        return _SIGNED_AXES[key]
    vec = tuple(float(x) for x in v)
    if len(vec) != 3 or _norm(vec) <= 0.0:
        raise MegError(f"block {mid}: coil axis must be a non-zero (x, y, z) vector")
    return vec


def _as_axes(expected) -> dict[int, tuple[float, float, float]]:
    """``{mid: "+z" | (x, y, z)}`` -> ``{mid: (x, y, z)}``."""
    if expected is None:
        return {}
    if isinstance(expected, Mapping):
        return {int(k): _as_axis(k, v) for k, v in expected.items()}
    raise MegError("coil axes must be a {mid: '+z' or (x, y, z)} mapping")


def check_coil_directions(mesh: MegMesh, expected=None, *, tol_deg: float = 5.0,
                          max_spread_deg: float = 20.0) -> dict[int, dict]:
    """Verify MCL8T current directions; returns ``coil_report``.

    ``expected`` is ``{mid: (x, y, z)}``: the direction the positive current
    must have for that coil material.  Raises ``MegError`` when an element is
    off that axis by more than ``tol_deg`` (reversed ones are named as such),
    or when an element's four 1-5 edges disagree by more than
    ``max_spread_deg`` (twisted or mis-ordered element).  Without ``expected``
    only the twist check runs; read the report to see what direction you got.
    """
    axes = _as_axes(expected)
    for c in coil_directions(mesh):
        if c["spread_deg"] > max_spread_deg:
            raise MegError(
                f"MCL8T element {c['id']} (MID {c['mid']}): edges 1-5/2-6/3-7/4-8 "
                f"differ by {c['spread_deg']:.1f} deg; the node order looks twisted")
        want = axes.get(c["mid"])
        if want is None:
            continue
        ang = _angle_deg(c["direction"], want)
        if ang > tol_deg:
            kind = "reversed" if ang > 180.0 - tol_deg else "not along the requested axis"
            raise MegError(
                f"block {c['mid']}: MCL8T nodes {c['n1']} -> {c['n5']} (element "
                f"{c['id']}) give current direction "
                f"{tuple(round(x, 6) for x in c['direction'])}, which is {kind} "
                f"({ang:.1f} deg from {tuple(want)}); reorder the nodes with "
                f"orient_coil_current")
    unknown = sorted(set(axes) - {c["mid"] for c in coil_directions(mesh)})
    if unknown:
        raise MegError(f"no MCL8T elements with MID {unknown}")
    return coil_report(mesh)


def orient_coil_current(mesh: MegMesh, axes, *, mids=None) -> MegMesh:
    """Return a copy whose MCL8T elements carry current along ``axes``.

    ``axes`` is ``{mid: (x, y, z)}``.  Each element's nodes are re-listed as a
    proper rotation of its own local frame (no mirroring, so the element is not
    turned inside out) whose node 1 -> 5 edge is the one closest to the axis.
    Only the node order changes; coordinates are untouched.
    """
    import copy
    want = _as_axes(axes)
    if mids is not None:
        want = {m: v for m, v in want.items() if m in set(mids)}
    new = copy.deepcopy(mesh)
    for e in new.elements:
        d = want.get(e.mid)
        if d is None or e.label[:4] != "MCL8" or len(e.nodes) != 8:
            continue
        frame = _hex_axes(mesh, e)
        best = max(((abs(_dot(_unit(frame[k]), _unit(d))), k,
                     1 if _dot(frame[k], d) >= 0 else -1) for k in range(3)))
        _, k, sgn = best
        unit = [(1, 0, 0), (0, 1, 0), (0, 0, 1)]
        e_c = tuple(sgn * x for x in unit[k])
        e_a = unit[(k + 1) % 3]
        e_b = tuple(sgn * x for x in unit[(k + 2) % 3])
        old_index = {s: i for i, s in enumerate(_HEX_SIGNS)}
        order = []
        for t in _HEX_SIGNS:
            s = tuple(t[0] * e_a[j] + t[1] * e_b[j] + t[2] * e_c[j] for j in range(3))
            order.append(e.nodes[old_index[s]])
        e.nodes = tuple(order)
    return new


# ----------------------------------------------------------------------
# Writer
# ----------------------------------------------------------------------
def _fmt_node(tag: str, nid: int, p: Sequence[float]) -> str:
    return f"{tag} {nid:7d} {0:3d} " + " ".join(f"{v:.13E}" for v in p)


def _fmt_element(e: MegElement) -> str:
    line = f"{e.label:<5s}{e.id:7d}{e.pid:7d}{e.mid:7d}" + "".join(
        f"{n:7d}" for n in e.nodes)
    if len(line) > 120:
        raise MegError(f"element {e.id}: line longer than 120 characters")
    return line


def format_meg(mesh: MegMesh) -> str:
    """Return the deck text for ``mesh`` (LF newlines)."""
    validate(mesh)
    out = [
        "BOOK  MEP  3.50",
        f"* ELF/MESH VERSION {mesh.version}",
        "* SOLVER = ELF/MAGIC",
        f"MGSC {mesh.scale:.15g}",
    ]
    out += [f"MIMA {s}" for s in mesh.symmetry]
    out.append("* NODE")
    out += [_fmt_node("MGR1", i, p) for i, p in mesh.nodes.items()]
    out.append(f"* ELEMENT {mesh.dim}")
    out += [_fmt_element(e) for e in mesh.elements]
    out.append("* FIGURE")
    out.append("* NODE")
    out += [_fmt_node("MGR2", i, p) for i, p in mesh.space_nodes.items()]
    out.append(f"* ELEMENT {mesh.dim}")
    out += [_fmt_element(e) for e in mesh.space_elements]
    out.append("* FIGURE")
    out.append("BOOK  END")
    return "\n".join(out) + "\n"


def write_meg(mesh: MegMesh, path: str | Path, *, overwrite: bool = False) -> Path:
    """Write ``mesh`` to ``path``; refuse to replace a file unless asked."""
    target = Path(path)
    if target.exists() and not overwrite:
        raise MegError(f"{target} exists; pass overwrite=True to replace it")
    text = format_meg(mesh)
    target.write_text(text, encoding="ascii", newline="\n")
    return target


# ----------------------------------------------------------------------
# Reader (used for round-trip checks and for reading existing decks)
# ----------------------------------------------------------------------
def parse_meg(text: str) -> MegMesh:
    """Parse a deck into a ``MegMesh``.

    Records before the first ``MGR2`` line belong to the source section, the
    rest to the evaluation section; this holds for the sample decks, where the
    second ``* NODE`` block starts the evaluation geometry.
    """
    mesh = MegMesh(dim="")
    section = 0     # 0 = source, 1 = evaluation
    node_blocks = 0
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("*"):
            body = line[1:].strip()
            if body.startswith("ELF/MESH VERSION"):
                mesh.version = body.split()[-1]
            elif body.startswith("NODE"):
                node_blocks += 1
                section = 0 if node_blocks == 1 else 1
            elif body.startswith("ELEMENT"):
                dim = body.split()[-1]
                if mesh.dim and dim != mesh.dim:
                    raise MegError(f"mixed DIM in one deck: {mesh.dim} and {dim}")
                mesh.dim = dim
            continue
        tok = line.split()
        key = tok[0]
        if key == "BOOK":
            continue
        if key == "MGSC":
            mesh.scale = float(tok[1])
        elif key == "MIMA":
            mesh.symmetry.append(" ".join(tok[1:]))
        elif key in ("MGR1", "MGR2"):
            target = mesh.nodes if key == "MGR1" else mesh.space_nodes
            if key == "MGR2":
                section = 1
            target[int(tok[1])] = (float(tok[3]), float(tok[4]), float(tok[5]))
        elif len(key) == 5 and key[0] == "M" and key[3].isdigit():
            e = MegElement(key, int(tok[1]), int(tok[2]), int(tok[3]),
                           tuple(int(t) for t in tok[4:]))
            (mesh.elements if section == 0 else mesh.space_elements).append(e)
        else:
            raise MegError(f"unrecognised record: {line[:60]!r}")
    if not mesh.dim:
        labels = {e.label[4] for e in mesh.elements + mesh.space_elements}
        if len(labels) != 1:
            raise MegError("cannot determine DIM: no '* ELEMENT <DIM>' line")
        mesh.dim = labels.pop()
    return mesh


def read_meg(path: str | Path) -> MegMesh:
    return parse_meg(Path(path).read_text(encoding="ascii", errors="strict"))
