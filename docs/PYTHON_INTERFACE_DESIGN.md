# ELF/MAGIC Python Interface Design

- schema: `elf-python-interface-design/v1`
- topic: `overview`
- boundary: Public package scope: API design, schemas, prompt routing, deck-builder contracts, validation gates, and local-runner handoff contracts. The package must not bundle product binaries, execute ELF/MAGIC, expose raw solver output, or publish private validation provenance.

## Implementation Policy
- `product_python_is_reference_not_required`: The existing product-side Python implementation is useful as a reference, but the public facade does not have to depend on it or mirror its surface if a clearer API is needed for MCP users.
- `vendor_dll_is_immutable_boundary`: The ELF/MAGIC DLL boundary is owned by the product vendor and is not modified by this project. Public work wraps, discovers, and orchestrates it from the outside.
- `public_api_may_expand_above_product_python`: If the current Python implementation is insufficient as an API collection, the MCP server and public Python facade may add typed schemas, deck builders, validators, routers, and result contracts as public code.

## Layered Architecture
- `elfmagic-python public facade`: A small, typed Python package that turns user intent into stable data models and public input-deck text. It can be published without product binaries and without requiring the product-side Python implementation, because the backend is discovered at runtime on the user's machine.
  artifacts: `MotorSpec / MaterialSpec / WindingSpec / StudySpec dataclasses`, `DeckBundle containing .mai text, .meg text or reference, and metadata`, `ObservableRequest for flux linkage, torque, force, field, loss, and status`, `DQAxisMapPlan, MTPASearchPlan, ReluctanceMotorDesignPlan, EfficiencyMapPlan, LossModelContract, TorqueSpeedEnvelope, InductionSlipSweepPlan, WindingLayoutPlan, TopologyParameterPlan, DemagMarginPlan, DriveCyclePlan, OptimizationStudyPlan, VoltageFieldWeakeningPlan, CoggingRipplePlan, AirgapHarmonicsNVHPlan, ThermalNetworkPlan, ManufacturingTolerancePlan, MaterialVariationPlan, FeasibilityStudy, OperatingPointRunQueue, InverterPWMHarmonicPlan, SaturationInductanceMapPlan, RotorStressRetentionPlan, RunResultParser, OptimizationLoop, NGSolveResultCrosscheck, DrawingBOMHandoff, and MotorValidationScorecard`, `RunRequest / RunResult JSON-compatible contracts`
- `backend adapter protocol`: A pluggable interface for a user-local product installation. The public package defines the protocol; local/private adapters may call a vendor DLL, command-line runner, or dry-run validator.
  artifacts: `discover() returns version/capability metadata without hard-coded paths`, `validate_inputs(bundle) checks .mai/.meg pairing and requested observables`, `run(request) executes only in a user-local environment`, `parse_result(run_directory) returns RunResult with normalized observables`
- `MCP orchestration`: The MCP server routes natural-language goals to sample-deck families, Python schemas, validation expectations, and a local runner contract. It remains product-solver-free while generating open validation scripts where appropriate.
  artifacts: `elf_python_interface_design(topic)`, `elf_python_ngsolve_validation_plan(goal)`, `elf_python_ngsolve_validation_script(goal)`, `elf_motor_hybrid_router(goal)`, `elf_local_simulation_handoff(goal)`, `elf_sample_decks_validation_matrix(quantity)`
- `independent validation bridge`: Use public-safe validation labels and independent open validation targets to decide whether a result is plausible before iterating design changes.
  artifacts: `observable contract checks`, `physics quantity labels`, `AGE validation targets`, `NGSolve thermal/NVH/stress validation scripts`, `MMM quick checks`, `public sample quality labels`

## Motor API Vocabulary
- `MotorSpec`
  required: `motor_type`, `pole_pairs`, `stator_slots`, `rotor_topology`, `airgap_m`, `stack_length_m`, `materials`, `windings`, `studies`
  motor_type_values: `spm`, `ipm`, `pm_assisted_synrm`, `bldc`, `line_start_pm`, `induction`, `deep_bar_induction`, `srm`, `synrm`, `hysteresis`, `wound_field_sync`, `axial_flux_pm`, `linear_pm`, `stepper`, `flux_switching_pm`, `vernier_pm`, `transverse_flux_pm`, `slotless_pm`, `claw_pole`, `commutator_dc`
- `StudySpec`
  values: `static_flux_linkage`, `static_torque_angle`, `back_emf_speed_sweep`, `dq_inductance`, `cogging_torque`, `induction_slip_loss`, `ac_loss_frequency_sweep`, `thermal_loss_export`
- `ObservableRequest`
  values: `flux_linkage`, `back_emf_constant`, `torque`, `torque_ripple`, `cogging_torque`, `ld_lq`, `field_probe`, `loss_proxy`, `convergence_status`
- `DQAxisMapPlan`
  required: `id_axis_a_peak`, `iq_axis_a_peak`, `current_limit_a_peak`, `pm_torque_nm_proxy`, `reluctance_torque_nm_proxy`, `total_torque_nm_proxy`
- `MTPASearchPlan`
  required: `current_angle_axis_deg_from_q_axis`, `torque_per_amp_proxy`, `best_proxy_point`, `local_runner_sequence`
- `ReluctanceMotorDesignPlan`
  required: `motor_type`, `saliency_targets`, `dq_axis_map_plan`, `mtpa_search_plan`, `aligned_unaligned_inductance_checks`
- `EfficiencyMapPlan`
  required: `torque_axis_nm`, `speed_axis_rpm`, `operating_points`, `loss_model_contract`, `postprocess_outputs`
- `InductionSlipSweepPlan`
  required: `pole_pairs`, `supply_frequency_hz`, `slip_axis`, `synchronous_speed_rpm`, `operating_points`
- `WindingLayoutPlan`
  required: `stator_slots`, `pole_pairs`, `slots_per_pole_per_phase`, `slot_electrical_angle_deg`, `coil_pitch_slots`, `winding_factors`, `slot_table`
- `TopologyParameterPlan`
  required: `motor_type`, `rotor_topology`, `outer_diameter_mm`, `stack_length_mm`, `parameters`, `geometry_regions`
- `DemagMarginPlan`
  required: `temperature_c`, `br_hot_t_proxy`, `hcj_ka_m`, `id_min_a_peak`, `risk_label`, `required_observables`
- `DriveCyclePlan`
  required: `target_market`, `operating_points`, `weighted_outputs`, `quality_gates`
- `OptimizationStudyPlan`
  required: `objective`, `budget`, `design_variables`, `constraints`, `ranking_outputs`, `workflow`
- `VoltageFieldWeakeningPlan`
  required: `dc_bus_v`, `current_limit_a_peak`, `dq_parameters`, `rows`, `required_observables`
- `CoggingRipplePlan`
  required: `stator_slots`, `poles`, `cogging_order_mechanical`, `mitigation_variables`, `parser_keys`
- `AirgapHarmonicsNVHPlan`
  required: `mechanical_force_orders`, `speed_rows`, `required_observables`, `ngsolve_follow_up`
- `ThermalNetworkPlan`
  required: `total_loss_w`, `nodes`, `required_inputs`, `ngsolve_follow_up`
- `ManufacturingTolerancePlan`
  required: `airgap_mm`, `production_intent`, `tolerance_variables`, `doe_rows`, `required_observables`
- `MaterialVariationPlan`
  required: `focus`, `variables`, `recommended_observables`, `study_rules`
- `FeasibilityStudy`
  required: `goal`, `production_intent`, `lanes`, `extra_quality_gates`, `mcp_can_do`, `mcp_cannot_claim_alone`
- `OperatingPointRunQueue`
  required: `run_rows`, `requested_observables`, `parser_keys`, `quality_gates`
- `InverterPWMHarmonicPlan`
  required: `modulation`, `switching_frequency_hz`, `harmonic_rows`, `required_observables`, `validation_routes`
- `SaturationInductanceMapPlan`
  required: `current_axis_a_peak`, `angle_axis_deg_from_q_axis`, `map_rows`, `parser_keys`, `quality_gates`
- `RotorStressRetentionPlan`
  required: `max_speed_rpm`, `tip_speed_m_s`, `hoop_stress_mpa_proxy`, `retention_margin_proxy`, `ngsolve_follow_up`
- `RunResultParser`
  required: `case_id`, `status`, `parsed_observables`, `warnings`, `validation_labels`
- `OptimizationLoop`
  required: `ranked_candidates`, `best_candidate`, `next_run_rows`, `promotion_rules`
- `NGSolveResultCrosscheck`
  required: `overall_status`, `run_result_status`, `lane_checks`, `next_actions`
- `DrawingBOMHandoff`
  required: `drawing_views`, `key_dimensions`, `bom`, `winding_summary`, `quality_gates`
- `MotorValidationScorecard`
  required: `overall_status`, `score`, `gate_results`, `promotion_decision`, `next_actions`
- `NGSolveValidationSpec`
  lanes: `thermal`, `nvh`, `stress`
  required_after_runresult: `loss inputs for thermal validation`, `torque-ripple/cogging/force-order inputs for NVH validation`, `speed/material/rotor-radius inputs for stress validation`

## Backend Protocol
- purpose: A pluggable interface for a user-local product installation. The public package defines the protocol; local/private adapters may call a vendor DLL, command-line runner, or dry-run validator.
- calls: `discover() returns version/capability metadata without hard-coded paths`, `validate_inputs(bundle) checks .mai/.meg pairing and requested observables`, `run(request) executes only in a user-local environment`, `parse_result(run_directory) returns RunResult with normalized observables`

## Deck Generation Contract
- inputs: `MotorSpec or ApplicationSpec`, `StudySpec`, `ObservableRequest list`, `source public sample deck path`, `parameter overrides`
- outputs: `DeckBundle.mai_text`, `DeckBundle.meg_text or meg_path`, `DeckBundle.metadata`, `DeckBundle.validation_label`
- rule: Deck generation may create or mutate input decks. Product execution and raw result files remain outside the public MCP package.

## MEG Generation Strategies
- `cubit_mesh_export`: Use a headless mesh-export backend to produce `.meg` input data from an explicit geometry script. The public API records the backend choice and checks the `.mai/.meg` pair, but does not start GUI sessions or bundle proprietary outputs.
  best for: `3D product-like geometry`, `curved solids`, `high-order or CAD-driven meshes`, `repeatable mesh export pipelines`
- `netgen_2d`: Use a deterministic 2D geometry/mesh pipeline, then emit `.meg` through the public deck-bundle contract.
  best for: `2D motor cross-sections`, `polygonal coils and magnets`, `quick air-gap studies`, `LLM-authored geometry that needs deterministic remeshing`
- `llm_2d_template`: Allow an LLM to draft constrained 2D geometry only inside a typed schema. The generated `.meg` path must pass syntax lint, geometry sanity checks, and independent physics trend checks before being advertised as validated.
  best for: `simple 2D educational decks`, `parametric slot/magnet/coil templates`, `rapid MCP prompt-to-deck prototyping`

## Validation Gates
- `schema_lint` (public): required fields are present, units are explicit, observable names match the parser contract, no product path is embedded
- `deck_contract_lint` (public): .mai and .meg are paired, SOL blocks match requested studies, FLUM/FIEL/FORC/FORT/FIXB requests match requested observables, quality label is carried forward
- `local_product_smoke` (user-local/private): backend is discoverable, dry-run input validation succeeds, solver return status is captured, raw outputs stay local unless explicitly scrubbed
- `independent_physics_cross_check` (public route plus local/private numeric result): sign and scale pass MMM quick check, AGE target is selected for the motor family, trend checks pass for current, angle, frequency, or slip sweep, deviation is reported as a quality label, not hidden
- `ngsolve_multiphysics_validation` (public script plus local numeric inputs): thermal rise is solved in an NGSolve H1 heat model, NVH order separation is checked with an NGSolve modal proxy, rotor stress margin is checked with an NGSolve VectorH1 elasticity model, generated scripts do not call product solvers or product DLLs

## Recommended MCP Calls
- `elf_python_interface_design("motor_api")`
- `elf_motor_hybrid_router("SPM back EMF and torque ripple")`
- `elf_local_simulation_handoff("IPM torque angle sweep")`
- `elf_sample_decks_validation_matrix(quantity="motor")`
- `elf_motor_mmm_quick_check(motor_type="spm")`

## Vendor Proposal
- `stable runtime discovery`: A Python interface becomes much easier to support if the product can report version, installed modules, license state, and supported entry points through a stable call.
- `thin official DLL boundary, rich open Python facade`: The vendor can keep product implementation and binaries closed while the community-facing Python layer improves ergonomics, typing, MCP routing, and examples.
- `machine-readable run status and result index`: Agents need structured status, generated-file manifests, warnings, and observable names to avoid scraping logs or overclaiming results.
- `small conformance deck set`: A fixed public-safe set of input-only decks plus expected observable names lets Python adapters test compatibility without exposing private benchmark numbers.

## Roadmap
- `P0 design contract` [started]: public API/layer design in MCP, motor schema and observable vocabulary, backend adapter protocol, validation gate list
- `P1 public facade skeleton` [next]: standalone dataclasses and JSON schema export, deck bundle builder interface, dry-run lints over public .mai/.meg decks, no product binary dependency
- `P2 user-local backend adapter` [private/user-local]: runtime discovery, local run request/response, result parser to normalized observables, private validation logs outside the public package
- `P3 motor integrated workflow` [planned]: SPM/IPM/PMa-SynRM/BLDC/line-start PM/deep-bar IM/flux-switching/Vernier/transverse-flux/slotless/claw-pole/commutator routing, AGE validation target selection, MMM quick-check trend labels, MCP prompt-to-runner orchestration
