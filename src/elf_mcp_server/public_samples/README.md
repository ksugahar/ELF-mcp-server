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

- `motor/`: 362 motor-oriented examples, including 332 permanent-magnet
  pickup decks, 10 explicit SPM decks, 10 SRM switched-reluctance decks,
  and 10 induction cage decks
- `motor/spm_surface_pm_10/`: 10 surface permanent-magnet motor examples
  using `MWL8T` magnets, `MMB8T` iron, three-phase `MCL8T` coils, and `FLUM`
- `motor/induction_cage_10/`: 10 induction motor cage examples using
  three-phase coils, `MAB8T` conducting bars, `OHM2`, and transient `FLUM`
- `motor/srm_switched_reluctance_10/`: 10 switched-reluctance motor examples
  using salient `MMB8T` stator/rotor iron, phase `MCL8T` coils, and `FLUM`
- `application/transformer_core_pickup_12/`: 12 transformer core, primary,
  secondary, and passive pickup-coil examples
- `application/mri_gradient_shield_12/`: 12 MRI gradient-coil and
  eddy-current shield examples using linear AC `SOL MOMC`
- `application/wpt_coupled_coils_10/`: 10 wireless-power-transfer coupled
  coil examples using `SOL MOMC`, primary/secondary `MCL8T` coils, optional
  conducting shields, and `FLUM`
