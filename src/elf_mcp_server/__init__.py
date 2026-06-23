"""ELF-mcp-server: MCP server providing ELF600 electromagnetic field analysis documentation.

ELF600 (https://www.science-solutions.jp/elf/) is a BEM-based commercial
electromagnetic analysis suite (MAGIC magnetostatic / ELFIN electrostatic /
BEAM particle tracking solvers, with eddy current support in MAGIC via
MAB/MAT/MBB elements).

This server exposes 24 MCP tools plus one prompt: curated documentation,
workflow recipes, public PM/SPM/SRM/reluctance/hysteresis motor and
WPT/MRI/IH/transformer/accelerator-electromagnet sample-deck playbooks,
bundled help/example/wiki/Python API search, and compact planning aids for
authoring ELF input files.
"""

__version__ = "1.41.0"
