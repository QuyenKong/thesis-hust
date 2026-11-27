"""Side-by-side demo of 27/11 (request relayed by thesis-03): Video A (B0, SUMO default) | Video B (best rule set of
BENCH_v1127), same day, seed, window, view and speed, from two encode_video.py outputs; optionally a third panel with
the IMG_4801 clip (real time sped up by the same factor) on the left; plus stills for Figure A1 at one sim instant.

    SUMO/.venv/Scripts/python report/2026-11-27/scripts/combine_video.py --a <A.mp4> --b <B.mp4> \
        --out report/2026-11-27/video_AB_VIDEO_V1_seed1.mp4 [--real SUMO/data/IMG_4801.MOV --real-start 0 --speed 3]
    SUMO/.venv/Scripts/python report/2026-11-27/scripts/combine_video.py --stills --rec-a <recA> --rec-b <recB> \
        --t 700 --real SUMO/data/IMG_4801.MOV --real-t 120 --out-dir Latex_SOICT/Figure

ffmpeg from PATH (filters hstack, scale, pad, setpts, tpad, drawtext are standard ffmpeg filters).
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

H = 540  # panel height of the combined video (each 1600x900 panel scaled to 960x540)
FONT = "C\\:/Windows/Fonts/segoeuib.ttf"


def label(text: str, size: int = 24) -> str:
    t = text.replace(":", "\\:").replace("'", "")
    return (f"drawtext=fontfile='{FONT}':text='{t}':x=(w-text_w)/2:y=h-th-10:fontsize={size}:fontcolor=white:"
            f"box=1:boxcolor=black@0.6:boxborderw=8")


def combine(a: Path, b: Path, out: Path, real: Path | None, real_start: float, speed: float, la: str, lb: str):
    inputs = ["-i", str(a), "-i", str(b)]
    fa = f"[0:v]scale=-2:{H},{label(la)}[va]"
    fb = f"[1:v]scale=-2:{H},{label(lb)}[vb]"
    if real is None:
        graph = f"{fa};{fb};[va][vb]hstack=inputs=2:shortest=1[v]"
    else:
        inputs = ["-ss", f"{real_start}", "-i", str(real)] + inputs
        fa = fa.replace("[0:v]", "[1:v]")
        fb = fb.replace("[1:v]", "[2:v]")
        fr = (f"[0:v]setpts=PTS/{speed},scale=-2:{H},tpad=stop_mode=clone:stop_duration=600,"
              f"{label(f'Video thực x{speed:g}', 18)}[vr]")
        graph = f"{fr};{fa};{fb};[vr][va][vb]hstack=inputs=3:shortest=1[v]"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", graph, "-map", "[v]", "-an",
           "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "22", "-preset", "medium", str(out)]
    subprocess.run(cmd, check=True)
    print("wrote", out)


def frame_at(rec: Path, t: float) -> Path:
    meta = json.loads((rec / "frames" / "frames.json").read_text(encoding="utf-8"))
    m = min(meta, key=lambda r: abs(r["t"] - t))
    return rec / "frames" / f"f{m['i']:06d}.png"


def stills(rec_a: Path, rec_b: Path, t: float, real: Path | None, real_t: float, out_dir: Path, suffix: str):
    out_dir.mkdir(parents=True, exist_ok=True)
    for tag, rec in (("A_B0", rec_a), ("B_best", rec_b)):
        src = frame_at(rec, t)
        dst = out_dir / f"still_{tag}_{suffix}_t{int(t)}.png"
        dst.write_bytes(src.read_bytes())
        print("wrote", dst)
    if real is not None:
        dst = out_dir / f"still_real_IMG_4801_t{int(real_t)}.png"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{real_t}", "-i", str(real), "-frames:v", "1",
                        str(dst)], check=True)
        print("wrote", dst)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", type=Path)
    ap.add_argument("--b", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--label-a", default="Video A: B0, SUMO mặc định (trước hiệu chỉnh)")
    ap.add_argument("--label-b", default="Video B: bộ luật tốt nhất sau hiệu chỉnh")
    ap.add_argument("--real", type=Path, default=None)
    ap.add_argument("--real-start", type=float, default=0.0)
    ap.add_argument("--speed", type=float, default=3.0)
    ap.add_argument("--stills", action="store_true")
    ap.add_argument("--rec-a", type=Path)
    ap.add_argument("--rec-b", type=Path)
    ap.add_argument("--t", type=float, default=700.0)
    ap.add_argument("--real-t", type=float, default=120.0)
    ap.add_argument("--out-dir", type=Path)
    ap.add_argument("--suffix", default="v1127")
    a = ap.parse_args()
    if a.stills:
        stills(a.rec_a, a.rec_b, a.t, a.real, a.real_t, a.out_dir, a.suffix)
    else:
        combine(a.a, a.b, a.out, a.real, a.real_start, a.speed, a.label_a, a.label_b)


if __name__ == "__main__":
    main()
