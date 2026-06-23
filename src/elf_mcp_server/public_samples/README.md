# Public ELF/MAGIC Sample Decks

This directory contains lab-authored ELF-runnable ELF/MAGIC input decks.
Only validation-passed input-deck pairs are published here; candidate,
failed, or unverified cases stay outside this directory until they pass the
public sample validation gate and are listed in `VALIDATED_MANIFEST.json`.

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

For these compact public examples, `.meg` files are generated as small ASCII
ELF/MAGIC mesh decks directly by lab-authored Python generators. They are not
generated through Cubit. The normal ELF authoring route remains `.mei` through
IEmesh/mesh750.exe. Cubit also remains useful for larger CAD/mesh workflows:
`cubit_mesh_export.export_meg(...)` and `cubit_mesh_export.export_3D_meg(...)`
can emit ELF-compatible `.meg` meshes when that route is appropriate.

Current families:

- `motor/`: 652 motor-oriented examples, including 332 permanent-magnet
  pickup decks, 10 explicit SPM decks, 10 SRM switched-reluctance decks,
  10 induction cage decks, and 40 loop-reviewed SR/SPM/reluctance/hysteresis
  motor decks, plus 200 EMDLAB-style motor decks covering all bundled EMDLAB
  v0.2.0 motor example scripts, plus 50 Loop13 IPM, wound-field synchronous,
  axial-flux PM, linear PM, and stepper motor decks
- `motor/emdlab_bldc_spm_10/`: 10 EMDLAB-style BLDC/SPM examples using
  slotted stator iron, surface PM rotor proxies, phase coils, and `FLUM`
- `motor/emdlab_ipm_hairpin_10/`: 10 EMDLAB-style IPM hairpin examples with
  buried PM rotor proxies, hairpin-conductor proxy counts, and `FLUM`
- `motor/emdlab_induction_bar_10/`: 10 EMDLAB-style induction-machine rotor-bar
  examples using phase coils, conductive bar proxies, `OHM2`, and `FLUM`
- `motor/emdlab_synrm_flux_barrier_10/`: 10 EMDLAB-style SynRM flux-barrier
  examples with saliency, rotor-angle proxies, and `FLUM`
- `motor/emdlab_srm_pole_variants_10/`: 10 EMDLAB-style SRM pole-variant
  examples covering 6/4, 8/6, 12/8, and 12/16 pole proxy patterns
- `motor/emdlab_afpm_linearized_10/`: 10 EMDLAB-style AFPM linearized-airgap
  examples with unfolded pole pitch, face magnets, stator coils, and `FLUM`
- `motor/emdlab_bldc_outer_rotor_10/`: 10 EMDLAB-style BLDC outer-rotor
  examples with surface PM proxies, stator iron, phase coils, and `FLUM`
- `motor/emdlab_induction_fraction_10/`: 10 EMDLAB-style fractional-sector
  induction-machine examples with phase coils, conducting bars, and `OHM2`
- `motor/emdlab_ipm_hairpin_fraction_10/`: 10 EMDLAB-style fractional-sector
  IPM hairpin examples with buried PMs, hairpin proxies, and `FLUM`
- `motor/emdlab_spmsm_10/`, `motor/emdlab_spmsm_fraction_10/`, and
  `motor/emdlab_spmsm_static_torque_10/`: 30 EMDLAB-style SPMSM examples
  covering full, fractional-sector, and static-torque variants
- `motor/emdlab_srm64_10/`, `motor/emdlab_srm86_10/`,
  `motor/emdlab_srm86_fraction_10/`, `motor/emdlab_srm86_static_torque_10/`,
  `motor/emdlab_srm128_10/`, and `motor/emdlab_srm1216_outer_rotor_10/`: 60
  EMDLAB-style SRM examples covering 6/4, 8/6, 12/8, and 12/16 proxy patterns
- `motor/emdlab_synrm_static_torque_10/` and
  `motor/emdlab_synrm_fraction_static_torque_10/`: 20 EMDLAB-style SynRM
  static-torque examples with flux-barrier and fractional-sector proxies
- `motor/ipm_interior_pm_10/`: 10 Loop13 IPM examples with buried PM pairs,
  rotor/stator iron, phase coils, rotor-angle parameters, and `FLUM`
- `motor/wound_field_sync_10/`: 10 Loop13 wound-field synchronous motor
  examples with DC rotor field coils, stator phase coils, soft iron, and `FLUM`
- `motor/axial_flux_pm_10/`: 10 Loop13 axial-flux PM motor examples with dual
  axial yokes, face magnets, skew offsets, stator coils, and `FLUM`
- `motor/linear_pm_motor_10/`: 10 Loop13 linear PM motor examples with
  alternating PM tracks, moving three-coil forcers, translator offsets, and
  `FLUM`
- `motor/stepper_motor_10/`: 10 Loop13 stepper motor examples with four stator
  phases, PM rotor proxies, detent offsets, and `FLUM`
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
- `application/`: 274 application examples covering transformers, MRI,
  wireless power transfer, induction heating, accelerator electromagnets,
  actuator plungers, maglev bearings, magnetic separators, eddy-current
  brakes, NDT eddy-current probes, magnetic gears, voice-coil actuators,
  relay solenoids, Hall-sensor fixtures, electromagnetic clutches, WPT
  misalignment, MRI gradient sequences, transformer leakage, IH susceptors,
  accelerator corrector magnets, and EMDLAB-style transformer/benchmark decks
- `application/emdlab_1ph_transformer_static_10/`: 10 EMDLAB-style
  single-phase transformer static examples with core limbs, primary/secondary
  coils, and `FLUM`
- `application/emdlab_benchmark_ccore_10/`,
  `application/emdlab_benchmark_geometry_10/`, and
  `application/emdlab_benchmark_magnet_10/`: 30 EMDLAB-style benchmark
  examples covering C-core, geometry, and magnet patterns
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
- `application/actuator_plunger_10/`: 10 actuator plunger examples with
  U-yokes, movable plungers, dual coils, air-gap pickups, and `FLUM`
- `application/maglev_bearing_10/`: 10 maglev/magnetic-bearing examples with
  opposed pole pairs, differential coils, mover offsets, and `FLUM`
- `application/magnetic_separator_10/`: 10 magnetic separator examples with
  PM pole pairs, steel back-yokes, conductive belt proxies, and `FLUM`
- `application/eddy_current_brake_10/`: 10 eddy-current brake examples with
  conducting plates, `OHM2`, AC `SOL MOMC`, and pickup coils
- `application/ndt_eddy_probe_10/`: 10 NDT eddy-current probe examples with
  conductive plates, local flaw-property patches, `OHM2`, and `FLUM`
- `application/magnetic_gear_10/`: 10 magnetic gear examples with alternating
  PM teeth, soft yokes, relative tooth offsets, `HBCN`, and `FLUM`
- `application/voice_coil_10/`: 10 voice-coil actuator examples with PM bias
  fields, moving differential coils, return iron, and `FLUM`
- `application/relay_solenoid_10/`: 10 relay/solenoid examples with U-cores,
  armature gaps, twin coil legs, and `FLUM`
- `application/hall_sensor_fixture_10/`: 10 Hall-sensor fixture examples with
  opposed PM blocks, flux concentrator yokes, probe coils, and `FLUM`
- `application/electromagnetic_clutch_10/`: 10 electromagnetic clutch examples
  with AC coils, steel plates, conducting armatures, `OHM2`, and `FLUM`
- `application/wpt_misalignment_10/`: 10 Loop13 wireless-power-transfer
  misalignment examples with primary/secondary pad offsets, conducting shields,
  `OHM2`, `SOL MOMC`, and `FLUM`
- `application/mri_gradient_sequence_10/`: 10 Loop13 MRI gradient-sequence
  examples with bipolar coils, split eddy-current shields, `OHM2`, `FREQ`, and
  `FLUM`
- `application/transformer_leakage_10/`: 10 Loop13 transformer leakage examples
  with gapped cores, primary/secondary coils, leakage pickup coils, and `FLUM`
- `application/ih_susceptor_ring_10/`: 10 Loop13 induction-heating susceptor
  examples with nested conducting workpieces, `OHM2` contrast, AC coils, and
  `FLUM`
- `application/accelerator_corrector_10/`: 10 Loop13 accelerator corrector
  magnet examples with main dipole coils, trim-correction coils, aperture
  pickup, and `FLUM`
