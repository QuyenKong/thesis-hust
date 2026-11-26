"""Figure for the thesis: (a) lane layout of LVL x HMG x NT from scenario/net/site.net.xml, (b) signal stages over one
cycle from config/site.yaml. Vietnamese labels, decimal comma, readable in black and white (hatching + labels).

    .venv/Scripts/python scripts/fig_junction_layout.py  ->  ../Latex_SOICT/Figure/nut_LVL_HMG_NT.{pdf,png}
"""
from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import sumolib
import yaml
from matplotlib.patches import Polygon, Rectangle

from thesis_sumo.config import REPO_ROOT
from thesis_sumo.net.build_net import approach_edges, exit_edges, target_node, target_tls

OUT = REPO_ROOT.parent / "Latex_SOICT" / "Figure" / "nut_LVL_HMG_NT"
NAME = {"LVL_W": "Lê Văn Lương\n(phía Tố Hữu)", "LVL_E": "Lê Văn Lương\n(phía Láng Hạ)",
        "HMG": "Hoàng Minh Giám", "NT": "Nguyễn Tuân"}
MV = {"r": "phải", "s": "thẳng", "l": "trái", "u": "quay đầu"}


def lane_poly(lane):
    from sumolib.geomhelper import move2side
    shp, w = lane.getShape(), lane.getWidth() / 2
    return move2side(shp, -w) + list(reversed(move2side(shp, w)))


def main():
    mpl.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.formatter.use_locale": False})
    net = sumolib.net.readNet(str(REPO_ROOT / "scenario/net/site.net.xml"), withInternal=True, withPrograms=True)
    site = yaml.safe_load((REPO_ROOT / "config/site.yaml").read_text(encoding="utf-8"))
    node = target_node(target_tls(net))
    cx, cy = node.getCoord()
    apps, exs = approach_edges(net), exit_edges(net)
    cont = {apps[a["id"]] for a in site["approaches"] if a["continuous_right_lane"]}
    moves = {apps[a["id"]]: a["lane_movements"] for a in site["approaches"]}

    fig = plt.figure(figsize=(16 / 2.54, 21 / 2.54), layout="constrained")
    gs = fig.add_gridspec(2, 1, height_ratios=[3.2, 1])
    ax = fig.add_subplot(gs[0])
    R = 62
    for e in net.getEdges(withInternal=False):
        for ln in e.getLanes():
            hatch = "////" if (e.getID() in cont and ln.getIndex() == 0) else None
            ax.add_patch(Polygon(lane_poly(ln), closed=True, facecolor="0.88" if hatch else "0.80",
                                 edgecolor="white", lw=0.8, hatch=hatch, zorder=1))
    sh = node.getShape()
    ax.add_patch(Polygon(sh, closed=True, facecolor="0.80", edgecolor="none", zorder=0))
    for a, eid in apps.items():
        e = net.getEdge(eid)
        x, y = e.getShape()[-1]
        x0, y0 = e.getShape()[0]
        dx, dy = x0 - x, y0 - y
        d = (dx * dx + dy * dy) ** 0.5
        nl = chr(10)
        lanes = nl.join(f"làn {k}: " + ", ".join(MV[m] for m in moves[eid][k]) for k in range(e.getLaneNumber()))
        ax.text(x + dx / d * 40, y + dy / d * 40, f"Nhánh vào {NAME[a]}{nl}{e.getLaneNumber()} làn{nl}" + lanes,
                fontsize=6.3, ha="center", va="center", zorder=5, linespacing=1.15,
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="black", lw=0.5))
    for x_id, eid in exs.items():
        e = net.getEdge(eid)
        x, y = e.getShape()[0]
        x1, y1 = e.getShape()[-1]
        dx, dy = x1 - x, y1 - y
        d = (dx * dx + dy * dy) ** 0.5
        ax.text(x + dx / d * 20, y + dy / d * 20, f"ra: {e.getLaneNumber()} làn", fontsize=6, ha="center",
                va="center", style="italic", zorder=5, bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none"))
    ax.annotate("", xy=(cx + R * 0.86, cy + R * 0.95), xytext=(cx + R * 0.86, cy + R * 0.75),
                arrowprops=dict(arrowstyle="-|>", lw=1.2, color="black"))
    ax.text(cx + R * 0.86, cy + R * 0.98, "B", ha="center", va="bottom", fontsize=9, weight="bold")
    ax.plot([cx - 10, cx + 10], [cy - R * 0.95] * 2, color="black", lw=1.5)
    ax.text(cx, cy - R * 0.92, "20 m", ha="center", va="bottom", fontsize=7)
    ax.add_patch(Rectangle((cx + R * 0.35, cy - R * 0.98), 6, 4, facecolor="0.88", edgecolor="0.4", hatch="////"))
    ax.text(cx + R * 0.35 + 8, cy - R * 0.98 + 2, "làn rẽ phải liên tục (30 m cuối)", fontsize=6.5, va="center")
    ax.set_xlim(cx - R, cx + R)
    ax.set_ylim(cy - R, cy + R)
    ax.set_aspect("equal")
    ax.set_axis_off()
    ax.set_title("(a) Mặt bằng phân làn (làn 0 = làn sát lề phải theo hướng xe chạy)", fontsize=8.5, loc="left")

    bx = fig.add_subplot(gs[1])
    sig = site["signal"]
    stages = [("LVL đi thẳng (hai nhánh)", "LVL_straight"), ("LVL rẽ trái, quay đầu (hai nhánh)", "LVL_left"),
              ("HMG và NT", "cross")]
    t, rows = 0.0, {}
    for p in sig["phases"]:
        rows.setdefault(p["name"].split("_yellow")[0].split("_allred")[0].replace("cross_green", "cross"), []).append(
            (t, p["duration_s"], "yellow" if "yellow" in p["name"] else "allred" if "allred" in p["name"] else "green"))
        t += p["duration_s"]
    style = {"green": dict(facecolor="0.35", hatch=None), "yellow": dict(facecolor="0.75", hatch="...."),
             "allred": dict(facecolor="white", hatch="xxxx")}
    for k, (label, key) in enumerate(stages):
        y = len(stages) - 1 - k
        for t0, dur, kind in rows[key]:
            bx.add_patch(Rectangle((t0, y - 0.32), dur, 0.64, edgecolor="black", lw=0.5, **style[kind]))
            if kind == "green":
                bx.text(t0 + dur / 2, y, f"xanh {dur:g} s", ha="center", va="center", color="white", fontsize=7)
        bx.text(-3, y, label, ha="right", va="center", fontsize=7)
    for kind, lab in (("green", "xanh"), ("yellow", "vàng 4 s"), ("allred", "đỏ toàn phần 2 s")):
        bx.add_patch(Rectangle((0, -9), 1, 1, **style[kind], edgecolor="black", lw=0.5, label=lab))
    bx.legend(loc="upper center", bbox_to_anchor=(0.62, -0.32), ncol=3, fontsize=7, frameon=False)
    bx.set_xlim(0, sig["cycle_s"])
    bx.set_ylim(-0.6, len(stages) - 0.4)
    bx.set_yticks([])
    bx.set_xticks(range(0, int(sig["cycle_s"]) + 1, 20))
    bx.set_xlabel("Thời gian trong chu kỳ (s); chu kỳ 160 s")
    for s in ("top", "right", "left"):
        bx.spines[s].set_visible(False)
    bx.set_title("(b) Sơ đồ pha một chu kỳ", fontsize=8.5, loc="left")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(OUT.with_suffix(f".{ext}"), dpi=300)
    print(OUT.with_suffix(".png"))


if __name__ == "__main__":
    main()
