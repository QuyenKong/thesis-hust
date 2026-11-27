"""Comparison figures of 2026-11-27 (decision D34): SUMO default (B0) against the calibrated specs on the validation
day VIDEO_V1 (benchmark BENCH_v1127, seeds 1-20, net N7 with the split LVL signal plan D30).

  fig_behaviour_v1127.png  one panel per behaviour metric: bar = mean over 20 seeds (+- sd) for B0, B2, P1, P2;
                           dashed line = target of the observed day (generated from video G0 + literature targets)
  fig_spacetime_v1127.png  space-time trajectories on one LVL approach over two signal cycles (seed 1), B0 | best LLM;
                           background = the approach's signal state; red-light runners and box waiters stand out
  fig_flows_v1127.png      vehicles/h per approach x movement: video target (IMG_4801 tracking, D18, D33 owner
                           estimate marked) against the simulated stop-line counts, GEH 5 band, B0 | best LLM
  results/benchmark_v1127/counts.csv, summary.csv  metric values per run (and for the observed day)

Run from SUMO/: .venv/Scripts/python experiments/operator/n1127/figures.py [--campaign BENCH_v1127] [--suffix v1127]
                [--out-dir ../Latex_SOICT/Figure] [--recount]
"""
from __future__ import annotations

import argparse
import json
import math
import pickle
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import yaml  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "n1126"))
import compare_video as V  # noqa: E402  (compare.py constants and row_from for N7, M8 in, M10 out)

C = V.C
from thesis_sumo.config import REPO_ROOT, load_experiment, load_site  # noqa: E402
from thesis_sumo.metrics.common import MetricContext, read_tables  # noqa: E402
from thesis_sumo.sim.outputs import _annotate, _vtype_info, junction_geometry, scan_fcd  # noqa: E402

CAMP_DIR = REPO_ROOT / "experiments" / "campaigns"
DAY = "VIDEO_V1"
SEEDS = list(range(1, 21))
# label -> spec file stem (spec_id in the benchmark = <stem>__bench); filled per campaign suffix in main()
LABELS = {"B0": "B0", "B2": "B2_{s}_best", "P1": "P1_{s}_best", "P2": "P2_{s}_best"}
# Okabe-Ito (colour-blind safe), one colour per source; the target is a black dashed line
COL = {"B0": "#999999", "B2": "#E69F00", "P1": "#56B4E9", "P2": "#009E73", "target": "#000000"}
LONG = {"B0": "B0: SUMO mặc định (trước hiệu chỉnh)", "B2": "B2: Optuna", "P1": "P1: LLM, chỉ tham số", "P2": "P2: LLM, tham số và luật"}
METRICS = [  # (counts.csv column, panel title, unit scale)
    ("red_share_moto", "Xe máy vượt đèn đỏ (%)", 100),
    ("early_share_moto", "Xe máy xuất phát sớm (%)", 100),
    ("overshoot_share_moto", "Xe máy dừng quá vạch (%)", 100),
    ("box_waiting_per_cycle", "Xe rẽ trái cấm chờ giữa nút\n(xe/chu kỳ)", 1),
    ("wrong_lane_share_moto", "Xe máy đi sai làn (%)", 100),
    ("right_lane_block_per_cycle", "Xe chờ đỏ trên làn rẽ phải\n(xe/chu kỳ)", 1),
]
RUN_METRICS = [("lane_collisions_per_hour", "Va chạm trên làn (vụ/h)"), ("end_backlog", "Xe chờ vào mạng cuối lượt (xe)")]
MOVE_VI = {"s": "thẳng", "r": "phải", "l": "trái", "u": "quay đầu", "illegal_l": "trái cấm"}


def run_dir(campaign: str, spec: str, seed: int) -> Path:
    return CAMP_DIR / campaign / "runs" / f"{spec}__bench__{DAY}" / f"seed_{seed:02d}"


def counts(campaign: str, specs: dict, ctx: MetricContext, out: Path, recount: bool) -> pd.DataFrame:
    path = out / "counts.csv"
    if path.is_file() and not recount:
        return pd.read_csv(path)
    rows = [{"source": "target", "seed": None, **V.row_from(read_tables(C.OBSERVED / DAY), ctx)}]
    for label, stem in specs.items():
        for seed in SEEDS:
            d = run_dir(campaign, stem, seed)
            if (d / "observed_schema").is_dir():
                rows.append({"source": label, "seed": seed, **V.row_from(read_tables(d), ctx)})
    df = pd.DataFrame(rows)
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    cols = [c for c in df.columns if c not in ("source", "seed")]
    df.groupby("source")[cols].agg(["mean", "std", "count"]).to_csv(out / "summary.csv")
    return df


def run_rows(campaign: str, specs: dict) -> pd.DataFrame:
    """Per-run collision rate and end backlog from the benchmark pickles (EvalResult.runs)."""
    rows = []
    for label, stem in specs.items():
        pkl = CAMP_DIR / campaign / f"{stem}.pkl"
        if not pkl.is_file():
            continue
        res = pickle.loads(pkl.read_bytes())
        for r in res.runs:
            man = Path(r["run_dir"]) / "manifest.json"
            backlog = json.loads(man.read_text(encoding="utf-8")).get("insertion_backlog") if man.is_file() else None
            rows.append({"source": label, "seed": r["seed"], "lane_collisions_per_hour": r["lane_collisions_per_hour"],
                         "end_backlog": np.nan if backlog is None else backlog})
    return pd.DataFrame(rows)


def fig_behaviour(df: pd.DataFrame, runs: pd.DataFrame, labels: list[str], path: Path) -> None:
    panels = METRICS + RUN_METRICS
    ncol = 4
    fig, axes = plt.subplots(math.ceil(len(panels) / ncol), ncol, figsize=(10, 5.2), layout="constrained")
    for ax, (col, title, *scale) in zip(axes.flat, panels):
        k = scale[0] if scale else 1
        src = runs if col in dict(RUN_METRICS) else df
        means = [src.loc[src.source == lb, col].mean() * k for lb in labels]
        sds = [src.loc[src.source == lb, col].std() * k for lb in labels]
        x = np.arange(len(labels))
        ax.bar(x, means, yerr=sds, color=[COL[lb] for lb in labels], capsize=2, edgecolor="black", linewidth=0.4)
        if col in df.columns and not df.loc[df.source == "target", col].isna().all():
            tv = df.loc[df.source == "target", col].mean() * k
            ax.axhline(tv, color=COL["target"], ls="--", lw=1)
        ax.set_xticks(x, labels, fontsize=8)
        ax.set_title(title, fontsize=8.5)
        ax.tick_params(axis="y", labelsize=7)
        ax.set_ylim(bottom=0)
    for ax in axes.flat[len(panels):]:
        ax.set_axis_off()
    handles = [plt.Rectangle((0, 0), 1, 1, color=COL[lb]) for lb in labels]
    handles.append(plt.Line2D([], [], color="black", ls="--"))
    fig.legend(handles, [LONG[lb] for lb in labels] + ["Ngày quan sát VIDEO_V1 (dữ liệu sinh)"], loc="outside lower center",
               ncol=len(labels) + 1, fontsize=8, frameon=False)
    fig.savefig(path, dpi=200)
    plt.close(fig)


def spacetime_rows(d: Path, approach: str, t0: float, t1: float) -> pd.DataFrame:

    cfg = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
    net = Path(cfg.get("net") or REPO_ROOT / "scenario" / "net" / "site.net.xml")
    if not net.is_file():
        net = REPO_ROOT / "scenario" / "net" / "site.net.xml"
    geo = junction_geometry(net)
    times = {round(t, 1) for t in np.arange(t0, t1, 0.5)}
    scan = scan_fcd(d / "fcd.xml.gz", geo, times, 1e9)
    fr = _annotate(scan.frames, geo, _vtype_info(d))
    return fr[fr.approach == approach]


def fig_spacetime(campaign: str, specs: dict, pair: list[str], approach: str, seed: int, t0: float, t1: float,
                  path: Path) -> None:
    fig, axes = plt.subplots(1, len(pair), figsize=(10, 4.2), sharey=True, layout="constrained")
    for ax, lb in zip(np.atleast_1d(axes), pair):
        d = run_dir(campaign, specs[lb], seed)
        ev = pd.read_csv(d / "observed_schema" / "signal_events.csv")
        ev = ev[ev.approach_group == approach].sort_values("t")
        tt = list(ev.t) + [t1]
        for (a, b, s) in zip(tt[:-1], tt[1:], ev.state):
            a, b = max(a, t0), min(b, t1)
            if b > a:
                ax.axvspan(a, b, color={"G": "#009E73", "y": "#F0E442", "r": "#D55E00"}.get(s, "#cccccc"),
                           alpha=0.12, lw=0)
        fr = spacetime_rows(d, approach, t0, t1)
        fr = fr[(fr.dist_m <= 80) & (fr.dist_m >= -40)]
        for vid, g in fr.groupby("track_id"):
            viol = "violator" in str(g.type.iloc[0])
            col = "#D55E00" if viol else ("#0072B2" if g.vclass.iloc[0] == "moto" else "#555555")
            ax.plot(g.t, g.dist_m, color=col, lw=0.5 if not viol else 0.9, alpha=0.6)
        ax.axhline(0, color="black", lw=0.8)
        ax.set_title(LONG[lb], fontsize=9)
        ax.set_xlabel("Thời gian mô phỏng (s)", fontsize=8)
        ax.set_xlim(t0, t1)
        ax.tick_params(labelsize=7)
    np.atleast_1d(axes)[0].set_ylabel(f"Khoảng cách tới vạch dừng nhánh {approach} (m)\n(âm: đã qua vạch, trong nút)",
                                      fontsize=8)
    np.atleast_1d(axes)[0].invert_yaxis()
    h = [plt.Line2D([], [], color=c, lw=1.2) for c in ("#0072B2", "#555555", "#D55E00")]
    h += [plt.Rectangle((0, 0), 1, 1, color=c, alpha=0.25) for c in ("#009E73", "#D55E00")]
    fig.legend(h, ["Xe máy", "Ô tô", "Xe máy lớp vi phạm", "Đèn xanh", "Đèn đỏ"], loc="outside lower center",
               ncol=5, fontsize=8, frameon=False)
    fig.savefig(path, dpi=200)
    plt.close(fig)


def target_flows() -> pd.DataFrame:
    t = yaml.safe_load((REPO_ROOT / "data" / "video_targets" / "targets_video.yaml").read_text(encoding="utf-8"))
    g = t["targets"]["G0_counts"]
    vol, split = g["approach_volume_veh_h"]["value"], g["movement_split"]["value"]
    rows = [{"approach": a, "movement": m, "target": vol[a] * s, "owner_estimate": (a, m) in {("LVL_W", "s"), ("HMG", "s")}}
            for a in vol for m, s in split[a].items()]
    return pd.DataFrame(rows)


def sim_flows(campaign: str, stem: str) -> pd.DataFrame:
    parts = []
    for seed in SEEDS:
        f = run_dir(campaign, stem, seed) / "observed_schema" / "turn_counts.csv"
        if f.is_file():
            tc = pd.read_csv(f)
            w = tc.interval_end.max() - tc.interval_start.min()
            parts.append(tc.groupby(["approach", "movement"])["count"].sum() * 3600.0 / w)
    return pd.concat(parts, axis=1).mean(axis=1).rename("sim").reset_index()


def geh(m, c):
    return np.sqrt(2 * (m - c) ** 2 / (m + c)) if (m + c) > 0 else 0.0


def fig_flows(campaign: str, specs: dict, pair: list[str], path: Path) -> None:
    tg = target_flows()
    fig, axes = plt.subplots(1, len(pair), figsize=(10, 4.6), sharey=True, layout="constrained")
    lim = 1.1 * tg.target.max()
    xs = np.linspace(1, lim, 200)
    for ax, lb in zip(np.atleast_1d(axes), pair):
        df = tg.merge(sim_flows(campaign, specs[lb]), on=["approach", "movement"], how="left").fillna({"sim": 0})
        # GEH = 5 band: |m - c| = 5 sqrt((m + c) / 2) solved for m given c
        lo = [max(0.0, c - 5 * math.sqrt(c)) for c in xs]
        hi = [c + 5 * math.sqrt(c) for c in xs]
        ax.fill_between(xs, lo, hi, color="#cccccc", alpha=0.5, lw=0, label="GEH < 5 (xấp xỉ)")
        ax.plot([0, lim], [0, lim], color="black", lw=0.6)
        for _, r in df.iterrows():
            ok = geh(r.sim, r.target) < 5
            ax.scatter(r.target, r.sim, marker="s" if r.owner_estimate else "o", s=26,
                       color=COL[lb], edgecolor="black" if ok else "#D55E00", linewidth=0.5 if ok else 1.4, zorder=3)
            if r.target > 600 or r.owner_estimate:
                ax.annotate(f"{r.approach} {MOVE_VI.get(r.movement, r.movement)}", (r.target, r.sim), fontsize=6.5,
                            xytext=(3, -8), textcoords="offset points")
        n_ok = sum(geh(s, t) < 5 for s, t in zip(df.sim, df.target))
        ax.set_title(f"{LONG[lb]} ({n_ok}/{len(df)} hướng có GEH < 5)", fontsize=9)
        ax.set_xlabel("Lưu lượng mục tiêu từ video (xe/h)", fontsize=8)
        ax.set_xlim(0, lim)
        ax.set_ylim(0, lim)
        ax.tick_params(labelsize=7)
    np.atleast_1d(axes)[0].set_ylabel("Lưu lượng qua vạch dừng trong mô phỏng (xe/h, trung bình 20 seed)", fontsize=8)
    h = [plt.Line2D([], [], marker="o", ls="", color="#777777", markeredgecolor="black"),
         plt.Line2D([], [], marker="s", ls="", color="#777777", markeredgecolor="black"),
         plt.Line2D([], [], marker="o", ls="", color="white", markeredgecolor="#D55E00", markeredgewidth=1.4),
         plt.Rectangle((0, 0), 1, 1, color="#cccccc")]
    fig.legend(h, ["Đếm theo vết (IMG_4801)", "Ước lượng (không phải số đo)", "GEH ≥ 5", "Dải GEH < 5"],
               loc="outside lower center", ncol=4, fontsize=8, frameon=False)
    fig.savefig(path, dpi=200)
    plt.close(fig)


def best_llm(campaign: str, specs: dict) -> str:
    """LLM label with the lowest benchmark S among P1 / P2 (fallback P1)."""
    best, s_best = "P1", math.inf
    for lb in ("P1", "P2"):
        pkl = CAMP_DIR / campaign / f"{specs.get(lb, '')}.pkl"
        if lb in specs and pkl.is_file():
            s = pickle.loads(pkl.read_bytes()).to_row().get("S", math.inf)
            if s < s_best:
                best, s_best = lb, s
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign", default="BENCH_v1127")
    ap.add_argument("--suffix", default="v1127")
    ap.add_argument("--out-dir", type=Path, default=REPO_ROOT.parent / "Latex_SOICT" / "Figure")
    ap.add_argument("--approach", default="LVL_E")
    ap.add_argument("--t0", type=float, default=640.0)
    ap.add_argument("--recount", action="store_true")
    ap.add_argument("--rs", default=None, help="second panel label (B2|P1|P2); default: best LLM by benchmark S")
    ap.add_argument("--tag", default="", help="extra file-name tag, e.g. _llm")
    a = ap.parse_args()
    specs = {lb: stem.format(s=a.suffix) for lb, stem in LABELS.items()}
    specs = {lb: st for lb, st in specs.items() if (CAMP_DIR / a.campaign / "runs" / f"{st}__bench__{DAY}").is_dir()}
    labels = [lb for lb in LABELS if lb in specs]
    print("specs", specs, flush=True)
    ctx = MetricContext.from_config(load_experiment(), site=load_site(REPO_ROOT / "config" / "site.yaml"))
    out_res = REPO_ROOT / "results" / f"benchmark_{a.suffix}"
    df = counts(a.campaign, specs, ctx, out_res, a.recount)
    runs = run_rows(a.campaign, specs)
    a.out_dir.mkdir(parents=True, exist_ok=True)
    fig_behaviour(df, runs, labels, a.out_dir / f"fig_behaviour_{a.suffix}.png")
    second = a.rs or best_llm(a.campaign, specs)
    pair = ["B0", second]
    fig_spacetime(a.campaign, specs, pair, a.approach, 1, a.t0, a.t0 + 320.0,
                  a.out_dir / f"fig_spacetime{a.tag}_{a.suffix}.png")
    fig_flows(a.campaign, specs, pair, a.out_dir / f"fig_flows{a.tag}_{a.suffix}.png")
    print("wrote figures to", a.out_dir, "pair", pair, flush=True)


if __name__ == "__main__":
    main()
