# 3D coreless axial-flux PM motor | IEmesh and ELF/MAGIC

This independently authored benchmark demonstrates the IEmesh-to-MAGIC workflow. The included scripts generate the input decks and extract the results. The benchmark does not qualify a customer design or add a cross-solver comparison.

## Model and execution
- One rotor with four 60-degree arc magnets (17–38 mm radius, 2 mm thick), alternating axial MWV magnetization, with a 2 mm annular back iron (13–40 mm radius, constant relative permeability 500). Nominal magnet remanence is 0.932 T model input.
- Six coreless closed circular coils, 60 turns each, coil-centre radius 27 mm, winding-ring radii 5 and 9 mm, thickness 1 mm. The nearest magnet face is 2 mm above the winding. Series pairs are MID 10+13, 11+14 and 12+15.
- IEmesh (mesh750) compiles .mei to .meg, then MAGIC (magh1600) runs each full .mai deck. For each mesh, adjacent rotor positions are 7.5 mechanical degrees apart, covering one electrical period in 24 points. Each position is solved once at zero current and once under load, using identical MEG bytes. Across both meshes there are 48 accepted mesh compilations and 96 accepted solves.
- Radial and azimuthal subdivisions are refined between the two meshes. Axial subdivisions are fixed. The full geometry is 3D.
- Loaded solves use balanced sinusoidal currents with 2 A phase peak, phased using the fine-grid no-load linkage fundamental. Currents are the same on both meshes. This is a set load point without current-angle optimization.
- Read phase linkage from SOL FIXA / FLUM (M1MF records, Wb-turn). Back-EMF is derived at 1000 rpm with e = -omega_mech d(lambda)/d(theta_mech), using a periodic centered difference on the no-load phase linkage.
- Rotor reaction torque is negative total stator-coil torque about the z axis. The stator is coreless. SOL FIXB / COIM produces coil forces. Summing x Fy - y Fx from M3GFG positions in metres and M3GF forces in N gives coil torque; element TORQUE Z totals from the .mao cross-check the arithmetic. No direct FORT value for the corrected MWV model is claimed.
- The MWL diagnostic was stopped when the expected four-pole fundamental was absent. In this geometry MWL magnetic axes were in-plane, because MWL uses element order. The accepted MWV case uses VEC3 to set alternating axial magnetization. Actual linkage signs reverse between 0 and 90 mechanical degrees. FORT pilot discrepancy and original MWL results are stored separately and were excluded from the accepted sweep.

## Evidence and limits
- The analysis writes summary.json, waveforms.csv, and afpm-waveforms.png.
- Run on Windows with Python, NumPy, Matplotlib, and a licensed ELF600 installation. Set ELF_PRODUCT_HOME to the product directory containing bin/mesh750.exe and bin/magh1600.exe. From a new scratch directory, run the repository's scripts/afpm_benchmark/sweep.py, then scripts/afpm_benchmark/analyze.py. Raw inputs and outputs stay in the scratch directory. The sweep pins itself to CPU 0 and runs the solver with one thread.
- Observed coarse to fine: 152 to 384 elements, phase linkage peak 2.252 to 2.428 mWb-turn, phase back-EMF RMS 0.361 to 0.389 V, mean rotor reaction 14.514 to 14.924 mN m, and sampled peak-to-peak ripple 11.996 to 12.272 mN m.
- Results use linear back iron, ideal closed windings, quasi-static fields, and no thermal, loss or controller model. The two mesh levels measure sensitivity. There is no independent accuracy reference or acceptance limit here, and the sampled peak-to-peak can miss extrema between angles.
