"""Scratch SUMO runs (no repo changes): python run_variant.py NAME [--net F] [--vtypes F] [--end S] [--seeds 1 2 3] -- <extra sumo args>
Uses the sumo binary with the B0 SYNTHETIC inputs (same as the runner); outputs: collisions, lanechange, statistics, log.
fcd/ssm/detectors are left out (they only observe)."""
import argparse, subprocess, sys, os, json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import xml.etree.ElementTree as ET

R = Path(__file__).resolve().parents[3]
ap = argparse.ArgumentParser()
ap.add_argument("name"); ap.add_argument("--net", default=str(R / "scenario/net/site.proxy.net.xml"))
ap.add_argument("--vtypes", default=str(R / "rules/compiled/B0/vtypes.add.xml"))
ap.add_argument("--routes", default=str(R / "scenario/demand/routes_SYNTHETIC.rou.xml"))
ap.add_argument("--end", default="3600"); ap.add_argument("--seeds", nargs="+", default=["1", "2", "3"])
ap.add_argument("--latres", default="0.4"); ap.add_argument("--fcd", action="store_true")
a, extra = ap.parse_known_args()
a.extra = extra
a.net = str(Path(a.net).resolve()); a.vtypes = str(Path(a.vtypes).resolve()); a.routes = str(Path(a.routes).resolve())
out = R / "experiments/operator/task4/runs" / a.name

def one(seed):
    d = out / f"seed_{int(seed):02d}"; d.mkdir(parents=True, exist_ok=True)
    cmd = ["sumo", "-n", a.net, "-r", a.routes, "-a", a.vtypes, "--begin", "0", "--end", a.end, "--step-length", "0.1",
           "--lateral-resolution", a.latres, "--device.rerouting.probability", "0", "--no-step-log", "true", "--seed", seed,
           "--collision-output", "collisions.xml", "--statistic-output", "statistics.xml",
           "--lanechange-output", "lanechange.xml", "--log", "sumo.log"]
    if a.fcd: cmd += ["--fcd-output", "fcd.xml.gz", "--fcd-output.attributes", "x,y,angle,type,speed,pos,lane,posLat,speedLat,acceleration"]
    cmd += a.extra  # later duplicates override earlier (command line: last wins)
    # dedupe: drop earlier occurrence of an option overridden in extra
    r = subprocess.run(cmd, cwd=d, capture_output=True, text=True)
    (d / "cmd.txt").write_text(" ".join(cmd))
    cols = [c.attrib for c in ET.parse(d / "collisions.xml").getroot().iter("collision")] if (d / "collisions.xml").exists() else []
    st = {}
    if (d / "statistics.xml").exists() and ET.parse(d / "statistics.xml").getroot().find("teleports") is not None:
        t = ET.parse(d / "statistics.xml").getroot()
        st = {"tp": float(t.find("teleports").get("total")), "jam": float(t.find("teleports").get("jam")),
              "yield": float(t.find("teleports").get("yield")), "wl": float(t.find("teleports").get("wrongLane")),
              "wait": int(t.find("vehicles").get("waiting"))}
    return seed, r.returncode, cols, st, r.stderr[-300:]

with ThreadPoolExecutor(3) as ex:
    res = list(ex.map(one, a.seeds))
tot = 0
for seed, rc, cols, st, err in res:
    byt = {}
    for c in cols: byt[c["type"]] = byt.get(c["type"], 0) + 1
    n900 = sum(float(c["time"]) < 900 for c in cols)
    onint = sum(c["lane"].startswith(":") for c in cols)
    print(f"{a.name} seed {seed} rc={rc} collisions={len(cols)} (t<900: {n900}) by_type={byt} on_internal={onint} {st} {err.strip()[:200]}")
    tot += len(cols)
print(f"{a.name} TOTAL collisions {tot}")
