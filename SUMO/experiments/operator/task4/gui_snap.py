"""sumo-gui (traci) screenshots around a collision.  python gui_snap.py NAME SEED T_EVENT X Y ZOOM OFFSETS_S... 
Vehicles within 60 m of (X,Y) are coloured by |speedLat| (grey 0 -> red >=1.2 m/s); collider/victim are highlighted.
Screenshots at T_EVENT+offset (offset in s, e.g. -10 -5 0)."""
import sys, os
from pathlib import Path
import xml.etree.ElementTree as ET
os.environ.setdefault("SUMO_HOME", r"C:\Program Files (x86)\Eclipse\Sumo")
import traci
R = Path(__file__).resolve().parents[3]
name, seed, tev, x, y, zoom = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6])
offs = [float(o) for o in sys.argv[7:]] or [-10.0]
col = [c.attrib for c in ET.parse(R / f"experiments/runs/B0__SYNTHETIC/seed_{seed:02d}/collisions.xml").getroot().iter("collision") if abs(float(c.get("time")) - tev) < 0.01]
ids = {col[0]["collider"], col[0]["victim"]} if col else set()
out = R / "experiments/operator/task4/screens"; out.mkdir(exist_ok=True)
shots = sorted(tev + o for o in offs); last = shots[-1]
cmd = ["sumo-gui", "-n", str(R / "scenario/net/site.proxy.net.xml"), "-r", str(R / "scenario/demand/routes_SYNTHETIC.rou.xml"),
       "-a", str(R / "rules/compiled/B0/vtypes.add.xml"), "--step-length", "0.1", "--lateral-resolution", "0.4",
       "--device.rerouting.probability", "0", "--seed", str(seed), "--start", "--quit-on-end", "--window-size", "1500,950",
       "--delay", "0", "--no-step-log", "true", "--log", str(out / f"{name}.log"), "--collision-output", str(out / f"{name}_coll.xml")]
traci.start(cmd, port=None) if False else traci.start(cmd)
view = traci.gui.getIDList()[0]
traci.gui.setSchema(view, "real world")
traci.gui.setZoom(view, zoom); traci.gui.setOffset(view, x, y)
t0 = shots[0] - 12
if not col: t0 = 0
pending = None
while traci.simulation.getTime() < last + 0.05 or pending is not None:
    traci.simulationStep()
    t = traci.simulation.getTime()
    if t >= t0:
        for v in traci.vehicle.getIDList():
            px, py = traci.vehicle.getPosition(v)
            if (px - x) ** 2 + (py - y) ** 2 > 70 ** 2: continue
            s = min(abs(traci.vehicle.getLateralSpeed(v)) / 1.2, 1.0)
            c = (int(150 + 105 * s), int(150 * (1 - s)), int(150 * (1 - s)), 255)
            if v in ids: c = (0, 90, 255, 255) if v == col[0]["collider"] else (0, 200, 0, 255)  # collider blue, victim green
            traci.vehicle.setColor(v, c)
    if pending is not None and pending.exists() and pending.stat().st_size > 0:
        print("saved", pending.name, flush=True); pending = None
    if shots and pending is None and t >= shots[0] - 1e-6:
        traci.gui.setZoom(view, zoom); traci.gui.setOffset(view, x, y)
        pending = out / f"{name}_t{t:.0f}.png"; traci.gui.screenshot(view, str(pending), 1500, 950); shots.pop(0)
for _ in range(200):  # screenshots are written asynchronously while stepping; requesting a second one first crashes sumo-gui
    if pending is None or (pending.exists() and pending.stat().st_size > 0): break
    traci.simulationStep()
if pending is not None: print("saved" if pending.exists() else "MISSING", pending.name)
traci.close()
