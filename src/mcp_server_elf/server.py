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
from .examples_access import list_examples, search_examples, get_example
from .wiki_access import list_wiki_pages, search_wiki, get_wiki_page
from .python_access import list_python_files, search_python, get_python_file

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
def elf_examples_index(solver: str = "", category: str = "", ext: str = "") -> str:
    """
    List all 332 ELF600 example input files (.mai analysis + .mei mesh + .txt + .props + .model)
    bundled with this server, from C:/ELF600/examples/.

    Use this to discover authoritative input file templates for any ELF analysis pattern.
    The examples cover: BASIC, IPM motors, LscLl inductance, MK Maxwell, MOMC sinusoidal,
    MR moment, MT time-stepping, V6Conv, WorkBook (MAGIC: 228 files), ELFIN: 66, BEAM: 38.

    Args:
        solver: "MAGIC" / "ELFIN" / "BEAM" (case-insensitive, empty = all).
        category: Subcategory filter ("BASIC", "IPM", "MOMC", "LscLl", etc.).
        ext: File extension ("mai", "mei", "txt", "props", "model"). Empty = all.

    Returns:
        Tab-separated: PATH<TAB>SOLVER<TAB>CATEGORY<TAB>EXT<TAB>CHARS per line.
    """
    files = list_examples(solver=solver or None, category=category or None, ext=ext or None)
    if not files:
        return f"No examples match (solver='{solver}', category='{category}', ext='{ext}')."
    lines = [f"{f['path']}\t{f['solver']}\t{f['category']}\t{f['ext']}\t{f['char_count']}"
             for f in files]
    filt = []
    if solver: filt.append(f"solver={solver}")
    if category: filt.append(f"category={category}")
    if ext: filt.append(f"ext={ext}")
    header = f"# {len(files)} examples" + (f" ({', '.join(filt)})" if filt else " total")
    return header + "\n" + "\n".join(lines)


@mcp.tool()
def elf_examples_search(query: str, top_k: int = 10, solver: str = "", ext: str = "") -> str:
    """
    Substring-search across all 332 ELF600 example input files (case-insensitive).

    Multiple keywords (space-separated) require ALL to match (AND).
    Find concrete .mai/.mei templates that demonstrate specific keywords/elements.

    Args:
        query: Keywords (e.g. "MOMC FREQ", "OHM2 MAB", "AMP1I", "HBA1 lamination").
        top_k: Max results.
        solver: Restrict to "MAGIC" / "ELFIN" / "BEAM".
        ext: Restrict to "mai" / "mei" / "txt".

    Returns:
        Ranked snippets — drill into specific files via ``elf_examples_get``.
    """
    results = search_examples(query, top_k=top_k, solver=solver or None, ext=ext or None)
    if not results:
        return f"No matches for '{query}'"
    out = [f"# {len(results)} matches for '{query}'\n"]
    for i, r in enumerate(results, 1):
        out.append(f"## [{i}] {r['path']}  ({r['solver']}/{r['category']}, .{r['ext']}, score={r['score']})")
        out.append(r["snippet"])
        out.append("")
    return "\n".join(out)


@mcp.tool()
def elf_examples_get(path: str, max_chars: int = 30000) -> str:
    """
    Get full text of a specific ELF600 example input file.

    Args:
        path: Relative path under C:/ELF600/examples/, e.g. "magic/BASIC/ABCL2.mai",
              "magic/MOMC/coil_eddy.mai", "elfin/MOMC/cap1.mei".
              Filename-only also works if unambiguous.
        max_chars: Truncate output if longer (default 30000).

    Returns:
        File metadata + raw text (Shift_JIS decoded if needed).
    """
    result = get_example(path, max_chars=max_chars)
    if "error" in result:
        return f"Error reading '{path}': {result['error']}"
    head = f"# {result['path']}  ({result['solver']}/{result['category']}, .{result['ext']})"
    head += f"\n_chars: {result['char_count']}_"
    if result["truncated"]:
        head += " (truncated)"
    return head + "\n\n" + result["text"]


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
# Wiki tools (elf.co.jp PukiWiki vendor pages)
# ============================================================

@mcp.tool()
def elf_wiki_index() -> str:
    """
    List 146 ELF600 vendor wiki pages (https://elf.co.jp/) bundled with this server.

    Full crawl of all PukiWiki pages discoverable via cmd=list, including
    technical articles, case studies, FAQ, product info, download portals,
    and version-specific pages.

    Returns:
        Tab-separated: NAME<TAB>CHARS<TAB>URL per line.
    """
    pages = list_wiki_pages()
    lines = [f"{p['name']}\t{p['char_count']}\t{p['url']}" for p in pages]
    return f"# {len(pages)} wiki pages from elf.co.jp\n" + "\n".join(lines)


@mcp.tool()
def elf_wiki_search(query: str, top_k: int = 10) -> str:
    """
    Substring-search across all 146 bundled ELF vendor wiki pages.

    Multiple keywords (space-separated) require ALL to match (AND).

    Args:
        query: Keywords (e.g. "磁気モーメント法", "MRI 比較", "渦電流").
        top_k: Max results.

    Returns:
        Ranked snippets with page name, URL, and ~300-char excerpt.
    """
    results = search_wiki(query, top_k=top_k)
    if not results:
        return f"No matches for '{query}'"
    out = [f"# {len(results)} matches for '{query}'\n"]
    for i, r in enumerate(results, 1):
        out.append(f"## [{i}] {r['name']}  (score={r['score']})")
        out.append(f"_{r['url']}_")
        out.append(r["snippet"])
        out.append("")
    return "\n".join(out)


@mcp.tool()
def elf_wiki_get(name: str, max_chars: int = 30000) -> str:
    """
    Get full extracted text of a specific ELF vendor wiki page.

    Args:
        name: Page name (e.g. "磁場解析", "解析手順の紹介(magic)",
              "有限要素法との違い", "磁気モーメント法", "FAQ").
              Substring match also works if unambiguous.
        max_chars: Truncate output if longer (default 30000).

    Returns:
        Page name + URL + extracted text.
    """
    result = get_wiki_page(name, max_chars=max_chars)
    if "error" in result:
        return f"Error reading '{name}': {result['error']}"
    head = f"# {result['name']}\n_url: {result['url']}_"
    if result["title"]:
        head += f"\n_title: {result['title']}_"
    head += f"\n_chars: {result['char_count']}_"
    if result["truncated"]:
        head += " (truncated)"
    return head + "\n\n" + result["text"]


# ============================================================
# Python interface tools (C:/ELF600/bin/ Python wrappers + configs)
# ============================================================

@mcp.tool()
def elf_python_index(ext: str = "") -> str:
    """
    List 15 ELF600 bin/ files bundled with this server: Python ctypes
    interface (.py), configs (.cfg), definitions (.def, error codes etc.),
    and helper scripts (.bat, .txt) from C:/ELF600/bin/.

    Includes:
    - **elftypes.py / magtypes.py**: ctypes wrappers for elfh1300.dll /
      magh1600.dll exposing 83 API functions each (PRE / SOL / GET_FIEL /
      SET_AMP1 etc.) — the official Python interface for automating ELF.
    - **ELFERR.def / MESERR.def**: error code definitions.
    - **MAGIC.cfg / ELFIN.cfg**: solver default configs.
    - **Wmap2def.txt, *.def**: tool/format definitions.

    Args:
        ext: Filter by extension ("py", "cfg", "def", "txt", "bat"). Empty = all.

    Returns:
        Tab-separated: PATH<TAB>EXT<TAB>CHARS per line.
    """
    files = list_python_files(ext=ext or None)
    if not files:
        return f"No files match ext='{ext}'."
    lines = [f"{f['path']}\t{f['ext']}\t{f['char_count']}" for f in files]
    header = f"# {len(files)} bin/ files" + (f" (ext={ext})" if ext else " total")
    return header + "\n" + "\n".join(lines)


@mcp.tool()
def elf_python_search(query: str, top_k: int = 10, ext: str = "") -> str:
    """
    Substring-search across all 15 bundled ELF600 bin/ text files.

    Useful for finding specific API functions in elftypes.py / magtypes.py
    (e.g. "GET_FIEL" → see all related ctypes signatures), or looking up
    error codes (e.g. "ELF-Q103" in ELFERR.def).

    Args:
        query: Keywords (e.g. "GET_FIEL", "SET_AMP1", "MAGIC.cfg",
               "ELF-Q103", "MOMC").
        top_k: Max results.
        ext: Restrict to "py" / "cfg" / "def" / "txt" / "bat".

    Returns:
        Ranked snippets with file path and ~350-char excerpt.
    """
    results = search_python(query, top_k=top_k, ext=ext or None)
    if not results:
        return f"No matches for '{query}'"
    out = [f"# {len(results)} matches for '{query}'\n"]
    for i, r in enumerate(results, 1):
        out.append(f"## [{i}] {r['path']}  (.{r['ext']}, score={r['score']})")
        out.append(r["snippet"])
        out.append("")
    return "\n".join(out)


@mcp.tool()
def elf_python_get(path: str, max_chars: int = 30000) -> str:
    """
    Get full text of a specific ELF600 bin/ file.

    Args:
        path: Filename or relative path under C:/ELF600/bin/, e.g.
              "elftypes.py", "magtypes.py", "ELFERR.def", "MAGIC.cfg".
        max_chars: Truncate output if longer (default 30000).

    Returns:
        File text (UTF-8 / Shift_JIS auto-decoded).
    """
    result = get_python_file(path, max_chars=max_chars)
    if "error" in result:
        return f"Error reading '{path}': {result['error']}"
    head = f"# {result['path']}  (.{result['ext']})"
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
        print("[1/13] elf_usage topics:")
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
        print("[2/13] elf_help_index:")
        idx = elf_help_index()
        n_files = idx.count("\n") - 1
        assert n_files > 1000, f"Expected >1000 files, got {n_files}"
        print(f"  {n_files} files indexed")
        idx_mrf1 = elf_help_index("m_rf1/")
        assert "m_rf1/index.htm" in idx_mrf1, "m_rf1/ filter missed index.htm"
        print(f"  m_rf1/ filter OK")

        # 3. Help search
        print("[3/13] elf_help_search:")
        for q in ["MOMC", "渦電流", "OHM2", "FORC"]:
            r = elf_help_search(q, top_k=5)
            assert "No matches" not in r, f"Query '{q}' had no matches"
        print(f"  4 queries OK")

        # 4. Help get
        print("[4/13] elf_help_get:")
        for p in ["m_rf1/index.htm", "d_ken/MOMC.htm", "u_support/error.htm"]:
            r = elf_help_get(p)
            assert "Error reading" not in r, f"Failed to read {p}"
            assert len(r) > 100, f"{p} returned too little"
        print(f"  3 files OK")

        # 5. Examples index
        print("[5/13] elf_examples_index:")
        all_idx = elf_examples_index()
        n_ex = all_idx.count("\n") - 1
        assert n_ex > 300, f"Expected >300 examples, got {n_ex}"
        magic_idx = elf_examples_index(solver="MAGIC")
        assert "magic/BASIC/" in magic_idx, "MAGIC filter missed BASIC/"
        mai_idx = elf_examples_index(ext="mai")
        n_mai = mai_idx.count("\n") - 1
        assert n_mai > 100, f"Expected >100 .mai files, got {n_mai}"
        print(f"  {n_ex} examples ({n_mai} .mai), filters OK")

        # 6. Examples search
        print("[6/13] elf_examples_search:")
        for q in ["MOMC", "OHM2", "FREQ", "PRE"]:
            r = elf_examples_search(q, top_k=5)
            assert "No matches" not in r, f"Query '{q}' had no matches"
        print(f"  4 queries OK")

        # 7. Examples get
        print("[7/13] elf_examples_get:")
        for p in ["magic/BASIC/ABCL2.mai"]:
            r = elf_examples_get(p)
            assert "Error reading" not in r, f"Failed to read {p}"
            assert "MOMC" in r or "PRE" in r, f"{p} missing expected MAGIC keyword"
        print(f"  1 file OK")

        # 8-10. Wiki tools
        print("[8/13] elf_wiki_index:")
        wi = elf_wiki_index()
        n_w = wi.count("\n") - 1
        assert n_w >= 50, f"Expected >=50 wiki pages, got {n_w}"
        print(f"  {n_w} wiki pages")

        print("[9/13] elf_wiki_search:")
        for q in ["磁場解析", "MAGIC", "渦電流"]:
            r = elf_wiki_search(q, top_k=3)
            assert "No matches" not in r, f"Wiki query '{q}' had no matches"
        print(f"  3 queries OK")

        print("[10/13] elf_wiki_get:")
        for p in ["FAQ", "磁場解析"]:
            r = elf_wiki_get(p)
            assert "Error reading" not in r, f"Failed to read wiki '{p}'"
            assert len(r) > 100
        print(f"  2 pages OK")

        # 11-13. Python interface tools
        print("[11/13] elf_python_index:")
        pi = elf_python_index()
        n_p = pi.count("\n") - 1
        assert n_p >= 10, f"Expected >=10 bin files, got {n_p}"
        py_only = elf_python_index(ext="py")
        assert "elftypes.py" in py_only and "magtypes.py" in py_only
        print(f"  {n_p} files (py filter OK)")

        print("[12/13] elf_python_search:")
        for q in ["GET_FIEL", "SET_AMP1", "ctypes"]:
            r = elf_python_search(q, top_k=3)
            assert "No matches" not in r, f"Python query '{q}' had no matches"
        print(f"  3 queries OK")

        print("[13/13] elf_python_get:")
        for p in ["elftypes.py", "magtypes.py", "ELFERR.def"]:
            r = elf_python_get(p)
            assert "Error reading" not in r, f"Failed to read python '{p}'"
        print(f"  3 files OK")

        print("PASSED")
        return

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
