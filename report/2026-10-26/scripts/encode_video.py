"""Overlay run info on the frames of record_video.py and encode them to H.264 MP4.

Needs Pillow, PyYAML and imageio-ffmpeg (any Python):

    python report/2026-10-26/scripts/encode_video.py --rec report/2026-10-26/_rec \
        --out report/2026-10-26/sumo_B0_PROXY_D1_seed1.mp4 --fps 20

Overlay values come from `frames.json` (written by the recorder through TraCI at each frame) and from the site
file (signal phase names, cycle). Times shown are simulation time; 0 s = 07:30.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import imageio_ffmpeg
import yaml
from PIL import Image, ImageDraw, ImageFont

FONT_DIR = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
PHASE_VI = {
    "LVL_green": ("LVL xanh", "HDT đỏ"), "LVL_yellow": ("LVL vàng", "HDT đỏ"), "LVL_allred": ("đỏ toàn phần", ""),
    "HDT_green": ("HDT xanh", "LVL đỏ"), "HDT_yellow": ("HDT vàng", "LVL đỏ"), "HDT_allred": ("đỏ toàn phần", ""),
}
# arms as seen in the view (scenario/net/edge_table.csv: LVL_W from SW, LVL_E from NE, HDT_N from NW, HDT_S from SE)
ORIENTATION = "Nhánh: LVL_W dưới-trái (từ Tố Hữu, cấm rẽ trái) · LVL_E trên-phải · HDT_N trên-trái · HDT_S dưới-phải"
LEGEND = [((60, 140, 255), "Ô tô (car)"), ((255, 210, 0), "Xe máy (moto)"),
          ((255, 40, 40), "Xe máy rẽ trái trái luật (moto_violator)")]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / ("segoeuib.ttf" if bold else "segoeui.ttf")), size)


def panel(draw: ImageDraw.ImageDraw, xy, lines, pad=12, fill=(0, 0, 0, 170)) -> None:
    """Draw `lines` = [(text, font, rgb)] on a rounded dark box at `xy`."""
    x, y = xy
    width = max(draw.textlength(t, font=f) for t, f, _ in lines)
    height = sum(f.size + 6 for _, f, _ in lines)
    draw.rounded_rectangle([x, y, x + width + 2 * pad, y + height + 2 * pad], 8, fill=fill)
    yy = y + pad
    for text, f, color in lines:
        draw.text((x + pad, yy), text, font=f, fill=color)
        yy += f.size + 6


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rec", type=Path, required=True, help="record_video.py --out directory")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--fps", type=int, default=20)
    ap.add_argument("--title", default="B0 (setup luận văn, vType mặc định) · PROXY_D1 · seed 1 · check-junctions BẬT")
    ap.add_argument("--no-violators", action="store_true", help="drop the moto_violator legend row (--plain-sumo runs)")
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

    f_title, f_big, f_txt = font(22, True), font(30, True), font(20)
    writer = imageio_ffmpeg.write_frames(str(a.out), size, fps=a.fps, codec="libx264", pix_fmt_out="yuv420p",
                                         macro_block_size=2,  # 1600x900: even sizes are enough for yuv420p
                                         output_params=["-crf", "22", "-preset", "medium", "-movflags", "+faststart"])
    writer.send(None)
    for m, path in frames:
        img = Image.open(path).convert("RGBA")
        over = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(over)
        t = m["t"]
        hh, rem = divmod(int(7 * 3600 + 30 * 60 + t), 3600)
        clock = f"{hh:02d}:{rem // 60:02d}:{rem % 60:02d}"
        p1, p2 = PHASE_VI[phases[m["tls_phase"]]]
        light = (120, 255, 120) if "xanh" in p1 else (255, 220, 80) if "vàng" in p1 else (255, 120, 120)
        panel(d, (14, 14), [
            ("Lê Văn Lương × Hoàng Đạo Thúy · SUMO 1.27 sumo-gui", f_title, (255, 255, 255)),
            (f"t = {t:7.1f} s   ({clock})   ·   tốc độ ×{speedup:.0f}", f_big, (255, 255, 255)),
            (a.title, f_txt, (220, 220, 220)),
            (ORIENTATION, f_txt, (220, 220, 220)),
            (f"Đèn: {p1}{' · ' + p2 if p2 else ''}   (giây {t % cycle:5.1f} / chu kỳ {cycle:.0f} s)", f_txt, light),
            (f"Xe trong mạng: {m['n_veh']}   ·   chờ chèn: {m['pending']}   ·   xe dừng ở 4 nhánh vào: "
             f"{m['halting_approaches']}", f_txt, (255, 255, 255)),
            (f"Tích lũy: va chạm {m['collisions']}   ·   teleport {m['teleports']}", f_txt, (255, 255, 255)),
        ])
        if m["last_collision_t"] is not None and t - m["last_collision_t"] <= 2.0:
            d.rounded_rectangle([14, 268, 214, 318], 8, fill=(200, 0, 0, 220))
            d.text((30, 274), "VA CHẠM", font=f_big, fill=(255, 255, 255))
        legend = LEGEND[:2] if a.no_violators else LEGEND
        lw = max(d.textlength(txt, font=f_txt) for _, txt in legend) + 70  # legend, bottom right
        lh = 24 + 30 * len(legend)
        lx, ly = size[0] - 14 - lw, size[1] - 14 - lh
        d.rounded_rectangle([lx, ly, size[0] - 14, size[1] - 14], 8, fill=(0, 0, 0, 170))
        for k, (c, txt) in enumerate(legend):
            yy = ly + 12 + k * 30
            d.rectangle([lx + 14, yy + 4, lx + 34, yy + 20], fill=c + (255,))
            d.text((lx + 44, yy), txt, font=f_txt, fill=(255, 255, 255))
        writer.send(Image.alpha_composite(img, over).convert("RGB").tobytes())
    writer.close()
    print(f"{a.out}: {len(frames)} frames, {len(frames) / a.fps:.1f} s at {a.fps} fps, speed x{speedup:.1f}")


if __name__ == "__main__":
    main()
