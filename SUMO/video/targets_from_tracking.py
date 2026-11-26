"""G0 targets (approach volumes, per-approach movement split, motorcycle share) from a tracking run (count.py output).

Runs in either venv (json + yaml only). Usage:
    python video/targets_from_tracking.py --run video/runs/V2_IMG_4801 --out data/video_targets/V2.yaml

Method (decision D18, docs/DECISIONS_2026-11-26.md):
- The exit counts of the visible exits (`gate_out` of LVL_W_out, LVL_E_out, NT_out) are taken as the movement totals
  into them: tracking misses many motorcycles at the dense stop lines but sees them once they spread out in the box.
- Each exit total is split over the movements that feed it in proportion to the complete origin -> destination tracks.
- The HMG exit is hidden behind the window frame in both videos and the NT exit lies in the glare: the movements into
  the HMG exit (LVL_W left, LVL_E right, NT straight) and HMG straight are not observed. Each is set to
  UNOBSERVED_SHARE of its approach (assumed); the approach's observed movements keep their measured ratios.
- U-turns (LVL only) keep their complete-track count, scaled like the approach's other movements.
Every value carries `evidence: measured_video` (reconstructed) or `assumed`.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

UNOBSERVED_SHARE = 0.15  # assumed share of an approach going to the hidden HMG exit (proxy split: LVL right 0.15)
ARMS = ["LVL_W", "HMG", "LVL_E", "NT"]
# movement from origin to destination (build_net.MOVE_OFFSET_DEG; banned lefts are illegal_l)
MOVE = {("LVL_W", "LVL_E"): "s", ("LVL_W", "NT"): "r", ("LVL_W", "HMG"): "l", ("LVL_W", "LVL_W"): "u",
        ("LVL_E", "LVL_W"): "s", ("LVL_E", "HMG"): "r", ("LVL_E", "NT"): "l", ("LVL_E", "LVL_E"): "u",
        ("HMG", "NT"): "s", ("HMG", "LVL_W"): "r", ("HMG", "LVL_E"): "illegal_l",
        ("NT", "HMG"): "s", ("NT", "LVL_E"): "r", ("NT", "LVL_W"): "illegal_l"}
VISIBLE_EXITS = ["LVL_W", "LVL_E", "NT"]
# movements whose destination is not seen: the HMG exit (window frame) and HMG straight into the NT exit (glare on the
# NT exit side; the NT exit count is used only for its other two feeders, LVL_W right and LVL_E left)
UNOBSERVED = [("LVL_W", "HMG"), ("LVL_E", "HMG"), ("NT", "HMG"), ("HMG", "NT")]


def flows(d: dict) -> dict[tuple[str, str], float]:
    """(origin, destination) -> vehicles over the clip, for one vclass block of od_summary.json."""
    od = d["complete_od"]
    out = {}
    for dest in VISIBLE_EXITS:
        j = ARMS.index(dest)
        feeders = {o: od[ARMS.index(o)][j] for o in ARMS if (o, dest) in MOVE and o != dest and (o, dest) not in UNOBSERVED}
        tot = sum(feeders.values())
        exit_n = d["gate_out"][j]
        for o, n in feeders.items():
            out[(o, dest)] = exit_n * n / tot if tot else 0.0
    for o in ("LVL_W", "LVL_E"):  # U-turns: complete tracks, scaled by the approach's exit/complete ratio below
        out[(o, o)] = float(od[ARMS.index(o)][ARMS.index(o)])
    for o, dest in UNOBSERVED:  # assumed share of the approach
        seen = sum(v for (oo, dd), v in out.items() if oo == o and dd != o and (oo, dd) not in UNOBSERVED)
        out[(o, dest)] = seen * UNOBSERVED_SHARE / (1 - UNOBSERVED_SHARE)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    s = json.loads((a.run / "od_summary.json").read_text(encoding="utf-8"))
    clip_s = s["t1_s"] - s["t0_s"]
    per_h = 3600.0 / clip_s
    f = {vc: flows(s["by_vclass"][vc]) for vc in ("car", "moto")}
    volume, split, moto_n, all_n = {}, {}, 0.0, 0.0
    for o in ARMS:
        mv = {}
        for (oo, dd), _ in f["moto"].items():
            if oo == o:
                mv[MOVE[(oo, dd)]] = f["moto"][(oo, dd)] + f["car"].get((oo, dd), 0.0)
        tot = sum(mv.values())
        volume[o] = round(tot * per_h)
        split[o] = {m: round(v / tot, 3) for m, v in sorted(mv.items())} if tot else {}
        moto_n += sum(v for (oo, _), v in f["moto"].items() if oo == o)
        all_n += tot
    out = {
        "source_run": str(a.run).replace("\\", "/"), "clip_s": round(clip_s, 1),
        "approach_volume_veh_h": volume, "movement_split": split,
        "moto_share": round(moto_n / all_n, 3),
        "unobserved_share_to_HMG": UNOBSERVED_SHARE,
        "evidence": "measured_video (reconstructed from exit counts and complete tracks; HMG-bound movements assumed)",
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(yaml.safe_dump(out, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(yaml.safe_dump(out, allow_unicode=True, sort_keys=False))


if __name__ == "__main__":
    main()
