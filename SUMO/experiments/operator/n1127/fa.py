"""Figure F-A of 2026-11-27 (decision D37): a pair of sumo-gui stills at the same simulation second, same seed, view
and zoom (B0 left, final rule set "RS" right), plus a JSON with every behaviour instance visible in the RS still
(vehicle id, behaviour number of the Ch5 behaviour table, pixel x, y), for TikZ circles placed in LaTeX.

1. pick: scan the RS benchmark run (VIDEO_V1, --seed) for the second with the most distinct behaviours at once,
   from its own outputs: red runners (M3 classification, last 3 s) = 1, >= 2 of them on one approach
   in the last 3 s = 2, early starts (M2 classification, last 3 s) = 3, wrong-lane cut-backs in progress
   (queue_space_seeking wrong_lane, executed, t <= now <= t_end) = 5, illegal-left waiters standing in the box = 10,
   U-turn bypasses in progress = 12 (uturn_bypass). Ties: more instances, then closer to the end of an LVL red phase.
2. record: report/2026-11-27/scripts/record_video.py for B0 and RS from 0 to t + 0.3 s, frames from t - 0.2 s every
   step, view --angle -45, --calib (pixel mapping, view_transform.py) and --dump-veh.
3. json: instances at the frame of time t in the RS recording (its own run outputs), mapped to pixels; behaviours with
   no instance are listed as absent, with the reason "p = 0 in the spec" when profile.zero_flags says so.

Run from SUMO/: .venv/Scripts/python experiments/operator/n1127/fa.py --rs-stem P2_v1127_best [--seed 1]
                [--campaign BENCH_v1127] [--t <force a time>] [--out-dir ../Latex_SOICT/Figure]
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from thesis_sumo.config import REPO_ROOT, load_experiment, load_site
from thesis_sumo.metrics.common import MetricContext
from thesis_sumo.metrics.m2_early_start import classified
from thesis_sumo.metrics.common import read_tables
from thesis_sumo.sim.outputs import junction_geometry, scan_fcd

import importlib.util  # noqa: E402  (profile.py would clash with the stdlib module name on a plain import)
_spec = importlib.util.spec_from_file_location("behaviour_profile", Path(__file__).resolve().parent / "profile.py")
_bp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bp)
zero_flags = _bp.zero_flags

THESIS = REPO_ROOT.parent
SCRIPTS = THESIS / "report" / "2026-11-27" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import view_transform as VT  # noqa: E402

CAMP_DIR = REPO_ROOT / "experiments" / "campaigns"
DAY = "VIDEO_V1"
NAMES = {1: "vượt đèn đỏ", 2: "vượt đèn đỏ theo đoàn", 3: "xuất phát sớm", 4: "dừng quá vạch", 5: "đi sai làn rồi cắt về",
         6: "chặn làn rẽ phải", 7: "đi trên vỉa hè", 10: "rẽ trái trái phép chờ giữa nút", 12: "lách xe quay đầu"}
ZERO_TO_NUM = {"vượt đèn đỏ (M3)": [1, 2], "xuất phát sớm (M2)": [3], "đi sai làn (M8)": [5],
               "chờ trên làn rẽ phải (M9)": [], "đi trên vỉa hè (M10)": [7], "lách xe quay đầu": [12]}
WIN = 3.0


def classified_ids(tables: dict, ctx) -> "pd.DataFrame":
    """m2_early_start.classified (M2/M3 kinds) with the vehicle id, joined back from stopline_crossings on
    (approach, vclass, t): classified keeps the crossing times as they are, so the join is exact."""
    c = classified(tables, ctx)
    cr = tables["stopline_crossings"][["approach", "vclass", "t", "track_id"]]
    return c.merge(cr, on=["approach", "vclass", "t"], how="left")


def events(run: Path) -> dict[int, pd.DataFrame]:
    """Behaviour events of a run: number -> DataFrame(t_start, t_end, veh)."""
    t = read_tables(run)
    ctx = MetricContext.from_config(load_experiment(), site=load_site(REPO_ROOT / "config" / "site.yaml"))
    c = classified_ids(t, ctx)  # M2/M3 classification of stop-line crossings (red runner / early start)
    red = c[c["kind"] == "red"]
    early = c[c["kind"] == "early"]
    out = {1: pd.DataFrame({"t_start": red["t"], "t_end": red["t"] + WIN, "veh": red["track_id"],
                            "approach": red["approach"]}),
           3: pd.DataFrame({"t_start": early["t"], "t_end": early["t"] + WIN, "veh": early["track_id"]})}
    iv = pd.read_csv(run / "interventions.csv") if (run / "interventions.csv").is_file() else pd.DataFrame(
        columns=["t", "veh_id", "rule", "action", "executed", "t_end"])
    iv = iv[iv["executed"].astype(str) == "True"]
    sel = {5: (iv["rule"] == "queue_space_seeking") & (iv["action"] == "wrong_lane"),
           12: iv["rule"] == "uturn_bypass"}
    for k, m in sel.items():
        e = iv[m]
        t_end = pd.to_numeric(e["t_end"], errors="coerce").fillna(e["t"])
        if k == 3:
            t_end = e["t"] + WIN
        out[k] = pd.DataFrame({"t_start": e["t"], "t_end": t_end, "veh": e["veh_id"]})
    geo = junction_geometry(REPO_ROOT / "scenario" / "net" / "site.net.xml")
    box = scan_fcd(run / "fcd.xml.gz", geo, set(), 80.0).box_rows
    box = box[box["speed"] < 0.5]
    out[10] = pd.DataFrame({"t_start": box["t"], "t_end": box["t"], "veh": box["track_id"]})
    return out


def active(ev: dict, t: float) -> dict[int, list[str]]:
    act = {}
    for k, e in ev.items():
        if k == 10:
            v = e.loc[np.isclose(e["t_start"], round(t, 1)), "veh"].tolist()
        else:
            v = e.loc[(e["t_start"] <= t) & (e["t_end"] >= t), "veh"].tolist()
        if v:
            act[k] = sorted(set(v))
    reds = ev[1][(ev[1]["t_start"] <= t) & (ev[1]["t_end"] >= t)]
    if len(reds) and reds.groupby("approach").size().max() >= 2:
        act[2] = sorted(set(reds["veh"]))
    return act


def lvl_red_end(run: Path) -> np.ndarray:
    sig = read_tables(run)["signal_events"]
    g = sig[sig["approach_group"].isin(["LVL_E", "LVL_W"]) & (sig["state"].str.upper() == "G")]
    return g["t"].to_numpy()


def pick(run: Path, t0: float = 480.0, t1: float = 2000.0) -> tuple[float, dict]:
    ev = events(run)
    onsets = lvl_red_end(run)
    best = None
    for t in np.arange(t0, t1, 1.0):
        act = active(ev, t)
        n_types, n_inst = len(act), sum(len(v) for v in act.values())
        dt = onsets[onsets >= t] - t
        near = 1 if len(dt) and dt.min() <= 10 else 0
        key = (n_types, n_inst, near)
        if best is None or key > best[0]:
            best = (key, float(t), act)
    return best[1], best[2]


def record(spec_json: Path, t: float, seed: int, out: Path) -> None:
    if out.exists():
        shutil.rmtree(out)
    cmd = [sys.executable, str(SCRIPTS / "record_video.py"), "--spec-json", str(spec_json), "--day", DAY,
           "--seed", str(seed), "--begin", f"{t - 0.2:.1f}", "--end", f"{t + 0.35:.2f}", "--every", "1",
           "--angle", "-45", "--calib", "--dump-veh", "--site", str(REPO_ROOT / "config" / "site.yaml"),
           "--out", str(out)]
    subprocess.run(cmd, check=True, cwd=THESIS)


def frame_at(rec: Path, t: float) -> tuple[int, dict]:
    meta = json.loads((rec / "frames" / "frames.json").read_text(encoding="utf-8"))
    i = min(range(1, len(meta)), key=lambda k: abs(meta[k]["t"] - t))  # frame 0 carries the markers
    return i, meta[i]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign", default="BENCH_v1127")
    ap.add_argument("--rs-stem", required=True)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--t", type=float, default=None)
    ap.add_argument("--suffix", default="v1127")
    ap.add_argument("--out-dir", type=Path, default=THESIS / "Latex_SOICT" / "Figure")
    ap.add_argument("--rec-root", type=Path, default=THESIS / "report" / "2026-11-27")
    a = ap.parse_args()
    bench_run = CAMP_DIR / a.campaign / "runs" / f"{a.rs_stem}__bench__{DAY}" / f"seed_{a.seed:02d}"
    if a.t is None:
        t, act = pick(bench_run)
        print("picked t =", t, {k: len(v) for k, v in act.items()}, flush=True)
    else:
        t = a.t
    recs = {}
    for tag, stem in (("A_B0", "B0"), ("B_RS", a.rs_stem)):
        recs[tag] = a.rec_root / f"_fa_{tag}_{a.suffix}"
        record(REPO_ROOT / "rules" / "specs" / f"{stem}.json", t, a.seed, recs[tag])
    a.out_dir.mkdir(parents=True, exist_ok=True)
    stills = {}
    for tag, rec in recs.items():
        try:
            VT.fit(rec)
        except SystemExit as exc:  # markers not drawn: same view as the reference calibration
            print("calibration markers not found:", exc, "- using the reference transform", flush=True)
            shutil.copyfile(SCRIPTS / "view_transform_angle-45_1600x900_hw100.json", rec / "view_transform.json")
        i, m = frame_at(rec, t)
        dst = a.out_dir / f"fig_FA_{tag}_{a.suffix}.png"
        shutil.copyfile(rec / "frames" / f"f{i:06d}.png", dst)
        stills[tag] = (dst, i, m)
    # instances in the RS still, from the RS recording's own outputs
    rec = recs["B_RS"]
    run = next((rec / "run").glob("*__VIDEO_V1")) / f"seed_{a.seed:02d}"
    tr = json.loads((rec / "view_transform.json").read_text(encoding="utf-8"))
    _, i, m = stills["B_RS"]
    t_frame = m["t"]
    act = active(events(run), t_frame)
    pos = {v["id"]: v for v in m["veh"]}
    inst = []
    for k, vehs in sorted(act.items()):
        for v in vehs:
            if v in pos:
                px, py = VT.to_px(tr, pos[v]["x"], pos[v]["y"])
                if 0 <= px < 1600 and 0 <= py < 900:
                    inst.append({"veh": v, "behaviour": k, "name": NAMES.get(k, str(k)), "px": round(px, 1),
                                 "py": round(py, 1)})
    for b in m.get("blockers", []):  # recorder classification: straight vehicle standing in the right-turn lane
        px, py = VT.to_px(tr, b["x"], b["y"])  # (the recorder's own "px" ignores the view rotation)
        if 0 <= px < 1600 and 0 <= py < 900:
            inst.append({"veh": None, "behaviour": 6, "name": NAMES[6], "px": round(px, 1), "py": round(py, 1),
                         "queue_behind": b["behind"]})
    spec = json.loads((REPO_ROOT / "rules" / "specs" / f"{a.rs_stem}.json").read_text(encoding="utf-8"))
    zero = {n for z in zero_flags(spec) for n in ZERO_TO_NUM.get(z, [])}
    present = {x["behaviour"] for x in inst}
    absent = [{"behaviour": k, "name": n, "reason": "p = 0 hoặc không có luật trong đặc tả" if k in zero
               else "không xuất hiện tại thời điểm này"} for k, n in NAMES.items() if k not in present]
    info = {"t": t_frame, "seed": a.seed, "day": DAY, "spec": a.rs_stem, "view": {"angle_deg": -45, "size": [1600, 900],
            "px_per_m": tr["scale_px_per_m"]}, "png_B0": stills["A_B0"][0].name, "png_RS": stills["B_RS"][0].name,
            "instances": inst, "absent": absent,
            "note": "px, py = vehicle front position (SUMO getPosition) one step before the rendered frame"}
    out = a.out_dir / f"fig_FA_instances_{a.suffix}.json"
    out.write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote", out, len(inst), "instances", flush=True)


if __name__ == "__main__":
    main()
