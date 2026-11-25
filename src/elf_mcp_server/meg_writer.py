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
