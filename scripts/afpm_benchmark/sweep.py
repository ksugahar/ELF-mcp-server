"""Run one electrical period on two IEmesh decks; preserve raw solver outputs."""
from collections import Counter
import hashlib
import json
import math
import re
import shutil
import time

import numpy as np
from run_afpm import affinity, control, run, mesh_text, ROOT, COILS, product_bin

ANGLES = np.arange(24) * 7.5
LEVELS = ("coarse", "fine")
RPM = 1000.0
POLE_PAIRS = 2
CURRENT_PEAK = 2.0
BASE = ROOT / "sweep_mwv"
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def solve(level, index, currents=None):
    tag = "open" if currents is None else "loaded"
    parent = BASE / level / f"{index:02d}"
    parent.mkdir(parents=True, exist_ok=True)
    directory = parent / tag
    directory.mkdir()
    angle = ANGLES[index]
    started = time.monotonic()
    if currents is None:
        mei = mesh_text(angle, level)
        (directory/"afpm.mei").write_text(mei, encoding="ascii", newline="\n")
        run(directory,"mesh750.exe","afpm.mei",90)
    else:
        shutil.copyfile(parent/"open"/"afpm.meg",directory/"afpm.meg")
    mai = control((0,0,0) if currents is None else currents)
    if currents is not None:
        mai += "\nSOL FIXB\n  TIME 0\n" + "".join(f"  COIM {mid}\n" for mid in COILS) + "END\n"
    (directory/"afpm.mai").write_text(mai, encoding="ascii", newline="\n")
    run(directory,"magh1600.exe","afpm",110)
    mag=(directory/"afpm.mag").read_text(errors="replace")
    seq=[(int(i),float(v)) for i,v in re.findall(r"^M1MF\s+\d+\s+\d+\s+(\d+)\s+\d+\s+([+\-\d.E]+)",mag,re.M)]
    assert [i for i,_ in seq]==list(COILS),seq
    coils=np.array([v for _,v in seq])
    mao=(directory/"afpm.mao").read_text(errors="replace")
    warnings=[line.strip() for line in mao.splitlines() if re.search(r"ELF-[WEQ]\(\d+\)",line)]
    assert not warnings, (directory,warnings)
    row={"level":level,"index":index,"mechanical_deg":float(angle),"electrical_deg":float(angle*POLE_PAIRS),
         "coil_flux":coils.tolist(),"phase_flux":(coils[:3]+coils[3:]).tolist(),"elapsed_s":time.monotonic()-started,
         "meg_sha256":digest(directory/"afpm.meg"),"mag_sha256":digest(directory/"afpm.mag"),
         "mao_sha256":digest(directory/"afpm.mao")}
    records=[line.split() for line in (directory/"afpm.meg").read_text().splitlines() if line.strip()]
    mesh_summary=Counter(r[0] for r in records if r[0] in {"MGR1","MMB8T","MWV8T","MCL8T"})
    row["mesh_counts"]=dict(mesh_summary)
    if currents is not None:
        # Six individual coil sections. The element total torque is about the global origin.
        sections=re.split(r"\.\.\s+COIL FORCE MID=\s*(\d+)",mao)
        by_mid={}
        expected=Counter(int(r[3]) for r in records if r[0]=="MCL8T")
        for mid, content in zip(sections[1::2], sections[2::2]):
            values=[float(l.split()[-1]) for l in content.splitlines() if "ELEMENT TOTAL FORCE =" in l]
            assert len(values)==expected[int(mid)], (mid,len(values),expected[int(mid)])
            by_mid[int(mid)]=math.fsum(values)
        assert list(by_mid)==list(COILS)
        row.update(currents_a=list(currents),coil_torque_z_nm=by_mid,
                   rotor_reaction_z_nm=-math.fsum(by_mid.values()))
    return row

def write_json(path,value):
    path.write_text(json.dumps(value,indent=2)+"\n",encoding="utf-8",newline="\n")

def main():
    affinity()
    BASE.mkdir()
    data={level:{"open":[],"loaded":[]} for level in LEVELS}
    partial=BASE/"progress.json"
    for level in LEVELS:
        for index in range(len(ANGLES)):
            data[level]["open"].append(solve(level,index))
            write_json(partial,data)
            print(level,"open", index,flush=True)
    phase=np.radians(ANGLES*POLE_PAIRS)
    basis=np.column_stack((np.cos(phase),np.sin(phase)))
    fine=np.array([row["phase_flux"] for row in data["fine"]["open"]])
    fit=np.linalg.lstsq(basis,fine,rcond=None)[0]
    assert np.min(np.hypot(*fit)) > 0.5*np.max(np.abs(fine)), "Missing designed four-pole fundamental"
    derivative=np.column_stack((-np.sin(phase),np.cos(phase)))@fit
    # Positive load direction is referenced to the positive phase-A current pilot at 0ﾂｰ.
    # Preserve the signed direction from FIXB, without folding or rectifying it.
    derivative-=derivative.mean(axis=1,keepdims=True)
    currents=derivative*(CURRENT_PEAK/np.max(np.hypot(*np.linalg.lstsq(basis,derivative,rcond=None)[0])))
    data["settings"]={"speed_rpm":RPM,"pole_pairs":POLE_PAIRS,"current_peak_limit_a":CURRENT_PEAK,
        "angles_per_electrical_period":len(ANGLES),"current_policy":"balanced sinusoidal current parallel to fitted fine-grid PM linkage fundamental derivative, held identical across meshes"}
    for level in LEVELS:
        omega=math.tau*RPM/60
        no_load=np.array([row["phase_flux"] for row in data[level]["open"]])
        # Centered periodic derivative on mechanical angle at the stored sample.
        dlam=(np.roll(no_load,-1,axis=0)-np.roll(no_load,1,axis=0))/(2*math.radians(ANGLES[1]))
        for index in range(len(ANGLES)):
            result=solve(level,index,currents[index])
            result["phase_emf_v"]=(-omega*dlam[index]).tolist()
            result["pm_only_torque_from_linkage_nm"]=float(currents[index]@dlam[index])
            data[level]["loaded"].append(result)
            write_json(partial,data)
            print(level,"loaded",index,result["rotor_reaction_z_nm"],flush=True)
    data["solver_sha256"]={n:digest(product_bin() / n) for n in ("magh1600.exe","mesh750.exe")}
    write_json(BASE/"samples.json",data)

if __name__=="__main__":
    main()
