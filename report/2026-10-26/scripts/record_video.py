"""Record a sumo-gui run of the thesis scenario as PNG frames + per-frame metadata.

Run with the project venv (it imports thesis_sumo):

    SUMO/.venv/Scripts/python.exe report/2026-10-26/scripts/record_video.py \
        --spec B0 --day PROXY_D1 --seed 1 --end 1800 --every 3 --out report/2026-10-26/_rec
    SUMO/.venv/Scripts/python.exe report/2026-10-26/scripts/record_video.py --plain-sumo \
        --day PROXY_D1 --seed 1 --end 1800 --every 3 --out report/2026-10-26/_rec_plain

Spec mode uses `thesis_sumo.sim.runner.run(use_gui=True)` unchanged (same sumocfg, outputs, manifest as a batch
run), with `runs_root` pointed at `<out>/run` so `experiments/runs/` is not touched. The recorder is passed as the
`controller_factory`; it only colours vehicles (visual only) and asks sumo-gui for screenshots, so it only fits
specs WITHOUT `traci_rules.json` (B0, B1_manual): with TraCI rules it would replace their controller.

`--plain-sumo` is the "nothing of the thesis" baseline: same network, signal plan and demand day, but
- one SUMO-default vType per vehicle class: `car` = vClass passenger, `moto` = vClass motorcycle, no other attribute
  (so lane-change model LC2013, no sublane model: no `--lateral-resolution`);
- the `moto_violator` vehicles (the illegal LVL_W left turn, a thesis behaviour) are removed from the routes;
- every other SUMO option at its default (no `--collision.check-junctions`, no aggregated warnings, no SSM), except
  `--step-length` kept at the thesis value (0.1 s) so that both videos share the same frame clock, and `--seed`.
"""

from __future__ import annotations

import argparse
import ctypes
import ctypes.wintypes as wt
import json
import subprocess
import threading
import time
from pathlib import Path

import sumolib
import traci
from lxml import etree

from thesis_sumo.config import load_site
from thesis_sumo.sim import runner
from thesis_sumo.sim.runner import resolve_inputs, run

VIEW = "View #0"
COLORS = {"car": (60, 140, 255, 255), "moto_violator": (255, 40, 40, 255), "moto": (255, 210, 0, 255)}
PAUSE_S = 0.03     # > MIN_DRAW_DELAY (20 ms), see Recorder.on_step
NUDGE_AFTER_S = 0.7


def _gui_windows() -> list[int]:
    """Top-level windows of the sumo-gui started by the runner (title "run.sumocfg - SUMO <version>")."""
    user32, found = ctypes.windll.user32, []

    def cb(hwnd, _):
        n = user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(n + 1)
        user32.GetWindowTextW(hwnd, buf, n + 1)
        if buf.value.startswith("run.sumocfg - SUMO"):
            found.append(hwnd)
        return True

    user32.EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)(cb), 0)
    return found


def _nudge(d: int) -> None:
    """Resize the sumo-gui window by `d` px: the view's onConfigure calls checkSnapshots() (GUISUMOAbstractView.cpp)."""
    user32 = ctypes.windll.user32
    for hwnd in _gui_windows():
        r = wt.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(r))
        user32.SetWindowPos(hwnd, None, 0, 0, r.right - r.left + d, r.bottom - r.top,
                            0x0002 | 0x0004 | 0x0010)  # SWP_NOMOVE | SWP_NOZORDER | SWP_NOACTIVATE


def _color(type_id: str):
    for prefix in ("moto_violator", "moto", "car"):  # moto_violator before moto
        if type_id.startswith(prefix):
            return COLORS[prefix]
    return None


class Recorder:
    def __init__(self, tc, site, *, frames_dir: Path, every: int, size: tuple[int, int], half_w: float):
        self.tc, self.frames_dir, self.every, self.size = tc, frames_dir, every, size
        frames_dir.mkdir(parents=True, exist_ok=True)
        # site: thesis_sumo.config.Site (a dict)
        lon, lat = site.require("intersection.center_lonlat")
        self.cx, self.cy = tc.simulation.convertGeo(lon, lat, fromGeo=True)
        half_h = half_w * size[1] / size[0]
        tc.gui.setSchema(VIEW, "real world")
        tc.gui.setBoundary(VIEW, self.cx - half_w, self.cy - half_h, self.cx + half_w, self.cy + half_h)
        self.approach_lanes = [f"{a['edge']}_{i}" for a in site["approaches"] for i in range(len(a["lane_widths_m"]))]
        # the study junction's TLS id is not a junction id (GS_cluster_...): pick it by its controlled lanes
        self.tls = next((t for t in tc.trafficlight.getIDList()
                         if set(tc.trafficlight.getControlledLanes(t)) & set(self.approach_lanes)), None)
        self.step = 0
        self.teleports = 0
        self.collisions = 0
        self.last_collision_t = None
        self.meta: list[dict] = []
        self.pending: Path | None = None
        self.pending_since = 0.0
        self.nudges = 0
        threading.Thread(target=self._watchdog, daemon=True).start()

    def _watchdog(self) -> None:
        d = 1
        while True:
            time.sleep(0.1)
            p = self.pending
            if p is not None and not p.exists() and time.perf_counter() - self.pending_since > NUDGE_AFTER_S:
                _nudge(d)
                d = -d
                self.nudges += 1
                self.pending_since = time.perf_counter()

    def on_step(self, t: float) -> None:
        tc = self.tc
        # sumo-gui writes a TraCI screenshot at the end of the step after the request, from the GUI thread's
        # step event (GUISUMOViewParent::onSimStep -> checkSnapshots), and the run thread blocks until it is written
        # (GUIRunThread::waitForSnapshots). On Windows GUIApplicationWindow::handleEvent_SimulationStep drops step
        # events that come < 20 ms after the previous one (#6371): if that one is dropped, sumo-gui deadlocks (seen
        # here after 2-3 frames). Mitigation: pause after the request; the watchdog thread resizes the window by
        # 1 px when a screenshot is late, whose onConfigure also runs checkSnapshots and releases the run thread.
        if self.pending is not None:
            while not self.pending.exists():
                time.sleep(0.002)
            self.pending = None
        for vid in tc.simulation.getDepartedIDList():
            c = _color(tc.vehicle.getTypeID(vid))
            if c:
                tc.vehicle.setColor(vid, c)
        self.teleports += tc.simulation.getStartingTeleportNumber()
        n_coll = len(tc.simulation.getCollisions())
        if n_coll:
            self.collisions += n_coll
            self.last_collision_t = t
        self.step += 1
        if self.step % self.every:
            return
        idx = len(self.meta)
        halting = sum(tc.lane.getLastStepHaltingNumber(lane) for lane in self.approach_lanes)
        # the image shows the state one step (0.1 s) after `t`
        self.meta.append({
            "i": idx, "t": round(t, 2),
            "n_veh": tc.vehicle.getIDCount(),
            "pending": len(tc.simulation.getPendingVehicles()),
            "halting_approaches": halting,
            "tls_phase": tc.trafficlight.getPhase(self.tls) if self.tls else None,
            "tls_state": tc.trafficlight.getRedYellowGreenState(self.tls) if self.tls else None,
            "teleports": self.teleports, "collisions": self.collisions,
            "last_collision_t": self.last_collision_t,
        })
        self.pending_since = time.perf_counter()
        self.pending = self.frames_dir / f"f{idx:06d}.png"
        tc.gui.screenshot(VIEW, str(self.pending), *self.size)
        time.sleep(PAUSE_S)

    def close(self) -> None:
        (self.frames_dir / "frames.json").write_text(json.dumps(self.meta), encoding="utf-8")
        print(f"recorder: {len(self.meta)} frames, {self.nudges} watchdog nudges", flush=True)


def record_plain_sumo(a, out: Path) -> None:
    """Build and record the plain-SUMO baseline (see module doc) in `<out>/run/`."""
    site = load_site(a.site)
    inputs = resolve_inputs("B0", a.day, a.site)  # only for the net and routes paths of the day
    run_dir = out / "run" / f"SUMO_DEFAULT__{a.day}" / f"seed_{a.seed:02d}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "vtypes.add.xml").write_text(
        '<additional>\n    <vType id="car" vClass="passenger"/>\n    <vType id="moto" vClass="motorcycle"/>\n'
        '</additional>\n', encoding="utf-8")
    routes = etree.parse(str(inputs.routes))
    dropped = [v for v in routes.getroot().iter("vehicle") if v.get("type") == "moto_violator"]
    for v in dropped:
        v.getparent().remove(v)
    routes.write(str(run_dir / "routes.rou.xml"), encoding="UTF-8", xml_declaration=True)
    (run_dir / "dropped_violators.txt").write_text(f"{len(dropped)} moto_violator vehicles removed\n", encoding="utf-8")
    cfg = run_dir / "run.sumocfg"  # the watchdog finds the window by its title "run.sumocfg - SUMO <version>"
    subprocess.run([sumolib.checkBinary("sumo"), "-n", str(inputs.net), "-r", str(run_dir / "routes.rou.xml"),
                    "-a", str(run_dir / "vtypes.add.xml"), "--begin", "0", "--end", str(a.end),
                    "--step-length", "0.1", "--seed", str(a.seed),
                    "--statistic-output", str(run_dir / "statistics.xml"),
                    "--collision-output", str(run_dir / "collisions.xml"),
                    "--save-configuration", str(cfg)], check=True)
    traci.start([sumolib.checkBinary("sumo-gui"), "-c", str(cfg), "--log", str(run_dir / "sumo.log"),
                 *runner.GUI_OPTIONS])
    try:
        rec = Recorder(traci, site, frames_dir=out / "frames", every=a.every, size=tuple(a.size), half_w=a.half_width)
        try:
            while traci.simulation.getTime() < a.end - 1e-9:
                traci.simulationStep()
                rec.on_step(traci.simulation.getTime())
        finally:
            rec.close()
    finally:
        traci.close()
    stats = runner.read_statistics(run_dir / "statistics.xml")
    collisions = runner.read_collisions(run_dir / "collisions.xml")
    summary = {"run": run_dir.relative_to(out).as_posix(), "dropped_violators": len(dropped),
               "vehicles": stats["vehicles"], "teleports": stats["teleports"],
               "n_collisions": len(collisions), "collisions_by_class": runner.collision_classes(collisions),
               "n_collisions_junction": sum(map(runner.is_junction_collision, collisions))}
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default="B0")
    ap.add_argument("--plain-sumo", action="store_true", help="plain-SUMO baseline instead of --spec (module doc)")
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
    # sumo-gui --help: -d/--delay ms between steps (the GUI may remember a non-zero value), --window-size x,y
    runner.GUI_OPTIONS = [*runner.GUI_OPTIONS, "--delay", "0", "--window-size", f"{a.size[0] + 40},{a.size[1] + 160}"]
    if a.plain_sumo:
        record_plain_sumo(a, out)
        return
    inputs = resolve_inputs(a.spec, a.day, a.site)
    if inputs.traci_rules is not None:
        raise SystemExit(f"{a.spec} has traci_rules.json; this recorder would replace its controller")

    def factory(tc, inp, run_dir):
        return Recorder(tc, inp.site, frames_dir=out / "frames", every=a.every, size=tuple(a.size),
                        half_w=a.half_width)

    res = run(a.spec, a.day, a.seed, use_gui=True, site_path=a.site, sim_end_s=a.end, runs_root=out / "run",
              inputs=inputs, controller_factory=factory)
    print(json.dumps({k: res.manifest[k] for k in ("run_id", "seed", "wall_time_s", "n_teleports",
                                                   "n_teleports_noncollision", "n_collisions", "n_collisions_lane",
                                                   "n_collisions_junction", "insertion_backlog", "valid_strict")}))


if __name__ == "__main__":
    main()
