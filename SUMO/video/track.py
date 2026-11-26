"""Stabilise a handheld video to a reference frame, then detect and track vehicles.

Runs in .venv-video (torch + ultralytics + opencv), not in the thesis .venv.

Each sampled frame is warped onto the reference frame with a SIFT + RANSAC homography, so all
coordinates in the output share one image plane (the reference frame). Detection (YOLO, COCO classes)
and ByteTrack run on the warped frame.

Output (in --out):
  ref.jpg            reference frame (stabilised plane)
  detections.csv     frame, t_s, track_id, cls, conf, x1, y1, x2, y2, xb, yb (xb/yb = bottom centre)
  stabilise.csv      frame, t_s, n_inliers, ok
  run.json           arguments, model, video metadata
  preview.mp4        (optional) annotated, downscaled
"""
from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path

import cv2
import numpy as np

COCO_KEEP = {1: "bicycle", 2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}


def make_matcher():
    sift = cv2.SIFT_create(nfeatures=2000)
    flann = cv2.FlannBasedMatcher(dict(algorithm=1, trees=5), dict(checks=50))
    return sift, flann


def homography(sift, flann, ref_kp, ref_des, gray, scale, mask=None):
    small = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    kp, des = sift.detectAndCompute(small, mask)
    if des is None or len(kp) < 20:
        return None, 0
    matches = flann.knnMatch(des, ref_des, k=2)
    good = [m for m, n in (p for p in matches if len(p) == 2) if m.distance < 0.7 * n.distance]
    if len(good) < 20:
        return None, len(good)
    src = np.float32([kp[m.queryIdx].pt for m in good]) / scale
    dst = np.float32([ref_kp[m.trainIdx].pt for m in good]) / scale
    H, inl = cv2.findHomography(src, dst, cv2.RANSAC, 3.0)
    if H is None:
        return None, 0
    return H, int(inl.sum())


def load_mask(path: Path | None, shape, scale):
    """Polygon file (JSON list of [x, y] in reference-frame pixels): areas to EXCLUDE from matching."""
    if path is None:
        return None
    h, w = shape
    m = np.full((int(h * scale), int(w * scale)), 255, np.uint8)
    for poly in json.loads(path.read_text(encoding="utf-8")):
        cv2.fillPoly(m, [np.int32(np.array(poly) * scale)], 0)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--ref-time", type=float, default=0.0, help="reference frame time (s)")
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float, default=None)
    ap.add_argument("--fps", type=float, default=30.0, help="sampled frame rate")
    ap.add_argument("--model", default="yolo11x.pt")
    ap.add_argument("--imgsz", type=int, default=1920)
    ap.add_argument("--conf", type=float, default=0.15)
    ap.add_argument("--match-scale", type=float, default=0.5)
    ap.add_argument("--exclude", type=Path, default=None, help="JSON polygons excluded from matching")
    ap.add_argument("--min-inliers", type=int, default=40)
    ap.add_argument("--preview", action="store_true")
    a = ap.parse_args()

    from ultralytics import YOLO

    a.out.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(a.video), cv2.CAP_FFMPEG,
                           [cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY])
    src_fps = cap.get(cv2.CAP_PROP_FPS)
    n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    step = max(1, round(src_fps / a.fps))

    cap.set(cv2.CAP_PROP_POS_MSEC, a.ref_time * 1000)
    ok, ref = cap.read()
    if not ok:
        raise SystemExit(f"cannot read reference frame at {a.ref_time} s")
    h, w = ref.shape[:2]
    cv2.imwrite(str(a.out / "ref.jpg"), ref)
    sift, flann = make_matcher()
    mask = load_mask(a.exclude, (h, w), a.match_scale)
    ref_small = cv2.resize(cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY), None, fx=a.match_scale, fy=a.match_scale,
                           interpolation=cv2.INTER_AREA)
    ref_kp, ref_des = sift.detectAndCompute(ref_small, mask)

    model = YOLO(a.model)
    start_f = int(a.start * src_fps)
    end_f = n_frames if a.end is None else min(n_frames, int(a.end * src_fps))
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_f)

    det_f = open(a.out / "detections.csv", "w", newline="", encoding="utf-8")
    stab_f = open(a.out / "stabilise.csv", "w", newline="", encoding="utf-8")
    det_w, stab_w = csv.writer(det_f), csv.writer(stab_f)
    det_w.writerow(["frame", "t_s", "track_id", "cls", "conf", "x1", "y1", "x2", "y2", "xb", "yb"])
    stab_w.writerow(["frame", "t_s", "n_inliers", "ok"])
    writer = None
    if a.preview:
        pw, ph = w // 2, h // 2
        writer = cv2.VideoWriter(str(a.out / "preview.mp4"), cv2.VideoWriter_fourcc(*"mp4v"), a.fps, (pw, ph))

    H_last = np.eye(3)
    t0 = time.time()
    f = start_f
    while f < end_f:
        if (f - start_f) % step:
            if not cap.grab():
                break
            f += 1
            continue
        ok, frame = cap.read()
        if not ok:
            break
        t_s = f / src_fps
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        H, n_in = homography(sift, flann, ref_kp, ref_des, gray, a.match_scale)
        good = H is not None and n_in >= a.min_inliers
        if good:
            H_last = H
        stab_w.writerow([f, f"{t_s:.3f}", n_in, int(good)])
        warped = cv2.warpPerspective(frame, H_last, (w, h))
        res = model.track(warped, persist=True, tracker="bytetrack.yaml", imgsz=a.imgsz, conf=a.conf,
                          classes=list(COCO_KEEP), verbose=False)[0]
        if res.boxes is not None and res.boxes.id is not None:
            for (x1, y1, x2, y2), tid, c, cf in zip(res.boxes.xyxy.cpu().numpy(), res.boxes.id.int().cpu().numpy(),
                                                   res.boxes.cls.int().cpu().numpy(), res.boxes.conf.cpu().numpy()):
                det_w.writerow([f, f"{t_s:.3f}", int(tid), COCO_KEEP[int(c)], f"{cf:.3f}", f"{x1:.1f}", f"{y1:.1f}",
                                f"{x2:.1f}", f"{y2:.1f}", f"{(x1 + x2) / 2:.1f}", f"{y2:.1f}"])
        if writer is not None:
            vis = res.plot(line_width=1, font_size=8)
            writer.write(cv2.resize(vis, (w // 2, h // 2)))
        done = (f - start_f) / max(1, end_f - start_f)
        if (f - start_f) // step % 150 == 0:
            el = time.time() - t0
            print(f"t={t_s:7.2f}s  {done:5.1%}  inliers={n_in:4d}  elapsed={el:6.0f}s", flush=True)
            det_f.flush()
            stab_f.flush()
        f += 1

    det_f.close()
    stab_f.close()
    if writer is not None:
        writer.release()
    (a.out / "run.json").write_text(json.dumps({
        "video": a.video.name, "src_fps": src_fps, "n_frames": n_frames, "frame_size": [w, h],
        "sample_fps": src_fps / step, "ref_time_s": a.ref_time, "start_s": a.start, "end_s": end_f / src_fps,
        "model": a.model, "imgsz": a.imgsz, "conf": a.conf, "tracker": "bytetrack.yaml",
        "classes": COCO_KEEP, "min_inliers": a.min_inliers, "exclude": str(a.exclude) if a.exclude else None,
    }, indent=2), encoding="utf-8")
    print("done", a.out)


if __name__ == "__main__":
    main()
