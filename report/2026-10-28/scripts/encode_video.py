"""Overlay run info on the frames of record_video.py and encode them to H.264 MP4 (28/10 scenario; from
report/2026-10-27/scripts/encode_video.py, system `ffmpeg` and DejaVu fonts).

    SUMO/.venv/bin/python report/2026-10-28/scripts/encode_video.py --rec report/2026-10-28/_rec \
        --out report/2026-10-28/video_P2_n28_best_PROXY_D1_seed1.mp4 --fps 20

Overlay values come from `frames.json` (written by the recorder through TraCI at each frame) and `rec.json` (run
labels, the running TLS program: phase names, durations; box / sidewalk / right-lane approaches). Phase names are
translated word by word (`phase_vi`), unknown words are shown as they are. Times shown are simulation time;
0 s = 07:30.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
STATUS_VI = {"green": ("xanh", (120, 255, 120)), "yellow": ("vàng", (255, 220, 80)),
             "allred": ("đỏ toàn phần", (255, 120, 120))}
MOVE_VI = {"straight": "đi thẳng", "left": "rẽ trái/quay đầu"}
# view geometry (setBoundary around the junction centre, north up), as 27/10
POSITION = {"LVL_W": "dưới-trái", "LVL_E": "trên-phải", "HDT_N": "trên-trái", "HDT_S": "dưới-phải"}
# text goes on strips above / below the map, not over it: the LVL_E sidewalk and the HDT_S approach run to the top /
# bottom-right corners of the view
HEAD, FOOT = 170, 68


def phase_vi(name: str) -> tuple[str, tuple[int, int, int]]:
    """'<ROAD>[_<move>][_<status>]' (signal phase names of site.proxy.yaml) -> Vietnamese text and colour."""
    road, *rest = name.split("_")
    status = rest.pop() if rest and rest[-1] in STATUS_VI else "green"
    what = " ".join([road, *(MOVE_VI.get(w, w) for w in rest)])
    text, color = STATUS_VI[status]
    return (f"{what} {text}" if status != "allred" else f"{text} (sau {what})"), color


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
    ap.add_argument("--title", default=None, help="default: Spec <spec_id> · <day> · seed <seed> · check-junctions BẬT")
    a = ap.parse_args()

    meta = json.loads((a.rec / "frames" / "frames.json").read_text(encoding="utf-8"))
    rec = json.loads((a.rec / "frames" / "rec.json").read_text(encoding="utf-8"))
    title = ((a.title or f"Spec {rec['spec_id']} · {rec['day']} · seed {rec['seed']} · check-junctions BẬT")
             + f"  |  cấm rẽ trái: {', '.join(rec['box_approaches'])} · vỉa hè: {', '.join(rec['sidewalk_approaches'])}")
    cycle = sum(p["duration"] for p in rec["phases"])
    box_apps, sw_apps = rec["box_approaches"], rec["sidewalk_approaches"]
    orientation = "Nhánh: " + " · ".join(f"{k} {v}" for k, v in POSITION.items())
    legend = [((60, 140, 255), "Ô tô"), ((255, 210, 0), "Xe máy"),
              ((150, 80, 255), f"Xe rẽ trái trái luật ({'/'.join(box_apps)}, đang đi)"),
              ((255, 0, 0), "Xe rẽ trái trái luật đang chờ giữa nút"),
              ((0, 245, 255), f"Xe đi thẳng chặn làn rẽ phải ({len(rec['right_lane_approaches'])} nhánh)"),
              ((255, 130, 0), "Xe rẽ phải bị kẹt sau xe chặn"),
              ((255, 255, 255), f"Xe máy đi trên vỉa hè ({'/'.join(sw_apps)})")]
    frames = [(m, a.rec / "frames" / f"f{m['i']:06d}.png") for m in meta]
    frames = [(m, p) for m, p in frames if p.is_file()]  # the last request may never be written
    map_size = Image.open(frames[0][1]).size
    size = (map_size[0], map_size[1] + HEAD + FOOT)
    speedup = (frames[1][0]["t"] - frames[0][0]["t"]) * a.fps

    f_title, f_big, f_txt, f_small = font(19, True), font(26, True), font(17), font(15, True)
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{size[0]}x{size[1]}", "-r", str(a.fps), "-i", "-", "-c:v", "libx264",
                           "-pix_fmt", "yuv420p", "-crf", "22", "-preset", "medium", "-movflags", "+faststart",
                           str(a.out)], stdin=subprocess.PIPE)
    for m, path in frames:
        img = Image.new("RGBA", size, (16, 16, 16, 255))
        img.paste(Image.open(path).convert("RGBA"), (0, HEAD))
        over = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(over)
        t = m["t"]
        hh, rem = divmod(int(7 * 3600 + 30 * 60 + t), 3600)
        clock = f"{hh:02d}:{rem // 60:02d}:{rem % 60:02d}"
        light_txt, light = phase_vi(m["tls_phase_name"])
        now, tot, now_app, tot_app = m["now"], m["total"], m["now_app"], m["total_app"]
        white, grey = (255, 255, 255), (215, 215, 215)
        main = [
            ("Lê Văn Lương × Hoàng Đạo Thúy · SUMO 1.27 sumo-gui · dữ liệu PROXY (không phải số đo)", f_title, white),
            (f"t = {t:7.1f} s   ({clock})   ·   tốc độ ×{speedup:.0f}", f_big, white),
            (title, f_txt, grey),
            (orientation, f_txt, grey),
            (f"Đèn: {light_txt}   (pha {m['tls_phase'] + 1}/{len(rec['phases'])}, giây {m['cycle_pos']:5.1f} / chu kỳ "
             f"{cycle:.0f} s)", f_txt, light),
            (f"Xe trong mạng: {m['n_veh']}  ·  chờ chèn: {m['pending']}  ·  xe dừng ở 4 nhánh: "
             f"{m['halting_approaches']}  ·  va chạm {m['collisions']}  ·  teleport {m['teleports']}", f_txt, white),
        ]
        panel(d, (0, 0), main, fill=(0, 0, 0, 0))
        panel(d, (max(d.textlength(t, font=f) for t, f, _ in main) + 50, 0), [
            ("Đang có / tích lũy từ 07:30", f_small, grey),
            ("Rẽ trái trái luật chờ giữa nút: " + "  ·  ".join(
                f"{a} {now_app['box'][a]} / {tot_app['box'][a]}" for a in box_apps), f_txt, (255, 90, 90)),
            (f"Xe chặn làn rẽ phải: {now['blocker']} (đang dừng {m['blockers_halted']}) / {tot['blocker']}",
             f_txt, (0, 245, 255)),
            (f"Xe rẽ phải kẹt phía sau: {now['blocked']}", f_txt, (255, 150, 40)),
            ("Xe máy trên vỉa hè: " + "  ·  ".join(
                f"{a} {now_app['sidewalk'][a]} / {tot_app['sidewalk'][a]}" for a in sw_apps), f_txt, white),
            ("Đi ngược chiều: KHÔNG mô phỏng (hoãn, R38)", f_txt, (190, 190, 190)),
        ], fill=(0, 0, 0, 0))
        for b in m["blockers"]:  # queue behind each blocker, next to it
            if b["behind"] > 0:
                x, y = b["px"][0], b["px"][1] + HEAD
                label = f"+{b['behind']}"
                w = d.textlength(label, font=f_small)
                d.rounded_rectangle([x + 8, y - 22, x + 18 + w, y - 2], 5, fill=(255, 130, 0, 230))
                d.text((x + 13, y - 21), label, font=f_small, fill=(0, 0, 0))
        if m["last_collision_t"] is not None and t - m["last_collision_t"] <= 2.0:
            d.rounded_rectangle([size[0] - 190, HEAD + 12, size[0] - 12, HEAD + 56], 8, fill=(200, 0, 0, 220))
            d.text((size[0] - 176, HEAD + 18), "VA CHẠM", font=f_big, fill=white)
        lx, ly = 12, HEAD + map_size[1] + 8  # legend on the bottom strip, wrapped
        for c, txt in legend:
            w = d.textlength(txt, font=f_txt) + 60
            if lx + w > size[0]:
                lx, ly = 12, ly + 28
            d.rectangle([lx, ly + 3, lx + 18, ly + 18], fill=c + (255,), outline=(90, 90, 90))
            d.text((lx + 28, ly), txt, font=f_txt, fill=white)
            lx += w
        ff.stdin.write(Image.alpha_composite(img, over).convert("RGB").tobytes())
    ff.stdin.close()
    if ff.wait():
        raise SystemExit(f"ffmpeg failed ({ff.returncode})")
    print(f"{a.out}: {len(frames)} frames, {len(frames) / a.fps:.1f} s at {a.fps} fps, speed x{speedup:.1f}")


if __name__ == "__main__":
    main()
