"""Run one spec x day x seed in SUMO and record it (PLAN Phase 2.4).

    .venv/Scripts/python -m thesis_sumo.sim.runner --spec B0 --day SYNTHETIC --seeds 1 2 3 \
        --site config/site.proxy.yaml [--end 3600] [--nproc 3] [--gui] [--ssm off|violators|all]

`run()` writes `experiments/runs/<spec_id>__<day>/seed_XX/` (an existing seed dir is replaced):

- `run.sumocfg` + `outputs.add.xml` (`sumocfg.write_sumocfg`) and SUMO's outputs (`sumocfg.OUTPUT_FILES`);
- `sumo.log`: every SUMO message (`--log`, "Writes all messages to FILE"). The console copy is discarded in
  batch runs (it duplicates the log). Warnings of one type are aggregated after `sim.aggregate_warnings`
  lines (ruling R22); `summarise_log` adds the aggregated totals back into the counts;
- `vtypes.json`: vClass / length / width / minGap of every loaded vType, queried from SUMO at start;
- `manifest.json`: git hash, SUMO version, hashes of spec / net / routes / site, seed, effective config,
  `site_source`, teleports (all / non-collision), collisions (all / by class / under TraCI intervention),
  insertion backlog and `valid_strict` (alias `valid`);
- `observed_schema/*.csv`: the `schema_observed.TABLES` (`outputs.to_observed_schema`).

`valid_strict` is False when SUMO reports any teleport or collision (statistic-output `teleports total`,
`safety collisions`, and the number of `<collision>` records); nothing is suppressed by options.
`is_eligible(manifest, exp)` applies the looser `experiment.yaml validity` thresholds. Inputs
are resolved by convention: net `scenario/net/<site net>` (from the site file's `site_source`), routes
`scenario/demand/routes_<day>.rou.xml` (ruling R2), spec `rules/compiled/<spec_id>/vtypes.add.xml` (+
`traci_rules.json`: when it exists the TraCI rules run through `thesis_sumo.runtime.controller` (radius
`sim.fcd_radius_m`, seeded by the run seed), which writes `interventions.csv`; the manifest gets
`interventions` (per rule: attempted / executed / reasons). Backend: `experiment.yaml` `backend` (libsumo
for batch runs); `use_gui` always uses traci + sumo-gui (libsumo cannot drive the GUI). SSM device:
`ssm_mode` / `--ssm` (default `experiment.yaml sim.ssm.mode`, see `sumocfg.ssm_options`).
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import multiprocessing
import os
import re
import shutil
import subprocess
import sys
import time
from collections import Counter
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Callable

import sumolib
from lxml import etree

from thesis_sumo.config import REPO_ROOT, Site, load_experiment, load_site
from thesis_sumo.net.apply_patches import site_net_name
from thesis_sumo.runtime.controller import LOG_NAME as INTERVENTIONS_LOG
from thesis_sumo.runtime.controller import make_controller
from thesis_sumo.sim.outputs import VTYPES_JSON, to_observed_schema
from thesis_sumo.sim.sumocfg import OUTPUT_FILES, SSM_MODES, write_sumocfg

RUNS_DIR = REPO_ROOT / "experiments" / "runs"
NET_DIR = REPO_ROOT / "scenario" / "net"
DEMAND_DIR = REPO_ROOT / "scenario" / "demand"
COMPILED_DIR = REPO_ROOT / "rules" / "compiled"
SPECS_DIR = REPO_ROOT / "rules" / "specs"
MANIFEST_NAME = "manifest.json"
LOG_NAME = "sumo.log"
BACKENDS = ("libsumo", "traci")
GUI_OPTIONS = ["--start", "--quit-on-end"]  # sumo-gui --help: start after loading, close at the end
N_TOP_WARNINGS = 15
AGGREGATED_WARNING = re.compile(r"Warning: (\d+) total messages of type: (.*)$")  # sumo --aggregate-warnings
# SUMO collision `type` (sumo.dlr.de/docs/Simulation/Output/Collisions.html#collision_types) -> class
COLLISION_CLASS = {"collision": "rear_end", "side": "lateral", "junction": "junction", "frontal": "other",
                   "sharedLane": "other", "crossing": "other", "walkingarea": "other", "junctionPedestrian": "other"}
VALIDITY_KEYS = ("max_noncollision_teleports", "max_end_backlog", "max_collisions_per_hour",
                 "max_junction_collisions_per_hour", "max_intervened_collisions")


@dataclass(frozen=True)
class RunInputs:
    spec_id: str
    day: str
    site: Site
    net: Path
    routes: Path
    spec_dir: Path

    @property
    def vtypes(self) -> Path:
        return self.spec_dir / "vtypes.add.xml"

    @property
    def traci_rules(self) -> Path | None:
        p = self.spec_dir / "traci_rules.json"
        return p if p.is_file() else None


@dataclass
class RunResult:
    run_dir: Path
    manifest: dict


def resolve_inputs(spec_id: str, day: str, site_path: Path | None = None) -> RunInputs:
    site = load_site(site_path)
    inputs = RunInputs(spec_id, day, site, NET_DIR / site_net_name(site), DEMAND_DIR / f"routes_{day}.rou.xml",
                       COMPILED_DIR / spec_id)
    for what, p in (("network", inputs.net), ("routes", inputs.routes), ("compiled spec vTypes", inputs.vtypes)):
        if not p.is_file():
            raise FileNotFoundError(f"{what} file {p} not found")
    return inputs


# ---------------------------------------------------------------- hashing / provenance


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _dir_hash(d: Path) -> tuple[str, dict[str, str]]:
    files = {p.relative_to(d).as_posix(): _sha256(p) for p in sorted(d.rglob("*")) if p.is_file()}
    h = hashlib.sha256()
    for name, digest in files.items():
        h.update(f"{name}\0{digest}\n".encode())
    return h.hexdigest(), files


def _git() -> tuple[str | None, bool | None]:
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, check=True)
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT, capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None, None
    return head.stdout.strip(), bool(dirty.stdout.strip())


def _rel(p: Path) -> str:
    p = Path(p).resolve()
    try:
        return p.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return p.as_posix()


# ---------------------------------------------------------------- SUMO results


def read_statistics(path: Path) -> dict[str, dict[str, float]]:
    """statistic-output elements vehicles / teleports / safety as {element: {attribute: value}}."""
    root = etree.parse(str(path)).getroot()
    out = {}
    for tag in ("vehicles", "teleports", "safety"):
        el = root.find(tag)
        if el is None:
            raise ValueError(f"{path}: no <{tag}> element")
        out[tag] = {k: float(v) for k, v in el.attrib.items()}
    return out


def read_collisions(path: Path) -> list[dict[str, str]]:
    """All `<collision>` records (attributes as strings: time, type, lane, collider, victim, ...)."""
    return [dict(el.attrib) for el in etree.parse(str(path)).getroot().iter("collision")]


def collision_classes(collisions: list[dict]) -> dict[str, int]:
    """Count collisions per class of `COLLISION_CLASS` (SUMO collision `type`, docs Simulation/Output/Collisions)."""
    out = dict.fromkeys(dict.fromkeys(COLLISION_CLASS.values()), 0)
    for c in collisions:
        if c.get("type") not in COLLISION_CLASS:
            raise ValueError(f"collision type {c.get('type')!r} is not a documented SUMO collision type "
                             f"{sorted(COLLISION_CLASS)}")
        out[COLLISION_CLASS[c["type"]]] += 1
    return out


def is_junction_collision(c: dict) -> bool:
    """A collision on the junction: SUMO type `junction` ("collision between vehicles on a junction", only reported
    with --collision.check-junctions) or any collision whose lane is an internal lane (id starting with ':')."""
    return c.get("type") == "junction" or str(c.get("lane", "")).startswith(":")


def count_intervened(collisions: list[dict], controller) -> int:
    """Collisions in which collider or victim was inside an intervention window (ruling R30: from the command until
    the vehicle reaches its first non-internal lane after the stop line), asked through the controller's optional
    hook `intervened(vehicle_id, t) -> bool`; 0 without a controller or hook."""
    hook = getattr(controller, "intervened", None)
    if hook is None:
        return 0
    return sum(1 for c in collisions
               if hook(c["collider"], float(c["time"])) or hook(c["victim"], float(c["time"])))


def is_eligible(manifest: dict, exp: dict) -> tuple[bool, list[str]]:
    """Whether a run may count for "best spec" selection under `experiment.yaml validity` (the GEH gate is
    added in Task 11); returns (eligible, reasons it is not). Raises while a threshold is still null."""
    limits = exp.get("validity") or {}
    missing = [k for k in VALIDITY_KEYS if limits.get(k) is None]
    if missing:
        raise ValueError(f"experiment.yaml validity.{', validity.'.join(missing)} is null (TODO_DECIDE); "
                         f"the collision caps are set from the B0 p90 (floor 2) by the operator, with "
                         f"--collision.check-junctions on (ruling R28)")
    sim = manifest["config"]["sim"]
    hours = (float(sim["end_s"]) - float(sim["begin_s"])) / 3600.0
    checks = [
        (manifest["n_teleports_noncollision"], limits["max_noncollision_teleports"], "non-collision teleports"),
        (manifest["insertion_backlog"], limits["max_end_backlog"], "vehicles waiting for insertion at the end"),
        (manifest["n_collisions_lane"] / hours, limits["max_collisions_per_hour"], "lane collisions per hour"),
        (manifest["n_collisions_junction"] / hours, limits["max_junction_collisions_per_hour"],
         "junction collisions per hour"),
        (manifest["n_collisions_intervened"], limits["max_intervened_collisions"],
         "collisions involving a vehicle under TraCI intervention"),
    ]
    reasons = [f"{name}: {value:g} > {limit:g}" for value, limit, name in checks if value > limit]
    return not reasons, reasons


def _warning_template(line: str) -> str:
    return re.sub(r"\d+(\.\d+)?", "#", re.sub(r"'[^']*'", "'*'", line))


def _format_regex(fmt: str) -> re.Pattern:
    """Regex for the printed lines of an aggregated SUMO message format (see `summarise_log`)."""
    quoted = [r"\S+?".join(map(re.escape, part.split("%"))) for part in fmt.split("'%'")]
    return re.compile("Warning: " + "'[^']*'".join(quoted))


def summarise_log(path: Path) -> tuple[int, int, dict[str, int]]:
    """(n_warnings, n_errors, most frequent warning templates); ids, quoted names and numbers -> placeholders.

    With `--aggregate-warnings` SUMO prints the first lines of a warning type and, at the end, one line
    `Warning: N total messages of type: <format>` (`%` = placeholder). N counts every message of the type,
    the printed ones included (checked against a run without aggregation), so the printed lines that match the
    format are dropped and the type is counted as N. A printed line belongs to a format only if the whole line
    matches it with `'%'` = one quoted name and a bare `%` = one whitespace-free token, so a format made mostly
    of placeholders cannot absorb another warning type (a value with a space would be counted twice, never
    hidden)."""
    n_err, plain, totals = 0, [], Counter()
    with Path(path).open(encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line.startswith("Warning:"):
                agg = AGGREGATED_WARNING.match(line)
                if agg:
                    totals[agg.group(2)] += int(agg.group(1))
                else:
                    plain.append(line)
            elif line.startswith("Error:"):
                n_err += 1
    formats = [_format_regex(fmt) for fmt in totals]
    templates = Counter(_warning_template(line) for line in plain if not any(p.fullmatch(line) for p in formats))
    for fmt, n in totals.items():
        templates[_warning_template("Warning: " + fmt.replace("'%'", "'*'")).replace("%", "#")] += n
    return sum(templates.values()), n_err, dict(templates.most_common(N_TOP_WARNINGS))


@contextmanager
def _console_discarded():
    """Point the process' stdout/stderr file descriptors at the null device (SUMO writes to them directly)."""
    sys.stdout.flush()
    sys.stderr.flush()
    saved = os.dup(1), os.dup(2)
    null = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(null, 1)
        os.dup2(null, 2)
        yield
    finally:
        sys.stdout.flush()
        sys.stderr.flush()
        os.dup2(saved[0], 1)
        os.dup2(saved[1], 2)
        for fd in (*saved, null):
            os.close(fd)


def _simulate(cfg: Path, end_s: float, backend_name: str, use_gui: bool, controller_factory, inputs: RunInputs) -> dict:
    run_dir = cfg.parent
    if use_gui:
        import traci as backend
        cmd = [sumolib.checkBinary("sumo-gui"), "-c", str(cfg), "--log", str(run_dir / LOG_NAME), *GUI_OPTIONS]
    else:
        backend = __import__(backend_name)
        cmd = [sumolib.checkBinary("sumo"), "-c", str(cfg), "--log", str(run_dir / LOG_NAME)]
    try:
        with (nullcontext() if use_gui else _console_discarded()):
            backend.start(cmd)
            try:
                version = backend.getVersion()[1]
                # getIDList also lists the vTypeDistribution ids (SUMO answers for them too); outputs carry
                # the member vType ids, which are all here
                vtypes = {t: {"vclass": backend.vehicletype.getVehicleClass(t),
                              "length": backend.vehicletype.getLength(t),
                              "width": backend.vehicletype.getWidth(t),
                              "minGap": backend.vehicletype.getMinGap(t)} for t in backend.vehicletype.getIDList()}
                controller = controller_factory(backend, inputs, run_dir) if controller_factory else None
                backlog_max = 0
                try:
                    while backend.simulation.getTime() < end_s - 1e-9:
                        backend.simulationStep()
                        if controller is not None:
                            controller.on_step(backend.simulation.getTime())
                        backlog_max = max(backlog_max, len(backend.simulation.getPendingVehicles()))
                finally:
                    if controller is not None and hasattr(controller, "close"):
                        controller.close()
            finally:
                backend.close()
    except Exception as e:
        log = run_dir / LOG_NAME
        tail = log.read_text(encoding="utf-8", errors="replace")[-2000:] if log.is_file() else "(no log)"
        raise RuntimeError(f"SUMO run in {run_dir} failed: {e}\n--- end of {log.name} ---\n{tail}") from e
    (run_dir / VTYPES_JSON).write_text(json.dumps(vtypes, indent=2, sort_keys=True), encoding="utf-8")
    return {"sumo_version": version, "insertion_backlog_max": backlog_max, "controller": controller}


# ---------------------------------------------------------------- public API


def run(spec_id: str, day: str, seed: int, use_gui: bool = False, site_path: Path | None = None,
        sim_end_s: float | None = None, *, runs_root: Path | None = None, inputs: RunInputs | None = None,
        controller_factory: Callable | None = None, ssm_mode: str | None = None) -> RunResult:
    """Simulate `spec_id` on `day` with `seed`; write outputs, manifest and observed-schema tables. Without
    `sim_end_s` the run ends at `experiment.yaml sim.calib_end_s` (ruling R31).
    `ssm_mode` (off | violators | all) overrides `experiment.yaml sim.ssm.mode`."""
    inputs = inputs or resolve_inputs(spec_id, day, site_path)
    exp = copy.deepcopy(load_experiment())
    # ruling R31: without an explicit end the run stops at sim.calib_end_s (07:30-08:00)
    exp["sim"]["end_s"] = sim_end_s if sim_end_s is not None else exp["sim"]["calib_end_s"]
    if ssm_mode is not None:
        exp["sim"]["ssm"]["mode"] = ssm_mode
    backend_name = "traci" if use_gui else exp["backend"]
    if backend_name not in BACKENDS:
        raise ValueError(f"experiment.yaml backend must be one of {BACKENDS}, got {backend_name!r}")
    run_id = f"{spec_id}__{day}"
    run_dir = Path(runs_root or RUNS_DIR) / run_id / f"seed_{seed:02d}"
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True)
    if inputs.traci_rules is not None and controller_factory is None:
        controller_factory = partial(make_controller, seed=int(seed), radius_m=float(exp["sim"]["fcd_radius_m"]))

    t0 = time.perf_counter()
    cfg = write_sumocfg(run_dir, inputs.net, inputs.routes, [inputs.vtypes], seed, exp)
    sim = _simulate(cfg, float(exp["sim"]["end_s"]), backend_name, use_gui, controller_factory, inputs)
    wall = time.perf_counter() - t0

    stats = read_statistics(run_dir / OUTPUT_FILES["statistic-output"])
    collisions = read_collisions(run_dir / OUTPUT_FILES["collision-output"])
    n_coll_file = len(collisions)
    n_teleports = int(stats["teleports"]["total"])
    # collision.action teleport (default) moves the follower: those teleports are in `total` but in none of
    # jam / yield / wrongLane (checked in a run: 2 collisions, total 2, the three categories 0)
    n_tp_noncoll = int(sum(stats["teleports"][k] for k in ("jam", "yield", "wrongLane")))
    n_collisions = max(int(stats["safety"]["collisions"]), n_coll_file)
    n_coll_junction = sum(map(is_junction_collision, collisions))
    reasons = ([f"{n_teleports} teleports"] if n_teleports else []) + \
              ([f"{n_collisions} collisions"] if n_collisions else [])
    n_warn, n_err, top_warn = summarise_log(run_dir / LOG_NAME)
    spec_hash, spec_files = _dir_hash(inputs.spec_dir)
    spec_json = SPECS_DIR / f"{spec_id}.json"
    git_hash, git_dirty = _git()
    opts = {el.tag: el.get("value") for sec in etree.parse(str(cfg)).getroot() for el in sec
            if isinstance(el.tag, str)}
    # violators mode: the id list stays in run.sumocfg; the manifest keeps its length
    explicit = opts.get("device.ssm.explicit")
    n_explicit = len(explicit.replace(",", " ").split()) if explicit else 0
    if explicit:
        opts["device.ssm.explicit"] = f"{n_explicit} vehicle ids (list in {cfg.name})"
    manifest = {
        "run_id": run_id, "spec_id": spec_id, "day": day, "seed": int(seed),
        "git_hash": git_hash, "git_dirty": git_dirty,
        "sumo_version": sim["sumo_version"], "backend": backend_name, "gui": bool(use_gui),
        "spec_dir": _rel(inputs.spec_dir), "spec_hash": spec_hash, "spec_files": spec_files,
        "spec_json_hash": _sha256(spec_json) if spec_json.is_file() else None,
        "net": _rel(inputs.net), "net_hash": _sha256(inputs.net),
        "routes": _rel(inputs.routes), "routes_hash": _sha256(inputs.routes),
        "site_path": _rel(inputs.site.path), "site_hash": _sha256(inputs.site.path),
        "site_source": inputs.site.source,
        "config": exp, "sumo_options": opts, "ssm_n_explicit": n_explicit,
        "wall_time_s": round(wall, 2),
        "n_teleports": n_teleports, "n_teleports_noncollision": n_tp_noncoll, "teleports": stats["teleports"],
        "n_collisions": n_collisions, "collisions": {"statistics": int(stats["safety"]["collisions"]),
                                                     "collision_output_records": n_coll_file},
        "collisions_by_class": collision_classes(collisions),
        "n_collisions_lane": n_collisions - n_coll_junction, "n_collisions_junction": n_coll_junction,
        "n_collisions_intervened": count_intervened(collisions, sim["controller"]),
        "interventions": (sim["controller"].summary() if hasattr(sim["controller"], "summary") else None),
        "interventions_log": INTERVENTIONS_LOG if (run_dir / INTERVENTIONS_LOG).is_file() else None,
        "controller_wall_s": (round(sim["controller"].wall_s, 2) if hasattr(sim["controller"], "wall_s") else None),
        "safety": stats["safety"],
        "insertion_backlog": int(stats["vehicles"]["waiting"]),
        "insertion_backlog_max": sim["insertion_backlog_max"],
        "vehicles": stats["vehicles"],
        "n_warnings": n_warn, "n_errors": n_err, "warnings_top": top_warn,
        # valid_strict: no teleport and no collision at all; `valid` is kept as its alias. Eligibility for
        # spec selection under looser thresholds: is_eligible(manifest, exp)
        "valid_strict": not reasons, "valid": not reasons, "invalid_reasons": reasons,
    }
    _write_manifest(run_dir, manifest)
    tables = to_observed_schema(run_dir)
    manifest["observed_schema"] = {name: len(df) for name, df in tables.items()}
    _write_manifest(run_dir, manifest)
    return RunResult(run_dir, manifest)


def _write_manifest(run_dir: Path, manifest: dict) -> None:
    (run_dir / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def _run_job(spec_id: str, day: str, seed: int, site_path, sim_end_s, runs_root, ssm_mode) -> RunResult:
    return run(spec_id, day, seed, site_path=site_path, sim_end_s=sim_end_s, runs_root=runs_root, ssm_mode=ssm_mode)


def run_many(jobs: list[tuple[str, str, int]], n_proc: int, *, site_path: Path | None = None,
             sim_end_s: float | None = None, runs_root: Path | None = None,
             ssm_mode: str | None = None) -> list[RunResult]:
    """Run `(spec_id, day, seed)` jobs, one SUMO per worker process (spawned; one job per process)."""
    args = [(s, d, int(k), site_path, sim_end_s, runs_root, ssm_mode) for s, d, k in jobs]
    if n_proc <= 1:
        return [_run_job(*a) for a in args]
    with multiprocessing.get_context("spawn").Pool(n_proc, maxtasksperchild=1) as pool:
        return pool.starmap(_run_job, args)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m thesis_sumo.sim.runner", description=__doc__.split("\n\n")[0])
    ap.add_argument("--spec", required=True, help="spec id: rules/compiled/<spec>/")
    ap.add_argument("--day", required=True, help="demand day: scenario/demand/routes_<day>.rou.xml")
    ap.add_argument("--seeds", type=int, nargs="+", required=True)
    ap.add_argument("--site", type=Path, default=None, help="site file (default: the measured config/site.yaml)")
    ap.add_argument("--end", type=float, default=None,
                    help="sim end in s (default: experiment.yaml sim.calib_end_s, ruling R31)")
    ap.add_argument("--nproc", type=int, default=1)
    ap.add_argument("--gui", action="store_true", help="sumo-gui via traci (runs seeds one after another)")
    ap.add_argument("--ssm", choices=SSM_MODES, default=None,
                    help="SSM device: off | violators (moto_violator ids) | all (default: experiment.yaml sim.ssm.mode)")
    args = ap.parse_args(argv)
    if args.gui:
        results = [run(args.spec, args.day, s, use_gui=True, site_path=args.site, sim_end_s=args.end,
                       ssm_mode=args.ssm) for s in args.seeds]
    else:
        results = run_many([(args.spec, args.day, s) for s in args.seeds], args.nproc, site_path=args.site,
                           sim_end_s=args.end, ssm_mode=args.ssm)
    print("seed  wall_s  teleports(all/non-coll)  collisions(rear/lat/junc/other)  backlog(end/max)  "
          "valid_strict  run_dir")
    for r in results:
        m = r.manifest
        c = m["collisions_by_class"]
        print(f"{m['seed']:>4}  {m['wall_time_s']:>6.1f}  {m['n_teleports']:>12}/{m['n_teleports_noncollision']:<10}  "
              f"{m['n_collisions']:>6} ({c['rear_end']}/{c['lateral']}/{c['junction']}/{c['other']}){'':<14}  "
              f"{m['insertion_backlog']:>7}/{m['insertion_backlog_max']:<8}  {str(m['valid_strict']):>12}  "
              f"{_rel(r.run_dir)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
