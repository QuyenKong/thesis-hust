"""Draw tracks from detections.csv on the reference frame (start = green dot, end = red dot), and zones if given.

Runs in .venv-video. Usage: plot_tracks.py RUN_DIR [--zones zones.json] [--min-len 15] [--out tracks.jpg]
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("run", type=Path)
ap.add_argument("--zones", type=Path)
ap.add_argument("--min-len", type=int, default=15)
ap.add_argument("--out", default="tracks.jpg")
ap.add_argument("--grid", action="store_true")
a = ap.parse_args()

im = (cv2.imread(str(a.run / "ref.jpg")) * 0.55).astype(np.uint8)
pts = defaultdict(list)
cls = {}
with (a.run / "detections.csv").open(encoding="utf-8") as f:
    for r in csv.DictReader(f):
        pts[r["track_id"]].append((float(r["xb"]), float(r["yb"])))
        cls[r["track_id"]] = r["cls"]
n = 0
for tid, p in pts.items():
    if len(p) < a.min_len:
        continue
    n += 1
    p = np.int32(p)
    col = (255, 200, 0) if cls[tid] == "car" else (0, 200, 255)
    cv2.polylines(im, [p], False, col, 1)
    cv2.circle(im, tuple(p[0]), 4, (0, 255, 0), -1)
    cv2.circle(im, tuple(p[-1]), 4, (0, 0, 255), -1)
if a.zones:
    z = json.loads(a.zones.read_text(encoding="utf-8"))
    for name, poly in list(z["arms"].items()) + [("box", z["box"])]:
        poly = np.int32(poly)
        cv2.polylines(im, [poly], True, (255, 255, 255), 2)
        cv2.putText(im, name, tuple(poly.mean(0).astype(int)), 0, 1.0, (255, 255, 255), 2)
if a.grid:
    for x in range(0, im.shape[1], 100):
        cv2.line(im, (x, 0), (x, im.shape[0]), (80, 80, 80), 1)
        cv2.putText(im, str(x), (x + 2, 700), 0, 0.5, (200, 200, 200), 1)
    for y in range(0, im.shape[0], 100):
        cv2.line(im, (0, y), (im.shape[1], y), (80, 80, 80), 1)
        cv2.putText(im, str(y), (2, y - 3), 0, 0.5, (200, 200, 200), 1)
cv2.imwrite(str(a.run / a.out), im[650:])
print("tracks drawn", n)
