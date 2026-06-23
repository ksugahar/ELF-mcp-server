# Public ELF/MAGIC Sample Decks

This directory contains lab-authored ELF-runnable ELF/MAGIC input decks.

Included files are input decks only:

- `.mai` analysis-control files
- `.meg` mesh files

Excluded files:

- solver outputs such as `.mag`, `.mao`, `.mat`, `.mac`
- comparison tables, benchmark metrics, or regression summaries
- machine-local paths or private provenance

The decks are intended as public examples that users can inspect, copy, and run
with their own ELF/MAGIC installation. The MCP server itself does not execute
ELF/MAGIC or bundle solver results.

Current families:

- `motor/`: 332 permanent-magnet pickup examples for motor-oriented input
  authoring
- `application/transformer_core_pickup_12/`: 12 transformer core, primary,
  secondary, and passive pickup-coil examples
- `application/mri_gradient_shield_12/`: 12 MRI gradient-coil and
  eddy-current shield examples using linear AC `SOL MOMC`
