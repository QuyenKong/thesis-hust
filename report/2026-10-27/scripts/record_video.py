"""Record a sumo-gui run of a spec WITH its TraCI rules as PNG frames + per-frame metadata (Linux port of
report/2026-10-26/scripts/record_video.py).

Run from the repo root with the project venv, under a virtual X display:

    xvfb-run -a -s "-screen 0 1920x1200x24" SUMO/.venv/bin/python report/2026-10-27/scripts/record_video.py \
        --spec-json SUMO/rules/specs/B2_best.json --day PROXY_D1 --seed 1 --end 1800 --every 3 \
        --out report/2026-10-27/_rec

Changes from the Windows version:
- the spec is compiled into `<out>/compiled/<spec_id>` (rules/compiled/ is not touched) and its TraCI controller
  runs as in a batch run (`make_controller`, same seed and radius); the recorder wraps it and only reads state,
  colours vehicles and takes screenshots after the controller's step;
- no Win32 watchdog (the dropped-step-event deadlock #6371 is a Windows message-loop issue);
- each frame records the F2/box situations the video tracks (see `classify`).
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import replace
from pathlib import Path

from lxml import etree

from thesis_sumo.config import load_experiment, load_site
from thesis_sumo.rules.compiler import compile_spec
from thesis_sumo.runtime.controller import make_controller
from thesis_sumo.runtime.state import JunctionInfo
from thesis_sumo.sim import runner
from thesis_sumo.sim.runner import resolve_inputs, run

VIEW = "View #0"
# detectors are drawn magenta and motorcycles carry red details: tracked states use red / cyan / orange / white
BASE = {"car": (60, 140, 255, 255), "moto": (255, 210, 0, 255),
        "moto_violator": (150, 80, 255, 255), "car_violator": (150, 80, 255, 255)}
STATE = {"box": (255, 0, 0, 255), "blocker": (0, 245, 255, 255), "blocked": (255, 130, 0, 255),
         "sidewalk": (255, 255, 255, 255)}
HALT_V = 0.5  # m/s, below = standing (queue)
PAUSE_S = 0.03


def distribution_of(vtypes_xml: Path) -> dict[str, str]:
    """member vType id -> vTypeDistribution id of the compiled spec."""
    root = etree.parse(str(vtypes_xml)).getroot()
    return {vt.get("id"): d.get("id") for d in root.iter("vTypeDistribution") for vt in d.iter("vType")}


class Recorder:
    def __init__(self, controller, tc, site, dist: dict[str, str], *, frames_dir: Path, every: int,
                 size: tuple[int, int], half_w: float):
        self.ctrl, self.tc, self.dist = controller, tc, dist
        self.frames_dir, self.every, self.size = frames_dir, every, size
        frames_dir.mkdir(parents=True, exist_ok=True)
        lon, lat = site.require("intersection.center_lonlat")
        cx, cy = tc.simulation.convertGeo(lon, lat, fromGeo=True)
        half_h = half_w * size[1] / size[0]
        self.bounds = (cx - half_w, cy - half_h, cx + half_w, cy + half_h)
        tc.gui.setSchema(VIEW, "real world")
        tc.gui.setBoundary(VIEW, *self.bounds)
        info = JunctionInfo.build(tc, site, need_lane_movements=True, need_box=True)
        self.tls = info.tls_id
        self.stop_lanes = [lane for app in info.lanes for lane in info.lanes[app]]
        self.box_lanes = {lane for chain in info.box_lanes.values() for lane in chain}
        self.sidewalk_lanes = {lane for lane in tc.lane.getIDList()
                               if not lane.startswith(":") and tuple(tc.lane.getAllowed(lane)) == ("custom1",)}
        # lane-0 (continuous right turn) chain of every approach and the edges its right turn leads to
        self.lane0 = {}
        for app, lanes in info.lanes.items():
            right = {lk.to_edge for lk in info.links[lanes[0]] if lk.direction in ("r", "R")}
            chain = info.chains[app][0] if info.chains.get(app) else [lanes[0]]
            self.lane0[app] = (set(chain), right)
        self.offset = dict(info.lane_offset)
        self.range_m = float(load_experiment()["observation"]["queue_range_m"])
        self.length = {}
        self.step, self.teleports, self.collisions, self.last_collision_t = 0, 0, 0, None
        self.seen = {k: set() for k in STATE}
        self.colored: dict[str, str] = {}
        self.meta: list[dict] = []
        self.pending: Path | None = None

    def __getattr__(self, name):  # summary(), intervened(), wall_s ... of the wrapped controller (manifest)
        return getattr(self.ctrl, name)

    def _to_stop(self, lane: str, pos: float) -> float:
        if lane not in self.length:
            self.length[lane] = self.tc.lane.getLength(lane)
        return self.offset.get(lane, 0.0) + self.length[lane] - pos

    def classify(self) -> tuple[dict[str, str], list[dict]]:
        """vehicle -> state for the tracked situations, and the right-lane blockers with their queue:
        box      = vehicle on the internal chain of an illegal left turn (waiting inside the junction box);
        blocker  = vehicle on the lane-0 chain of an approach, at most `queue_range_m` (experiment.yaml, the M9
                   range) upstream of the stop line, whose route does not take that lane's right turn;
        blocked  = standing right-turner on lane 0 behind a blocker (counted for the nearest blocker ahead);
        sidewalk = vehicle on a custom1-only (sidewalk) lane."""
        tc, state, blockers = self.tc, {}, []
        per_app: dict[str, list] = {app: [] for app in self.lane0}
        for vid in tc.vehicle.getIDList():
            lane = tc.vehicle.getLaneID(vid)
            if lane in self.box_lanes:
                state[vid] = "box"
            elif lane in self.sidewalk_lanes:
                state[vid] = "sidewalk"
            else:
                for app, (chain, right) in self.lane0.items():
                    if lane in chain:
                        per_app[app].append((self._to_stop(lane, tc.vehicle.getLanePosition(vid)), vid, right))
                        break
        for app, vehs in per_app.items():
            current = None
            for dist, vid, right in sorted(vehs):
                if not right & set(tc.vehicle.getRoute(vid)[tc.vehicle.getRouteIndex(vid):]):
                    if dist > self.range_m:  # through traffic still free to leave lane 0 (outside the M9 range)
                        continue
                    x, y = tc.vehicle.getPosition(vid)
                    current = {"vid": vid, "app": app, "x": x, "y": y, "behind": 0,
                               "halted": tc.vehicle.getSpeed(vid) < HALT_V}
                    blockers.append(current)
                    state[vid] = "blocker"
                elif current is not None and tc.vehicle.getSpeed(vid) < HALT_V:
                    current["behind"] += 1
                    state[vid] = "blocked"
        return state, blockers

    def _recolor(self, state: dict[str, str]) -> None:
        tc = self.tc
        for vid in tc.simulation.getDepartedIDList():
            c = BASE.get(self.dist.get(tc.vehicle.getTypeID(vid), ""))
            if c:
                tc.vehicle.setColor(vid, c)
        for vid, old in list(self.colored.items()):
            if state.get(vid) != old:
                del self.colored[vid]
                try:
                    tc.vehicle.setColor(vid, BASE.get(self.dist.get(tc.vehicle.getTypeID(vid), ""), (200, 200, 200, 255)))
                except Exception:  # left the network this step
                    pass
        for vid, s in state.items():
            if self.colored.get(vid) != s:
                tc.vehicle.setColor(vid, STATE[s])
                self.colored[vid] = s
            self.seen[s].add(vid)

    def _px(self, x: float, y: float) -> tuple[int, int]:
        x0, y0, x1, y1 = self.bounds
        return round((x - x0) / (x1 - x0) * self.size[0]), round((y1 - y) / (y1 - y0) * self.size[1])

    def on_step(self, t: float) -> None:
        self.ctrl.on_step(t)
        tc = self.tc
        if self.pending is not None:  # sumo-gui writes it at the end of the next step
            while not self.pending.exists():
                time.sleep(0.002)
            self.pending = None
        self.teleports += tc.simulation.getStartingTeleportNumber()
        n_coll = len(tc.simulation.getCollisions())
        if n_coll:
            self.collisions += n_coll
            self.last_collision_t = t
        self.step += 1
        if self.step % self.every:
            for vid in tc.simulation.getDepartedIDList():
                c = BASE.get(self.dist.get(tc.vehicle.getTypeID(vid), ""))
                if c:
                    tc.vehicle.setColor(vid, c)
            return
        state, blockers = self.classify()
        self._recolor(state)
        counts = {s: sum(1 for v in state.values() if v == s) for s in STATE}
        idx = len(self.meta)
        self.meta.append({
            "i": idx, "t": round(t, 2),
            "n_veh": tc.vehicle.getIDCount(),
            "pending": len(tc.simulation.getPendingVehicles()),
            "halting_approaches": sum(tc.lane.getLastStepHaltingNumber(lane) for lane in self.stop_lanes),
            "tls_phase": tc.trafficlight.getPhase(self.tls),
            "teleports": self.teleports, "collisions": self.collisions,
            "last_collision_t": self.last_collision_t,
            "now": counts,
            "blockers_halted": sum(b["halted"] for b in blockers),
            "blockers": [{"px": self._px(b["x"], b["y"]), "behind": b["behind"]} for b in blockers],
            "total": {s: len(v) for s, v in self.seen.items()},
        })
        self.pending = self.frames_dir / f"f{idx:06d}.png"
        tc.gui.screenshot(VIEW, str(self.pending), *self.size)
        time.sleep(PAUSE_S)

    def close(self) -> None:
        self.ctrl.close()
        (self.frames_dir / "frames.json").write_text(json.dumps(self.meta), encoding="utf-8")
        print(f"recorder: {len(self.meta)} frames", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec-json", type=Path, required=True)
    ap.add_argument("--day", default="PROXY_D1")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--end", type=float, default=1800)
    ap.add_argument("--every", type=int, default=3, help="screenshot every N sim steps (step 0.1 s)")
    ap.add_argument("--size", type=int, nargs=2, default=(1600, 900))
    ap.add_argument("--half-width", type=float, default=100.0, help="half width of the view in m")
    ap.add_argument("--site", type=Path, default=Path(__file__).resolve().parents[3] / "SUMO/config/site.proxy.yaml")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    out = a.out.resolve()
    spec = json.loads(a.spec_json.read_text(encoding="utf-8"))
    site = load_site(a.site)
    spec_dir = out / "compiled" / spec["spec_id"]
    compile_spec(spec, spec_dir, site=site)
    inputs = replace(resolve_inputs("B0", a.day, a.site), spec_id=spec["spec_id"], spec_dir=spec_dir)
    dist = distribution_of(inputs.vtypes)
    radius = float(load_experiment()["sim"]["fcd_radius_m"])
    # sumo-gui --help: -d/--delay ms between steps, --window-size x,y
    runner.GUI_OPTIONS = [*runner.GUI_OPTIONS, "--delay", "0", "--window-size", f"{a.size[0] + 40},{a.size[1] + 160}"]

    def factory(tc, inp, run_dir):
        if inp.traci_rules is None:
            raise SystemExit(f"{inp.spec_id} has no TraCI rules; use report/2026-10-26/scripts/record_video.py")
        ctrl = make_controller(tc, inp, run_dir, seed=a.seed, radius_m=radius)
        return Recorder(ctrl, tc, inp.site, dist, frames_dir=out / "frames", every=a.every, size=tuple(a.size),
                        half_w=a.half_width)

    res = run(spec["spec_id"], a.day, a.seed, use_gui=True, site_path=a.site, sim_end_s=a.end, runs_root=out / "run",
              inputs=inputs, controller_factory=factory)
    keys = ("run_id", "seed", "wall_time_s", "n_teleports", "n_teleports_noncollision", "n_collisions",
            "n_collisions_lane", "n_collisions_junction", "insertion_backlog", "valid_strict")
    print(json.dumps({k: res.manifest.get(k) for k in keys}))


if __name__ == "__main__":
    main()
