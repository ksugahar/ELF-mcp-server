# mcp-server-elf

[![PyPI](https://img.shields.io/pypi/v/mcp-server-elf.svg)](https://pypi.org/project/mcp-server-elf/)
[![License: BSD-3-Clause](https://img.shields.io/badge/License-BSD_3--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![Python: 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)

**MCP server providing ELF600 electromagnetic field analysis documentation** — file formats, solver options, element types, and workflow recipes for the [ELF600](https://www.science-solutions.jp/elf/) BEM-based electromagnetic analysis suite (MAGIC magnetostatic, ELFIN electrostatic, BEAM particle tracking).

This server does **not** execute ELF600 simulations — it provides curated documentation that AI coding assistants (Claude Code, Cursor, etc.) can consult while authoring `.mai`/`.mei`/`.meg` input files for ELF.

---

## Features

**13 tools** providing curated docs + raw access to ELF600 help HTM, example inputs, vendor wiki, and Python ctypes API:

| Tool family | Purpose | Files |
|---|---|---|
| `elf_usage(topic)` | 26 curated topics — high-level recipes | (1762-line knowledge.py) |
| `elf_help_*(...)` | Help HTM files from `C:/ELF600/help/` | 1141 files, 1.18M chars |
| `elf_examples_*(...)` | Example .mai/.mei/.txt from `C:/ELF600/examples/` | 332 files, 533k chars |
| `elf_wiki_*(...)` | Vendor wiki pages from elf.co.jp PukiWiki | 67 pages, 176k chars |
| `elf_python_*(...)` | Python ctypes API + configs from `C:/ELF600/bin/` | 15 files, 246k chars |

Each `_*` family has 3 tools: `_index`, `_search(query)`, `_get(path)`.

Bundled data (all generated from fresh ELF600 install via `scripts/crawl_*.py`):
- `help_dump.json` — Shift_JIS HTM decoded + HTML-stripped
- `examples_dump.json` — 228 MAGIC + 66 ELFIN + 38 BEAM input files
- `wiki_dump.json` — 67 curated pages from https://elf.co.jp/
- `python_dump.json` — `elftypes.py`/`magtypes.py` (83 ctypes API functions each), `*.cfg`, `ELFERR.def`/`MESERR.def`, etc.

### Curated topics (`elf_usage`)

Returns documentation on:

- **File formats**: `.mai` (analysis input), `.mei` (mesh script), `.meg` (compiled mesh)
- **Solvers**: MAGIC (magnetostatic, transient, AC), ELFIN (electrostatic), BEAM (particle tracking)
- **Eddy current**: MAB / MAT / MBB elements, time-stepping, sinusoidal AC (SOL MOMC)
- **Element types**: full catalog with DOF counts and symmetry restrictions (3D / 2D / Axisym)
- **B-H curves**: anisotropy (HBA1/HBA2), recoil, extrapolation
- **IPM motor workflow**: Ld/Lq calculation
- **Inductance**: Lsc (JIS) and Ll (IEEJ) with 6 samples
- **Magnetization / demagnetization** (MAGNE2)
- **Convergence** troubleshooting, error codes (160+ ELF-Q/E/W codes)
- **Force methods**: FORC vs FORT vs FIXB
- **Tools**: IEmesh, Wmap3, MagFilter2, MaiEditor3, ELF/Bench

Available topics:
```
all, overview, mai_format, mei_format, meg_format,
magic, elfin, beam, element_types, bh_curves,
sol_commands, mei_commands, ipm_motor, inductance,
magnetization, examples, meg_export, treasure_box,
sinusoidal, anisotropy, sted, meshing, convergence,
force_methods, errors, iemesh, tools, cln_extraction
```

The `cln_extraction` topic documents the 6-step ELF MAGIC -> Cauer Ladder
Network synthesis workflow (Foster fit + Cauer-I/II + 3-way validation
against step response / Joule loss / Lorentz force). Distilled from the
21-script analysis suite in `S:/ELF_MAGIC/2026_04_01_長方形CLN/`.

---

## Installation

```bash
pip install mcp-server-elf
```

Verify:
```bash
mcp-server-elf --selftest
```

---

## Usage

### Claude Code

```bash
claude mcp add elf "C:/Program Files/Python312/Scripts/mcp-server-elf.exe"
```

(Adjust path for your Python install. On Linux/macOS, the script is typically `~/.local/bin/mcp-server-elf` or similar.)

### Cursor / Other MCP clients

Add to your MCP config:
```json
{
  "mcpServers": {
    "elf": {
      "command": "mcp-server-elf"
    }
  }
}
```

### Self-test

```bash
mcp-server-elf --selftest
```
Iterates through all 26 topics and asserts non-empty documentation.

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
