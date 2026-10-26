"""Catalogue every collision of a B0 campaign: link, signal state, fcd (posLat/speedLat) 5 s before, lane changes, log lines.
usage: python catalogue.py <runs_dir e.g. experiments/runs/B0__SYNTHETIC> [seeds...]  -> prints markdown-ish text"""
import gzip, re, sys, math
from pathlib import Path
import xml.etree.ElementTree as ET
import sumolib

root = Path(sys.argv[1])
seeds = sys.argv[2:] or ["01", "02", "03"]
net = sumolib.net.readNet("scenario/net/site.proxy.net.xml", withInternal=True)
tl = net.getTLSSecure(next(iter(net.getTrafficLights())).getID()) if False else None

# internal lane -> (from edge, to edge, dir, tl link index)
linkinfo = {}
for e in net.getEdges():
    for c in [c for l in e.getLanes() for c in l.getOutgoing()]:
        pass
for n in net.getNodes():
    for c in [c for e in n.getIncoming() for c in sum([l.getOutgoing() for l in e.getLanes()], [])]:
        via = c.getViaLaneID()
        if via:
            linkinfo[via] = (c.getFrom().getID(), c.getTo().getID(), c.getDirection(), c.getTLLinkIndex(),
                             c.getFromLane().getIndex(), c.getToLane().getIndex())
# 2nd internal lane of a link (via chain)
for via, info in list(linkinfo.items()):
    l = net.getLane(via)
    for nxt in l.getOutgoing():
        v2 = nxt.getViaLaneID() or nxt.getToLane().getID()
        if v2.startswith(":"):
            linkinfo[v2] = info

def tls_state(seed, t):
    best = None
    for ev in ET.iterparse(root / f"seed_{seed}" / "tls_states.xml"):
        pass
    return best

def tls_at(seed):
    rows = []
    for _, el in ET.iterparse(root / f"seed_{seed}" / "tls_states.xml"):
        if el.tag == "tlsState":
            rows.append((float(el.get("time")), el.get("state")))
        el.clear()
    return rows

for seed in seeds:
    d = root / f"seed_{seed}"
    cols = [c.attrib for c in ET.parse(d / "collisions.xml").getroot().iter("collision")]
    tlr = tls_at(seed)
    ids = {c["collider"] for c in cols} | {c["victim"] for c in cols}
    win = [(float(c["time"]) - 5.0, float(c["time"]), c) for c in cols]
    fcd = {}
    cur = None
    pat = re.compile(r'<timestep time="([\d.]+)"')
    vpat = re.compile(r'<vehicle id="([^"]+)"')
    with gzip.open(d / "fcd.xml.gz", "rt") as f:
        for line in f:
            m = pat.search(line)
            if m:
                cur = float(m.group(1)); continue
            m = vpat.search(line)
            if m and m.group(1) in ids and any(a <= cur <= b + 0.05 for a, b, _ in win):
                a = dict(re.findall(r'(\w+)="([^"]*)"', line)); a["t"] = cur
                fcd.setdefault(m.group(1), []).append(a)
    lcs = {}
    for el in ET.parse(d / "lanechange.xml").getroot().iter("change"):
        if el.get("id") in ids:
            lcs.setdefault(el.get("id"), []).append(el.attrib)
    log = (d / "sumo.log").read_text(errors="replace").splitlines()
    print(f"\n######## seed {seed}: {len(cols)} collisions")
    for i, (a, t, c) in enumerate(win):
        lane = c["lane"]; info = linkinfo.get(lane)
        st = [s for tt, s in tlr if tt <= t][-1]
        sc = st[info[3]] if info and info[3] is not None and info[3] >= 0 else "-"
        print(f"\n--- seed {seed} #{i} t={t} type={c['type']} lane={lane} pos={c['pos']}")
        print(f"  link={info}  signal char={sc}  tls={st}")
        print(f"  collider={c['collider']} ({c['colliderType']}, v={c['colliderSpeed']})  victim={c['victim']} ({c['victimType']}, v={c['victimSpeed']})")
        for who in (c["collider"], c["victim"]):
            rows = [r for r in fcd.get(who, []) if a <= r["t"] <= t + 0.05]
            print(f"  fcd {who}: " + " | ".join(f"{r['t']:.1f}:{r['lane'].split('_')[-2] if r['lane'].startswith(':') else r['lane']}_{r['lane'].split('_')[-1]} v={float(r['speed']):.1f} pl={float(r['posLat']):.2f} sl={float(r['speedLat']):.2f}" for r in rows[::5]))
            for ch in lcs.get(who, []):
                if t - 15 <= float(ch["time"]) <= t + 0.1:
                    print(f"  LC {who}: t={ch['time']} {ch['from']}->{ch['to']} dir={ch['dir']} reason={ch['reason']} latGap={ch['latGap']}")
        for ln in log:
            if (c["collider"] in ln or c["victim"] in ln) and ("Teleport" in ln or "emergency" in ln or "collision" in ln):
                print("  LOG:", ln[:260])
