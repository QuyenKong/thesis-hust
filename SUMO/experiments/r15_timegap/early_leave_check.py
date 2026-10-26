"""Ruling R15 check: does vType jmTimegapMinor on the custom1 archetype move the early-leave share of the
illegal-left box waiters on PROXY_D1 (the lever R15 chose instead of a TraCI early-leave rule)?

    .venv/Scripts/python experiments/r15_timegap/early_leave_check.py [--day PROXY_D1] [--seeds 1] [--end 1200]
        [--values 0.5] [--nproc 2] [--reanalyse]

Variants: B0 (rules/compiled/B0, jmTimegapMinor = SUMO default 1 s) and B0 with
`jmTimegapMinor=<value>` on the moto_violator vType only (sumo.dlr.de/docs/Definition_of_Vehicles,_Vehicle_Types,
_and_Routes.html#junction_model_parameters: minimum time gap when passing ahead of / after a prioritised vehicle
that has not yet entered the intersection). Each run goes through `thesis_sumo.sim.runner.run` (manifest.json,
observed-schema tables) into `experiments/runs/r15_timegap/<variant>__<day>/seed_XX/` (git-ignored).

Early-leave share (Phase 3 / targets.yaml M7 definition), from the observed-schema tables only: for each
box_queue row (opposing through green end t), entrants = illegal_l traversals of the approach with t_stopline in
(t_prev, t]; early leavers = entrants with t_exit < t; share = sum(early) / sum(early + n_waiting_in_box).
Summary -> experiments/r15_timegap/results.csv (printed too).
"""

from __future__ import annotations

import argparse
import dataclasses
import multiprocessing
import sys
from pathlib import Path

import pandas as pd
from lxml import etree

from thesis_sumo.config import REPO_ROOT
from thesis_sumo.sim.runner import resolve_inputs, run

HERE = Path(__file__).resolve().parent
RUNS = REPO_ROOT / "experiments" / "runs" / "r15_timegap"
SITE = REPO_ROOT / "config" / "site.proxy.yaml"
B0_DIR = REPO_ROOT / "rules" / "compiled" / "B0"
VIOLATOR_VTYPE = "moto_violator_B0"


def variant_dir(value: float) -> tuple[str, Path]:
    """B0 copy with jmTimegapMinor on the moto_violator vType (written under the git-ignored runs dir)."""
    name = f"R15_jmTGM{value:g}".replace(".", "p")
    d = RUNS / "specs" / name
    d.mkdir(parents=True, exist_ok=True)
    tree = etree.parse(str(B0_DIR / "vtypes.add.xml"))
    (vt,) = tree.getroot().iterfind(f".//vType[@id='{VIOLATOR_VTYPE}']")
    vt.set("jmTimegapMinor", f"{value:g}")
    tree.write(str(d / "vtypes.add.xml"), encoding="UTF-8", xml_declaration=True)
    return name, d


def _job(spec_id: str, spec_dir: str, day: str, seed: int, end_s: float) -> str:
    inputs = dataclasses.replace(resolve_inputs("B0", day, SITE), spec_id=spec_id, spec_dir=Path(spec_dir))
    return str(run(spec_id, day, seed, site_path=SITE, sim_end_s=end_s, runs_root=RUNS, inputs=inputs).run_dir)


def early_leave(run_dir: Path) -> dict:
    obs = Path(run_dir) / "observed_schema"
    box = pd.read_csv(obs / "box_queue.csv").sort_values("t")
    trav = pd.read_csv(obs / "traversals.csv")
    rows = []
    for appr, b in box.groupby("approach"):
        tr = trav[(trav["movement"] == "illegal_l") & (trav["approach"] == appr)]
        t_prev = -float("inf")
        for r in b.itertuples():
            ent = tr[(tr["t_stopline"] > t_prev) & (tr["t_stopline"] <= r.t)]
            rows.append({"entrants": len(ent), "early": int((ent["t_exit"] < r.t).sum()),
                         "waiting": int(r.n_waiting_in_box)})
            t_prev = r.t
    df = pd.DataFrame(rows)
    denom = df["early"].sum() + df["waiting"].sum()
    return {"cycles": len(df), "entrants": int(df["entrants"].sum()), "early": int(df["early"].sum()),
            "waiting_mean": round(df["waiting"].mean(), 2),
            "early_leave_share": round(df["early"].sum() / denom, 3) if denom else float("nan")}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--day", default="PROXY_D1")
    ap.add_argument("--seeds", type=int, nargs="+", default=[1])
    ap.add_argument("--end", type=float, default=1200.0, help="sim end in s (10 cycles of 120 s)")
    ap.add_argument("--values", type=float, nargs="+", default=[0.5], help="jmTimegapMinor values to test")
    ap.add_argument("--nproc", type=int, default=2)
    ap.add_argument("--reanalyse", action="store_true", help="only recompute the table from existing runs")
    args = ap.parse_args(argv)

    variants = [("B0", B0_DIR)] + [variant_dir(v) for v in args.values]
    jobs = [(name, str(d), args.day, s, args.end) for name, d in variants for s in args.seeds]
    if not args.reanalyse:
        if args.nproc <= 1:
            for j in jobs:
                _job(*j)
        else:
            with multiprocessing.get_context("spawn").Pool(args.nproc, maxtasksperchild=1) as pool:
                pool.starmap(_job, jobs)
    out = []
    for name, _, day, seed, _ in jobs:
        run_dir = RUNS / f"{name}__{day}" / f"seed_{seed:02d}"
        out.append({"variant": name, "day": day, "seed": seed, "end_s": args.end, **early_leave(run_dir)})
    res = pd.DataFrame(out)
    res.to_csv(HERE / "results.csv", index=False)
    print(res.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
