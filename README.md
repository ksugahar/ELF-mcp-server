# ELF-mcp-server

[![PyPI](https://img.shields.io/pypi/v/ELF-mcp-server.svg)](https://pypi.org/project/ELF-mcp-server/)
[![License: BSD-3-Clause](https://img.shields.io/badge/License-BSD_3--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![Python: 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)

**MCP server providing ELF600 electromagnetic field analysis documentation** — file formats, solver options, element types, workflow recipes, and ELF-runnable public input decks for the [ELF600](https://www.science-solutions.jp/elf/) BEM-based electromagnetic analysis suite (MAGIC magnetostatic, ELFIN electrostatic, BEAM particle tracking).

This server does **not** execute ELF600 simulations — it provides curated documentation and public `.mai`/`.meg` input decks that AI coding assistants (Claude Code, Cursor, etc.) can consult while authoring ELF input files.

---

## Features

**24 tools + 1 prompt** providing curated docs, workflow recipes, ELF-runnable public sample decks, and raw access to ELF600 help HTM, example inputs, vendor wiki, and Python ctypes API:

| Tool family | Purpose | Files |
|---|---|---|
| `elf_usage(topic)` | 31 curated topics — high-level recipes | (knowledge.py) |
| `elf_help_*(...)` | Help HTM files from `C:/ELF600/help/` | 1141 files, 1.18M chars |
| `elf_examples_*(...)` | Example .mai/.mei/.txt plus 100-card playbook from `C:/ELF600/examples/` | 332 files, 533k chars |
| `elf_sample_decks_*(...)` | Lab-authored ELF-runnable public `.mai`/`.meg` sample decks | 356 cases, 712 input files |
| `elf_recipe_*(...)` | Workflow decision cards for elements, PRE/SOL blocks, outputs, checks, and pitfalls | public-safe recipes |
| `elf_wiki_*(...)` | Vendor wiki pages from elf.co.jp PukiWiki | 146 pages, 211k chars |
| `elf_python_*(...)` | Python ctypes API + configs from `C:/ELF600/bin/` | 15 files, 246k chars |

Each `_*` family has 3 tools: `_index`, `_search(query)`, `_get(path)`.
The examples family also has `elf_examples_playbook(limit=100)`, which
summarizes 100 `.mai` examples as compact cards with detected SOL blocks,
element families, feature tags, companion `.mei/.model` files, and reuse hints.
The recipe family also has `elf_plan_workflow(goal)`, which chooses a short
public-safe recipe sequence from a natural-language analysis goal.
The sample deck family has `elf_sample_decks_index/search/get/playbook`
for ELF-runnable public `.mai`/`.meg` decks. The Python family also has
`elf_python_team28()`: a compact 28-case seed manifest from the public motor
cases for ELF Python-interface orchestration. `team28` is not a normal
ELF GUI/CLI deck-execution workflow. Solver outputs, comparison metrics,
executable orchestration state, and Python-interface runtime state are not
bundled.

### MCP quick start

For MCP clients, start with `elf_overview()` to discover the server surface and
public boundary. The most useful calls while authoring ELF/MAGIC inputs are:

- `elf_sample_decks_playbook(limit=20, family="pm_square")` for compact cards
  over the public motor decks
- `elf_sample_decks_playbook(limit=20, family="application")` for transformer
  and MRI gradient-coil application decks
- `elf_sample_decks_search("HBCN FLUM", ext="mai")` to find reusable input
  patterns
- `elf_sample_decks_search("MRI OHM2 FREQ", ext="mai")` to find AC shielding
  and eddy-current setup patterns
- `elf_sample_decks_get("motor/pm_cosine_pickup_72/pm001/pm001.mai")` to open a
  concrete public deck
- `elf_python_team28()` to inspect the Python-interface seed manifest

This MCP server is documentation and input-deck retrieval only; it does not
launch ELF, run solvers, manage licenses, or publish validation outputs.

### ELF/MAGIC application input authoring

ELF/MAGIC is useful for magnetostatic and AC magnetic input authoring when the
model is expressed as `.mai` analysis control plus `.meg` mesh data. This server
turns that knowledge into MCP tools:

- 332 public motor input-deck pairs covering 2-pole, 4-pole, 6-pole, 8-pole,
  and cosine-remanence PM pickup families
- 24 public application input-deck pairs covering transformer core/pickup
  coupling and MRI gradient-coil/eddy-current shield patterns
- playbook cards that expose each deck's SOL blocks, PRE keywords, element
  families, feature tags, and reuse hints
- curated motor topics for air-gap field, flux linkage/back-EMF pickup,
  polarity/angle conventions, force outputs, and eddy-current setup
- Python-interface `team28` seed manifest for higher-level orchestration,
  without bundling runtime state or solver outputs

Useful entry points are `elf_usage(topic="ipm_motor")`,
`elf_usage(topic="motor_radia_bridge")`,
`elf_recipe_search("motor pickup")`, and
`elf_sample_decks_playbook(limit=50, family="pm_square")`. For non-motor
applications, start with `elf_sample_decks_playbook(family="application")`,
`elf_sample_decks_search("transformer FLUM")`, or
`elf_sample_decks_search("MRI OHM2 FREQ")`.

### Public lint

Before publishing, run:

```bash
python -m pytest
elf-mcp-server --selftest
elf-mcp-policy-lint
```

`elf-mcp-policy-lint` checks the public package boundary: no private validation
paths, no unrelated commercial-tool references, and no bundled solver outputs
inside the public sample decks.

Bundled data (all generated from fresh ELF600 install via `scripts/crawl_*.py`):
- `help_dump.json` — Shift_JIS HTM decoded + HTML-stripped
- `examples_dump.json` — 228 MAGIC + 66 ELFIN + 38 BEAM input files
- `wiki_dump.json` — 146 curated pages from https://elf.co.jp/
- `python_dump.json` — `elftypes.py`/`magtypes.py` (83 ctypes API functions each), `*.cfg`, `ELFERR.def`/`MESERR.def`, etc.

### Curated topics (`elf_usage`)

Returns documentation on:

- **File formats**: `.mai` (analysis input), `.mei` (mesh script), `.meg` (compiled mesh)
- **Solvers**: MAGIC (magnetostatic, transient, AC), ELFIN (electrostatic), BEAM (particle tracking)
- **Eddy current**: MAB / MAT / MBB elements, time-stepping, sinusoidal AC (SOL MOMC)
- **Element types**: full catalog with DOF counts and symmetry restrictions (3D / 2D / Axisym)
- **B-H curves**: anisotropy (HBA1/HBA2), recoil, extrapolation
- **Motor workflows**: IPM Ld/Lq plus a radia-mcp/open-FEA concept bridge for air-gap field, torque, flux linkage/back-EMF, lamination, and eddy-current studies
- **Inductance**: Lsc (JIS) and Ll (IEEJ) with 6 samples
- **Magnetization / demagnetization** (MAGNE2)
- **Convergence** troubleshooting, error codes (160+ ELF-Q/E/W codes)
- **Force methods**: FORC vs FORT vs FIXB
- **Tools**: IEmesh, Wmap3, MagFilter2, MaiEditor3, ELF/Bench

Available topics:
```
all, overview, mai_format, mei_format, meg_format,
magic, elfin, beam, element_types, bh_curves,
sol_commands, mei_commands, ipm_motor, motor_radia_bridge, inductance,
magnetization, examples, meg_export, treasure_box,
sinusoidal, anisotropy, sted, meshing, convergence,
force_methods, errors, iemesh, tools, cln_extraction,
licensing, python_api, live_drive
```

The `cln_extraction` topic documents the 6-step ELF MAGIC -> Cauer Ladder
Network synthesis workflow (Foster fit + Cauer-I/II + 3-way validation
against step response / Joule loss / Lorentz force). Distilled from a
21-script rectangular-CLN reference analysis suite.

---

## Installation

```bash
pip install ELF-mcp-server
```

The current PyPI distribution name is `ELF-mcp-server`. The installed console
scripts remain lowercase: `elf-mcp-server` and `elf-mcp-policy-lint`.

Verify:
```bash
elf-mcp-server --selftest
```

---

## Usage

### Claude Code

```bash
claude mcp add elf "C:/Program Files/Python312/Scripts/elf-mcp-server.exe"
```

(Adjust path for your Python install. On Linux/macOS, the script is typically `~/.local/bin/elf-mcp-server` or similar.)

### Cursor / Other MCP clients

Add to your MCP config:
```json
{
  "mcpServers": {
    "elf": {
      "command": "elf-mcp-server"
    }
  }
}
```

### Self-test

```bash
elf-mcp-server --selftest
```
Iterates through all curated topics and asserts non-empty documentation.

---

## What is ELF600?

ELF600 is a commercial BEM (Boundary Element Method) electromagnetic analysis suite distributed by Science Solutions International Laboratory ([https://www.science-solutions.jp/elf/](https://www.science-solutions.jp/elf/)).

| Module | Purpose |
|--------|---------|
| **MAGIC** | Magnetostatic field (static, transient, AC). Eddy current via MAB/MAT/MBB. |
| **ELFIN** | Electrostatic field analysis (D-E curves) |
| **BEAM** | Charged particle beam tracking |

Workflow:
```
.mei (mesh script) --> IEmesh --> .meg (compiled mesh)
.mai (analysis) + .meg --> MAGIC/ELFIN/BEAM --> .mag/.mao results
```

---

## Why this server?

LLM coding agents authoring ELF input files (`.mai`/`.mei`) need access to:
- The ~60k character ELF reference manual content,
- Element naming conventions (T/K/R symmetry × element family),
- SOL block recipes (MOME / MOMC / FIEL / FORC / NONL),
- Frequency-sweep AC analysis structure,
- Common error code interpretation,

without polluting context with the entire vendor PDF. This MCP server returns just the relevant topical chunk on demand.

---

## License

BSD-3-Clause. See [LICENSE](./LICENSE).

ELF600 itself is a commercial product of Science Solutions International Laboratory and is not redistributed by this package — only documentation references.

---

## Author

Kengo Sugahara, Kindai University ([ksugahar@ele.kindai.ac.jp](mailto:ksugahar@ele.kindai.ac.jp))
