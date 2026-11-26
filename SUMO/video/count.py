"""Turn counts from tracked detections (output of track.py), by origin/destination zone.

Runs in .venv-video.

zones.json (reference-frame pixels): {"arms": {"LVL_W": [[x, y], ...], "HMG": ..., "NT": ..., "LVL_E": ...},
                                      "box": [[x, y], ...]}
Each arm polygon covers the whole cross-section of that arm (in and out lanes) just outside the junction box.

A track's origin is the first arm zone it is seen in, its destination the last arm zone after it has been in
the box. origin == destination after passing the box = U-turn. Tracks that never reach a second zone are
counted as entries only (n_entries), so the share of complete tracks is visible.

Movement from origin/destination: right-hand traffic, LVL runs SW-NE, HMG to the NW, NT to the SE; left
turns HMG->LVL_E and NT->LVL_W are banned (site.yaml field notes), so they are `illegal_l`.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

MOVEMENT = {  # origin -> {destination: movement}
    "LVL_W": {"LVL_E": "s", "NT": "r", "HMG": "l", "LVL_W": "u"},
    "LVL_E": {"LVL_W": "s", "HMG": "r", "NT": "l", "LVL_E": "u"},
    "HMG": {"NT": "s", "LVL_W": "r", "LVL_E": "illegal_l", "HMG": "u"},
    "NT": {"HMG": "s", "LVL_E": "r", "LVL_W": "illegal_l", "NT": "u"},
}
VCLASS = {"motorcycle": "moto", "bicycle": "moto", "car": "car", "bus": "excluded", "truck": "excluded"}


def inside(poly: np.ndarray, x: float, y: float) -> bool:
    n, ok, j = len(poly), False, len(poly) - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi:
            ok = not ok
        j = i
    return ok


def load_tracks(path: Path, min_len: int):
    pts = defaultdict(list)
    cls = defaultdict(Counter)
    with path.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            tid = int(r["track_id"])
            pts[tid].append((float(r["t_s"]), float(r["xb"]), float(r["yb"])))
            cls[tid][r["cls"]] += float(r["conf"])
    tracks = {}
    for tid, p in pts.items():
        if len(p) >= min_len:
            p.sort()
            tracks[tid] = (VCLASS[cls[tid].most_common(1)[0][0]], np.array(p))
    return tracks


def family(vc: str) -> str:
    return "moto" if vc == "moto" else "car"


def stitch(tracks: dict, max_gap_s: float, base_px: float, px_per_s: float):
    """Greedy tracklet stitching: an end joins the start whose position is closest to the constant-velocity
    prediction, if it starts 0 < gap <= max_gap_s later, within base_px + px_per_s * gap, same family."""
    items = []
    for tid, (vc, p) in tracks.items():
        k = min(len(p), 6)
        dt = p[-1, 0] - p[-k, 0]
        v = (p[-1, 1:] - p[-k, 1:]) / dt if dt > 0 else np.zeros(2)
        items.append((tid, vc, p, v))
    starts = sorted(((p[0, 0], tid) for tid, vc, p, v in items))
    start_t = np.array([s[0] for s in starts])
    by_id = {tid: (vc, p, v) for tid, vc, p, v in items}
    nxt, taken = {}, set()
    cands = []
    for tid, vc, p, v in items:
        te = p[-1, 0]
        lo, hi = np.searchsorted(start_t, te, "right"), np.searchsorted(start_t, te + max_gap_s, "right")
        for _, sid in starts[lo:hi]:
            svc, sp, _ = by_id[sid]
            if sid == tid or family(svc) != family(vc):
                continue
            gap = sp[0, 0] - te
            d = float(np.hypot(*(p[-1, 1:] + v * gap - sp[0, 1:])))
            if d <= base_px + px_per_s * gap:
                cands.append((d + 20 * gap, tid, sid))
    used_end = set()
    for _, tid, sid in sorted(cands):
        if tid in used_end or sid in taken:
            continue
        nxt[tid] = sid
        used_end.add(tid)
        taken.add(sid)
    out, n_links = {}, 0
    for tid in by_id:
        if tid in taken:
            continue
        chain, cur = [tid], tid
        while cur in nxt:
            cur = nxt[cur]
            chain.append(cur)
        n_links += len(chain) - 1
        vcs = Counter()
        for c in chain:
            vcs[by_id[c][0]] += len(by_id[c][1])
        out[tid] = (vcs.most_common(1)[0][0], np.vstack([by_id[c][1] for c in chain]))
    return out, n_links


def crossings(p: np.ndarray, arms: dict, box: np.ndarray):
    """First arm->box step ('in') and last box->arm step ('out') of a track, as (arm, dir, t)."""
    out, prev, first_in, last_out = [], None, None, None
    for t, x, y in p:
        z = "box" if inside(box, x, y) else next((k for k, poly in arms.items() if inside(poly, x, y)), None)
        if z is None:
            continue
        if prev is not None and prev != z:
            if z == "box" and prev != "box" and first_in is None:
                first_in = (prev, "in", t)
            elif prev == "box" and z != "box":
                last_out = (z, "out", t)
        prev = z
    return [c for c in (first_in, last_out) if c is not None]


def zone_sequence(p: np.ndarray, arms: dict, box: np.ndarray):
    seq = []  # (zone, t_first, t_last)
    for t, x, y in p:
        z = "box" if inside(box, x, y) else next((k for k, poly in arms.items() if inside(poly, x, y)), None)
        if z is None:
            continue
        if seq and seq[-1][0] == z:
            seq[-1][2] = t
        else:
            seq.append([z, t, t])
    return seq


def ipf(seed: np.ndarray, rows: np.ndarray, cols: np.ndarray, iters: int = 200) -> np.ndarray:
    """Iterative proportional fitting of `seed` (origin x destination) to row and column totals."""
    m = seed.astype(float).copy()
    for _ in range(iters):
        r = m.sum(1)
        m *= np.divide(rows, r, out=np.ones_like(r), where=r > 0)[:, None]
        c = m.sum(0)
        m *= np.divide(cols, c, out=np.ones_like(c), where=c > 0)[None, :]
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", type=Path, required=True, help="track.py output dir")
    ap.add_argument("--zones", type=Path, required=True)
    ap.add_argument("--min-len", type=int, default=3, help="min detections per tracklet")
    ap.add_argument("--bin-s", type=float, default=60.0)
    ap.add_argument("--stitch-gap-s", type=float, default=1.5)
    ap.add_argument("--stitch-base-px", type=float, default=35.0)
    ap.add_argument("--stitch-px-per-s", type=float, default=60.0)
    ap.add_argument("--uturn-min-px", type=float, default=250.0, help="min travel inside the box for a U-turn")
    a = ap.parse_args()

    z = json.loads(a.zones.read_text(encoding="utf-8"))
    arms = {k: np.array(v, float) for k, v in z["arms"].items()}
    names = list(arms)
    box = np.array(z["box"], float)
    raw = load_tracks(a.run / "detections.csv", a.min_len)
    tracks, n_links = stitch(raw, a.stitch_gap_s, a.stitch_base_px, a.stitch_px_per_s)
    t0 = min(p[0, 0] for _, p in tracks.values())
    t1 = max(p[-1, 0] for _, p in tracks.values())
    n_bins = int((t1 - t0) // a.bin_s) + 1

    rows = []
    gate = Counter()  # (arm, dir, vclass, bin)
    for tid, (vc, p) in tracks.items():
        for arm, d, t in crossings(p, arms, box):
            gate[(arm, d, vc, int((t - t0) // a.bin_s))] += 1
        seq = zone_sequence(p, arms, box)
        arm_visits = [x for x in seq if x[0] != "box"]
        if not arm_visits:
            continue
        origin = arm_visits[0]
        later = [x for x in arm_visits[1:] if x[0] != origin[0]]
        if later:
            dest = later[-1]
        elif len(arm_visits) > 1 and "box" in [x[0] for x in seq]:
            box_pts = np.array([q[1:] for q in p if inside(box, q[1], q[2])])
            if len(box_pts) == 0 or float(np.max(np.hypot(*(box_pts - box_pts[0]).T))) < a.uturn_min_px:
                continue
            dest = arm_visits[-1]
        else:
            continue
        rows.append({"track_id": tid, "vclass": vc, "origin": origin[0], "dest": dest[0],
                     "movement": MOVEMENT[origin[0]].get(dest[0]), "t_leave_origin": round(origin[2], 2),
                     "t_enter_dest": round(dest[1], 2), "bin": int((origin[2] - t0) // a.bin_s)})

    with (a.run / "od_tracks.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    summary = {"t0_s": round(t0, 2), "t1_s": round(t1, 2), "bin_s": a.bin_s, "n_bins": n_bins,
               "n_tracklets": len(raw), "n_stitch_links": n_links, "n_tracks": len(tracks),
               "n_complete_od": len(rows), "by_vclass": {}}
    for vc in ("car", "moto"):
        seed = np.zeros((len(names), len(names)))
        for r in rows:
            if r["vclass"] == vc:
                seed[names.index(r["origin"]), names.index(r["dest"])] += 1
        ins = np.array([sum(gate[(k, "in", vc, b)] for b in range(n_bins)) for k in names], float)
        outs = np.array([sum(gate[(k, "out", vc, b)] for b in range(n_bins)) for k in names], float)
        outs_scaled = outs * (ins.sum() / outs.sum()) if outs.sum() else outs
        fitted = ipf(seed, ins, outs_scaled)
        share = np.divide(fitted, fitted.sum(1, keepdims=True), out=np.zeros_like(fitted),
                          where=fitted.sum(1, keepdims=True) > 0)
        per_bin = {}
        for i, o in enumerate(names):
            for j, dname in enumerate(names):
                mv = MOVEMENT[o].get(dname)
                if share[i, j] == 0:
                    continue
                per_bin.setdefault(o, {})[mv] = [round(gate[(o, "in", vc, b)] * share[i, j], 2) for b in range(n_bins)]
        summary["by_vclass"][vc] = {
            "arms": names, "complete_od": seed.astype(int).tolist(), "gate_in": ins.astype(int).tolist(),
            "gate_out": outs.astype(int).tolist(), "od_fitted": np.round(fitted, 1).tolist(),
            "turn_share": np.round(share, 3).tolist(), "per_bin_by_origin_movement": per_bin}
    (a.run / "od_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print({k: summary[k] for k in ("n_tracklets", "n_stitch_links", "n_tracks", "n_complete_od", "n_bins", "t0_s", "t1_s")})
    for vc, s in summary["by_vclass"].items():
        print(f"--- {vc}: arms {s['arms']}  in {s['gate_in']}  out {s['gate_out']}")
        for o, mvs in s["per_bin_by_origin_movement"].items():
            print(f"  {o:6s}", {m: round(sum(v), 1) for m, v in mvs.items()})


if __name__ == "__main__":
    main()
