"""Net (x, y) -> pixel mapping of a record_video.py recording made with --calib: finds the three calibration markers
(colour CALIB_RGBA) in frame 0, fits the affine transform pixel = A @ [x, y, 1] from their known net positions
(frames.json "calib"), and writes view_transform.json next to the frames. Same view, size and angle => same transform.

    SUMO/.venv/Scripts/python report/2026-11-27/scripts/view_transform.py --rec <record dir> [--check 1]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

RGB = np.array([255, 0, 128])


def marker_centres(png: Path, tol: int = 40) -> list[tuple[float, float]]:
    a = np.asarray(Image.open(png).convert("RGB")).astype(int)
    mask = (np.abs(a - RGB).sum(axis=2) < tol)
    lab, n = ndimage.label(mask)
    cents = ndimage.center_of_mass(mask, lab, range(1, n + 1))
    sizes = ndimage.sum(mask, lab, range(1, n + 1))
    keep = [c for c, s in zip(cents, sizes) if s >= 4]
    return [(c[1], c[0]) for c in keep]  # (px, py)


def fit(rec: Path) -> dict:
    meta = json.loads((rec / "frames" / "frames.json").read_text(encoding="utf-8"))
    calib = meta[0]["calib"]
    found = marker_centres(rec / "frames" / "f000000.png")
    if len(found) != len(calib):
        raise SystemExit(f"found {len(found)} markers, expected {len(calib)}: {found}")
    net = np.array([[c["x"], c["y"]] for c in calib])
    pix = np.array(found)
    # match markers by geometry: marker 0 = centre, 1 = +x, 2 = +y; try every permutation, keep the best fit
    import itertools
    best = None
    for perm in itertools.permutations(range(len(pix))):
        P = pix[list(perm)]
        X = np.c_[net, np.ones(len(net))]
        A, *_ = np.linalg.lstsq(X, P, rcond=None)
        # an affine map from 3 points is exact; prefer the permutation whose linear part is a similarity
        L = A[:2].T
        sim = abs(np.linalg.norm(L[:, 0]) - np.linalg.norm(L[:, 1])) + abs(L[:, 0] @ L[:, 1])
        if np.linalg.det(L) >= 0:  # screen y points down: a rotation of the view has det < 0, a mirror det > 0
            continue
        if best is None or sim < best[0]:
            best = (sim, A)
    A = best[1]
    out = {"A": A.T.tolist(), "markers_px": found, "markers_net": net.tolist(),
           "scale_px_per_m": float(np.linalg.norm(A[:2].T[:, 0]))}
    (rec / "view_transform.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out


def to_px(tr: dict, x: float, y: float) -> tuple[float, float]:
    A = np.array(tr["A"])
    p = A @ np.array([x, y, 1.0])
    return float(p[0]), float(p[1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rec", type=Path, required=True)
    ap.add_argument("--check", type=int, default=None, help="frame index: draw every vehicle position on it")
    a = ap.parse_args()
    tr = fit(a.rec)
    print(json.dumps(tr))
    if a.check is not None:
        meta = json.loads((a.rec / "frames" / "frames.json").read_text(encoding="utf-8"))
        m = meta[a.check]
        img = Image.open(a.rec / "frames" / f"f{a.check:06d}.png").convert("RGB")
        d = ImageDraw.Draw(img)
        for v in m.get("veh", []):
            px, py = to_px(tr, v["x"], v["y"])
            d.ellipse([px - 4, py - 4, px + 4, py + 4], outline=(255, 0, 0), width=2)
        img.save(a.rec / f"check_{a.check:06d}.png")
        print("wrote", a.rec / f"check_{a.check:06d}.png")


if __name__ == "__main__":
    main()
