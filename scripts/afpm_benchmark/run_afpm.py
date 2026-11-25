"""Independent coreless 4-pole / 6-coil axial-flux PM design benchmark."""
from pathlib import Path
import ctypes
from ctypes import wintypes
import math
import subprocess
import os

ROOT = Path.cwd()
def product_bin():
    return Path(os.environ["ELF_PRODUCT_HOME"]).resolve() / "bin"
LEVELS = {"coarse": (2, 24, 4, 12), "fine": (3, 48, 8, 24)}
# rotor annular back iron z=5.5 mm; four arc magnets z=3.5 mm; stator at z=0
# No stator iron. Three series phases, each composed of two identical coils
# spaced 180 mechanical degrees apart.
COILS = tuple(range(10,16))

def affinity():
    k=ctypes.windll.kernel32
    k.GetCurrentProcess.restype=wintypes.HANDLE
    k.SetProcessAffinityMask.argtypes=[wintypes.HANDLE,ctypes.c_size_t]
    if not k.SetProcessAffinityMask(k.GetCurrentProcess(),1):
        raise OSError("CPU affinity setup failed")

def mesh_text(angle, level):
    radial,yoke_nt,mag_nt,coil_nt=LEVELS[level]
    lines=["MODEL MAGIC T","GSC 0.001","NB(NAME,MMB,1)","AA(O,0,0,5.5)",
           f"AA(ARCH3,13,40,{angle},{angle+360},2,{radial},{yoke_nt},1)"]
    for pole in range(4):
        centre=angle+90*pole
        lines += [f"NB(NAME,MWV,{30+pole})","AA(O,0,0,3.5)",
                  f"AA(ARCH3,17,38,{centre-30},{centre+30},2,{radial},{mag_nt},1)"]
    for k,mid in enumerate(COILS):
        theta=math.radians(k*60)
        lines += [f"NB(NAME,MCL,{mid})",f"AA(O,{27*math.cos(theta):.10g},{27*math.sin(theta):.10g},0)",
                  f"AA(RINGB,5,9,1,{coil_nt})"]
    lines += ["AA(O)", "SE(ADD,ALL)", "SN(ADD,ALL)", "RB(MERGE,0.00001)", "SPACE", "STOP"]
    return "\n".join([*lines, ""])


def control(currents):
    lines=["USE  MAGIC  3.50","","PRE","  HBUN 1 OE G","  HBSC 1 1 1","  HBCU 1 0 0","  HBCU 1 1 500"]
    for pole in range(4):
        mid=30+pole
        lines += [f"  HBUN {mid} OE G",f"  HBSC {mid} 1 1",f"  HBCU {mid} -9320 0",
                  f"  HBCU {mid} 0 9320",f"  HBRM {mid} 1 9320",f"  HBCN {mid} 0 {mid}",
                  f"  VEC3 {mid} 0 0 0 {(-1)**pole}"]
    for i,mid in enumerate(COILS):
        lines += [f"  COI1 {mid} 0 60 6 6 A",f"  AMP1 {mid} 0 {currents[i%3]:.13E}"]
    lines += ["END","","SOL MOME","  NCPU 1","  BLAS 1","  TIME 0","  NONL 30 0.001","  DMEG","END","",
              "SOL FIXA","  TIME 0",*(f"  FLUM {mid}" for mid in COILS),"END"]
    return "\n".join([*lines,""])

def run(path,exe,arg,timeout):
    with (path/(exe+".log")).open("wb") as log:
        p=subprocess.run([str(product_bin() / exe),arg],cwd=path,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,timeout=timeout)
    if p.returncode:
        raise RuntimeError(f"{path.name}: {exe} exit {p.returncode}")
