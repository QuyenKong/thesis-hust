"""Overlay run info on the frames of record_video.py and encode them to H.264 MP4 (Linux port of
report/2026-10-26/scripts/encode_video.py: system `ffmpeg` and DejaVu fonts instead of imageio-ffmpeg and Segoe UI).

    SUMO/.venv/bin/python report/2026-10-27/scripts/encode_video.py --rec report/2026-10-27/_rec \
        --out report/2026-10-27/video_B2_best_PROXY_D1_seed1.mp4 --fps 20

Overlay values come from `frames.json` (written by the recorder through TraCI at each frame) and from the site
file (signal phase names, cycle). Times shown are simulation time; 0 s = 07:30.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFont

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
PHASE_VI = {
    "LVL_green": ("LVL xanh", "HDT đỏ"), "LVL_yellow": ("LVL vàng", "HDT đỏ"), "LVL_allred": ("đỏ toàn phần", ""),
    "HDT_green": ("HDT xanh", "LVL đỏ"), "HDT_yellow": ("HDT vàng", "LVL đỏ"), "HDT_allred": ("đỏ toàn phần", ""),
}
ORIENTATION = "Nhánh: LVL_W dưới-trái (cấm rẽ trái, có vỉa hè) · LVL_E trên-phải · HDT_N trên-trái · HDT_S dưới-phải"
LEGEND = [((60, 140, 255), "Ô tô"), ((255, 210, 0), "Xe máy"), ((150, 80, 255), "Xe rẽ trái trái luật (đang đi)"),
          ((255, 0, 0), "Xe rẽ trái trái luật đang chờ giữa nút"), ((0, 245, 255), "Xe đi thẳng chặn làn rẽ phải"),
          ((255, 130, 0), "Xe rẽ phải bị kẹt sau xe chặn"), ((255, 255, 255), "Xe máy đi trên vỉa hè")]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")), size)


def panel(draw: ImageDraw.ImageDraw, xy, lines, pad=10, fill=(0, 0, 0, 175)) -> None:
    """Draw `lines` = [(text, font, rgb)] on a rounded dark box at `xy`."""
    x, y = xy
    width = max(draw.textlength(t, font=f) for t, f, _ in lines)
    height = sum(f.size + 5 for _, f, _ in lines)
    draw.rounded_rectangle([x, y, x + width + 2 * pad, y + height + 2 * pad], 8, fill=fill)
    yy = y + pad
    for text, f, color in lines:
        draw.text((x + pad, yy), text, font=f, fill=color)
        yy += f.size + 5


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rec", type=Path, required=True, help="record_video.py --out directory")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--fps", type=int, default=20)
    ap.add_argument("--title", default="Spec B2_best (Optuna, cấu trúc B1) · PROXY_D1 · seed 1 · check-junctions BẬT")
    ap.add_argument("--site", type=Path, default=Path(__file__).resolve().parents[3] / "SUMO/config/site.proxy.yaml")
    a = ap.parse_args()

    meta = json.loads((a.rec / "frames" / "frames.json").read_text(encoding="utf-8"))
    site = yaml.safe_load(a.site.read_text(encoding="utf-8"))
    phases = [p["name"] for p in site["signal"]["phases"]]  # same order as the tlLogic phases (signal.tll.xml)
    cycle = float(site["signal"]["cycle_s"])
    frames = [(m, a.rec / "frames" / f"f{m['i']:06d}.png") for m in meta]
    frames = [(m, p) for m, p in frames if p.is_file()]  # the last request may never be written
    size = Image.open(frames[0][1]).size
    speedup = (frames[1][0]["t"] - frames[0][0]["t"]) * a.fps

    f_title, f_big, f_txt, f_small = font(19, True), font(26, True), font(17), font(15, True)
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{size[0]}x{size[1]}", "-r", str(a.fps), "-i", "-", "-c:v", "libx264",
                           "-pix_fmt", "yuv420p", "-crf", "22", "-preset", "medium", "-movflags", "+faststart",
                           str(a.out)], stdin=subprocess.PIPE)
    for m, path in frames:
        img = Image.open(path).convert("RGBA")
        over = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(over)
        t = m["t"]
        hh, rem = divmod(int(7 * 3600 + 30 * 60 + t), 3600)
        clock = f"{hh:02d}:{rem // 60:02d}:{rem % 60:02d}"
        p1, p2 = PHASE_VI[phases[m["tls_phase"]]]
        light = (120, 255, 120) if "xanh" in p1 else (255, 220, 80) if "vàng" in p1 else (255, 120, 120)
        now, tot = m["now"], m["total"]
        white, grey = (255, 255, 255), (215, 215, 215)
        panel(d, (12, 12), [
            ("Lê Văn Lương × Hoàng Đạo Thúy · SUMO 1.27 sumo-gui · dữ liệu PROXY (không phải số đo)", f_title, white),
            (f"t = {t:7.1f} s   ({clock})   ·   tốc độ ×{speedup:.0f}", f_big, white),
            (a.title, f_txt, grey),
            (ORIENTATION, f_txt, grey),
            (f"Đèn: {p1}{' · ' + p2 if p2 else ''}   (giây {t % cycle:5.1f} / chu kỳ {cycle:.0f} s)", f_txt, light),
            (f"Xe trong mạng: {m['n_veh']}  ·  chờ chèn: {m['pending']}  ·  xe dừng ở 4 nhánh: "
             f"{m['halting_approaches']}  ·  va chạm {m['collisions']}  ·  teleport {m['teleports']}", f_txt, white),
        ])
        panel(d, (12, 232), [
            ("Đang có / tích lũy từ 07:30", f_small, grey),
            (f"Rẽ trái trái luật chờ giữa nút: {now['box']} / {tot['box']}", f_txt, (255, 90, 90)),
            (f"Xe chặn làn rẽ phải: {now['blocker']} (đang dừng {m['blockers_halted']}) / {tot['blocker']}",
             f_txt, (0, 245, 255)),
            (f"Xe rẽ phải kẹt phía sau: {now['blocked']}", f_txt, (255, 150, 40)),
            (f"Xe máy trên vỉa hè: {now['sidewalk']} / {tot['sidewalk']}", f_txt, white),
            ("Đi ngược chiều: KHÔNG mô phỏng (hoãn, R38)", f_txt, (190, 190, 190)),
        ])
        for b in m["blockers"]:  # queue behind each blocker, next to it
            if b["behind"] > 0:
                x, y = b["px"]
                label = f"+{b['behind']}"
                w = d.textlength(label, font=f_small)
                d.rounded_rectangle([x + 8, y - 22, x + 18 + w, y - 2], 5, fill=(255, 130, 0, 230))
                d.text((x + 13, y - 21), label, font=f_small, fill=(0, 0, 0))
        if m["last_collision_t"] is not None and t - m["last_collision_t"] <= 2.0:
            d.rounded_rectangle([size[0] - 190, 12, size[0] - 12, 56], 8, fill=(200, 0, 0, 220))
            d.text((size[0] - 176, 18), "VA CHẠM", font=f_big, fill=white)
        lw = max(d.textlength(txt, font=f_txt) for _, txt in LEGEND) + 56  # legend, bottom right
        lh = 18 + 25 * len(LEGEND)
        lx, ly = size[0] - 12 - lw, size[1] - 12 - lh
        d.rounded_rectangle([lx, ly, size[0] - 12, size[1] - 12], 8, fill=(0, 0, 0, 175))
        for k, (c, txt) in enumerate(LEGEND):
            yy = ly + 9 + k * 25
            d.rectangle([lx + 12, yy + 3, lx + 30, yy + 18], fill=c + (255,), outline=(90, 90, 90))
            d.text((lx + 40, yy), txt, font=f_txt, fill=white)
        ff.stdin.write(Image.alpha_composite(img, over).convert("RGB").tobytes())
    ff.stdin.close()
    if ff.wait():
        raise SystemExit(f"ffmpeg failed ({ff.returncode})")
    print(f"{a.out}: {len(frames)} frames, {len(frames) / a.fps:.1f} s at {a.fps} fps, speed x{speedup:.1f}")


if __name__ == "__main__":
    main()
