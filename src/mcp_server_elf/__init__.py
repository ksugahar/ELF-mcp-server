"""mcp-server-elf: MCP server providing ELF600 electromagnetic field analysis documentation.

ELF600 (https://www.science-solutions.jp/elf/) is a BEM-based commercial
electromagnetic analysis suite (MAGIC magnetostatic / ELFIN electrostatic /
BEAM particle tracking solvers, with eddy current support in MAGIC via
MAB/MAT/MBB elements).

This server exposes one tool, ``elf_usage(topic)``, returning curated
documentation on file formats (.mai/.mei/.meg), solver modules, element
types, B-H curves, IPM motor workflows, sinusoidal AC analysis (SOL MOMC),
and more.
"""

__version__ = "1.33.0"
