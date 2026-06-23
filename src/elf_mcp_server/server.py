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
    elf-mcp-server              # Start MCP server (stdio transport)
    elf-mcp-server --selftest   # Run self-test
"""

import sys

from mcp.server.fastmcp import FastMCP

from .elf_knowledge import get_elf_documentation
from .help_access import list_help_files, search_help, get_help_file
from .examples_access import list_examples, search_examples, get_example
from .example_playbook import build_example_cards, format_example_cards
from .sample_decks import (
    list_sample_decks,
    search_sample_decks,
    get_sample_deck,
    build_sample_deck_cards,
    build_team28_cards,
    format_sample_deck_cards,
    format_team28_cards,
)
from .recipes import (
    list_recipes,
    search_recipes,
    get_recipe,
    format_recipe_index,
    format_search_results,
    format_recipe,
    plan_workflow,
)
from .wiki_access import list_wiki_pages, search_wiki, get_wiki_page
from .python_access import list_python_files, search_python, get_python_file

mcp = FastMCP("elf-mcp-server")


# ============================================================
# Meta / overview (★ recommended first call)
# Pattern adopted 2026-05-25 from radia-mcp.meta (Sugahara lab
# discovery infrastructure). The tool surface is large enough that a cold-start
# LLM benefits from an overview before browsing tool-by-tool.
# ============================================================

_TOOL_CATALOG = [
    ("elf_usage(topic)", "Curated documentation across 31 topics: "
                          ".mai/.mei/.meg formats, MAGIC/ELFIN/BEAM "
                          "solvers, element conventions, B-H, IPM motor, "
                          "radia motor bridge, SOL MOMC AC, cln_extraction, "
                          "licensing (dongle)"),
    ("elf_help_index / search / get", "Raw access to C:/ELF600/help/ "
                                       "(1141 files, 1.18 MB)"),
    ("elf_examples_index / search / get / playbook", "C:/ELF600/examples/ "
                                                       "(332 .mai/.mei/.txt, 533 KB) "
                                                       "plus 100 compact example cards"),
    ("elf_sample_decks_index / search / get / playbook",
                                              "Lab-authored ELF-runnable "
                                              "public .mai/.meg input decks "
                                              "(input files only; no solver outputs)"),
    ("elf_recipe_index / search / get / plan", "Public-safe workflow "
                                                "recipes for choosing ELF "
                                                "elements, PRE/SOL blocks, "
                                                "outputs, checks, and pitfalls"),
    ("elf_wiki_index / search / get", "elf.co.jp PukiWiki cache "
                                       "(146 pages, 211 KB)"),
    ("elf_python_index / search / get; elf_python_team28",
                                                  "C:/ELF600/bin/ Python ctypes "
                                                  "API + config (15 files, 246 KB) "
                                                  "plus Python-interface seed manifest"),
]

_RELATED_PUBLIC_PACKAGES = [
    ("radia-mcp", "pip install radia-mcp",
     "https://github.com/ksugahar/Radia",
     "Optional public companion for open electromagnetic modeling references"),
]


@mcp.tool()
def elf_overview() -> dict:
    """RECOMMENDED FIRST CALL. Catalog of ELF MCP's 24 tools + 1
    prompt, with public-safe routing hints for MCP clients.

    Returns:
        dict with `tool_families` (curated 24-tool grouping), `n_tools`,
        public boundary notes, recommended calls, and public companion package
        hints.
    """
    return {
        "n_tools": 24,
        "n_prompts": 1,
        "tool_families": [
            {"signature": sig, "description": desc}
            for sig, desc in _TOOL_CATALOG
        ],
        "recommended_calls": [
            {
                "goal": "Inspect the server surface",
                "call": "elf_overview()",
            },
            {
                "goal": "Find the right ELF/MAGIC command pattern",
                "call": "elf_usage(topic='all') or elf_recipe_search(query)",
            },
            {
                "goal": "Learn from the 586 public input-deck cases",
                "call": "elf_sample_decks_playbook(limit=20, family='srm')",
            },
            {
                "goal": "Open a specific public .mai/.meg input deck",
                "call": "elf_sample_decks_get(path)",
            },
            {
                "goal": "Inspect the Python-interface team28 seed manifest",
                "call": "elf_python_team28()",
            },
        ],
        "public_boundary": (
            "Documentation and lab-authored public input decks only. This MCP "
            "server does not execute ELF, launch GUI/CLI solvers, bundle solver "
            "outputs, expose comparison metrics, or publish private validation "
            "provenance."
        ),
        "related_public_packages": [
            {"name": n, "install": inst, "github": gh, "description": d}
            for n, inst, gh, d in _RELATED_PUBLIC_PACKAGES
        ],
        "next_step_hint":
            "Call elf_usage(topic='all') for the 31 curated topic "
            "catalogue, elf_plan_workflow('goal') for a workflow plan, "
            "elf_recipe_search('keyword') for decision cards, or "
            "elf_sample_decks_playbook() for ELF-runnable public .mai/.meg decks, "
            "elf_python_team28() for the Python-interface team28 seed manifest, "
            "elf_help_search('keyword') / "
            "elf_examples_search('keyword') for raw access, or "
            "elf_examples_playbook(limit=100) for compact example cards.",
    }


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
            "motor_radia_bridge" - Translate radia-mcp/open motor-FEA
                                 quantities (air-gap field, torque,
                                 flux linkage/back-EMF, lamination, eddy
                                 currents) to ELF/MAGIC elements, SOL blocks,
                                 and extraction steps
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
            "cln_extraction"   - ELF MAGIC -> Cauer Ladder Network synthesis
                                 workflow (6-step Foster + Cauer-I/II + 3-way
                                 cross-validation against step response /
                                 Joule loss / Lorentz force). Distilled from
                                 a 21-script rectangular-CLN reference suite.
            "licensing"        - Sentinel HL USB dongle (HASP): run-time,
                                 Admin Control Center (localhost:1947), and
                                 "dongle not recognized" troubleshooting
                                 (Code 43 / descriptor-request-failed on USB 3.x
                                 -> move to a USB 2.0 port)
            "python_api"       - Python ctypes API: DLL wrappers (magtypes /
                                 elftypes), Fortran-ABI calling convention,
                                 end-to-end call sequence, key function table,
                                 _R return variants, common pitfalls
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
def elf_examples_playbook(
    limit: int = 100,
    solver: str = "",
    category: str = "",
    feature: str = "",
    query: str = "",
) -> str:
    """
    Build compact public-safe cards from bundled ELF example .mai files.

    This is the fastest way to browse many authoritative examples without
    reading raw files one by one. Each card lists the example path, paired
    .mei/.model/.props files, detected SOL blocks, element families, keywords,
    feature tags, and a one-line reuse hint.

    Args:
        limit: Number of cards to return. Default 100. Max 200.
        solver: Optional solver filter: "MAGIC", "ELFIN", or "BEAM".
                Note: bundled MAGIC has 97 .mai examples; leaving this empty
                returns 100 cards by adding ELFIN/BEAM cards after MAGIC.
        category: Optional category filter such as "BASIC", "IPM", "MT",
                  "LscLl", "MOMC", "MK", "MR", "magne".
        feature: Optional feature tag filter, e.g. "motor", "flux-linkage",
                 "maxwell-force", "eddy-current", "sinusoidal-ac",
                 "electrostatic", "beam".
        query: Optional keyword filter across path, tags, and example text.

    Returns:
        Markdown-formatted compact cards. Drill down into any raw file with
        ``elf_examples_get(path)``.
    """
    cards = build_example_cards(
        limit=limit,
        solver=solver or None,
        category=category or None,
        feature=feature or None,
        query=query or None,
    )
    return format_example_cards(cards)


@mcp.tool()
def elf_sample_decks_index(family: str = "", case: str = "", ext: str = "") -> str:
    """
    List lab-authored public runnable ELF/MAGIC sample decks.

    These are `.mai` and `.meg` input files only. Solver outputs and
    comparison metrics are intentionally not bundled.

    Args:
        family: Optional family substring, e.g. "motor", "pm_square",
                "spm", "srm", "sr_motor", "induction", "reluctance",
                "hysteresis", "application", "wpt", "mri", "ih",
                "transformer", "accelerator", "actuator", "maglev",
                "separator", "brake", "ndt", "magnetic_gear",
                "voice_coil", "relay_solenoid", "hall_sensor",
                or "clutch".
        case: Optional case ID such as "pm001".
        ext: Optional file extension: "mai" or "meg".

    Returns:
        Tab-separated: PATH<TAB>FAMILY<TAB>CASE<TAB>EXT<TAB>CHARS per line.
    """
    decks = list_sample_decks(family=family or None, case=case or None, ext=ext or None)
    if not decks:
        return f"No sample decks match (family='{family}', case='{case}', ext='{ext}')."
    lines = [
        f"{d['path']}\t{d['family']}\t{d['case']}\t{d['ext']}\t{d['char_count']}"
        for d in decks
    ]
    filters = []
    if family:
        filters.append(f"family={family}")
    if case:
        filters.append(f"case={case}")
    if ext:
        filters.append(f"ext={ext}")
    header = f"# {len(decks)} sample decks" + (f" ({', '.join(filters)})" if filters else " total")
    return header + "\n" + "\n".join(lines)


@mcp.tool()
def elf_sample_decks_search(query: str, top_k: int = 10, ext: str = "") -> str:
    """
    Search lab-authored public sample deck paths and text.

    Multiple keywords require all terms to match. Use this to find runnable
    `.mai`/`.meg` input decks that contain specific ELF commands such as
    `HBCN`, `MWL8T`, `COI1`, or `FLUM`.

    Args:
        query: Search keywords.
        top_k: Max results.
        ext: Optional extension filter: "mai" or "meg".

    Returns:
        Ranked snippets. Drill down with ``elf_sample_decks_get(path)``.
    """
    results = search_sample_decks(query, top_k=top_k, ext=ext or None)
    if not results:
        return f"No sample deck matches for '{query}'"
    out = [f"# {len(results)} sample deck matches for '{query}'\n"]
    for i, r in enumerate(results, 1):
        out.append(
            f"## [{i}] {r['path']}  ({r['family']}/{r['case']}, .{r['ext']}, score={r['score']})"
        )
        out.append(r["snippet"])
        out.append("")
    return "\n".join(out)


@mcp.tool()
def elf_sample_decks_get(path: str, max_chars: int = 60000) -> str:
    """
    Get full text of a public runnable ELF/MAGIC sample deck.

    Args:
        path: Relative sample path, e.g.
              "motor/pm_cosine_pickup_72/pm001/pm001.mai".
              Filename-only works if unambiguous.
        max_chars: Truncate output if longer. Default 60000, enough for
                   the bundled public `.meg` decks.

    Returns:
        File metadata plus raw `.mai` or `.meg` text.
    """
    result = get_sample_deck(path, max_chars=max_chars)
    if "error" in result:
        return f"Error reading sample deck '{path}': {result['error']}"
    head = f"# {result['path']}  ({result['family']}/{result['case']}, .{result['ext']})"
    head += f"\n_chars: {result['char_count']}_"
    if result["truncated"]:
        head += " (truncated)"
    return head + "\n\n" + result["text"]


@mcp.tool()
def elf_sample_decks_playbook(limit: int = 100, family: str = "", query: str = "") -> str:
    """
    Build compact cards from the 586 public ELF-runnable `.mai`/`.meg` cases.

    Each card links the `.mai` and `.meg` pair and summarizes detected SOL
    blocks, PRE keywords, element types, feature tags, and a reuse hint. This
    is the fastest way to learn from the public deck corpus without reading
    every raw file.

    Args:
        limit: Number of cards to return. Default 100. Max 586.
        family: Optional family substring, e.g. "pm_square", "cosine",
            "spm", "srm", "sr_motor", "induction", "reluctance",
            "hysteresis", "wpt", "mri", "ih", "transformer",
            "accelerator", "actuator", "maglev", "separator",
            "brake", "ndt", "magnetic_gear", "voice_coil",
            "relay_solenoid", "hall_sensor", or "clutch".
        query: Optional keyword filter across paths, tags, and deck text.

    Returns:
        Markdown compact cards. Drill into raw files with
        ``elf_sample_decks_get(path)``.
    """
    cards = build_sample_deck_cards(limit=limit, family=family or None, query=query or None)
    return format_sample_deck_cards(cards)


@mcp.tool()
def elf_python_team28() -> str:
    """
    Return the Python-interface team28 seed manifest.

    team28 is a compact 28-case tour across 2-pole, 4-pole, 6-pole,
    8-pole, and cosine-remanence PM pickup families. Unlike the normal
    public `.mai`/`.meg` sample decks, team28 is intended for orchestration
    through the ELF Python interface, not normal ELF GUI/CLI deck execution.
    The listed public decks are seed/inspection material for that Python
    orchestration.

    Returns:
        Markdown compact cards for 28 Python-interface seed cases.
    """
    return format_team28_cards(build_team28_cards())


@mcp.tool()
def elf_recipe_index(tag: str = "", solver: str = "") -> str:
    """
    List public-safe workflow recipe cards.

    Recipes are decision cards for selecting ELF/MAGIC elements, PRE
    commands, SOL blocks, outputs, checks, and common pitfalls. They contain
    no solver outputs or machine-local validation paths.

    Args:
        tag: Optional tag filter, e.g. "motor", "flux-linkage",
             "maxwell-force", "eddy-current", "sinusoidal-ac".
        solver: Optional solver filter, currently mostly "MAGIC".

    Returns:
        Markdown index of recipe names. Drill down with ``elf_recipe_get``.
    """
    recipes = list_recipes(tag=tag or None, solver=solver or None)
    return format_recipe_index(recipes)


@mcp.tool()
def elf_recipe_search(query: str, top_k: int = 5, tag: str = "", solver: str = "") -> str:
    """
    Search public-safe workflow recipes by goal or keyword.

    Args:
        query: Goal or keywords, e.g. "back EMF pickup", "cogging torque",
               "current mutual flux", "MOMC frequency".
        top_k: Max recipes to return.
        tag: Optional tag filter.
        solver: Optional solver filter.

    Returns:
        Ranked recipe summaries with ``elf_recipe_get`` drilldown hints.
    """
    results = search_recipes(query, top_k=top_k, tag=tag or None, solver=solver or None)
    return format_search_results(results, query)


@mcp.tool()
def elf_recipe_get(name: str) -> str:
    """
    Get one public-safe workflow recipe by name.

    Args:
        name: Recipe name or unambiguous substring. Use
              ``elf_recipe_index`` or ``elf_recipe_search`` to discover
              names.

    Returns:
        Full recipe card with use cases, elements, PRE/SOL commands, outputs,
        checks, pitfalls, examples, and follow-up recipes.
    """
    recipe = get_recipe(name)
    if recipe is None:
        return f"No unique recipe named '{name}'. Try elf_recipe_index() or elf_recipe_search()."
    return format_recipe(recipe)


@mcp.tool()
def elf_plan_workflow(goal: str) -> str:
    """
    Propose a short ELF workflow plan from a natural-language goal.

    This is a recipe-level planner, not a solver. It chooses public-safe
    workflow cards and lists first checks and pitfalls.

    Args:
        goal: Natural-language target, e.g. "measure motor back EMF",
              "cogging torque sweep", "mutual inductance between coils".

    Returns:
        Markdown plan with recipe sequence and drilldown command.
    """
    return plan_workflow(goal)


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
        print("[1/16] elf_usage topics:")
        topics = [
            "overview", "mai_format", "mei_format", "meg_format",
            "magic", "elfin", "beam", "element_types", "bh_curves",
            "sol_commands", "mei_commands", "ipm_motor", "motor_radia_bridge",
            "inductance",
            "magnetization", "examples", "meg_export",
            "treasure_box", "sinusoidal", "anisotropy", "sted",
            "meshing", "convergence", "force_methods", "errors",
            "iemesh", "tools", "cln_extraction", "licensing", "python_api",
            "live_drive",
        ]
        for t in topics:
            result = elf_usage(t)
            assert len(result) > 50, f"Topic '{t}' too short"
        print(f"  {len(topics)} topics OK")

        # 2. Help index
        print("[2/16] elf_help_index:")
        idx = elf_help_index()
        n_files = len(list_help_files())
        assert n_files > 1000, f"Expected >1000 files, got {n_files}"
        print(f"  {n_files} files indexed")
        idx_mrf1 = elf_help_index("m_rf1/")
        assert "m_rf1/index.htm" in idx_mrf1, "m_rf1/ filter missed index.htm"
        print(f"  m_rf1/ filter OK")

        # 3. Help search
        print("[3/16] elf_help_search:")
        for q in ["MOMC", "渦電流", "OHM2", "FORC"]:
            r = elf_help_search(q, top_k=5)
            assert "No matches" not in r, f"Query '{q}' had no matches"
        print(f"  4 queries OK")

        # 4. Help get
        print("[4/16] elf_help_get:")
        for p in ["m_rf1/index.htm", "d_ken/MOMC.htm", "u_support/error.htm"]:
            r = elf_help_get(p)
            assert "Error reading" not in r, f"Failed to read {p}"
            assert len(r) > 100, f"{p} returned too little"
        print(f"  3 files OK")

        # 5. Examples index
        print("[5/16] elf_examples_index:")
        all_idx = elf_examples_index()
        n_ex = len(list_examples())
        assert n_ex > 300, f"Expected >300 examples, got {n_ex}"
        magic_idx = elf_examples_index(solver="MAGIC")
        assert "magic/BASIC/" in magic_idx, "MAGIC filter missed BASIC/"
        mai_idx = elf_examples_index(ext="mai")
        n_mai = len(list_examples(ext="mai"))
        assert n_mai > 100, f"Expected >100 .mai files, got {n_mai}"
        print(f"  {n_ex} examples ({n_mai} .mai), filters OK")

        # 6. Examples search
        print("[6/16] elf_examples_search:")
        for q in ["MOMC", "OHM2", "FREQ", "PRE"]:
            r = elf_examples_search(q, top_k=5)
            assert "No matches" not in r, f"Query '{q}' had no matches"
        print(f"  4 queries OK")

        # 7. Examples get
        print("[7/16] elf_examples_get:")
        for p in ["magic/BASIC/ABCL2.mai"]:
            r = elf_examples_get(p)
            assert "Error reading" not in r, f"Failed to read {p}"
            assert "MOMC" in r or "PRE" in r, f"{p} missing expected MAGIC keyword"
        print(f"  1 file OK")

        print("[8/16] elf_examples_playbook:")
        pb = elf_examples_playbook()
        assert pb.count("\n## ") >= 100, "Expected >=100 playbook cards"
        magic_pb = elf_examples_playbook(limit=120, solver="MAGIC")
        assert "97 cards" in magic_pb, "Expected 97 bundled MAGIC .mai cards"
        force_pb = elf_examples_playbook(limit=20, feature="maxwell-force")
        assert "SOL FORT" in force_pb or "MCM" in force_pb, "Maxwell-force filter missed force examples"
        print("  100-card playbook + filters OK")

        # 9. Public sample decks
        print("[9/16] elf_sample_decks tools:")
        sd = elf_sample_decks_index()
        assert "motor/pm_cosine_pickup_72/pm001/pm001.mai" in sd
        assert "motor/pm_cosine_pickup_72/pm001/pm001.meg" in sd
        assert "motor/spm_surface_pm_10/spm001/spm001.mai" in sd
        assert "motor/srm_switched_reluctance_10/srm001/srm001.mai" in sd
        assert "motor/induction_cage_10/im001/im001.mai" in sd
        assert "application/transformer_core_pickup_12/tf001/tf001.mai" in sd
        assert "application/mri_gradient_shield_12/mri001/mri001.mai" in sd
        assert "application/wpt_coupled_coils_10/wpt001/wpt001.mai" in sd
        assert "application/wpt_loop_10/wpl001/wpl001.mai" in sd
        assert "application/mri_loop_10/mrl001/mrl001.mai" in sd
        assert "motor/sr_motor_loop_10/srl001/srl001.mai" in sd
        assert "motor/spm_loop_10/spl001/spl001.mai" in sd
        assert "application/ih_induction_heating_10/ihl001/ihl001.mai" in sd
        assert "motor/reluctance_motor_10/ryl001/ryl001.mai" in sd
        assert "motor/hysteresis_motor_10/hyl001/hyl001.mai" in sd
        assert "application/transformer_loop_10/tfl001/tfl001.mai" in sd
        assert "application/accelerator_magnet_10/acl001/acl001.mai" in sd
        assert "application/actuator_plunger_10/atl001/atl001.mai" in sd
        assert "application/maglev_bearing_10/mvl001/mvl001.mai" in sd
        assert "application/magnetic_separator_10/msl001/msl001.mai" in sd
        assert "application/eddy_current_brake_10/ebl001/ebl001.mai" in sd
        assert "application/ndt_eddy_probe_10/ndl001/ndl001.mai" in sd
        assert "application/magnetic_gear_10/mgl001/mgl001.mai" in sd
        assert "application/voice_coil_10/vcl001/vcl001.mai" in sd
        assert "application/relay_solenoid_10/rsl001/rsl001.mai" in sd
        assert "application/hall_sensor_fixture_10/hsl001/hsl001.mai" in sd
        assert "application/electromagnetic_clutch_10/ecl001/ecl001.mai" in sd
        sd_mai = elf_sample_decks_index(ext="mai")
        assert sd_mai.count(".mai") == 586, "Expected 586 public .mai decks"
        sd_search = elf_sample_decks_search("HBCN FLUM", top_k=5, ext="mai")
        assert "pm001.mai" in sd_search and "No sample deck matches" not in sd_search
        sd_spm_search = elf_sample_decks_search("SPM HBRM FLUM", top_k=5, ext="mai")
        assert "motor/spm_surface_pm_10" in sd_spm_search
        sd_srm_search = elf_sample_decks_search("SRM reluctance FLUM", top_k=5, ext="mai")
        assert "motor/srm_switched_reluctance_10" in sd_srm_search
        sd_im_search = elf_sample_decks_search("induction motor cage OHM2 FLUM", top_k=5, ext="mai")
        assert "motor/induction_cage_10" in sd_im_search
        sd_app_search = elf_sample_decks_search("MRI OHM2 FREQ", top_k=5, ext="mai")
        assert "application/mri_gradient_shield_12" in sd_app_search
        sd_wpt_search = elf_sample_decks_search("WPT MOMC FLUM", top_k=5, ext="mai")
        assert "application/wpt_coupled_coils_10" in sd_wpt_search
        sd_wpt_loop_search = elf_sample_decks_search("Loop10 WPT MOMC FLUM", top_k=5, ext="mai")
        assert "application/wpt_loop_10" in sd_wpt_loop_search
        sd_mri_loop_search = elf_sample_decks_search("Loop10 MRI OHM2 FREQ", top_k=5, ext="mai")
        assert "application/mri_loop_10" in sd_mri_loop_search
        sd_sr_loop_search = elf_sample_decks_search("SR-motor reluctance FLUM", top_k=5, ext="mai")
        assert "motor/sr_motor_loop_10" in sd_sr_loop_search
        sd_spm_loop_search = elf_sample_decks_search("Loop10 SPM HBRM FLUM", top_k=5, ext="mai")
        assert "motor/spm_loop_10" in sd_spm_loop_search
        sd_ih_search = elf_sample_decks_search("IH induction-heating MOMC", top_k=5, ext="mai")
        assert "application/ih_induction_heating_10" in sd_ih_search
        sd_reluctance_search = elf_sample_decks_search("reluctance motor synchronous saliency", top_k=5, ext="mai")
        assert "motor/reluctance_motor_10" in sd_reluctance_search
        sd_hysteresis_search = elf_sample_decks_search("hysteresis motor high-coercivity", top_k=5, ext="mai")
        assert "motor/hysteresis_motor_10" in sd_hysteresis_search
        sd_transformer_loop_search = elf_sample_decks_search("Loop10 transformer FLUM", top_k=5, ext="mai")
        assert "application/transformer_loop_10" in sd_transformer_loop_search
        sd_accelerator_search = elf_sample_decks_search("accelerator electromagnet FLUM", top_k=5, ext="mai")
        assert "application/accelerator_magnet_10" in sd_accelerator_search
        sd_actuator_search = elf_sample_decks_search("Loop11 actuator plunger FLUM", top_k=5, ext="mai")
        assert "application/actuator_plunger_10" in sd_actuator_search
        sd_maglev_search = elf_sample_decks_search("Loop11 maglev bearing FLUM", top_k=5, ext="mai")
        assert "application/maglev_bearing_10" in sd_maglev_search
        sd_separator_search = elf_sample_decks_search("Loop11 magnetic separator FLUM", top_k=5, ext="mai")
        assert "application/magnetic_separator_10" in sd_separator_search
        sd_brake_search = elf_sample_decks_search("Loop11 eddy-current brake OHM2", top_k=5, ext="mai")
        assert "application/eddy_current_brake_10" in sd_brake_search
        sd_ndt_search = elf_sample_decks_search("Loop11 NDT eddy-current probe OHM2", top_k=5, ext="mai")
        assert "application/ndt_eddy_probe_10" in sd_ndt_search
        sd_gear_search = elf_sample_decks_search("Loop12 magnetic gear HBCN FLUM", top_k=5, ext="mai")
        assert "application/magnetic_gear_10" in sd_gear_search
        sd_voice_search = elf_sample_decks_search("Loop12 voice-coil actuator FLUM", top_k=5, ext="mai")
        assert "application/voice_coil_10" in sd_voice_search
        sd_relay_search = elf_sample_decks_search("Loop12 relay solenoid FLUM", top_k=5, ext="mai")
        assert "application/relay_solenoid_10" in sd_relay_search
        sd_hall_search = elf_sample_decks_search("Loop12 Hall-sensor fixture FLUM", top_k=5, ext="mai")
        assert "application/hall_sensor_fixture_10" in sd_hall_search
        sd_clutch_search = elf_sample_decks_search("Loop12 electromagnetic clutch OHM2", top_k=5, ext="mai")
        assert "application/electromagnetic_clutch_10" in sd_clutch_search
        sd_get = elf_sample_decks_get("motor/pm_cosine_pickup_72/pm001/pm001.mai")
        assert "HBCN 1 0 1" in sd_get and "HBCN 2 0 2" in sd_get
        sd_pb = elf_sample_decks_playbook(limit=28, family="pm_square")
        assert sd_pb.count("\n## ") == 28, "Expected 28 sample deck playbook cards"
        sd_app_pb = elf_sample_decks_playbook(limit=20, family="transformer_core_pickup_12")
        assert sd_app_pb.count("\n## ") == 12, "Expected 12 transformer sample cards"
        sd_loop_pb = elf_sample_decks_playbook(limit=20, family="accelerator_magnet_10")
        assert sd_loop_pb.count("\n## ") == 10, "Expected 10 accelerator sample cards"
        sd_loop11_pb = elf_sample_decks_playbook(limit=20, family="actuator_plunger_10")
        assert sd_loop11_pb.count("\n## ") == 10, "Expected 10 actuator sample cards"
        sd_loop12_pb = elf_sample_decks_playbook(limit=20, family="magnetic_gear_10")
        assert sd_loop12_pb.count("\n## ") == 10, "Expected 10 magnetic-gear sample cards"
        assert "Python-interface seed manifest" not in sd_pb, "Normal sample playbook must not claim team28"
        sample_text = (
            sd + sd_mai + sd_search + sd_spm_search + sd_srm_search
            + sd_im_search + sd_app_search + sd_wpt_search + sd_get + sd_pb + sd_app_pb
            + sd_wpt_loop_search + sd_mri_loop_search + sd_sr_loop_search
            + sd_spm_loop_search + sd_ih_search + sd_reluctance_search
            + sd_hysteresis_search + sd_transformer_loop_search
            + sd_accelerator_search + sd_actuator_search + sd_maglev_search
            + sd_separator_search + sd_brake_search + sd_ndt_search
            + sd_gear_search + sd_voice_search + sd_relay_search
            + sd_hall_search + sd_clutch_search + sd_loop_pb + sd_loop11_pb
            + sd_loop12_pb
        )
        forbidden_sample_markers = ("C:" + "\\temp", "S:" + "\\", "_cross" + "val", ".mag", ".mao")
        assert not any(marker in sample_text for marker in forbidden_sample_markers)
        print("  586-case .mai/.meg sample deck corpus OK")

        # 10. Recipe tools
        print("[10/16] elf_recipe tools:")
        ri = elf_recipe_index()
        assert "passive_flum_pickup" in ri and "maxwell_torque_surface" in ri
        rs = elf_recipe_search("back EMF pickup", top_k=3)
        assert "passive_flum_pickup" in rs
        rg = elf_recipe_get("mutual_flux_current_pickup")
        assert "FLUM <pickup_mid>" in rg and "AMP1" in rg
        rp = elf_plan_workflow("cogging torque sweep")
        assert "maxwell_torque_surface" in rp
        recipe_text = ri + rs + rg + rp
        private_markers = ("C:" + "\\temp", "_cross" + "val")
        assert not any(marker in recipe_text for marker in private_markers)
        print("  recipe index/search/get/plan OK")

        # 11-13. Wiki tools
        print("[11/16] elf_wiki_index:")
        wi = elf_wiki_index()
        n_w = len(list_wiki_pages())
        assert n_w >= 50, f"Expected >=50 wiki pages, got {n_w}"
        print(f"  {n_w} wiki pages")

        print("[12/16] elf_wiki_search:")
        for q in ["磁場解析", "MAGIC", "渦電流"]:
            r = elf_wiki_search(q, top_k=3)
            assert "No matches" not in r, f"Wiki query '{q}' had no matches"
        print(f"  3 queries OK")

        print("[13/16] elf_wiki_get:")
        for p in ["FAQ", "磁場解析"]:
            r = elf_wiki_get(p)
            assert "Error reading" not in r, f"Failed to read wiki '{p}'"
            assert len(r) > 100
        print(f"  2 pages OK")

        # 14-16. Python interface tools
        print("[14/16] elf_python_index:")
        pi = elf_python_index()
        n_p = len(list_python_files())
        assert n_p >= 10, f"Expected >=10 bin files, got {n_p}"
        py_only = elf_python_index(ext="py")
        assert "elftypes.py" in py_only and "magtypes.py" in py_only
        print(f"  {n_p} files (py filter OK)")

        print("[15/16] elf_python_search:")
        for q in ["GET_FIEL", "SET_AMP1", "ctypes"]:
            r = elf_python_search(q, top_k=3)
            assert "No matches" not in r, f"Python query '{q}' had no matches"
        print(f"  3 queries OK")

        print("[16/16] elf_python_get:")
        for p in ["elftypes.py", "magtypes.py", "ELFERR.def"]:
            r = elf_python_get(p)
            assert "Error reading" not in r, f"Failed to read python '{p}'"
        team28 = elf_python_team28()
        assert "Python-interface seed manifest" in team28
        assert "normal ELF GUI/CLI" in team28
        assert "outside this documentation MCP server" in team28
        assert team28.count("\n## ") == 28, "Expected 28 Python-interface team28 cards"
        print(f"  3 files + Python-interface team28 OK")

        print("PASSED")
        return

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
