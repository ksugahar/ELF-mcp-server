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
- `application/`: 184 application examples covering transformers, MRI,
  wireless power transfer, induction heating, accelerator electromagnets,
  actuator plungers, maglev bearings, magnetic separators, eddy-current
  brakes, NDT eddy-current probes, magnetic gears, voice-coil actuators,
  relay solenoids, Hall-sensor fixtures, and electromagnetic clutches
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
