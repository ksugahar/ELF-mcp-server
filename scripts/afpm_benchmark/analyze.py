"""Independently reconstruct torque from MAGIC force records and export plots."""
from collections import defaultdict
import csv
import hashlib
import json
import math
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path.cwd()
SWEEP = ROOT / "sweep_mwv"
PHASES = "ABC"

def force_records(file):
    positions = {}
    forces = {}
    for line in file.read_text(errors="replace").splitlines():
        if not line.startswith(("M3GF ", "M3GFG ")):
            continue
        tag, eid, time_id, mid, sub_id, x, y, z = line.split()
        key = tuple(map(int, (eid, time_id, mid, sub_id)))
        values = positions if tag == "M3GFG" else forces
        assert key not in values
        values[key] = (float(x), float(y), float(z))
    assert positions.keys() == forces.keys() and positions
    by_mid = defaultdict(list)
    for key, (x, y, _) in positions.items():
        fx, fy, _ = forces[key]
        by_mid[key[2]].append(x * fy - y * fx)
    assert set(by_mid) == set(range(10,16))
    return -math.fsum(math.fsum(values) for values in by_mid.values()),len(positions)

def rms(x):
    return float(np.sqrt(np.mean(x*x)))

def summary(flux, emf, torque):
    mean = float(torque.mean())
    pp = float(np.ptp(torque))
    return {
        "flux_peak_abs_wb_turn_per_phase": np.max(np.abs(flux),axis=0).tolist(),
        "flux_rms_wb_turn_per_phase": np.sqrt(np.mean(flux**2,axis=0)).tolist(),
        "emf_peak_abs_v_per_phase": np.max(np.abs(emf),axis=0).tolist(),
        "emf_rms_v_per_phase": np.sqrt(np.mean(emf**2,axis=0)).tolist(),
        "torque_mean_nm": mean,
        "torque_min_nm": float(torque.min()),
        "torque_max_nm": float(torque.max()),
        "torque_ripple_peak_to_peak_nm": pp,
        "torque_ripple_pct_of_abs_mean": 100*pp/abs(mean) if mean else None,
    }

def main():
    samples=json.loads((SWEEP/"samples.json").read_text(encoding="utf-8"))
    meta=samples["settings"]
    counts=meta["angles_per_electrical_period"]
    assert all(len(samples[level][mode])==counts for level in ("coarse", "fine") for mode in ("open","loaded"))
    deg=np.array([row["mechanical_deg"] for row in samples["fine"]["open"]])
    assert len(deg)==counts and np.allclose(np.diff(deg),deg[1])
    dtheta=math.radians(deg[1])
    omega=math.tau*meta["speed_rpm"]/60
    results={}
    waves={}
    csv_path=ROOT/"waveforms.csv"
    with csv_path.open("w",encoding="utf-8",newline="") as csv_file:
        writer=csv.writer(csv_file,lineterminator="\n")
        writer.writerow(["mesh","mechanical_deg","electrical_deg",
                         *[f"lambda_{p}_wb_turn" for p in PHASES],
                         *[f"emf_{p}_v" for p in PHASES],
                         *[f"load_{p}_a" for p in PHASES],
                         "rotor_reaction_nm","pm_linkage_only_torque_nm","mao_rotor_reaction_nm"])
        for level in ("coarse","fine"):
            open_rows=samples[level]["open"]
            loaded=samples[level]["loaded"]
            flux=np.array([row["phase_flux"] for row in open_rows])
            emf=np.array([row["phase_emf_v"] for row in loaded])
            previous_moment=np.array([row["rotor_reaction_z_nm"] for row in loaded])
            pm=np.array([row["pm_only_torque_from_linkage_nm"] for row in loaded])
            current=np.array([row["currents_a"] for row in loaded])
            assert np.allclose(current.sum(axis=1),0.0,atol=1e-12)
            torque=[]
            force_count=[]
            for a,b in zip(open_rows,loaded):
                assert a["index"]==b["index"] and a["meg_sha256"]==b["meg_sha256"]
                mag=SWEEP/level/f"{b['index']:02d}"/"loaded"/"afpm.mag"
                assert hashlib.sha256(mag.read_bytes()).hexdigest()==b["mag_sha256"]
                value, points=force_records(mag)
                torque.append(value)
                force_count.append(points)
            torque=np.array(torque)
            assert np.allclose(emf,-omega*(np.roll(flux,-1,axis=0)-np.roll(flux,1,axis=0))/(2*dtheta))
            result=summary(flux,emf,torque)
            result["mesh_counts"]=open_rows[0]["mesh_counts"]
            for stage in ("open","loaded"):
                yoke_max=[]
                for i in range(counts):
                    file=SWEEP/level/f"{i:02d}"/stage/"afpm.mao"
                    line=re.search(r"BMAX ELEMENT=\s*\d+\s+MID=\s*1\s+BMAX=\s*([+\-\d.E]+)",file.read_text(errors="replace"))
                    assert line, file
                    yoke_max.append(float(line.group(1)))
                result[f"{stage}_max_reported_yoke_b_t"]=max(yoke_max)
            fit=np.fft.rfft(flux,axis=0)*(2/counts)
            result["phase_flux_fundamental_peak_wb_turn"]=np.abs(fit[1]).tolist()
            result["phase_flux_fundamental_angle_deg"]=np.angle(fit[1],deg=True).tolist()
            result["phase_flux_half_period_mismatch_max_wb_turn"]=float(np.max(np.abs(flux+np.roll(flux,counts//2,axis=0))))
            result["pm_only_linkage_torque_mean_nm"]=float(pm.mean())
            result["torque_printed_vs_force_records_max_abs_diff_nm"]=float(np.max(np.abs(torque-previous_moment)))
            result["fixb_force_records_per_angle"]=force_count[0]
            result["paired_coils_max_abs_linkage_mismatch_wb_turn"]=max(
                abs(a-b) for row in open_rows for a,b in zip(row["coil_flux"][:3],row["coil_flux"][3:]))
            results[level]=result
            waves[level]=flux,emf,torque
            for i in range(counts):
                writer.writerow([level,deg[i],deg[i]*meta["pole_pairs"],*flux[i],*emf[i],
                                 *current[i],torque[i],pm[i],previous_moment[i]])

    c,f=waves["coarse"],waves["fine"]
    results["fine_minus_coarse"]={
        "flux_waveform_rms_diff_wb_turn": rms(f[0]-c[0]),
        "flux_waveform_rms_diff_pct_of_fine": 100*rms(f[0]-c[0])/rms(f[0]),
        "emf_waveform_rms_diff_v": rms(f[1]-c[1]),
        "emf_waveform_rms_diff_pct_of_fine": 100*rms(f[1]-c[1])/rms(f[1]),
        "torque_waveform_rms_diff_nm": rms(f[2]-c[2]),
        "torque_waveform_rms_diff_pct_of_fine": 100*rms(f[2]-c[2])/rms(f[2]),
        "torque_mean_diff_nm": float(f[2].mean()-c[2].mean()),
        "torque_mean_diff_pct_of_coarse_abs_mean": 100*float(f[2].mean()-c[2].mean())/abs(float(c[2].mean())),
        "torque_ripple_pp_diff_nm": float(np.ptp(f[2])-np.ptp(c[2])),
        "torque_ripple_pp_diff_pct_of_coarse":100*float(np.ptp(f[2])-np.ptp(c[2]))/float(np.ptp(c[2])),
    }

    fig, axes=plt.subplots(3,1,figsize=(9,9),sharex=True,layout="constrained")
    x=meta["pole_pairs"]*np.append(deg,180)
    palettes=["#005d9c","#ad3c1d","#19734e"]
    for level,style in (("coarse","--"),("fine","-")):
        flux,emf,torque=waves[level]
        for j, color in enumerate(palettes):
            axes[0].plot(x,1e3*np.r_[flux[:,j],flux[0,j]],style,color=color,label=f"{PHASES[j]} {level}")
            axes[1].plot(x,1e3*np.r_[emf[:,j],emf[0,j]],style,color=color,label=f"{PHASES[j]} {level}")
        axes[2].plot(x,1e3*np.r_[torque,torque[0]],style,color="#25234c",label=f"{level} FIXB")
    for ax,label in zip(axes,("Phase flux linkage (mWb-turn)","Open-circuit back-EMF (mV)","Rotor reaction torque (mN m)")):
        ax.set_ylabel(label)
        ax.grid(alpha=.22)
        ax.legend(ncol=3,fontsize=8,loc="upper right")
    axes[-1].set_xlabel("Electrical angle (deg)")
    axes[-1].set_xticks(np.arange(0,361,60))
    axes[-1].set_xlim(0,360)
    fig.suptitle("3D coreless axial-flux PM motor | IEmesh + MAGIC")
    fig.savefig(ROOT/"afpm-waveforms.png",dpi=180)
    plt.close(fig)
    results["settings"]=meta
    results["measurement"]={"torque":"Rotor reaction estimate: negative sum of coil moments r x F, from M3GFG positions (m) and M3GF forces (N).",
                            "emf":"Faraday sign convention; -omega_m times centered periodic mechanical-angle linkage derivative.","angle_step_deg_mechanical":float(deg[1])}
    (ROOT/"summary.json").write_text(json.dumps(results,indent=2)+"\n",encoding="utf-8",newline="\n")

if __name__=="__main__":
    main()
