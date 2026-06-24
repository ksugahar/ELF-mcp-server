"""Public ELF-runnable ELF/MAGIC sample input decks.

This corpus contains lab-authored .mai/.meg decks only. It intentionally
excludes solver outputs, comparison metrics, private paths, and provenance.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
import json
import re
from typing import Any


ROOT = "public_samples"

VALIDATION_LEVEL_DESCRIPTIONS = {
    "solver_smoke": (
        "ELF/MAGIC input-pair presence and local solver-run smoke checks passed."
    ),
    "ngsolve_proxy_energy": (
        "ELF/MAGIC run checks passed, and an independent NGSolve proxy-field "
        "energy sanity check was positive."
    ),
    "ngsolve_numeric_invariant": (
        "ELF FLUM-derived numeric invariants and independent NGSolve proxy "
        "invariants both passed for numeric anchor cases."
    ),
}

VALIDATION_LEVEL_ORDER = (
    "ngsolve_numeric_invariant",
    "ngsolve_proxy_energy",
    "solver_smoke",
)

VALIDATION_LIMITATIONS = (
    "The public package bundles input decks and validation metadata only; "
    "solver outputs, regression logs, private paths, and provenance are not bundled.",
    "`ngsolve_proxy_energy` is a broad independent proxy-field gate for deck "
    "sanity, not a full absolute field/force/torque/loss agreement suite.",
    "`ngsolve_numeric_invariant` is used for numeric anchor families where "
    "ELF FLUM-derived flux, energy, force/torque-gradient, AC-loss, "
    "magnetic-circuit, and permanent-magnet invariants and NGSolve proxy "
    "invariants are both checked.",
)

FAMILY_META = {
    "application/mri_gradient_shield_12": {
        "title": "MRI gradient coil with eddy-current shield",
        "tags": (
            "application",
            "mri",
            "gradient-coil",
            "eddy-current",
            "shield",
            "momc",
            "mab8t",
            "ohm2",
            "fiel",
            "flum",
        ),
        "hint": "Use when a linear AC gradient-coil, conducting shield, or MOMC/FREQ pattern is needed.",
    },
    "application/mri_loop_10": {
        "title": "Loop10 MRI gradient and shield campaign",
        "tags": (
            "application",
            "mri",
            "gradient-coil",
            "eddy-current",
            "shield",
            "momc",
            "mab8t",
            "ohm2",
            "freq",
            "flum",
            "loop10",
        ),
        "hint": "Use for loop-reviewed MRI gradient-coil/shield input patterns with AC MOMC/FREQ setup and FLUM probes.",
    },
    "application/accelerator_magnet_10": {
        "title": "Loop10 accelerator electromagnet campaign",
        "tags": (
            "application",
            "accelerator",
            "electromagnet",
            "quadrupole",
            "dipole",
            "yoke",
            "mmb8t",
            "mcl8t",
            "flum",
            "loop10",
        ),
        "hint": "Use for accelerator-style yoke electromagnets, coil polarity patterns, quadrupole/dipole variants, and FLUM pickup.",
    },
    "application/actuator_plunger_10": {
        "title": "Loop11 actuator plunger campaign",
        "tags": (
            "application",
            "actuator",
            "plunger",
            "solenoid",
            "u-yoke",
            "mome",
            "mmb8t",
            "mcl8t",
            "coi1",
            "amp1",
            "flum",
            "loop11",
        ),
        "hint": "Use for solenoid/actuator input decks with a U-yoke, movable plunger, dual coils, air-gap pickup, and static FLUM.",
    },
    "application/eddy_current_brake_10": {
        "title": "Loop11 eddy-current brake campaign",
        "tags": (
            "application",
            "eddy-current",
            "brake",
            "conducting-plate",
            "momc",
            "freq",
            "ohm2",
            "mab8t",
            "mmb8t",
            "mcl8t",
            "flum",
            "loop11",
        ),
        "hint": "Use for AC eddy-current brake decks with a conducting plate, steel yoke, differential coils, OHM2, FREQ, and FLUM pickup.",
    },
    "application/electromagnetic_clutch_10": {
        "title": "Loop12 electromagnetic clutch campaign",
        "tags": (
            "application",
            "electromagnetic-clutch",
            "clutch",
            "eddy-current",
            "momc",
            "freq",
            "ohm2",
            "mab8t",
            "mmb8t",
            "mcl8t",
            "flum",
            "loop12",
        ),
        "hint": "Use for AC electromagnetic-clutch decks with steel plates, conducting armature plates, differential coils, OHM2, FREQ, and FLUM pickup.",
    },
    "application/hall_sensor_fixture_10": {
        "title": "Loop12 Hall-sensor fixture campaign",
        "tags": (
            "application",
            "hall-sensor",
            "sensor-fixture",
            "pm",
            "flux-concentrator",
            "mome",
            "mwl8t",
            "mmb8t",
            "mcl8t",
            "flum",
            "loop12",
        ),
        "hint": "Use for Hall-sensor fixture decks with opposed PM blocks, flux concentrator yokes, probe/pickup coils, and static FLUM.",
    },
    "application/ih_induction_heating_10": {
        "title": "Loop10 induction-heating coil campaign",
        "tags": (
            "application",
            "ih",
            "induction-heating",
            "momc",
            "freq",
            "mab8t",
            "ohm2",
            "mcl8t",
            "flum",
            "loop10",
        ),
        "hint": "Use for induction-heating coils, conducting workpieces, AC MOMC/FREQ setup, OHM2 conductors, and FLUM checks.",
    },
    "application/maglev_bearing_10": {
        "title": "Loop11 maglev bearing campaign",
        "tags": (
            "application",
            "maglev",
            "bearing",
            "differential-coils",
            "mome",
            "mmb8t",
            "mcl8t",
            "coi1",
            "amp1",
            "flum",
            "loop11",
        ),
        "hint": "Use for magnetic-bearing or maglev-style pole pairs, mover-offset sweeps, differential coil signs, and static FLUM pickup.",
    },
    "application/magnetic_separator_10": {
        "title": "Loop11 magnetic separator campaign",
        "tags": (
            "application",
            "magnetic-separator",
            "separator",
            "pm",
            "belt",
            "mome",
            "mwl8t",
            "mmb8t",
            "mab8t",
            "ohm2",
            "flum",
            "loop11",
        ),
        "hint": "Use for magnetic-separator decks with PM pole pairs, steel back-yokes, conductive belt proxies, and FLUM pickup.",
    },
    "application/magnetic_gear_10": {
        "title": "Loop12 magnetic gear campaign",
        "tags": (
            "application",
            "magnetic-gear",
            "pm",
            "soft-yoke",
            "mome",
            "mwl8t",
            "mmb8t",
            "mcl8t",
            "hbrm",
            "hbcn",
            "flum",
            "loop12",
        ),
        "hint": "Use for magnetic-gear input decks with alternating PM teeth, soft yokes, relative tooth offsets, and FLUM pickup.",
    },
    "application/ndt_eddy_probe_10": {
        "title": "Loop11 NDT eddy-current probe campaign",
        "tags": (
            "application",
            "ndt",
            "eddy-current",
            "probe",
            "flaw",
            "conductivity-contrast",
            "momc",
            "freq",
            "ohm2",
            "mab8t",
            "mcl8t",
            "flum",
            "loop11",
        ),
        "hint": "Use for NDT eddy-current probe decks with conductive plates, flaw-property patches, OHM2 contrast, FREQ sweeps, and FLUM pickup.",
    },
    "application/relay_solenoid_10": {
        "title": "Loop12 relay solenoid campaign",
        "tags": (
            "application",
            "relay",
            "solenoid",
            "armature",
            "u-core",
            "mome",
            "mmb8t",
            "mcl8t",
            "coi1",
            "amp1",
            "flum",
            "loop12",
        ),
        "hint": "Use for relay/solenoid decks with U-cores, armature air gaps, twin coil legs, and static FLUM pickup.",
    },
    "application/transformer_loop_10": {
        "title": "Loop10 transformer core and pickup campaign",
        "tags": (
            "application",
            "transformer",
            "core",
            "primary",
            "secondary",
            "pickup",
            "mmb8t",
            "mcl8t",
            "flum",
            "loop10",
        ),
        "hint": "Use for loop-reviewed transformer-style core/coil coupling, primary-secondary polarity, passive pickup FLUM, and B-H setup.",
    },
    "application/wpt_coupled_coils_10": {
        "title": "WPT coupled coils with AC flux pickup",
        "tags": (
            "application",
            "wpt",
            "wireless-power-transfer",
            "coupled-coils",
            "momc",
            "freq",
            "mcl8t",
            "mab8t",
            "ohm2",
            "flum",
            "shield",
        ),
        "hint": "Use for WPT primary/secondary coil pads, AC MOMC/FREQ setup, optional conducting shields, and FLUM coupling checks.",
    },
    "application/wpt_loop_10": {
        "title": "Loop10 WPT coupled-coil campaign",
        "tags": (
            "application",
            "wpt",
            "wireless-power-transfer",
            "coupled-coils",
            "momc",
            "freq",
            "mcl8t",
            "mab8t",
            "ohm2",
            "flum",
            "loop10",
        ),
        "hint": "Use for loop-reviewed WPT primary/secondary coil pads, AC MOMC/FREQ setup, conducting shields, and FLUM coupling checks.",
    },
    "application/voice_coil_10": {
        "title": "Loop12 voice-coil actuator campaign",
        "tags": (
            "application",
            "voice-coil",
            "actuator",
            "pm-bias",
            "moving-coil",
            "mome",
            "mwl8t",
            "mmb8t",
            "mcl8t",
            "coi1",
            "amp1",
            "flum",
            "loop12",
        ),
        "hint": "Use for voice-coil actuator decks with PM bias fields, moving differential coils, return iron, and static FLUM pickup.",
    },
    "application/transformer_core_pickup_12": {
        "title": "Transformer core and passive pickup coil",
        "tags": (
            "application",
            "transformer",
            "core",
            "primary",
            "secondary",
            "pickup",
            "mmb8t",
            "mcl8t",
            "flum",
        ),
        "hint": "Use for transformer-style core/coil coupling, passive pickup FLUM, and nonlinear B-H setup.",
    },
    "motor/emdlab_afpm_linearized_10": {
        "title": "EMDLAB-style AFPM linearized-airgap campaign",
        "tags": (
            "motor",
            "emdlab-style",
            "afpm",
            "axial-flux",
            "pm",
            "linearized-airgap",
            "line-airgap",
            "mwl8t",
            "mmb8t",
            "mcl8t",
            "hbrm",
            "hbcn",
            "flum",
            "ngsolve-crossval",
        ),
        "hint": "Use for axial-flux PM motor authoring patterns represented as unfolded line-airgap decks with face magnets, stator coils, and FLUM pickup.",
    },
    "motor/emdlab_bldc_spm_10": {
        "title": "EMDLAB-style BLDC/SPM slotted-stator campaign",
        "tags": (
            "motor",
            "emdlab-style",
            "bldc",
            "spm",
            "surface-pm",
            "pm",
            "slotted-stator",
            "three-phase",
            "mwl8t",
            "mmb8t",
            "mcl8t",
            "hbrm",
            "hbcn",
            "flum",
            "ngsolve-crossval",
        ),
        "hint": "Use for BLDC/SPM motor input patterns with surface PM rotor proxies, slotted stator iron, phase coils, and passive FLUM pickup.",
    },
    "motor/emdlab_induction_bar_10": {
        "title": "EMDLAB-style induction-machine rotor-bar campaign",
        "tags": (
            "motor",
            "emdlab-style",
            "induction",
            "im",
            "rotor-bar",
            "squirrel-cage",
            "three-phase",
            "mab8t",
            "ohm2",
            "mcl8t",
            "flum",
            "ngsolve-crossval",
        ),
        "hint": "Use for induction-machine rotor-bar decks with stator phase coils, conductive bar proxies, OHM2 material data, and FLUM pickup.",
    },
    "motor/emdlab_ipm_hairpin_10": {
        "title": "EMDLAB-style IPM hairpin campaign",
        "tags": (
            "motor",
            "emdlab-style",
            "ipm",
            "interior-pm",
            "hairpin",
            "54-slot",
            "buried-pm",
            "three-phase",
            "mwl8t",
            "mmb8t",
            "mcl8t",
            "hbrm",
            "hbcn",
            "flum",
            "ngsolve-crossval",
        ),
        "hint": "Use for IPM hairpin-style authoring with buried PM rotor proxies, stator phase coils, rotor-angle sweeps, and FLUM pickup.",
    },
    "motor/emdlab_srm_pole_variants_10": {
        "title": "EMDLAB-style SRM pole-variant campaign",
        "tags": (
            "motor",
            "emdlab-style",
            "srm",
            "switched-reluctance",
            "reluctance",
            "pole-variant",
            "6-4",
            "8-6",
            "12-8",
            "12-16",
            "salient",
            "mmb8t",
            "mcl8t",
            "coi1",
            "amp1",
            "flum",
            "ngsolve-crossval",
        ),
        "hint": "Use for SRM 6/4, 8/6, 12/8, and 12/16 pole-variant decks with salient iron, phase-pair excitation, and FLUM pickup.",
    },
    "motor/emdlab_synrm_flux_barrier_10": {
        "title": "EMDLAB-style SynRM flux-barrier campaign",
        "tags": (
            "motor",
            "emdlab-style",
            "synrm",
            "synchronous-reluctance",
            "reluctance",
            "flux-barrier",
            "saliency",
            "mmb8t",
            "mcl8t",
            "coi1",
            "amp1",
            "flum",
            "ngsolve-crossval",
        ),
        "hint": "Use for synchronous-reluctance flux-barrier rotor proxies, stator phase coils, rotor-angle sweeps, and FLUM pickup.",
    },
    "application/accelerator_corrector_10": {
        "title": "Loop13 accelerator corrector magnet campaign",
        "tags": (
            "application",
            "accelerator",
            "corrector",
            "electromagnet",
            "dipole",
            "trim-coil",
            "mome",
            "mmb8t",
            "mcl8t",
            "coi1",
            "amp1",
            "flum",
            "loop13",
            "ngsolve-crossval",
        ),
        "hint": "Use for accelerator corrector magnet decks with main dipole coils, trim-correction coils, aperture pickup, and static FLUM.",
    },
    "application/ih_susceptor_ring_10": {
        "title": "Loop13 IH susceptor ring campaign",
        "tags": (
            "application",
            "ih",
            "induction-heating",
            "susceptor",
            "ring",
            "momc",
            "freq",
            "mab8t",
            "ohm2",
            "mcl8t",
            "flum",
            "loop13",
            "ngsolve-crossval",
        ),
        "hint": "Use for induction-heating susceptor decks with nested conducting workpieces, OHM2 contrast, AC coils, and FLUM pickup.",
    },
    "application/mri_gradient_sequence_10": {
        "title": "Loop13 MRI gradient sequence campaign",
        "tags": (
            "application",
            "mri",
            "gradient-sequence",
            "bipolar-gradient",
            "eddy-current",
            "shield",
            "momc",
            "freq",
            "mab8t",
            "ohm2",
            "flum",
            "loop13",
            "ngsolve-crossval",
        ),
        "hint": "Use for MRI gradient sequence decks with bipolar coils, split eddy-current shields, OHM2, FREQ, and FLUM pickup.",
    },
    "application/transformer_leakage_10": {
        "title": "Loop13 transformer leakage campaign",
        "tags": (
            "application",
            "transformer",
            "leakage",
            "gapped-core",
            "primary",
            "secondary",
            "mome",
            "mmb8t",
            "mcl8t",
            "coi1",
            "amp1",
            "flum",
            "loop13",
            "ngsolve-crossval",
        ),
        "hint": "Use for transformer leakage-flux decks with gapped cores, primary/secondary coils, leakage pickup coils, and FLUM.",
    },
    "application/wpt_misalignment_10": {
        "title": "Loop13 WPT misalignment campaign",
        "tags": (
            "application",
            "wpt",
            "wireless-power-transfer",
            "misalignment",
            "lateral-offset",
            "conducting-shield",
            "momc",
            "freq",
            "mab8t",
            "ohm2",
            "mcl8t",
            "flum",
            "loop13",
            "ngsolve-crossval",
        ),
        "hint": "Use for WPT decks with primary/secondary pad offset, conducting shield plates, AC MOMC/FREQ setup, and FLUM pickup.",
    },
    "motor/axial_flux_pm_10": {
        "title": "Loop13 axial-flux PM motor campaign",
        "tags": (
            "motor",
            "afpm",
            "axial-flux",
            "pm",
            "face-magnet",
            "skew",
            "mwl8t",
            "mmb8t",
            "mcl8t",
            "hbrm",
            "hbcn",
            "flum",
            "loop13",
            "ngsolve-crossval",
        ),
        "hint": "Use for axial-flux PM motor decks with dual axial yokes, face magnets, central stator coils, skew offsets, and FLUM.",
    },
    "motor/ipm_interior_pm_10": {
        "title": "Loop13 IPM interior permanent-magnet campaign",
        "tags": (
            "motor",
            "ipm",
            "interior-pm",
            "buried-pm",
            "pm",
            "rotor-angle",
            "mwl8t",
            "mmb8t",
            "mcl8t",
            "hbrm",
            "hbcn",
            "flum",
            "loop13",
            "ngsolve-crossval",
        ),
        "hint": "Use for interior permanent-magnet motor decks with buried PM pairs, rotor/stator iron, phase coils, rotor-angle parameters, and FLUM.",
    },
    "motor/linear_pm_motor_10": {
        "title": "Loop13 linear PM motor campaign",
        "tags": (
            "motor",
            "linear-pm",
            "linear-motor",
            "pm",
            "translator",
            "forcer",
            "offset",
            "mwl8t",
            "mmb8t",
            "mcl8t",
            "hbrm",
            "hbcn",
            "flum",
            "loop13",
            "ngsolve-crossval",
        ),
        "hint": "Use for linear PM motor decks with alternating PM tracks, moving three-coil forcers, translator offsets, and FLUM pickup.",
    },
    "motor/stepper_motor_10": {
        "title": "Loop13 stepper motor campaign",
        "tags": (
            "motor",
            "stepper",
            "stepper-motor",
            "pm",
            "four-phase",
            "detent",
            "mwl8t",
            "mmb8t",
            "mcl8t",
            "hbrm",
            "hbcn",
            "flum",
            "loop13",
            "ngsolve-crossval",
        ),
        "hint": "Use for stepper motor decks with four stator phases, PM rotor proxies, detent offsets, and FLUM pickup.",
    },
    "motor/wound_field_sync_10": {
        "title": "Loop13 wound-field synchronous motor campaign",
        "tags": (
            "motor",
            "wound-field",
            "synchronous",
            "field-coil",
            "rotor-field",
            "mome",
            "mmb8t",
            "mcl8t",
            "coi1",
            "amp1",
            "flum",
            "loop13",
            "ngsolve-crossval",
        ),
        "hint": "Use for wound-field synchronous motor decks with DC rotor field coils, stator phase coils, soft iron, and FLUM pickup.",
    },
    "motor/induction_cage_10": {
        "title": "Induction motor cage and transient pickup",
        "tags": (
            "motor",
            "induction",
            "im",
            "squirrel-cage",
            "cage",
            "eddy-current",
            "three-phase",
            "mab8t",
            "ohm2",
            "mcl8t",
            "flum",
            "transient",
        ),
        "hint": "Use for induction-motor cage bars, three-phase stator COI1/AMP1 patterns, OHM2 conductors, and transient FLUM pickup.",
    },
    "motor/srm_switched_reluctance_10": {
        "title": "Switched-reluctance motor phase excitation",
        "tags": (
            "motor",
            "srm",
            "switched-reluctance",
            "reluctance",
            "salient",
            "stator",
            "rotor",
            "mmb8t",
            "mcl8t",
            "coi1",
            "amp1",
            "flum",
            "pickup",
        ),
        "hint": "Use for SRM-style salient stator/rotor iron, phase-pair excitation, rotor-angle sweeps, and passive FLUM pickup.",
    },
    "motor/hysteresis_motor_10": {
        "title": "Loop10 hysteresis motor input-deck proxy",
        "tags": (
            "motor",
            "hysteresis",
            "hysteresis-motor",
            "high-coercivity",
            "rotor-ring",
            "mmb8t",
            "mcl8t",
            "flum",
            "loop10",
            "proxy",
        ),
        "hint": "Use as an input-deck proxy and authoring pattern for high-coercivity rotor rings; ELF B-H curves start at the origin.",
    },
    "motor/pm_cosine_pickup_72": {
        "title": "2-pole cosine-amplitude PM pickup",
        "tags": ("motor", "pm", "cosine-remanence", "hbrm", "hbcn", "flum", "pickup"),
        "hint": "Use when spatially varying PM remanence or per-segment HBCN curve assignment matters.",
    },
    "motor/spm_surface_pm_10": {
        "title": "Surface PM motor with stator coils",
        "tags": (
            "motor",
            "spm",
            "surface-pm",
            "pm",
            "three-phase",
            "stator",
            "rotor",
            "mwl8t",
            "mmb8t",
            "mcl8t",
            "hbrm",
            "hbcn",
            "flum",
            "pickup",
        ),
        "hint": "Use for compact SPM motor authoring with surface MWL8T magnets, stator coils, rotor/stator iron, and passive FLUM pickup.",
    },
    "motor/reluctance_motor_10": {
        "title": "Loop10 synchronous reluctance motor campaign",
        "tags": (
            "motor",
            "reluctance",
            "synchronous-reluctance",
            "synrm",
            "salient",
            "mmb8t",
            "mcl8t",
            "coi1",
            "amp1",
            "flum",
            "loop10",
        ),
        "hint": "Use for synchronous-reluctance saliency patterns, stator phase excitation, rotor-angle sweeps, and passive FLUM pickup.",
    },
    "motor/spm_loop_10": {
        "title": "Loop10 surface PM motor campaign",
        "tags": (
            "motor",
            "spm",
            "surface-pm",
            "pm",
            "mwl8t",
            "mmb8t",
            "mcl8t",
            "hbrm",
            "hbcn",
            "flum",
            "loop10",
        ),
        "hint": "Use for loop-reviewed SPM motor decks with surface MWL8T magnets, stator coils, rotor/stator iron, and FLUM pickup.",
    },
    "motor/sr_motor_loop_10": {
        "title": "Loop10 SR-motor reluctance campaign",
        "tags": (
            "motor",
            "sr-motor",
            "srm",
            "switched-reluctance",
            "reluctance",
            "salient",
            "mmb8t",
            "mcl8t",
            "coi1",
            "amp1",
            "flum",
            "loop10",
        ),
        "hint": "Use for loop-reviewed SR-motor salient stator/rotor iron, phase excitation, rotor-angle sweeps, and passive FLUM pickup.",
    },
    "motor/pm_square_2pole_pickup_100": {
        "title": "2-pole square-wave PM pickup",
        "tags": ("motor", "pm", "2-pole", "square-wave", "mwl8t", "flum", "pickup"),
        "hint": "Use as the broadest PM-only passive pickup baseline.",
    },
    "motor/pm_square_4pole_pickup_60": {
        "title": "4-pole square-wave PM pickup",
        "tags": ("motor", "pm", "4-pole", "square-wave", "mwl8t", "flum", "pickup"),
        "hint": "Use for multipole polarity, rotor-angle sign, and passive FLUM checks.",
    },
    "motor/pm_square_6pole_pickup_72": {
        "title": "6-pole square-wave PM pickup",
        "tags": ("motor", "pm", "6-pole", "square-wave", "mwl8t", "flum", "pickup"),
        "hint": "Use for shorter mechanical period PM pickup examples.",
    },
    "motor/pm_square_8pole_pickup_28": {
        "title": "8-pole square-wave PM pickup subset",
        "tags": ("motor", "pm", "8-pole", "square-wave", "mwl8t", "flum", "pickup"),
        "hint": "Use for compact high-pole-count PM pickup examples.",
    },
}

FAMILY_META.update(
    {
        "application/emdlab_1ph_transformer_static_10": {
            "title": "EMDLAB-style single-phase transformer static campaign",
            "tags": ("application", "emdlab-style", "transformer", "single-phase", "static", "mmb8t", "mcl8t", "coi1", "amp1", "flum", "ngsolve-crossval"),
            "hint": "Use for single-phase transformer static decks with core limbs, primary/secondary coils, passive pickup, and FLUM.",
        },
        "application/emdlab_benchmark_ccore_10": {
            "title": "EMDLAB-style benchmark C-core campaign",
            "tags": ("application", "emdlab-style", "benchmark", "c-core", "core", "mome", "mmb8t", "mcl8t", "coi1", "amp1", "flum", "ngsolve-crossval"),
            "hint": "Use for compact C-core benchmark-style decks with a driven coil and pickup FLUM.",
        },
        "application/emdlab_benchmark_geometry_10": {
            "title": "EMDLAB-style benchmark geometry campaign",
            "tags": ("application", "emdlab-style", "benchmark", "geometry", "mab8t", "mmb8t", "mcl8t", "ohm2", "flum", "ngsolve-crossval"),
            "hint": "Use for geometry benchmark coverage with steel, conductor, coil, and pickup entities.",
        },
        "application/emdlab_benchmark_magnet_10": {
            "title": "EMDLAB-style benchmark magnet campaign",
            "tags": ("application", "emdlab-style", "benchmark", "magnet", "pm", "mwl8t", "mmb8t", "hbrm", "hbcn", "flum", "ngsolve-crossval"),
            "hint": "Use for benchmark magnet decks with opposed PM blocks, yoke steel, and pickup FLUM.",
        },
        "application/numeric_validation_anchors_10": {
            "title": "Numeric validation anchor campaign",
            "tags": (
                "application",
                "numeric-validation",
                "anchor",
                "validation-level:numeric-invariant",
                "flum",
                "ngsolve-crossval",
                "ngsolve-numeric-invariant",
                "current-scaling",
                "sign-reversal",
                "distance-decay",
                "symmetry",
                "cancellation",
                "mcl8t",
            ),
            "hint": "Use for compact validation anchor decks where ELF FLUM invariants and independent NGSolve proxy invariants are both expected to pass.",
        },
        "application/numeric_flum_law_64": {
            "title": "Numeric FLUM law validation campaign",
            "tags": (
                "application",
                "numeric-validation",
                "flum-law",
                "flux-linkage",
                "validation-level:numeric-invariant",
                "flum",
                "ngsolve-crossval",
                "ngsolve-numeric-invariant",
                "current-linearity",
                "turn-linearity",
                "sign-reversal",
                "distance-decay",
                "mirror-symmetry",
                "superposition",
                "cancellation",
                "mcl8t",
            ),
            "hint": "Use for FLUM law validation decks covering current, turns, sign, distance, symmetry, superposition, and cancellation invariants.",
        },
        "application/numeric_inductance_energy_100": {
            "title": "Numeric inductance and co-energy validation campaign",
            "tags": (
                "application",
                "numeric-validation",
                "inductance",
                "co-energy",
                "energy",
                "flum-law",
                "flux-linkage",
                "validation-level:numeric-invariant",
                "flum",
                "ngsolve-crossval",
                "ngsolve-numeric-invariant",
                "current-linearity",
                "turn-scaling",
                "mutual-inductance",
                "distance-decay",
                "mirror-symmetry",
                "superposition",
                "cancellation",
                "mcl8t",
            ),
            "hint": "Use for FLUM-derived inductance L = Phi/I and co-energy W = 1/2 sum(I Phi) validation decks covering current, turns, distance, symmetry, superposition, and add/cancel energy invariants.",
        },
        "application/numeric_ac_loss_100": {
            "title": "Numeric AC loss and eddy-current scaling validation campaign",
            "tags": (
                "application",
                "numeric-validation",
                "ac-loss",
                "eddy-current",
                "frequency",
                "freq",
                "momc",
                "ohm2",
                "mab8t",
                "resistivity",
                "conductivity",
                "loss-proxy",
                "i2f2-over-rho",
                "frequency-square",
                "current-square",
                "distance-decay",
                "mirror-symmetry",
                "lateral-symmetry",
                "add-cancel",
                "thickness-sweep",
                "width-sweep",
                "flum",
                "ngsolve-crossval",
                "ngsolve-numeric-invariant",
                "validation-level:numeric-invariant",
                "mcl8t",
            ),
            "hint": "Use for MOMC/FREQ/OHM2 AC-loss decks with FLUM checks and NGSolve proxy invariants covering P proportional to I^2 f^2 / rho, distance decay, symmetry, add/cancel, thickness, and width trends.",
        },
        "application/numeric_magnetic_circuit_100": {
            "title": "Numeric magnetic-circuit and B-H scaling validation campaign",
            "tags": (
                "application",
                "numeric-validation",
                "magnetic-circuit",
                "b-h",
                "bh-curve",
                "hbcu",
                "hbun",
                "mmb8t",
                "yoke",
                "air-gap",
                "reluctance",
                "core-area",
                "core-depth",
                "return-yoke",
                "pickup-coupling",
                "current-scaling",
                "turn-scaling",
                "add-cancel",
                "flum",
                "co-energy",
                "ngsolve-crossval",
                "ngsolve-numeric-invariant",
                "validation-level:numeric-invariant",
                "mcl8t",
            ),
            "hint": "Use for MMB8T/HBUN/HBCU magnetic-circuit decks with FLUM and NGSolve proxy checks covering B-H slope, air-gap reluctance, core area/depth, current/turn scaling, return-yoke continuity, and add/cancel bias behavior.",
        },
        "application/numeric_permanent_magnet_100": {
            "title": "Numeric permanent-magnet and magnetization validation campaign",
            "tags": (
                "application",
                "numeric-validation",
                "permanent-magnet",
                "pm",
                "magnetization",
                "hbrm",
                "hbcn",
                "vec3",
                "mwl8t",
                "pickup-coupling",
                "remanence",
                "distance-decay",
                "magnet-volume",
                "angle-cosine",
                "polarity-reversal",
                "lateral-symmetry",
                "add-cancel",
                "array-count",
                "pickup-turn-scaling",
                "flum",
                "ngsolve-crossval",
                "ngsolve-numeric-invariant",
                "validation-level:numeric-invariant",
                "mcl8t",
            ),
            "hint": "Use for MWL8T/HBRM/HBCN/VEC3 permanent-magnet decks with pickup FLUM and NGSolve proxy checks covering remanence, distance, magnet volume/depth, magnetization angle, polarity reversal, symmetry, add/cancel, array count, and pickup-turn scaling.",
        },
        "application/numeric_force_torque_100": {
            "title": "Numeric force and torque-gradient validation campaign",
            "tags": (
                "application",
                "numeric-validation",
                "force",
                "torque",
                "co-energy",
                "energy-gradient",
                "finite-difference",
                "dwdx",
                "dwdtheta",
                "flum-law",
                "flux-linkage",
                "validation-level:numeric-invariant",
                "flum",
                "ngsolve-crossval",
                "ngsolve-numeric-invariant",
                "current-square-scaling",
                "distance-force",
                "mirror-symmetry",
                "lateral-symmetry",
                "angular-symmetry",
                "balanced-torque",
                "mcl8t",
            ),
            "hint": "Use for FLUM-derived co-energy force/torque-gradient checks: distance-force sign, current-square scaling, mirror/lateral symmetry, angular dW/dtheta trends, and balanced-torque invariants.",
        },
        "motor/emdlab_bldc_outer_rotor_10": {
            "title": "EMDLAB-style BLDC outer-rotor campaign",
            "tags": ("motor", "emdlab-style", "bldc", "outer-rotor", "spm", "surface-pm", "pm", "mwl8t", "mmb8t", "mcl8t", "hbrm", "hbcn", "flum", "ngsolve-crossval"),
            "hint": "Use for BLDC outer-rotor decks with surface PM proxies outside the stator and FLUM pickup.",
        },
        "motor/emdlab_induction_fraction_10": {
            "title": "EMDLAB-style induction-machine fractional-sector campaign",
            "tags": ("motor", "emdlab-style", "induction", "im", "fractional-sector", "rotor-bar", "mab8t", "ohm2", "mcl8t", "flum", "ngsolve-crossval"),
            "hint": "Use for induction-machine fractional-sector decks with rotor-bar conductors, OHM2, phase coils, and FLUM.",
        },
        "motor/emdlab_ipm_hairpin_fraction_10": {
            "title": "EMDLAB-style IPM hairpin fractional-sector campaign",
            "tags": ("motor", "emdlab-style", "ipm", "hairpin", "fractional-sector", "interior-pm", "buried-pm", "mwl8t", "mmb8t", "mcl8t", "flum", "ngsolve-crossval"),
            "hint": "Use for fractional-sector IPM hairpin decks with buried PMs, phase coils, rotor-angle proxies, and FLUM.",
        },
        "motor/emdlab_spmsm_10": {
            "title": "EMDLAB-style SPMSM campaign",
            "tags": ("motor", "emdlab-style", "spmsm", "spm", "surface-pm", "pm", "mwl8t", "mmb8t", "mcl8t", "hbrm", "hbcn", "flum", "ngsolve-crossval"),
            "hint": "Use for SPMSM decks with surface PM rotor proxies, stator coils, and FLUM pickup.",
        },
        "motor/emdlab_spmsm_fraction_10": {
            "title": "EMDLAB-style SPMSM fractional-sector campaign",
            "tags": ("motor", "emdlab-style", "spmsm", "spm", "fractional-sector", "surface-pm", "mwl8t", "mmb8t", "mcl8t", "flum", "ngsolve-crossval"),
            "hint": "Use for fractional-sector SPMSM decks with surface PM proxies and stator phase coils.",
        },
        "motor/emdlab_spmsm_static_torque_10": {
            "title": "EMDLAB-style SPMSM static-torque campaign",
            "tags": ("motor", "emdlab-style", "spmsm", "spm", "static-torque", "surface-pm", "rotor-angle", "mwl8t", "mmb8t", "mcl8t", "flum", "ngsolve-crossval"),
            "hint": "Use for SPMSM static-torque proxy decks with rotor-angle sweeps and FLUM pickup.",
        },
        "motor/emdlab_srm64_10": {
            "title": "EMDLAB-style SRM 6/4 campaign",
            "tags": ("motor", "emdlab-style", "srm", "6-4", "switched-reluctance", "salient", "mmb8t", "mcl8t", "coi1", "amp1", "flum", "ngsolve-crossval"),
            "hint": "Use for SRM 6/4 pole-pattern decks with salient iron, phase-pair excitation, and FLUM.",
        },
        "motor/emdlab_srm86_10": {
            "title": "EMDLAB-style SRM 8/6 campaign",
            "tags": ("motor", "emdlab-style", "srm", "8-6", "switched-reluctance", "salient", "mmb8t", "mcl8t", "coi1", "amp1", "flum", "ngsolve-crossval"),
            "hint": "Use for SRM 8/6 pole-pattern decks with salient iron, phase-pair excitation, and FLUM.",
        },
        "motor/emdlab_srm86_fraction_10": {
            "title": "EMDLAB-style SRM 8/6 fractional-sector campaign",
            "tags": ("motor", "emdlab-style", "srm", "8-6", "fractional-sector", "switched-reluctance", "mmb8t", "mcl8t", "flum", "ngsolve-crossval"),
            "hint": "Use for fractional-sector SRM 8/6 decks with salient iron and phase excitation.",
        },
        "motor/emdlab_srm86_static_torque_10": {
            "title": "EMDLAB-style SRM 8/6 static-torque campaign",
            "tags": ("motor", "emdlab-style", "srm", "8-6", "static-torque", "switched-reluctance", "rotor-angle", "mmb8t", "mcl8t", "flum", "ngsolve-crossval"),
            "hint": "Use for SRM 8/6 static-torque proxy decks with rotor-position sweeps and FLUM.",
        },
        "motor/emdlab_srm128_10": {
            "title": "EMDLAB-style SRM 12/8 campaign",
            "tags": ("motor", "emdlab-style", "srm", "12-8", "switched-reluctance", "salient", "mmb8t", "mcl8t", "flum", "ngsolve-crossval"),
            "hint": "Use for SRM 12/8 pole-pattern decks with salient iron and phase excitation.",
        },
        "motor/emdlab_srm1216_outer_rotor_10": {
            "title": "EMDLAB-style SRM 12/16 outer-rotor campaign",
            "tags": ("motor", "emdlab-style", "srm", "12-16", "outer-rotor", "switched-reluctance", "salient", "mmb8t", "mcl8t", "flum", "ngsolve-crossval"),
            "hint": "Use for SRM 12/16 outer-rotor pole-pattern decks with salient iron and FLUM.",
        },
        "motor/emdlab_synrm_static_torque_10": {
            "title": "EMDLAB-style SynRM static-torque campaign",
            "tags": ("motor", "emdlab-style", "synrm", "synchronous-reluctance", "static-torque", "flux-barrier", "saliency", "mmb8t", "mcl8t", "flum", "ngsolve-crossval"),
            "hint": "Use for SynRM static-torque proxy decks with flux-barrier rotor proxies and FLUM.",
        },
        "motor/emdlab_synrm_fraction_static_torque_10": {
            "title": "EMDLAB-style SynRM fractional static-torque campaign",
            "tags": ("motor", "emdlab-style", "synrm", "synchronous-reluctance", "fractional-sector", "static-torque", "flux-barrier", "mmb8t", "mcl8t", "flum", "ngsolve-crossval"),
            "hint": "Use for fractional-sector SynRM static-torque proxy decks with saliency and FLUM.",
        },
    }
)

TEAM28_CASES: tuple[tuple[str, str], ...] = (
    ("motor/pm_square_2pole_pickup_100", "pm001"),
    ("motor/pm_square_2pole_pickup_100", "pm006"),
    ("motor/pm_square_2pole_pickup_100", "pm019"),
    ("motor/pm_square_2pole_pickup_100", "pm024"),
    ("motor/pm_square_2pole_pickup_100", "pm049"),
    ("motor/pm_square_2pole_pickup_100", "pm072"),
    ("motor/pm_square_2pole_pickup_100", "pm097"),
    ("motor/pm_square_2pole_pickup_100", "pm100"),
    ("motor/pm_square_4pole_pickup_60", "pm001"),
    ("motor/pm_square_4pole_pickup_60", "pm012"),
    ("motor/pm_square_4pole_pickup_60", "pm025"),
    ("motor/pm_square_4pole_pickup_60", "pm036"),
    ("motor/pm_square_4pole_pickup_60", "pm060"),
    ("motor/pm_square_6pole_pickup_72", "pm001"),
    ("motor/pm_square_6pole_pickup_72", "pm018"),
    ("motor/pm_square_6pole_pickup_72", "pm025"),
    ("motor/pm_square_6pole_pickup_72", "pm042"),
    ("motor/pm_square_6pole_pickup_72", "pm061"),
    ("motor/pm_square_6pole_pickup_72", "pm072"),
    ("motor/pm_square_8pole_pickup_28", "pm001"),
    ("motor/pm_square_8pole_pickup_28", "pm013"),
    ("motor/pm_square_8pole_pickup_28", "pm028"),
    ("motor/pm_cosine_pickup_72", "pm001"),
    ("motor/pm_cosine_pickup_72", "pm004"),
    ("motor/pm_cosine_pickup_72", "pm025"),
    ("motor/pm_cosine_pickup_72", "pm049"),
    ("motor/pm_cosine_pickup_72", "pm071"),
    ("motor/pm_cosine_pickup_72", "pm072"),
)

SAMPLE_ROUTE_RULES: tuple[dict[str, Any], ...] = (
    {
        "intent": "BLDC or surface-PM motor",
        "family": "motor/emdlab_bldc_spm_10",
        "query": "EMDLAB-style BLDC SPM surface-pm FLUM",
        "recipe": "pm_airgap_field",
        "terms": ("bldc", "brushless", "spm", "surface pm", "surface-pm", "slotted", "stator"),
        "why": "Start here for slotted-stator surface-PM machines with phase coils and passive FLUM pickup.",
    },
    {
        "intent": "IPM hairpin motor",
        "family": "motor/emdlab_ipm_hairpin_10",
        "query": "EMDLAB-style IPM hairpin buried-pm FLUM",
        "recipe": "ipm_ldlq_flux",
        "terms": ("ipm", "interior pm", "interior-pm", "hairpin", "buried pm", "buried-pm", "54-slot"),
        "why": "Use these decks when the prompt mentions IPM, buried magnets, hairpin conductors, or dq flux work.",
    },
    {
        "intent": "Interior-PM angle sweep",
        "family": "motor/ipm_interior_pm_10",
        "query": "Loop13 IPM interior permanent-magnet rotor angle FLUM",
        "recipe": "ipm_ldlq_flux",
        "terms": ("interior", "rotor angle", "angle sweep", "dq", "ld", "lq"),
        "why": "Use these simpler IPM decks when rotor-angle variation or current-on flux is the main task.",
    },
    {
        "intent": "Induction machine rotor bars",
        "family": "motor/emdlab_induction_bar_10",
        "query": "induction-machine bar OHM2 FLUM",
        "recipe": "eddy_current_time_domain",
        "terms": ("induction", "im", "rotor bar", "rotor-bar", "squirrel cage", "squirrel-cage", "ohm2"),
        "why": "Use these decks for induction-machine stator phase coils with conductive rotor-bar proxies.",
    },
    {
        "intent": "Synchronous reluctance or flux-barrier motor",
        "family": "motor/emdlab_synrm_flux_barrier_10",
        "query": "EMDLAB-style SynRM flux-barrier saliency FLUM",
        "recipe": "maxwell_torque_surface",
        "terms": ("synrm", "synchronous reluctance", "flux barrier", "flux-barrier", "saliency"),
        "why": "Use these decks for SynRM-style flux-barrier rotor proxies and saliency-driven studies.",
    },
    {
        "intent": "Switched-reluctance motor pole variant",
        "family": "motor/emdlab_srm_pole_variants_10",
        "query": "EMDLAB-style SRM pole-variant switched-reluctance FLUM",
        "recipe": "maxwell_torque_surface",
        "terms": ("srm", "switched reluctance", "switched-reluctance", "pole variant", "6/4", "8/6", "12/8", "12/16"),
        "why": "Use these decks for SRM 6/4, 8/6, 12/8, or 12/16 pole proxy prompts.",
    },
    {
        "intent": "Axial-flux PM motor",
        "family": "motor/axial_flux_pm_10",
        "query": "Loop13 axial-flux PM face magnet FLUM",
        "recipe": "pm_airgap_field",
        "terms": ("afpm", "axial flux", "axial-flux", "face magnet", "face-magnet", "skew"),
        "why": "Use these decks for axial-flux PM motors with face magnets, axial yokes, and skew offsets.",
    },
    {
        "intent": "Linear PM motor",
        "family": "motor/linear_pm_motor_10",
        "query": "Loop13 linear PM motor translator offset FLUM",
        "recipe": "pm_airgap_field",
        "terms": ("linear pm", "linear-pm", "linear motor", "translator", "forcer"),
        "why": "Use these decks for linear PM tracks, moving forcer coils, and translator offset sweeps.",
    },
    {
        "intent": "Stepper motor",
        "family": "motor/stepper_motor_10",
        "query": "Loop13 stepper motor detent FLUM",
        "recipe": "pm_airgap_field",
        "terms": ("stepper", "stepper motor", "detent", "four phase", "four-phase"),
        "why": "Use these decks for four-phase stepper motors, PM rotor proxies, and detent-offset prompts.",
    },
    {
        "intent": "Wound-field synchronous motor",
        "family": "motor/wound_field_sync_10",
        "query": "Loop13 wound-field synchronous rotor field FLUM",
        "recipe": "mutual_flux_current_pickup",
        "terms": ("wound field", "wound-field", "field coil", "field-coil", "synchronous motor", "rotor field"),
        "why": "Use these decks for DC rotor field coils, stator phase coils, and synchronous-machine prompts without PMs.",
    },
    {
        "intent": "PM pickup or back-EMF seed",
        "family": "motor/pm_cosine_pickup_72",
        "query": "HBCN FLUM cosine-remanence PM pickup",
        "recipe": "passive_flum_pickup",
        "terms": ("back emf", "back-emf", "flux linkage", "flux-linkage", "pickup", "flum", "pm pickup"),
        "why": "Use this broad PM pickup baseline before adding coils, iron, saliency, or current excitation.",
    },
    {
        "intent": "WPT misalignment",
        "family": "application/wpt_misalignment_10",
        "query": "Loop13 WPT misalignment OHM2 FLUM",
        "recipe": "sinusoidal_momc",
        "terms": ("wpt", "wireless power", "wireless-power", "misalignment", "lateral offset", "lateral-offset"),
        "why": "Use these decks for primary/secondary pad offsets, conducting shields, MOMC/FREQ, and FLUM.",
    },
    {
        "intent": "MRI gradient sequence",
        "family": "application/mri_gradient_sequence_10",
        "query": "Loop13 MRI gradient sequence OHM2 FREQ FLUM",
        "recipe": "sinusoidal_momc",
        "terms": ("mri", "gradient", "gradient sequence", "bipolar", "shield"),
        "why": "Use these decks for bipolar gradient coils, eddy-current shields, OHM2, FREQ, and FLUM.",
    },
    {
        "intent": "Transformer leakage",
        "family": "application/transformer_leakage_10",
        "query": "Loop13 transformer leakage gapped-core FLUM",
        "recipe": "mutual_flux_current_pickup",
        "terms": ("transformer", "leakage", "gapped core", "gapped-core", "primary", "secondary"),
        "why": "Use these decks for gapped transformer cores, primary/secondary coils, and leakage pickup.",
    },
    {
        "intent": "Induction-heating susceptor",
        "family": "application/ih_susceptor_ring_10",
        "query": "Loop13 IH susceptor OHM2 MOMC FLUM",
        "recipe": "sinusoidal_momc",
        "terms": ("ih", "induction heating", "induction-heating", "susceptor", "ring"),
        "why": "Use these decks for AC induction-heating coils with nested conducting workpieces and OHM2 contrast.",
    },
    {
        "intent": "Accelerator corrector magnet",
        "family": "application/accelerator_corrector_10",
        "query": "Loop13 accelerator corrector trim coil FLUM",
        "recipe": "linear_iron_boost",
        "terms": ("accelerator", "corrector", "trim coil", "trim-coil", "dipole", "aperture"),
        "why": "Use these decks for main dipole coils, trim-correction coils, aperture pickup, and yoke checks.",
    },
    {
        "intent": "General motor authoring starter",
        "family": "motor/emdlab_bldc_spm_10",
        "query": "EMDLAB-style motor FLUM",
        "recipe": "pm_airgap_field",
        "terms": ("motor", "machine", "rotor", "stator"),
        "why": "Use this as the first public motor deck when the prompt is broad and does not name a machine type.",
    },
)

SAMPLE_ROUTE_RULES = (
    {
        "intent": "Numeric permanent-magnet and magnetization validation",
        "family": "application/numeric_permanent_magnet_100",
        "query": "numeric permanent magnet HBRM HBCN VEC3 magnetization angle polarity FLUM",
        "recipe": "pm_airgap_field",
        "terms": (
            "permanent magnet",
            "permanent-magnet",
            "pm scaling",
            "hbrm",
            "hbcn",
            "vec3",
            "mwl8t",
            "magnetization angle",
            "magnet angle",
            "remanence",
            "polarity reversal",
            "magnet polarity",
            "magnet volume",
            "pickup turn",
            "magnet array",
            "add cancel",
            "add/cancel",
        ),
        "why": "Use these decks when the prompt asks how to validate MWL8T/HBRM/HBCN/VEC3 permanent-magnet behavior, magnetization direction, polarity, PM volume, array count, or pickup-turn coupling before detailed motor PM studies.",
    },
    {
        "intent": "Numeric magnetic-circuit and B-H scaling validation",
        "family": "application/numeric_magnetic_circuit_100",
        "query": "numeric magnetic circuit B-H HBCU MMB8T air gap reluctance yoke FLUM",
        "recipe": "magnetic_circuit_yoke_gap",
        "terms": (
            "magnetic circuit",
            "magnetic-circuit",
            "b-h",
            "bh curve",
            "hbcu",
            "hbun",
            "mmb8t",
            "air gap",
            "air-gap",
            "reluctance",
            "yoke",
            "return yoke",
            "return-yoke",
            "core area",
            "core depth",
            "pickup coupling",
            "magnetic path",
            "flux path",
        ),
        "why": "Use these decks when the prompt asks how to validate MMB8T/HBUN/HBCU magnetic-circuit behavior, air-gap reluctance, yoke continuity, or pickup coupling before detailed nonlinear material studies.",
    },
    {
        "intent": "Numeric AC loss and eddy-current scaling validation",
        "family": "application/numeric_ac_loss_100",
        "query": "numeric AC loss eddy current MOMC FREQ OHM2 frequency square resistivity",
        "recipe": "eddy_current_frequency_sweep",
        "terms": (
            "ac loss",
            "eddy loss",
            "eddy-current loss",
            "eddy current loss",
            "frequency square",
            "frequency-square",
            "current square",
            "current-square",
            "resistivity inverse",
            "i2f2",
            "i^2 f^2",
            "ohm2",
            "momc",
            "freq",
            "skin",
            "conducting plate",
            "loss proxy",
            "add cancel",
            "add/cancel",
        ),
        "why": "Use these decks when the prompt asks how to validate MOMC/FREQ/OHM2 AC-loss or eddy-current scaling behavior before moving to detailed loss post-processing.",
    },
    {
        "intent": "Numeric force and torque-gradient validation",
        "family": "application/numeric_force_torque_100",
        "query": "numeric force torque co-energy gradient FLUM dWdx dWdtheta",
        "recipe": "maxwell_torque_surface",
        "terms": (
            "force",
            "torque",
            "force law",
            "torque law",
            "co-energy gradient",
            "coenergy gradient",
            "energy gradient",
            "dwdx",
            "dw/dx",
            "dwdtheta",
            "dw/dtheta",
            "finite difference force",
            "finite-difference force",
            "angular torque",
            "balanced torque",
            "distance force",
        ),
        "why": "Use these decks when the prompt asks how to validate force or torque behavior from FLUM-derived co-energy gradients before moving to direct FORT/FIXB post-processing.",
    },
    {
        "intent": "Numeric inductance and co-energy validation",
        "family": "application/numeric_inductance_energy_100",
        "query": "numeric inductance co-energy FLUM current turns superposition energy",
        "recipe": "mutual_flux_current_pickup",
        "terms": (
            "inductance",
            "co-energy",
            "coenergy",
            "energy law",
            "phi over current",
            "phi/i",
            "l = phi/i",
            "w = 1/2",
            "half i phi",
            "mutual inductance",
            "self inductance",
            "turn scaling",
            "energy current square",
            "energy turns square",
            "add cancel energy",
            "what physical quantity",
            "what quantity",
        ),
        "why": "Use these decks when the prompt asks what physical quantity should be evaluated after FLUM, especially inductance L = Phi/I or co-energy W = 1/2 sum(I Phi).",
    },
    {
        "intent": "Numeric FLUM law validation",
        "family": "application/numeric_flum_law_64",
        "query": "numeric FLUM law current turns symmetry superposition cancellation",
        "recipe": "passive_flum_pickup",
        "terms": (
            "flum law",
            "flux linkage law",
            "numeric flum",
            "current linearity",
            "turn linearity",
            "superposition",
            "cancellation",
            "mirror symmetry",
            "pickup ratio",
            "distance decay",
        ),
        "why": "Use these decks when the prompt asks which physical quantity is validated or needs FLUM law checks across current, turns, distance, symmetry, and superposition.",
    },
    {
        "intent": "Numeric validation anchor",
        "family": "application/numeric_validation_anchors_10",
        "query": "numeric-validation anchor FLUM NGSolve invariant",
        "recipe": "passive_flum_pickup",
        "terms": (
            "numeric validation",
            "validation anchor",
            "ngsolve invariant",
            "flux invariant",
            "flum invariant",
            "current scaling",
            "sign reversal",
            "distance decay",
            "symmetry check",
            "cancellation check",
        ),
        "why": "Use these decks when the prompt asks whether validation is stronger than a simple run/pass or proxy-energy gate.",
    },
    {
        "intent": "BLDC outer-rotor motor",
        "family": "motor/emdlab_bldc_outer_rotor_10",
        "query": "EMDLAB-style BLDC outer-rotor surface-pm FLUM",
        "recipe": "pm_airgap_field",
        "terms": ("outer rotor", "outer-rotor", "bldc outer", "outside rotor"),
        "why": "Use these decks when the prompt specifically asks for a BLDC/SPM outer-rotor topology.",
    },
    {
        "intent": "Fractional-sector induction machine",
        "family": "motor/emdlab_induction_fraction_10",
        "query": "EMDLAB-style induction fractional-sector OHM2 FLUM",
        "recipe": "eddy_current_time_domain",
        "terms": ("induction fraction", "fractional induction", "fractional-sector induction", "im fraction"),
        "why": "Use these decks for reduced-sector induction-machine rotor-bar prompts.",
    },
    {
        "intent": "Fractional-sector IPM hairpin motor",
        "family": "motor/emdlab_ipm_hairpin_fraction_10",
        "query": "EMDLAB-style IPM hairpin fractional-sector FLUM",
        "recipe": "ipm_ldlq_flux",
        "terms": ("ipm fraction", "hairpin fraction", "fractional-sector ipm", "fractional ipm"),
        "why": "Use these decks for reduced-sector IPM hairpin prompts with buried PMs and phase coils.",
    },
    {
        "intent": "SPMSM motor",
        "family": "motor/emdlab_spmsm_10",
        "query": "EMDLAB-style SPMSM surface-pm FLUM",
        "recipe": "pm_airgap_field",
        "terms": ("spmsm", "surface pm synchronous", "surface-pm synchronous"),
        "why": "Use these decks for SPMSM prompts that name the synchronous-machine form explicitly.",
    },
    {
        "intent": "SPMSM static torque",
        "family": "motor/emdlab_spmsm_static_torque_10",
        "query": "EMDLAB-style SPMSM static-torque rotor-angle FLUM",
        "recipe": "maxwell_torque_surface",
        "terms": ("spmsm torque", "spmsm static torque", "surface pm torque", "static torque spm"),
        "why": "Use these decks for SPMSM rotor-angle/static-torque proxy prompts.",
    },
    {
        "intent": "SPMSM fractional-sector",
        "family": "motor/emdlab_spmsm_fraction_10",
        "query": "EMDLAB-style SPMSM fractional-sector FLUM",
        "recipe": "pm_airgap_field",
        "terms": ("spmsm fraction", "fractional spmsm", "fractional-sector spmsm"),
        "why": "Use these decks for reduced-sector SPMSM prompt variants.",
    },
    {
        "intent": "Specific SRM pole count",
        "family": "motor/emdlab_srm86_10",
        "query": "EMDLAB-style SRM 8-6 switched-reluctance FLUM",
        "recipe": "maxwell_torque_surface",
        "terms": ("srm 8/6", "srm86", "8/6 srm", "8-6 srm"),
        "why": "Use these decks when the prompt names the common SRM 8/6 example.",
    },
    {
        "intent": "SRM 6/4 pole count",
        "family": "motor/emdlab_srm64_10",
        "query": "EMDLAB-style SRM 6-4 switched-reluctance FLUM",
        "recipe": "maxwell_torque_surface",
        "terms": ("srm 6/4", "srm64", "6/4 srm", "6-4 srm"),
        "why": "Use these decks for SRM 6/4 pole-pattern prompts.",
    },
    {
        "intent": "SRM 12/8 pole count",
        "family": "motor/emdlab_srm128_10",
        "query": "EMDLAB-style SRM 12-8 switched-reluctance FLUM",
        "recipe": "maxwell_torque_surface",
        "terms": ("srm 12/8", "srm128", "12/8 srm", "12-8 srm"),
        "why": "Use these decks for SRM 12/8 pole-pattern prompts.",
    },
    {
        "intent": "SRM 12/16 outer-rotor",
        "family": "motor/emdlab_srm1216_outer_rotor_10",
        "query": "EMDLAB-style SRM 12-16 outer-rotor FLUM",
        "recipe": "maxwell_torque_surface",
        "terms": ("srm 12/16", "srm1216", "12/16 srm", "12-16 srm", "srm outer rotor"),
        "why": "Use these decks for SRM 12/16 outer-rotor prompts.",
    },
    {
        "intent": "SynRM static torque",
        "family": "motor/emdlab_synrm_static_torque_10",
        "query": "EMDLAB-style SynRM static-torque flux-barrier FLUM",
        "recipe": "maxwell_torque_surface",
        "terms": ("synrm torque", "synrm static torque", "reluctance torque"),
        "why": "Use these decks for SynRM static-torque proxy prompts.",
    },
    {
        "intent": "Single-phase transformer static example",
        "family": "application/emdlab_1ph_transformer_static_10",
        "query": "EMDLAB-style single-phase transformer static FLUM",
        "recipe": "mutual_flux_current_pickup",
        "terms": ("1ph transformer", "single phase transformer", "single-phase transformer", "transformer static"),
        "why": "Use these decks for single-phase transformer static core/coil prompts.",
    },
    {
        "intent": "EMDLAB benchmark C-core",
        "family": "application/emdlab_benchmark_ccore_10",
        "query": "EMDLAB-style benchmark C-core FLUM",
        "recipe": "linear_iron_boost",
        "terms": ("benchmark ccore", "benchmark c-core", "c-core", "ccore"),
        "why": "Use these decks for compact C-core benchmark-style prompts.",
    },
    {
        "intent": "EMDLAB benchmark magnet",
        "family": "application/emdlab_benchmark_magnet_10",
        "query": "EMDLAB-style benchmark magnet HBCN FLUM",
        "recipe": "pm_airgap_field",
        "terms": ("benchmark magnet", "magnet benchmark"),
        "why": "Use these decks for benchmark-style PM/yoke prompts.",
    },
    {
        "intent": "EMDLAB benchmark geometry",
        "family": "application/emdlab_benchmark_geometry_10",
        "query": "EMDLAB-style benchmark geometry OHM2 FLUM",
        "recipe": "linear_iron_boost",
        "terms": ("benchmark geometry", "geometry benchmark"),
        "why": "Use these decks for geometry benchmark prompts with mixed steel, conductor, and coil primitives.",
    },
    *SAMPLE_ROUTE_RULES,
)

SOL_RE = re.compile(r"^\s*SOL\s+([A-Z0-9_]+)", re.MULTILINE)
ELEMENT_RE = re.compile(
    r"\b(MWL8T|MWV8T|MCL8T|MMB8T|MAB8T|MAT[0-9A-Z]*|MBB[0-9A-Z]*|"
    r"MCO[0-9A-Z]*|MCM[0-9A-Z]*|MJH[0-9A-Z]*)\b"
)
KEYWORDS = (
    "HBUN",
    "HBSC",
    "HBCU",
    "HBRM",
    "HBCN",
    "VEC3",
    "COI1",
    "AMP1",
    "AMP1I",
    "OHM2",
    "CMU1",
    "CMU1I",
    "TIME",
    "FREQ",
    "NONL",
    "DMEG",
    "FLUM",
)


@dataclass(frozen=True)
class SampleDeck:
    path: str
    family: str
    case: str
    ext: str
    char_count: int
    text: str


def _sample_root():
    return resources.files("elf_mcp_server").joinpath(ROOT)


@lru_cache(maxsize=1)
def load_validated_manifest() -> dict[str, Any]:
    """Load the public validation manifest for sample deck families."""
    path = _sample_root().joinpath("VALIDATED_MANIFEST.json")
    return json.loads(path.read_text(encoding="ascii"))


@lru_cache(maxsize=1)
def load_publication_batches() -> dict[str, Any]:
    """Load the public 100-case publication checkpoint manifest."""
    path = _sample_root().joinpath("PUBLICATION_BATCHES.json")
    return json.loads(path.read_text(encoding="ascii"))


def _validation_counts(families: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    counts: dict[str, dict[str, Any]] = {}
    for entry in families.values():
        level = entry.get("validation_level") or "unknown"
        bucket = counts.setdefault(
            level,
            {
                "families": 0,
                "cases": 0,
                "input_files": 0,
                "description": VALIDATION_LEVEL_DESCRIPTIONS.get(level, ""),
            },
        )
        bucket["families"] += 1
        bucket["cases"] += int(entry.get("cases", 0))
        bucket["input_files"] += int(entry.get("input_files", 0))
    return counts


def validation_level_counts() -> dict[str, dict[str, Any]]:
    """Return validation-level counts for all public sample families."""
    families = load_validated_manifest().get("families", {})
    return _validation_counts(families)


def build_publication_batch_summary() -> dict[str, Any]:
    """Return public-safe 100-case checkpoint metadata."""
    batches = load_publication_batches()
    return {
        "checkpoint_size": int(batches.get("checkpoint_size", 0)),
        "total_cases": int(batches.get("total_cases", 0)),
        "total_batches": int(batches.get("total_batches", 0)),
        "full_100_case_batches": int(batches.get("full_100_case_batches", 0)),
        "remainder_cases": int(batches.get("remainder_cases", 0)),
        "next_checkpoint_cases": int(batches.get("next_checkpoint_cases", 0)),
        "additional_cases_needed_for_next_100_case_checkpoint": int(
            batches.get("additional_cases_needed_for_next_100_case_checkpoint", 0)
        ),
        "batches": [
            {
                "batch_id": batch.get("batch_id", ""),
                "batch_kind": batch.get("batch_kind", ""),
                "status": batch.get("status", ""),
                "case_count": int(batch.get("case_count", 0)),
                "case_start": int(batch.get("case_start", 0)),
                "case_end": int(batch.get("case_end", 0)),
                "validation_level_counts": dict(batch.get("validation_level_counts", {})),
            }
            for batch in batches.get("batches", [])
        ],
    }


def get_family_validation(family: str) -> dict[str, Any]:
    """Return public validation metadata for one sample family."""
    entry = load_validated_manifest().get("families", {}).get(family)
    if entry is None:
        return {
            "family": family,
            "validation": "unknown",
            "validation_level": "unknown",
            "validation_scope": "No public validation manifest entry found.",
            "checks": [],
            "cases": 0,
            "input_files": 0,
        }
    return {
        "family": family,
        "validation": entry.get("validation", ""),
        "validation_level": entry.get("validation_level", ""),
        "validation_scope": entry.get("validation_scope", ""),
        "checks": list(entry.get("checks", [])),
        "cases": int(entry.get("cases", 0)),
        "input_files": int(entry.get("input_files", 0)),
        "validated_on": entry.get("validated_on", ""),
    }


def build_validation_summary(
    family: str | None = None,
    level: str | None = None,
) -> dict[str, Any]:
    """Build a public validation summary for MCP clients."""
    manifest = load_validated_manifest()
    all_families = manifest.get("families", {})
    family_filter = family.lower() if family else None
    level_filter = level.strip() if level else None

    selected: dict[str, dict[str, Any]] = {}
    for name, entry in sorted(all_families.items()):
        if family_filter and family_filter not in name.lower():
            continue
        if level_filter and entry.get("validation_level") != level_filter:
            continue
        selected[name] = entry

    family_rows = []
    for name, entry in selected.items():
        family_rows.append(
            {
                "family": name,
                "cases": int(entry.get("cases", 0)),
                "input_files": int(entry.get("input_files", 0)),
                "validation": entry.get("validation", ""),
                "validation_level": entry.get("validation_level", ""),
                "validation_scope": entry.get("validation_scope", ""),
                "checks": list(entry.get("checks", [])),
                "validated_on": entry.get("validated_on", ""),
            }
        )

    return {
        "schema_version": manifest.get("schema_version"),
        "total_cases": int(manifest.get("total_cases", 0)),
        "total_input_files": int(manifest.get("total_input_files", 0)),
        "total_families": len(all_families),
        "level_counts": _validation_counts(all_families),
        "selected_cases": sum(row["cases"] for row in family_rows),
        "selected_input_files": sum(row["input_files"] for row in family_rows),
        "selected_family_count": len(family_rows),
        "selected_level_counts": _validation_counts(selected),
        "families": family_rows,
        "publication_batches": build_publication_batch_summary(),
        "family_filter": family or "",
        "level_filter": level or "",
        "limitations": list(VALIDATION_LIMITATIONS),
        "recommended_calls": [
            'elf_sample_decks_validation(level="ngsolve_numeric_invariant")',
            'elf_sample_decks_validation(family="numeric_permanent_magnet")',
            'elf_sample_decks_validation(family="numeric_magnetic_circuit")',
            'elf_sample_decks_validation(family="numeric_ac_loss")',
            'elf_sample_decks_validation(family="numeric_force_torque")',
            'elf_sample_decks_validation(family="numeric_inductance_energy")',
            'elf_sample_decks_validation(family="numeric_flum_law")',
            'elf_sample_decks_validation(family="numeric_validation")',
            'elf_sample_decks_route("permanent magnet HBRM polarity FLUM")',
            'elf_sample_decks_route("magnetic circuit air gap HBCU")',
            'elf_sample_decks_route("AC loss frequency square OHM2")',
            'elf_sample_decks_route("force torque co-energy gradient")',
            'elf_sample_decks_route("inductance co-energy FLUM turn scaling")',
            'elf_sample_decks_route("FLUM law current linearity superposition")',
            'elf_sample_decks_route("numeric validation anchor FLUM invariant")',
        ],
    }


def _ordered_levels(counts: dict[str, dict[str, Any]]) -> list[str]:
    ordered = [level for level in VALIDATION_LEVEL_ORDER if level in counts]
    ordered.extend(sorted(level for level in counts if level not in ordered))
    return ordered


def format_validation_summary(summary: dict[str, Any], max_families: int = 20) -> str:
    """Format public validation metadata as Markdown."""
    lines = [
        "# Public sample-deck validation",
        "",
        f"- manifest schema: {summary['schema_version']}",
        (
            f"- public corpus: {summary['total_cases']} cases, "
            f"{summary['total_input_files']} input files, "
            f"{summary['total_families']} families"
        ),
        "- publication rule: only manifest-listed `validation: passed` families are bundled",
        "",
        "## Validation levels",
    ]
    for level in _ordered_levels(summary["level_counts"]):
        count = summary["level_counts"][level]
        description = count.get("description") or VALIDATION_LEVEL_DESCRIPTIONS.get(level, "")
        lines.append(
            f"- `{level}`: {count['families']} families, "
            f"{count['cases']} cases, {count['input_files']} input files"
        )
        if description:
            lines.append(f"  scope: {description}")

    lines.extend(["", "## Selected families"])
    filter_bits = []
    if summary["family_filter"]:
        filter_bits.append(f"family contains `{summary['family_filter']}`")
    if summary["level_filter"]:
        filter_bits.append(f"level is `{summary['level_filter']}`")
    if filter_bits:
        lines.append(f"- filter: {', '.join(filter_bits)}")
    else:
        lines.append("- filter: none")
    lines.append(
        f"- selected: {summary['selected_family_count']} families, "
        f"{summary['selected_cases']} cases, "
        f"{summary['selected_input_files']} input files"
    )

    shown = summary["families"][: max(0, max_families)]
    for row in shown:
        lines.append(
            f"- `{row['family']}`: {row['cases']} cases, "
            f"level `{row['validation_level']}`, checks: {', '.join(row['checks'])}"
        )
        if row.get("validation_scope"):
            lines.append(f"  scope: {row['validation_scope']}")
    hidden = summary["selected_family_count"] - len(shown)
    if hidden > 0:
        lines.append(f"- ... {hidden} more families. Narrow with `family=` or `level=`.")

    lines.extend(["", "## Limits"])
    lines.extend(f"- {item}" for item in summary["limitations"])
    batches = summary.get("publication_batches", {})
    if batches:
        lines.extend(["", "## 100-case publication checkpoints"])
        lines.append(f"- checkpoint size: {batches['checkpoint_size']} cases")
        lines.append(
            f"- baseline: {batches['full_100_case_batches']} full checkpoints "
            f"+ {batches['remainder_cases']} release-remainder cases "
            f"({batches['total_cases']} cases total)"
        )
        lines.append(
            f"- next checkpoint: {batches['next_checkpoint_cases']} cases; "
            f"{batches['additional_cases_needed_for_next_100_case_checkpoint']} "
            "additional validated cases needed"
        )
        for batch in batches["batches"][:5]:
            level_bits = ", ".join(
                f"{name}:{count}"
                for name, count in sorted(batch["validation_level_counts"].items())
            )
            lines.append(
                f"- `{batch['batch_id']}`: {batch['case_start']}-{batch['case_end']} "
                f"({batch['case_count']} cases, {batch['batch_kind']}, {level_bits})"
            )
        hidden_batches = batches["total_batches"] - min(5, len(batches["batches"]))
        if hidden_batches > 0:
            lines.append(f"- ... {hidden_batches} more checkpoint batches.")
    lines.extend(["", "## Recommended MCP calls"])
    lines.extend(f"- `{call}`" for call in summary["recommended_calls"])
    return "\n".join(lines).rstrip()


def _walk_files(node, prefix: str = "") -> list[tuple[str, Any]]:
    files: list[tuple[str, Any]] = []
    for child in sorted(node.iterdir(), key=lambda p: p.name):
        rel = f"{prefix}/{child.name}" if prefix else child.name
        if child.is_dir():
            files.extend(_walk_files(child, rel))
        elif child.is_file() and child.name.lower().endswith((".mai", ".meg")):
            files.append((rel.replace("\\", "/"), child))
    return files


@lru_cache(maxsize=1)
def load_sample_decks() -> dict[str, SampleDeck]:
    """Load bundled public sample decks once and cache them."""
    decks: dict[str, SampleDeck] = {}
    root = _sample_root()
    for rel_path, file_ref in _walk_files(root):
        text = file_ref.read_text(encoding="ascii")
        parts = rel_path.split("/")
        family = "/".join(parts[:-2]) if len(parts) >= 3 else ""
        case = parts[-2] if len(parts) >= 2 else ""
        ext = parts[-1].rsplit(".", 1)[-1].lower()
        decks[rel_path] = SampleDeck(
            path=rel_path,
            family=family,
            case=case,
            ext=ext,
            char_count=len(text),
            text=text,
        )
    return decks


def list_sample_decks(family: str | None = None, case: str | None = None, ext: str | None = None) -> list[dict[str, Any]]:
    """List public sample input decks, optionally filtered."""
    decks = load_sample_decks()
    e = ext.lower().lstrip(".") if ext else None
    out = []
    for deck in decks.values():
        if family and family not in deck.family:
            continue
        if case and case != deck.case:
            continue
        if e and e != deck.ext:
            continue
        out.append(
            {
                "path": deck.path,
                "family": deck.family,
                "case": deck.case,
                "ext": deck.ext,
                "char_count": deck.char_count,
            }
        )
    return sorted(out, key=lambda d: d["path"])


def search_sample_decks(query: str, top_k: int = 10, ext: str | None = None) -> list[dict[str, Any]]:
    """Substring-search public sample deck text and paths."""
    keywords = [k.strip() for k in query.split() if k.strip()]
    if not keywords:
        return []
    e = ext.lower().lstrip(".") if ext else None
    hits = []
    for deck in load_sample_decks().values():
        if e and deck.ext != e:
            continue
        meta = _family_meta(deck.family)
        haystack = "\n".join(
            [
                deck.path,
                deck.family,
                meta["title"],
                " ".join(meta["tags"]),
                meta["hint"],
                deck.text,
            ]
        )
        lower = haystack.lower()
        scores = [lower.count(kw.lower()) for kw in keywords]
        if not all(score > 0 for score in scores):
            continue
        first = lower.find(keywords[0].lower())
        start = max(0, first - 80)
        end = min(len(haystack), first + 220)
        snippet = haystack[start:end].replace("\n", " | ").strip()
        if start > 0:
            snippet = "..." + snippet
        if end < len(haystack):
            snippet += "..."
        hits.append(
            {
                "path": deck.path,
                "family": deck.family,
                "case": deck.case,
                "ext": deck.ext,
                "score": sum(scores),
                "snippet": snippet,
            }
        )
    hits.sort(key=lambda h: (-h["score"], h["path"]))
    return hits[:top_k]


def _route_score(goal_l: str, words: set[str], rule: dict[str, Any]) -> int:
    score = 0
    for term in rule["terms"]:
        term_l = term.lower()
        if " " in term_l or "-" in term_l or "/" in term_l:
            if term_l in goal_l:
                score += 4
        elif term_l in words:
            score += 3
        elif len(term_l) > 3 and term_l in goal_l:
            score += 1
    return score


def route_sample_decks(goal: str, limit: int = 5) -> list[dict[str, Any]]:
    """Route a natural-language goal to sample families and follow-up calls."""
    goal_l = goal.lower()
    words = set(re.findall(r"[a-z0-9]+", goal_l))
    scored: list[tuple[int, int, dict[str, Any]]] = []
    for index, rule in enumerate(SAMPLE_ROUTE_RULES):
        score = _route_score(goal_l, words, rule)
        if score > 0:
            scored.append((score, index, rule))
    if not scored:
        scored = [(1, index, rule) for index, rule in enumerate(SAMPLE_ROUTE_RULES[-1:])]
    scored.sort(key=lambda item: (-item[0], item[1]))

    routes: list[dict[str, Any]] = []
    max_routes = max(1, min(limit, 12))
    for score, _index, rule in scored[:max_routes]:
        family = rule["family"]
        meta = _family_meta(family)
        validation = get_family_validation(family)
        examples = [d["path"] for d in list_sample_decks(family=family, ext="mai")[:3]]
        routes.append(
            {
                "score": score,
                "intent": rule["intent"],
                "family": family,
                "title": meta["title"],
                "tags": list(meta["tags"]),
                "validation_level": validation["validation_level"],
                "validation_scope": validation["validation_scope"],
                "why": rule["why"],
                "query": rule["query"],
                "recipe": rule["recipe"],
                "representative_decks": examples,
                "next_calls": [
                    f'elf_sample_decks_validation(family="{family.rsplit("/", 1)[-1]}")',
                    f'elf_sample_decks_playbook(limit=10, family="{family.rsplit("/", 1)[-1]}")',
                    f'elf_sample_decks_search("{rule["query"]}", ext="mai")',
                    f'elf_recipe_get("{rule["recipe"]}")',
                ],
            }
        )
    return routes


def format_sample_deck_routes(routes: list[dict[str, Any]], goal: str) -> str:
    """Format goal-to-sample routes for MCP clients."""
    if not routes:
        return f"No sample-deck route found for '{goal}'. Try elf_sample_decks_search(goal, ext='mai')."
    lines = [
        f"# Sample-deck route for: {goal}",
        "",
        "Use the first route as the default seed, then inspect the playbook card and open one representative `.mai` deck.",
        "",
    ]
    for i, route in enumerate(routes, 1):
        lines.append(f"## {i}. {route['intent']}  (score={route['score']})")
        lines.append(f"- family: `{route['family']}`")
        lines.append(f"- title: {route['title']}")
        if route.get("validation_level"):
            lines.append(
                f"- validation: `{route['validation_level']}` - "
                f"{route.get('validation_scope', '')}"
            )
        lines.append(f"- why: {route['why']}")
        lines.append(f"- tags: {', '.join(route['tags'][:10])}")
        lines.append("- next calls:")
        lines.extend(f"  - `{call}`" for call in route["next_calls"])
        if route["representative_decks"]:
            lines.append("- representative decks:")
            lines.extend(f"  - `{path}`" for path in route["representative_decks"])
        lines.append("")
    return "\n".join(lines).rstrip()


def get_sample_deck(rel_path: str, max_chars: int = 60000) -> dict[str, Any]:
    """Get full text of a public sample .mai/.meg deck."""
    decks = load_sample_decks()
    deck = decks.get(rel_path)
    if deck is None:
        candidates = [p for p in decks if p.endswith("/" + rel_path) or p == rel_path]
        if len(candidates) == 1:
            deck = decks[candidates[0]]
        else:
            return {
                "path": rel_path,
                "error": f"not found (try one of: {candidates[:5]})" if candidates
                else "not found in public sample decks",
            }
    text = deck.text
    truncated = len(text) > max_chars
    if truncated:
        text = text[:max_chars] + f"\n\n[... truncated, full length: {deck.char_count} chars]"
    return {
        "path": deck.path,
        "family": deck.family,
        "case": deck.case,
        "ext": deck.ext,
        "text": text,
        "char_count": deck.char_count,
        "truncated": truncated,
    }


def _uniq(items: list[str]) -> list[str]:
    seen = set()
    out = []
    for item in items:
        if item not in seen:
            out.append(item)
            seen.add(item)
    return out


def _family_meta(family: str) -> dict[str, Any]:
    return FAMILY_META.get(
        family,
        {
            "title": family.rsplit("/", 1)[-1] if family else "sample deck",
            "tags": ("sample-deck",),
            "hint": "Use as a public ELF/MAGIC input deck for a local ELF installation.",
        },
    )


def build_sample_deck_cards(
    limit: int = 100,
    family: str | None = None,
    query: str | None = None,
    team28: bool = False,
) -> list[dict[str, Any]]:
    """Build compact cards over public ELF-runnable sample deck cases."""
    decks = load_sample_decks()
    mai_decks = [d for d in decks.values() if d.ext == "mai"]
    if team28:
        wanted = set(TEAM28_CASES)
        mai_decks = [d for d in mai_decks if (d.family, d.case) in wanted]
    if family:
        mai_decks = [d for d in mai_decks if family in d.family]

    cards = []
    for mai in sorted(mai_decks, key=lambda d: d.path):
        meg_path = mai.path[:-4] + ".meg"
        meg = decks.get(meg_path)
        meta = _family_meta(mai.family)
        haystack = " ".join(
            [
                mai.path,
                mai.family,
                mai.case,
                mai.text,
                meg.text if meg else "",
                " ".join(meta["tags"]),
            ]
        ).lower()
        if query:
            keywords = [k.lower() for k in query.split() if k.strip()]
            if not all(k in haystack for k in keywords):
                continue
        sol_blocks = _uniq(SOL_RE.findall(mai.text))
        pre_keywords = [kw for kw in KEYWORDS if re.search(rf"^\s*{kw}\b", mai.text, re.MULTILINE)]
        elements = _uniq(ELEMENT_RE.findall(meg.text if meg else ""))
        tags = list(meta["tags"])
        hint = meta["hint"]
        validation = get_family_validation(mai.family)
        if team28:
            hint = (
                "Use as a Python-interface seed/inspection deck; team28 is "
                "an orchestration manifest, not a normal ELF GUI/CLI "
                "deck-execution workflow."
            )
        cards.append(
            {
                "family": mai.family,
                "case": mai.case,
                "title": meta["title"],
                "tags": tags,
                "mai_path": mai.path,
                "meg_path": meg_path if meg else "",
                "sol_blocks": sol_blocks,
                "pre_keywords": pre_keywords,
                "elements": elements,
                "validation_level": validation["validation_level"],
                "validation_scope": validation["validation_scope"],
                "char_count": mai.char_count + (meg.char_count if meg else 0),
                "hint": hint,
            }
        )
    if team28:
        order = {key: i for i, key in enumerate(TEAM28_CASES)}
        cards.sort(key=lambda c: order[(c["family"], c["case"])])
    return cards[: max(0, limit)]


def build_team28_cards() -> list[dict[str, Any]]:
    """Build the curated 28-card Python-interface representative set."""
    return build_sample_deck_cards(limit=28, team28=True)


def format_sample_deck_cards(cards: list[dict[str, Any]], title: str = "ELF public sample deck playbook") -> str:
    """Format compact sample deck cards as Markdown."""
    if not cards:
        return f"# {title}\n\nNo sample deck cards matched."
    lines = [f"# {title} ({len(cards)} cards)", ""]
    for i, card in enumerate(cards, 1):
        lines.append(f"## {i}. {card['title']} / {card['case']}")
        lines.append(f"- family: `{card['family']}`")
        lines.append(f"- files: `{card['mai_path']}` + `{card['meg_path']}`")
        lines.append(f"- tags: {', '.join(card['tags'])}")
        lines.append(f"- SOL: {', '.join(card['sol_blocks']) if card['sol_blocks'] else '(none)'}")
        lines.append(f"- PRE: {', '.join(card['pre_keywords']) if card['pre_keywords'] else '(none)'}")
        lines.append(f"- elements: {', '.join(card['elements']) if card['elements'] else '(none)'}")
        lines.append(
            f"- validation: `{card['validation_level']}` - {card['validation_scope']}"
        )
        lines.append(f"- hint: {card['hint']}")
        lines.append("")
    return "\n".join(lines).rstrip()


def format_team28_cards(cards: list[dict[str, Any]]) -> str:
    """Format team28 cards with the required Python-interface manifest note."""
    body = format_sample_deck_cards(cards, title="ELF Python-interface team28")
    note = (
        "# team28 Python-interface seed manifest\n\n"
        "team28 is a Python-interface seed manifest, not a normal ELF GUI/CLI "
        "deck-execution workflow. The public `.mai`/`.meg` paths below are "
        "seed decks and inspection material; runtime orchestration belongs to "
        "the ELF Python interface, outside this documentation MCP server.\n\n"
    )
    return note + body
