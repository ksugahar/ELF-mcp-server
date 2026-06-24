# ELF-mcp-server

[![PyPI](https://img.shields.io/pypi/v/ELF-mcp-server.svg)](https://pypi.org/project/ELF-mcp-server/)
[![License: BSD-3-Clause](https://img.shields.io/badge/License-BSD_3--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![Python: 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)

**MCP server providing ELF600 electromagnetic field analysis documentation** — file formats, solver options, element types, workflow recipes, and ELF-runnable public input decks for the [ELF600](https://www.science-solutions.jp/elf/) BEM-based electromagnetic analysis suite (MAGIC magnetostatic, ELFIN electrostatic, BEAM particle tracking).

This server does **not** execute ELF600 simulations — it provides curated documentation and public `.mai`/`.meg` input decks that AI coding assistants (Claude Code, Cursor, etc.) can consult while authoring ELF input files.

---

## Features

**26 tools + 1 prompt** providing curated docs, workflow recipes, ELF-runnable public sample decks, prompt-to-sample routing, validation summaries, and raw access to ELF600 help HTM, example inputs, vendor wiki, and Python ctypes API:

| Tool family | Purpose | Files |
|---|---|---|
| `elf_usage(topic)` | 31 curated topics — high-level recipes | (knowledge.py) |
| `elf_help_*(...)` | Help HTM files from `C:/ELF600/help/` | 1141 files, 1.18M chars |
| `elf_examples_*(...)` | Example .mai/.mei/.txt plus 100-card playbook from `C:/ELF600/examples/` | 332 files, 533k chars |
| `elf_sample_decks_*(...)` | Lab-authored ELF-runnable public `.mai`/`.meg` sample decks | 1500 cases, 3000 input files |
| `elf_recipe_*(...)` | Workflow decision cards for elements, PRE/SOL blocks, outputs, checks, and pitfalls | public-safe recipes |
| `elf_wiki_*(...)` | Vendor wiki pages from elf.co.jp PukiWiki | 146 pages, 211k chars |
| `elf_python_*(...)` | Python ctypes API + configs from `C:/ELF600/bin/` | 15 files, 246k chars |

Each `_*` family has 3 tools: `_index`, `_search(query)`, `_get(path)`.
The examples family also has `elf_examples_playbook(limit=100)`, which
summarizes 100 `.mai` examples as compact cards with detected SOL blocks,
element families, feature tags, companion `.mei/.model` files, and reuse hints.
The recipe family also has `elf_plan_workflow(goal)`, which chooses a short
public-safe recipe sequence from a natural-language analysis goal.
The sample deck family has `elf_sample_decks_index/search/route/validation/get/playbook`
for ELF-runnable public `.mai`/`.meg` decks. `elf_sample_decks_route(goal)`
maps a user prompt such as "IPM hairpin motor flux linkage" or
"WPT misalignment" to the most relevant public deck families, follow-up MCP
calls, validation levels, and representative `.mai` files.
`elf_sample_decks_validation()` summarizes the validation level and public
limitations for the corpus before an agent claims a deck is validated.
The Python family also has
`elf_python_team28()`: a compact 28-case seed manifest from the public motor
cases for ELF Python-interface orchestration. `team28` is not a normal
ELF GUI/CLI deck-execution workflow. Solver outputs, comparison metrics,
executable orchestration state, and Python-interface runtime state are not
bundled.

### MCP quick start

For MCP clients, start with `elf_overview()` to discover the server surface and
public boundary. The most useful calls while authoring ELF/MAGIC inputs are:

- `elf_sample_decks_route("IPM hairpin motor flux linkage")` to map a user
  prompt to the right sample family, playbook call, recipe, and representative
  `.mai` decks
- `elf_sample_decks_validation()` to check the public validation levels,
  counts, and limitations before claiming a deck is validated
- `elf_plan_workflow("WPT misalignment with conducting shield")` to get both
  a recipe-level plan and related public sample-deck routes
- `elf_sample_decks_playbook(limit=20, family="pm_square")` for compact cards
  over the public PM motor decks
- `elf_sample_decks_playbook(limit=20, family="spm")` for surface-PM motor
  decks with stator coils, rotor/stator iron, and pickup coils
- `elf_sample_decks_playbook(limit=20, family="srm")` for switched-reluctance
  motor decks with salient iron and phase-pair excitation
- `elf_sample_decks_playbook(limit=20, family="induction_cage_10")` for induction
  motor cage decks with transient eddy-current pickup patterns
- `elf_sample_decks_playbook(limit=20, query="EMDLAB-style")` for 240
  EMDLAB-style decks covering BLDC/SPM, BLDC outer-rotor, SPM static-torque,
  IPM hairpin, induction, SynRM, SRM, AFPM, transformer, and benchmark
  patterns
- `elf_sample_decks_playbook(limit=20, query="Loop13 motor")` for extra IPM,
  wound-field synchronous, axial-flux PM, linear PM, and stepper motor decks
- `elf_sample_decks_playbook(limit=20, family="application")` for transformer
  MRI gradient-coil, WPT coupled-coil, induction-heating, and accelerator
  electromagnet application decks, plus actuator, maglev, separator, brake,
  NDT probe, magnetic-gear, voice-coil, relay/solenoid, Hall-sensor fixture,
  and electromagnetic-clutch decks
- `elf_sample_decks_playbook(limit=20, query="Loop10")` for the 10-cycle
  learning-loop decks across WPT, MRI, SR motor, SPM, IH, reluctance motor,
  hysteresis motor, transformer, and accelerator electromagnet families
- `elf_sample_decks_playbook(limit=20, query="Loop11")` for actuator,
  maglev bearing, magnetic separator, eddy-current brake, and NDT probe decks
- `elf_sample_decks_playbook(limit=20, query="Loop12")` for magnetic gear,
  voice-coil actuator, relay solenoid, Hall-sensor fixture, and
  electromagnetic-clutch decks
- `elf_sample_decks_playbook(limit=20, query="Loop13 application")` for WPT
  misalignment, MRI gradient sequence, transformer leakage, IH susceptor, and
  accelerator corrector decks
- `elf_sample_decks_route("numeric validation anchor FLUM invariant")` for
  decks whose ELF `FLUM` ratios/signs and independent NGSolve proxy invariants
  are both checked
- `elf_sample_decks_route("FLUM law current linearity superposition")` for
  64 numeric FLUM-law decks that validate magnetic flux linkage against
  current, turns, sign, distance, symmetry, superposition, and cancellation
  invariants
- `elf_sample_decks_route("inductance co-energy FLUM turn scaling")` for
  100 numeric decks validating `FLUM`-derived inductance `L = Phi/I` and
  co-energy `W = 1/2 sum(I Phi)` across current, turns, distance, symmetry,
  superposition, and add/cancel energy invariants
- `elf_sample_decks_route("force torque co-energy gradient")` for 100 numeric
  decks validating `FLUM`-derived co-energy force/torque-gradient behavior
  across distance-force sign, current-square scaling, mirror/lateral
  symmetry, angular `dW/dtheta`, and balanced-torque invariants
- `elf_sample_decks_route("AC loss frequency square OHM2")` for 100 numeric
  MOMC/FREQ/OHM2 decks validating AC-loss proxy behavior across frequency
  square, current square, resistivity inverse, distance decay, symmetry,
  add/cancel, thickness, width, and combined `I-f-rho` scaling invariants
- `elf_sample_decks_route("magnetic circuit air gap HBCU")` for 100 numeric
  MMB8T/HBUN/HBCU decks validating magnetic-circuit proxy behavior across
  B-H slope, air-gap reluctance, core area/depth, current/turn scaling,
  mirror sanity, return-yoke continuity, and add/cancel bias invariants
- `elf_sample_decks_route("permanent magnet HBRM polarity FLUM")` for 100
  numeric MWL8T/HBRM/HBCN/VEC3 decks validating permanent-magnet pickup
  behavior across remanence scaling, distance decay, magnet dimensions,
  magnetization angle, polarity reversal, symmetry, add/cancel, array count,
  and pickup-turn scaling invariants
- `elf_sample_decks_search("HBCN FLUM", ext="mai")` to find reusable input
  patterns
- `elf_sample_decks_search("SPM HBRM FLUM", ext="mai")` to find surface-PM
  motor setup patterns
- `elf_sample_decks_search("SRM reluctance FLUM", ext="mai")` to find
  switched-reluctance motor setup patterns
- `elf_sample_decks_search("WPT MOMC FLUM", ext="mai")` to find wireless
  power-transfer AC coupling patterns
- `elf_sample_decks_search("MRI OHM2 FREQ", ext="mai")` to find AC shielding
  and eddy-current setup patterns
- `elf_sample_decks_search("induction motor cage OHM2 FLUM", ext="mai")` to find
  induction-motor cage and pickup setup patterns
- `elf_sample_decks_search("EMDLAB-style IPM hairpin FLUM", ext="mai")` to find
  IPM hairpin motor setup patterns
- `elf_sample_decks_search("EMDLAB-style SynRM flux-barrier FLUM", ext="mai")`
  to find synchronous-reluctance flux-barrier setup patterns
- `elf_sample_decks_search("EMDLAB-style AFPM linearized-airgap FLUM", ext="mai")`
  to find axial-flux PM line-airgap setup patterns
- `elf_sample_decks_search("Loop13 wound-field synchronous FLUM", ext="mai")`
  to find wound-field synchronous motor setup patterns
- `elf_sample_decks_search("Loop13 stepper motor detent FLUM", ext="mai")` to
  find stepper motor setup patterns
- `elf_sample_decks_search("accelerator electromagnet FLUM", ext="mai")` to
  find coil/yoke electromagnet setup patterns
- `elf_sample_decks_search("IH induction-heating MOMC", ext="mai")` to find
  induction-heating AC conductor setup patterns
- `elf_sample_decks_search("Loop11 actuator plunger FLUM", ext="mai")` to find
  solenoid/plunger actuator setup patterns
- `elf_sample_decks_search("Loop11 NDT eddy-current probe OHM2", ext="mai")` to
  find eddy-current inspection probe setup patterns
- `elf_sample_decks_search("Loop12 magnetic gear HBCN FLUM", ext="mai")` to
  find PM magnetic-gear setup patterns
- `elf_sample_decks_search("Loop12 electromagnetic clutch OHM2", ext="mai")` to
  find AC clutch and conducting-plate setup patterns
- `elf_sample_decks_search("Loop13 WPT misalignment OHM2", ext="mai")` to find
  wireless-power-transfer misalignment setup patterns
- `elf_sample_decks_get("motor/pm_cosine_pickup_72/pm001/pm001.mai")` to open a
  concrete public deck
- `elf_python_team28()` to inspect the Python-interface seed manifest

This MCP server is documentation and input-deck retrieval only; it does not
launch ELF, run solvers, manage licenses, or publish validation outputs.

### ELF/MAGIC application input authoring

ELF/MAGIC is useful for magnetostatic and AC magnetic input authoring when the
model is expressed as `.mai` analysis control plus `.meg` mesh data. This server
turns that knowledge into MCP tools:

- 652 public motor input-deck pairs covering 2-pole, 4-pole, 6-pole, 8-pole,
  cosine-remanence PM pickup families, 10 explicit SPM motor examples, and
  10 SRM switched-reluctance examples, 10 induction cage examples, plus
  loop-reviewed SPM, SR motor, synchronous-reluctance motor, hysteresis motor,
  and 200 EMDLAB-style motor cases spanning BLDC/SPM, BLDC outer-rotor,
  induction, IPM hairpin, SPMSM static torque, SynRM, SRM 6/4 through 12/16,
  and AFPM variants, plus Loop13 IPM, wound-field synchronous, axial-flux PM,
  linear PM, and stepper families
- 848 public application input-deck pairs covering transformer core/pickup
  coupling, MRI gradient-coil/eddy-current shield patterns, WPT coupled coils,
  IH induction-heating workpieces, accelerator electromagnets, actuator
  plungers, maglev bearings, magnetic separators, eddy-current brakes,
  NDT eddy-current probes, magnetic gears, voice-coil actuators,
  relay solenoids, Hall-sensor fixtures, electromagnetic clutches, WPT
  misalignment, MRI gradient sequences, transformer leakage, IH susceptors,
  accelerator corrector magnets, 40 EMDLAB-style transformer/benchmark
  application decks, 10 compact numeric-validation anchor decks, and 64
  numeric FLUM-law validation decks, plus 100 numeric inductance/co-energy
  validation decks, 100 numeric force/torque-gradient validation decks, and
  100 numeric AC-loss validation decks, plus 100 numeric magnetic-circuit
  validation decks and 100 numeric permanent-magnet/magnetization validation
  decks
- playbook cards that expose each deck's SOL blocks, PRE keywords, element
  families, feature tags, and reuse hints
- curated motor topics for air-gap field, flux linkage/back-EMF pickup,
  polarity/angle conventions, force outputs, and eddy-current setup
- Python-interface `team28` seed manifest for higher-level orchestration,
  without bundling runtime state or solver outputs

Useful entry points are `elf_usage(topic="ipm_motor")`,
`elf_usage(topic="motor_radia_bridge")`,
`elf_recipe_search("motor pickup")`, and
`elf_sample_decks_route("IPM hairpin motor flux linkage")`,
`elf_sample_decks_playbook(limit=50, family="pm_square")`,
`elf_sample_decks_playbook(family="spm")`, or
`elf_sample_decks_playbook(family="srm")`, or
`elf_sample_decks_playbook(family="induction_cage_10")`, or
`elf_sample_decks_playbook(query="EMDLAB-style")`, or
`elf_sample_decks_playbook(query="Loop13 motor")`. For non-motor applications,
start with `elf_sample_decks_playbook(family="application")`,
`elf_sample_decks_search("transformer FLUM")`,
`elf_sample_decks_search("WPT MOMC FLUM")`, or
`elf_sample_decks_search("MRI OHM2 FREQ")`,
`elf_sample_decks_search("IH induction-heating MOMC")`, or
`elf_sample_decks_search("accelerator electromagnet FLUM")`,
`elf_sample_decks_search("Loop11 actuator plunger FLUM")`, or
`elf_sample_decks_search("Loop11 NDT eddy-current probe OHM2")`,
`elf_sample_decks_search("Loop12 magnetic gear HBCN FLUM")`, or
`elf_sample_decks_search("Loop12 electromagnetic clutch OHM2")`, or
`elf_sample_decks_search("Loop13 WPT misalignment OHM2")`, or
`elf_sample_decks_search("FLUM law superposition")`, or
`elf_sample_decks_route("inductance co-energy FLUM turn scaling")`, or
`elf_sample_decks_route("force torque co-energy gradient")`, or
`elf_sample_decks_route("AC loss frequency square OHM2")`, or
`elf_sample_decks_route("magnetic circuit air gap HBCU")`, or
`elf_sample_decks_route("permanent magnet HBRM polarity FLUM")`.

### Public `.meg` mesh generation

For normal ELF/MAGIC authoring, the canonical mesh path is:

```text
.mei (mesh script) --> IEmesh / mesh750.exe --> .meg
```

For the bundled public sample corpus, the `.meg` files are generated as small
ASCII ELF/MAGIC mesh decks directly by lab-authored Python generators. The
writer emits `BOOK MEP 3.50`, `MGSC`, `MGR1` node records, and 8-node element
connectivity records such as `MMB8T`, `MCL8T`, `MAB8T`, and `MWL8T`. Cubit is
not used for these compact public examples.

For larger CAD/mesh workflows, Cubit-side `cubit_mesh_export` also supports
ELF-compatible `.meg` export through helper calls such as
`cubit_mesh_export.export_meg(cubit, "model.meg", DIM="T")` and
`cubit_mesh_export.export_3D_meg(cubit, "model")`. A command-style route such
as `radia_export meg "output.meg" threed labels "1:MMB,2:MWL"` is documented in
`elf_usage(topic="meg_export")`. The published examples keep the geometry
deliberately inspectable and dependency-free.

### Public lint

Before publishing, run:

```bash
python -m pytest
elf-mcp-server --selftest
elf-mcp-policy-lint
```

`elf-mcp-policy-lint` checks the public package boundary: no private validation
paths, no unrelated commercial-tool references, no bundled solver outputs
inside the public sample decks, and exact agreement with
`public_samples/VALIDATED_MANIFEST.json` and
`public_samples/PUBLICATION_BATCHES.json`. Only sample families marked
`validation: passed` in that manifest are intended for publication.
The manifest records the validation level for each family:
`ngsolve_proxy_energy` or `ngsolve_numeric_invariant`. All 1500 public sample
decks are cross-checked with an independent NGSolve proxy-field energy gate
before they are listed. The numeric-validation anchor decks and numeric
FLUM-law decks go one level further; the numeric inductance/co-energy decks
also require `FLUM`-derived `L = Phi/I` and `W = 1/2 sum(I Phi)` invariants.
The numeric force/torque-gradient decks add `FLUM`-derived co-energy
finite-difference checks for `dW/dx` and angular `dW/dtheta` trends.
The numeric AC-loss decks add MOMC/FREQ/OHM2 decks with AC `FLUM` series
checks and NGSolve proxy invariants for `P ~ I^2 f^2 / rho` trends.
The numeric magnetic-circuit decks add MMB8T/HBUN/HBCU decks with `FLUM`
sanity checks and NGSolve proxy invariants for B-H slope, air-gap reluctance,
core area/depth, return-yoke, and add/cancel bias trends.
The numeric permanent-magnet decks add MWL8T/HBRM/HBCN/VEC3 decks with
`FLUM` sanity checks and NGSolve proxy invariants for remanence, PM volume,
magnetization angle, polarity reversal, add/cancel, array count, and pickup
turn scaling trends.
ELF `FLUM` invariants and independent NGSolve proxy invariants must both pass.
MCP clients can inspect this contract with `elf_sample_decks_validation()`;
the broad proxy gate is intentionally not claimed as a full absolute field,
force, torque, or loss agreement suite.
The publication batch manifest groups the validated baseline into deterministic
100-case checkpoints: 15 full checkpoints, 1500 cases total.
The next 100-case checkpoint is 1600 cases, so 100 additional validated cases
are needed before the next clean 100-case publication increment.

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
