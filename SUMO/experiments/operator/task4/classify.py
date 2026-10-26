"""Classify collisions of run dirs: python classify.py DIR [DIR...]  (DIR/seed_XX/collisions.xml)"""
import sys, collections
from pathlib import Path
import xml.etree.ElementTree as ET
import sumolib
net = sumolib.net.readNet("scenario/net/site.proxy.net.xml", withInternal=True)
def cls(c):
    lane = c["lane"]; pos = float(c["pos"])
    kinds = sorted({c["colliderType"].split("_")[0], c["victimType"].split("_")[0]})
    pair = "+".join(kinds)
    if lane.startswith(":"):
        l = net.getLane(lane); where = f"A_internal(pos<{'1.5' if pos<1.5 else '>=1.5'})"
        return where, pair
    L = net.getLane(lane).getLength()
    return ("B_arm_end(<15m to stop line)" if L - pos < 15 else "C_arm_other"), pair
for d in sys.argv[1:]:
    n = collections.Counter(); rows = []
    for sd in sorted(Path(d).glob("seed_*")):
        for c in ET.parse(sd / "collisions.xml").getroot().iter("collision"):
            k = cls(c.attrib); n[k] += 1
            L = net.getLane(c.get("lane")).getLength()
            rows.append((sd.name, c.get("time"), c.get("type"), c.get("lane")[-22:], c.get("pos"), round(L - float(c.get("pos")), 1), *k))
    print(d, "total", sum(n.values()))
    for k, v in sorted(n.items()): print("  ", k, v)
    if "-v" in sys.argv: pass
    for r in rows: print("   ", *r)
