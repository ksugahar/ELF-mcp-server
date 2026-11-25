"""Read a Cubit mesh through ``import cubit`` and write an ELF/MAGIC ``.meg``.

The supported route is an *external* Python process that imports Cubit's
``cubit`` module itself (``load_cubit``); the elf-mcp server and Cubit's
embedded Python never run this.  Run it as a script or call
``export_meg_from_file``.  Where Cubit is unavailable use the IEMesh route
(``elf_iemesh_compile``).  Pure Python, no compiled plugin.

    python -I -B cubit_to_meg.py model.cub5 out.meg --dim T --labels 1:MMB,2:none

The Cubit calls (``get_block_id_list``, ``get_block_name``,
``get_block_<type>``, ``get_connectivity``, ``get_nodal_coordinates``,
``get_nodeset_*``) are exercised in tests only against a stub; they have not
yet been run against a licensed Cubit session.
"""

from __future__ import annotations

import argparse
import importlib
import os
import sys
from typing import Mapping, Sequence

from .meg_writer import (MegBlock, MegError, MegMesh, blocks_to_mesh,
                         prefix_from_block_name, write_meg)

# (cubit getter suffix, connectivity type, neutral shape, dims it may appear in)
_ELEMENTS = (
    ("hexes", "hex", "hex8", "T"),
    ("tets", "tet", "tet4", "T"),
    ("wedges", "wedge", "wedge6", "T"),
    ("pyramids", "pyramid", "pyramid5", "T"),
    ("quads", "quad", "quad4", "KR"),
    ("tris", "tri", "tri3", "KR"),
)


def mesh_from_cubit(
    cubit,
    dim: str = "T",
    labels: Mapping[int, str | None] | None = None,
    *,
    scale: float = 0.001,
    symmetry: Sequence[str] = (),
    space_nodeset_marker: str = "SPACE",
) -> MegMesh:
    """Build a ``MegMesh`` from the current Cubit mesh.

    ``labels`` maps block id -> ELF prefix (``None`` skips the block, e.g.
    air).  A block missing from ``labels`` is labeled from its name prefix;
    if that fails the call raises, so nothing is silently dropped or defaulted.
    Mesh order must be 1; connectivity uses corner nodes.  Nodes of nodesets
    whose name contains ``space_nodeset_marker`` become ``MGR2`` nodes.
    """
    labels = dict(labels or {})
    blocks: list[MegBlock] = []
    used: list[int] = []
    unlabeled: list[str] = []
    for bid in cubit.get_block_id_list():
        if bid in labels:
            prefix = labels[bid]
        else:
            prefix = prefix_from_block_name(cubit.get_block_name(bid))
            if prefix is None:
                unlabeled.append(f"{bid}:{cubit.get_block_name(bid)!r}")
                continue
        if prefix is None:
            continue
        for suffix, ctype, shape, dims in _ELEMENTS:
            getter = getattr(cubit, f"get_block_{suffix}", None)
            ids = list(getter(bid)) if getter else []
            if not ids:
                continue
            if dim not in dims:
                raise MegError(
                    f"block {bid} has {ctype} elements, not allowed in DIM {dim}")
            conn = [tuple(cubit.get_connectivity(ctype, i)) for i in ids]
            used.extend(n for c in conn for n in c)
            blocks.append(MegBlock(prefix.upper(), shape, conn, int(bid)))
    if unlabeled:
        raise MegError(
            "blocks without an ELF label (pass labels={id: prefix or None}): "
            + ", ".join(unlabeled))
    nodes = {int(n): tuple(cubit.get_nodal_coordinates(int(n)))
             for n in sorted(set(used))}
    space: list[tuple[float, float, float]] = []
    marker = space_nodeset_marker.upper()
    for nsid in cubit.get_nodeset_id_list():
        if marker in (cubit.get_nodeset_name(nsid) or "").upper():
            space += [tuple(cubit.get_nodal_coordinates(int(n)))
                      for n in cubit.get_nodeset_nodes_inclusive(nsid)]
    return blocks_to_mesh(nodes, blocks, dim, scale=scale,
                          symmetry=symmetry, space_nodes=space)


def export_meg_from_cubit(cubit, path, dim: str = "T", labels=None, *,
                          overwrite: bool = False, **kwargs):
    """Convenience: ``mesh_from_cubit`` then ``write_meg``; returns the path."""
    return write_meg(mesh_from_cubit(cubit, dim, labels, **kwargs), path,
                     overwrite=overwrite)


DEFAULT_CUBIT_BIN = r"C:\Program Files\Coreform Cubit 2026.8\bin"


def load_cubit(bin_dir: str | None = None):
    """Import Cubit's Python module in this external interpreter and init it.

    ``bin_dir`` defaults to ``$CUBIT_BIN`` then ``DEFAULT_CUBIT_BIN``.
    """
    bin_dir = bin_dir or os.environ.get("CUBIT_BIN") or DEFAULT_CUBIT_BIN
    if not os.path.isdir(bin_dir):
        raise MegError(f"Cubit bin directory not found: {bin_dir}")
    if bin_dir not in sys.path:
        sys.path.append(bin_dir)
    cubit = importlib.import_module("cubit")
    cubit.init(["cubit", "-noecho", "-nojournal", "-nographics"])
    return cubit


def export_meg_from_file(model_path, out_path, dim: str = "T", labels=None, *,
                         cubit=None, overwrite: bool = False, **kwargs):
    """Open a Cubit model (.cub5 etc.) in this process and write ``.meg``.

    ``cubit`` may be injected (tests); otherwise ``load_cubit()`` is used.
    The model must already be meshed with first-order elements.
    """
    cubit = cubit or load_cubit()
    cubit.cmd(f'open "{model_path}"')
    return export_meg_from_cubit(cubit, out_path, dim, labels,
                                 overwrite=overwrite, **kwargs)


def _parse_labels(text: str) -> dict:
    out: dict = {}
    for item in filter(None, (t.strip() for t in text.split(","))):
        bid, _, pre = item.partition(":")
        out[int(bid)] = None if pre.lower() in ("none", "skip", "") else pre.upper()
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Cubit mesh -> ELF/MAGIC .meg")
    ap.add_argument("model")
    ap.add_argument("out")
    ap.add_argument("--dim", default="T", choices=("T", "K", "R"))
    ap.add_argument("--labels", default="", help="1:MMB,2:none,...")
    ap.add_argument("--overwrite", action="store_true")
    a = ap.parse_args(argv)
    path = export_meg_from_file(a.model, a.out, a.dim, _parse_labels(a.labels),
                                overwrite=a.overwrite)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
