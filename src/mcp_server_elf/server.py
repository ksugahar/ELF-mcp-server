"""
ELF MCP Server

Provides documentation and knowledge for the ELF600 electromagnetic field
analysis suite (MAGIC / ELFIN / BEAM solvers) — file formats, commands,
element types, solver options, and mesh scripting.

Topics:
- .mai file format (analysis/solver control input)
- .mei file format (mesh generation script)
- .meg file format (compiled mesh data)
- MAGIC solver (magnetostatic BEM)
- ELFIN solver (eddy current BEM)
- BEAM solver (charged particle tracking)
- Element type naming convention
- B-H curve specification
- IPM motor analysis
- Inductance computation (LscLl)
- Magnetization / demagnetization

Usage:
    mcp-server-elf              # Start MCP server (stdio transport)
    mcp-server-elf --selftest   # Run self-test
"""

import sys

from mcp.server.fastmcp import FastMCP

from .elf_knowledge import get_elf_documentation
from .help_access import list_help_files, search_help, get_help_file

mcp = FastMCP("mcp-server-elf")


# ============================================================
# MCP Tools
# ============================================================

@mcp.tool()
def elf_usage(topic: str = "all") -> str:
    """
    Get ELF600 electromagnetic field analysis documentation.

    ELF600 is a BEM-based electromagnetic analysis suite with three solvers:
    MAGIC (magnetostatic), ELFIN (electrostatic), BEAM (particle tracking).
    Input consists of .mai (analysis control), .mei (mesh script), and
    .meg (compiled mesh) files.

    Args:
        topic: Documentation topic. Options:
            "all"              - Complete documentation (~60k chars)
            "overview"         - ELF600 suite overview, solver modules, tools
            "mai_format"       - .mai file format (PRE keywords, all solvers)
            "mei_format"       - .mei file format (mesh scripting structure)
            "meg_format"       - .meg file format (symmetry, nodes, elements)
            "magic"            - MAGIC magnetostatic solver details
            "elfin"            - ELFIN electrostatic solver (D-E curves)
            "beam"             - BEAM particle tracking (RELA, BINT, GRAV)
            "element_types"    - All element types (MAGIC/ELFIN/BEAM, DOF)
            "bh_curves"        - B-H curves, recoil, extrapolation
            "sol_commands"     - SOL blocks, NONL strategy, PASS optimization
            "mei_commands"     - IEmesh commands (AA/AN/AE/ME/BE/TE/NB/...)
            "ipm_motor"        - IPM motor Ld/Lq calculation workflow
            "inductance"       - Lsc (JIS) and Ll (IEEJ) with 6 samples
            "magnetization"    - Magnetization (MAGNE2) and demagnetization
            "examples"         - Example file catalog
            "meg_export"       - MEG export from Cubit (labels, DIM)
            "treasure_box"     - Quick-reference tables (element-PRE map, etc.)
            "sinusoidal"       - SOL MOMC, complex permeability, AC force
            "anisotropy"       - HBA1/HBA2, VEC1/VEC3, lamination
            "sted"             - Steady-state eddy current motion
            "meshing"          - Element quality, gaps, connectivity rules
            "convergence"      - Nonlinear convergence troubleshooting
            "force_methods"    - FORC vs FORT vs FIXB comparison
            "errors"           - Error messages (ELF-Q/E/W, 160+ codes)
            "iemesh"           - IEmesh tool overview and command families
            "tools"            - Wmap3, MagFilter2, MaiEditor3, ELF/Bench
    """
    return get_elf_documentation(topic)


@mcp.tool()
def elf_help_index(prefix: str = "") -> str:
    """
    List all 1141 ELF600 help files (HTM source) bundled with this server.

    Useful for discovering files to read with ``elf_help_get``.

    Args:
        prefix: Filter by path prefix (e.g. "m_rf1/" for MAGIC reference,
                "d_ken/" for technical docs, "u_support/" for error messages,
                "m_treasure/" for quick-reference tables, etc.).
                Empty string lists all files.

    Returns:
        Tab-separated list: PATH<TAB>CHARS<TAB>TITLE per line.
    """
    files = list_help_files(prefix=prefix or None)
    if not files:
        return f"No files match prefix '{prefix}'. Try 'm_rf1/', 'e_rf1/', 'b_rf1/', 'd_ken/', 't_iemesh/', etc."
    lines = [f"{f['path']}\t{f['char_count']}\t{f['title']}" for f in files]
    header = f"# {len(files)} files" + (f" under '{prefix}'" if prefix else " total")
    return header + "\n" + "\n".join(lines)


@mcp.tool()
def elf_help_search(query: str, top_k: int = 10, prefix: str = "") -> str:
    """
    Substring-search across all 1141 ELF600 help files (case-insensitive).

    Multiple keywords (space-separated) require ALL to match (AND).
    Returns ranked snippets — drill into specific files via ``elf_help_get``.

    Args:
        query: Search keywords (e.g. "MOMC sinusoidal", "渦電流 MAB",
               "OHM2 resistivity", "FORC FIXB").
        top_k: Max results to return (default 10).
        prefix: Restrict search to a directory (e.g. "m_rf1/", "d_ken/").

    Returns:
        Ranked list of matches with title and ~300-char snippet.
    """
    results = search_help(query, top_k=top_k, prefix=prefix or None)
    if not results:
        return f"No matches for '{query}'" + (f" under '{prefix}'" if prefix else "")
    out = [f"# {len(results)} matches for '{query}'\n"]
    for i, r in enumerate(results, 1):
        out.append(f"## [{i}] {r['path']}  (score={r['score']})")
        if r["title"]:
            out.append(f"_title: {r['title']}_")
        out.append(r["snippet"])
        out.append("")
    return "\n".join(out)


@mcp.tool()
def elf_help_get(path: str, max_chars: int = 30000) -> str:
    """
    Get full extracted text of a specific ELF600 help file.

    Args:
        path: Relative path under C:/ELF600/help/, e.g. "m_rf1/mr0003.htm",
              "d_ken/MOMC.htm", "u_support/error.htm". Use ``elf_help_index``
              or ``elf_help_search`` to discover paths. Filename-only also
              works if unambiguous.
        max_chars: Truncate output if longer (default 30000).

    Returns:
        File title + extracted text (HTML stripped, decoded from Shift_JIS).
    """
    result = get_help_file(path, max_chars=max_chars)
    if "error" in result:
        return f"Error reading '{path}': {result['error']}"
    head = f"# {result['path']}"
    if result["title"]:
        head += f"\n_title: {result['title']}_"
    head += f"\n_chars: {result['char_count']}_"
    if result["truncated"]:
        head += " (truncated)"
    return head + "\n\n" + result["text"]


# ============================================================
# MCP Prompts
# ============================================================

@mcp.prompt()
def new_elf_analysis(geometry: str, solver: str = "MAGIC") -> str:
    """Set up a new ELF analysis."""
    solver = solver.upper()
    if solver == "MAGIC":
        return (
            f"Set up a MAGIC magnetostatic analysis for: {geometry}\n\n"
            "Workflow:\n"
            "1. Create .mei mesh script (MODEL MAGIC T/K/R)\n"
            "2. Define coils (MCL), iron (MWL/MMB), magnets (HBRM)\n"
            "3. Add evaluation contour (MCO) after SPACE\n"
            "4. Run IEmesh to generate .meg\n"
            "5. Create .mai: USE MAGIC 3.50, PRE block (B-H, coils), SOL MOME\n"
            "6. Add SOL FIEL, SOL FORC/FORT as needed\n"
        )
    elif solver == "ELFIN":
        return (
            f"Set up an ELFIN eddy current analysis for: {geometry}\n\n"
            "Workflow:\n"
            "1. Create .mei mesh script (MODEL ELFIN T/K/R)\n"
            "2. Define conductors (ESC), magnetic bodies (EMB)\n"
            "3. Add evaluation contour (ECO) after SPACE\n"
            "4. Run IEmesh to generate .meg\n"
            "5. Create .mai: USE ELFIN 3.50, PRE block (VOL1, EDSC), SOL MOME\n"
            "6. Add SOL FIEL for field computation\n"
        )
    else:
        return (
            f"Set up a BEAM particle tracking analysis for: {geometry}\n\n"
            "Workflow:\n"
            "1. Compute EM fields with MAGIC or ELFIN first\n"
            "2. Create .mei mesh script (MODEL BEAM T/K/R)\n"
            "3. Define beam source nodes\n"
            "4. Create .mai: USE BEAM 3.50, PRE (CHAR, MASS, VOLB, FILE)\n"
            "5. SOL BEAM for tracking\n"
        )


# ============================================================
# Entry point
# ============================================================

def _use_utf8_stdout() -> None:
    """Force stdout/stderr to UTF-8 (cp932 Japanese consoles can't encode em-dashes etc).

    No-op if the streams don't expose ``reconfigure``. Never raises.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            pass


def main():
    if "--selftest" in sys.argv:
        _use_utf8_stdout()
        print("ELF MCP server self-test:")

        # 1. Curated topics
        print("[1/4] elf_usage topics:")
        topics = [
            "overview", "mai_format", "mei_format", "meg_format",
            "magic", "elfin", "beam", "element_types", "bh_curves",
            "sol_commands", "mei_commands", "ipm_motor", "inductance",
            "magnetization", "examples", "meg_export",
            "treasure_box", "sinusoidal", "anisotropy", "sted",
            "meshing", "convergence", "force_methods", "errors",
            "iemesh", "tools",
        ]
        for t in topics:
            result = elf_usage(t)
            assert len(result) > 50, f"Topic '{t}' too short"
        print(f"  {len(topics)} topics OK")

        # 2. Help index
        print("[2/4] elf_help_index:")
        idx = elf_help_index()
        n_files = idx.count("\n") - 1
        assert n_files > 1000, f"Expected >1000 files, got {n_files}"
        print(f"  {n_files} files indexed")
        idx_mrf1 = elf_help_index("m_rf1/")
        assert "m_rf1/index.htm" in idx_mrf1, "m_rf1/ filter missed index.htm"
        print(f"  m_rf1/ filter OK")

        # 3. Help search
        print("[3/4] elf_help_search:")
        for q in ["MOMC", "渦電流", "OHM2", "FORC"]:
            r = elf_help_search(q, top_k=5)
            assert "No matches" not in r, f"Query '{q}' had no matches"
        print(f"  4 queries OK")

        # 4. Help get
        print("[4/4] elf_help_get:")
        for p in ["m_rf1/index.htm", "d_ken/MOMC.htm", "u_support/error.htm"]:
            r = elf_help_get(p)
            assert "Error reading" not in r, f"Failed to read {p}"
            assert len(r) > 100, f"{p} returned too little"
        print(f"  3 files OK")

        print("PASSED")
        return

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
