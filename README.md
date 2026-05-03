# mcp-server-elf

[![PyPI](https://img.shields.io/pypi/v/mcp-server-elf.svg)](https://pypi.org/project/mcp-server-elf/)
[![License: BSD-3-Clause](https://img.shields.io/badge/License-BSD_3--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![Python: 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)

**MCP server providing ELF600 electromagnetic field analysis documentation** — file formats, solver options, element types, and workflow recipes for the [ELF600](https://www.science-solutions.jp/elf/) BEM-based electromagnetic analysis suite (MAGIC magnetostatic, ELFIN electrostatic, BEAM particle tracking).

This server does **not** execute ELF600 simulations — it provides curated documentation that AI coding assistants (Claude Code, Cursor, etc.) can consult while authoring `.mai`/`.mei`/`.meg` input files for ELF.

---

## Features

**4 tools** providing both curated topic-based docs and raw access to all 1141 ELF600 help HTM files:

| Tool | Purpose |
|---|---|
| `elf_usage(topic)` | 26 curated topics — high-level recipes |
| `elf_help_index(prefix)` | List all 1141 bundled help files (filterable by directory) |
| `elf_help_search(query, top_k, prefix)` | Substring search across all help text (AND multi-keyword) |
| `elf_help_get(path, max_chars)` | Get full extracted text of a specific HTM |

The bundled `help_dump.json` is generated from `C:/ELF600/help/` Shift_JIS HTM files via `scripts/crawl_help.py` (1141 files, ~1.18M characters, decoded + HTML-stripped).

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
force_methods, errors, iemesh, tools
```

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
