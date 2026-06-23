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

- `motor/`: 402 motor-oriented examples, including 332 permanent-magnet
  pickup decks, 10 explicit SPM decks, 10 SRM switched-reluctance decks,
  10 induction cage decks, and 40 loop-reviewed SR/SPM/reluctance/hysteresis
  motor decks
- `motor/spm_surface_pm_10/`: 10 surface permanent-magnet motor examples
  using `MWL8T` magnets, `MMB8T` iron, three-phase `MCL8T` coils, and `FLUM`
- `motor/spm_loop_10/`: 10 loop-reviewed surface-PM motor examples using
  `MWL8T` magnets, stator coils, rotor/stator iron, and `FLUM`
- `motor/induction_cage_10/`: 10 induction motor cage examples using
  three-phase coils, `MAB8T` conducting bars, `OHM2`, and transient `FLUM`
- `motor/srm_switched_reluctance_10/`: 10 switched-reluctance motor examples
  using salient `MMB8T` stator/rotor iron, phase `MCL8T` coils, and `FLUM`
- `motor/sr_motor_loop_10/`: 10 loop-reviewed SR-motor examples with salient
  stator/rotor iron, phase coils, rotor-angle sweeps, and `FLUM`
- `motor/reluctance_motor_10/`: 10 synchronous-reluctance motor examples with
  saliency, phase excitation, and passive pickup coils
- `motor/hysteresis_motor_10/`: 10 high-coercivity hysteresis-motor input-deck
  proxy examples using origin-starting B-H curves and pickup coils
- `application/`: 84 application examples covering transformers, MRI,
  wireless power transfer, induction heating, and accelerator electromagnets
- `application/transformer_core_pickup_12/`: 12 transformer core, primary,
  secondary, and passive pickup-coil examples
- `application/transformer_loop_10/`: 10 loop-reviewed transformer core,
  primary, secondary, and passive pickup-coil examples
- `application/mri_gradient_shield_12/`: 12 MRI gradient-coil and
  eddy-current shield examples using linear AC `SOL MOMC`
- `application/mri_loop_10/`: 10 loop-reviewed MRI gradient-coil and
  conducting-shield examples with `OHM2`, `FREQ`, and `FLUM`
- `application/wpt_coupled_coils_10/`: 10 wireless-power-transfer coupled
  coil examples using `SOL MOMC`, primary/secondary `MCL8T` coils, optional
  conducting shields, and `FLUM`
- `application/wpt_loop_10/`: 10 loop-reviewed wireless-power-transfer
  coupled-coil examples with primary/secondary coils, optional shields, and
  `FLUM`
- `application/ih_induction_heating_10/`: 10 induction-heating examples with
  `MCL8T` coils, `MAB8T` conducting workpieces, `OHM2`, and `SOL MOMC`
- `application/accelerator_magnet_10/`: 10 accelerator electromagnet examples
  with yokes, excitation coils, aperture pickups, and `FLUM`
