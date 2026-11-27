"""Behaviour profile of the rule set on the validation day (VIDEO_V1, benchmark seeds 1-20), request of 27/11:
the conclusion is about the rule set as a whole. Columns: observed day (target), B0 (SUMO default, before
calibration), and every calibrated spec of the benchmark (B2, P1, P2); rows grouped by behaviour group, then S and the
stability rows. Also lists every behaviour the final spec cannot produce (no rule, a zero probability, or rules only on
archetypes with zero share), so the conclusion claims only what the rule set produces.

  results/benchmark_<suffix>/profile.csv     row, group, source, mean, sd, n
  results/benchmark_<suffix>/profile.md      the table (mean (sd)) + the zero-probability flags per spec

Run from SUMO/: .venv/Scripts/python experiments/operator/n1127/profile.py [--campaign BENCH_v1127] [--suffix v1127]
"""
from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

from thesis_sumo.config import REPO_ROOT, load_experiment, load_site
from thesis_sumo.metrics.common import MetricContext, read_tables
from thesis_sumo.metrics.distance import MODULES

CAMP_DIR = REPO_ROOT / "experiments" / "campaigns"
DAY = "VIDEO_V1"
SEEDS = list(range(1, 21))
LABELS = {"B0": "B0", "B1": "B1_manual", "B2": "B2_{s}_best", "P1": "P1_{s}_best", "P2": "P2_{s}_best", "P2b": "P2b_{s}_best"}
# (group, row label, metric key, scale)
BEHAVIOUR_ROWS = [
    ("Nhóm 1: vi phạm đèn", "M3 xe máy vượt đèn đỏ (%)", "M3/share/moto", 100),
    ("Nhóm 1: vi phạm đèn", "M3 ô tô vượt đèn đỏ (%)", "M3/share/car", 100),
    ("Nhóm 1: vi phạm đèn", "M3 lượt vượt đỏ mỗi chu kỳ mỗi nhánh", "M3/per_cycle", 1),
    ("Nhóm 1: vi phạm đèn", "M3 tỷ số phương sai/trung bình", "M3/var_to_mean", 1),
    ("Nhóm 1: vi phạm đèn", "M2 xe máy xuất phát sớm (%)", "M2/early/moto", 100),
    ("Nhóm 1: vi phạm đèn", "M2 ô tô xuất phát sớm (%)", "M2/early/car", 100),
    ("Nhóm 1: vi phạm đèn", "M4 xe máy dừng quá vạch (%)", "M4/overshoot_share", 100),
    ("Nhóm 2: tìm khoảng trống", "M8 xe máy đi sai làn (%)", "M8/moto", 100),
    ("Nhóm 2: tìm khoảng trống", "M8 ô tô đi sai làn (%)", "M8/car", 100),
    ("Nhóm 2: tìm khoảng trống", "M9a xe chờ đỏ trên làn rẽ phải (xe/chu kỳ)", "M9a/per_cycle", 1),
    ("Nhóm 3: rẽ trái cấm", "M7a xe chờ giữa nút (xe/chu kỳ)", "M7a/n_waiting", 1),
    ("Nhóm 3: rẽ trái cấm", "M7b độ trễ giải phóng vùng chờ (s)", "M7b/clear_lag", 1),
]
STABILITY_ROWS = [("Độ ổn định", "Va chạm/h", "collisions_per_hour"),
                  ("Độ ổn định", "Va chạm trên làn/h", "lane_collisions_per_hour"),
                  ("Độ ổn định", "Teleport kẹt/h", "jam_yield_teleports_per_hour"),
                  ("Độ ổn định", "Xe chờ vào mạng cuối lượt", "backlog"),
                  ("Độ ổn định", "Qua cổng G0 (số lần chạy)", "g0_pass")]
# behaviour -> (rule types that produce it, probability params of those rules that must be > 0)
PRODUCERS = {
    "vượt đèn đỏ (M3)": (("swarm_red_running", "red_running"), ("p", "p0", "p_max")),
    "xuất phát sớm (M2)": (("early_start",), ("p",)),
    "đi sai làn (M8)": (("queue_space_seeking",), ("p_wrong_lane",)),
    "chờ trên làn rẽ phải (M9)": (("queue_space_seeking",), ("p_right_lane",)),
    "đi trên vỉa hè (M10)": (("queue_space_seeking",), ("p_sidewalk",)),
    "lách xe quay đầu": (("uturn_bypass",), ("p",)),
}


def run_dir(campaign: str, stem: str, seed: int) -> Path:
    return CAMP_DIR / campaign / "runs" / f"{stem}__bench__{DAY}" / f"seed_{seed:02d}"


def metric_values(tables: dict, ctx: MetricContext) -> dict:
    vals = {}
    for mod in MODULES:
        vals.update(mod.compute(tables, ctx))
    return {key: float(vals[key].mean()) if key in vals else np.nan
            for _, _, key, _ in BEHAVIOUR_ROWS}


def zero_flags(spec: dict) -> list[str]:
    """Behaviours the spec cannot produce."""
    share = {a["id"]: float(a.get("share", 0)) for a in spec.get("driver_archetypes", [])}
    out = []
    for beh, (types, pkeys) in PRODUCERS.items():
        live = []
        for r in spec.get("traci_rules", []) or []:
            if r.get("rule_type") not in types:
                continue
            if sum(share.get(a, 0.0) for a in r.get("applies_to", [])) <= 0:
                continue
            ps = [float(r["params"][k]) for k in pkeys if k in r.get("params", {})]
            if ps and all(p <= 0 for p in ps if p is not None) and (not pkeys or any(k in r["params"] for k in pkeys)):
                # a rule whose every listed probability is 0 produces nothing (p_max alone does not count)
                main = [float(r["params"][k]) for k in pkeys if k in r["params"] and k != "p_max"]
                if not main or all(p <= 0 for p in main):
                    continue
            live.append(r["rule_type"])
        if not live:
            out.append(beh)
    return out


def main():
    import sys
    sys.stdout.reconfigure(errors="replace", encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign", default="BENCH_v1127")
    ap.add_argument("--suffix", default="v1127")
    a = ap.parse_args()
    specs = {lb: st.format(s=a.suffix) for lb, st in LABELS.items()}
    specs = {lb: st for lb, st in specs.items() if (CAMP_DIR / a.campaign / f"{st}.pkl").is_file()}
    ctx = MetricContext.from_config(load_experiment(), site=load_site(REPO_ROOT / "config" / "site.yaml"))
    rows = []
    tgt = metric_values(read_tables(REPO_ROOT / "data" / "observed" / DAY), ctx)
    for g, lab, key, k in BEHAVIOUR_ROWS:
        rows.append({"group": g, "row": lab, "source": "Ngày quan sát VIDEO_V1 (sinh)", "mean": tgt[key] * k, "sd": np.nan, "n": 1})
    for lb, st in specs.items():
        per = [metric_values(read_tables(run_dir(a.campaign, st, s)), ctx) for s in SEEDS
               if (run_dir(a.campaign, st, s) / "observed_schema").is_dir()]
        for g, lab, key, k in BEHAVIOUR_ROWS:
            x = np.array([p[key] for p in per]) * k
            rows.append({"group": g, "row": lab, "source": lb, "mean": np.nanmean(x), "sd": np.nanstd(x, ddof=1),
                         "n": int(np.isfinite(x).sum())})
        res = pickle.loads((CAMP_DIR / a.campaign / f"{st}.pkl").read_bytes())
        rows.append({"group": "Điểm sai lệch", "row": "S", "source": lb, "mean": res.to_row().get("S"), "sd": np.nan,
                     "n": len(res.runs)})
        runs = res.runs
        for r in runs:
            man = Path(r["run_dir"]) / "manifest.json"
            r["backlog"] = json.loads(man.read_text(encoding="utf-8")).get("insertion_backlog") if man.is_file() else None
        for g, lab, key in STABILITY_ROWS:
            if key == "g0_pass":
                rows.append({"group": g, "row": lab, "source": lb, "mean": sum(bool(r["g0_pass"]) for r in runs),
                             "sd": np.nan, "n": len(runs)})
                continue
            x = np.array([np.nan if r.get(key) is None else float(r[key]) for r in runs])
            rows.append({"group": g, "row": lab, "source": lb, "mean": np.nanmean(x), "sd": np.nanstd(x, ddof=1),
                         "n": int(np.isfinite(x).sum())})
    df = pd.DataFrame(rows)
    out = REPO_ROOT / "results" / f"benchmark_{a.suffix}"
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "profile.csv", index=False)
    cols = ["Ngày quan sát VIDEO_V1 (sinh)"] + list(specs)
    cell = df.assign(txt=[(f"{m:.3g}" if not np.isfinite(s) else f"{m:.3g} ({s:.2g})") if np.isfinite(m) else "--"
                          for m, s in zip(df["mean"], df["sd"])])
    tab = cell.pivot_table(index=["group", "row"], columns="source", values="txt", aggfunc="first", sort=False)
    tab = tab.reindex(columns=[c for c in cols if c in tab.columns]).fillna("--")
    lines = ["| Nhóm | Chỉ số | " + " | ".join(tab.columns) + " |", "|" + "---|" * (len(tab.columns) + 2)]
    lines += [f"| {g} | {r} | " + " | ".join(tab.loc[(g, r)]) + " |" for g, r in tab.index]
    lines += ["", "Hành vi không thể xuất hiện (không có luật, xác suất 0, hoặc luật chỉ gắn với nguyên mẫu tỷ trọng 0). "
              "Rẽ trái cấm chờ giữa nút (M7) không nằm trong danh sách: xe custom1 chờ ở điểm chờ nội bộ của SUMO "
              "ngay cả khi không có luật; luật illegal_left_box chỉ kéo dài thời gian giữ xe."]
    for lb, st in specs.items():
        f = Path(f"rules/specs/{st}.json")
        if f.is_file():
            lines.append(f"- {lb} ({st}): " + (", ".join(zero_flags(json.loads(f.read_text(encoding="utf-8")))) or "không có"))
    (out / "profile.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
