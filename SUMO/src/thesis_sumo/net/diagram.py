"""Junction diagram (PLAN Phase 1.5): lanes drawn from the net, edges labelled with id, side and approach.

Links that allow only the illegal-left vClass are drawn in red, so the custom1-only left turn can be
checked against the field at a glance.
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import sumolib  # noqa: E402

from thesis_sumo.net.build_net import bearing_deg, compass8, target_node, target_tls  # noqa: E402

LABEL_DIST_M = 150.0    # labels sit this far from the junction centre along each edge ...
LABEL_OFFSET_M = 45.0   # ... pushed sideways to the edge's own side of the arm (right-hand traffic)


def _point_at_distance(shape, center, dist):
    """First shape point at least `dist` from `center` (the edge's far end if it is shorter)."""
    for p in shape:
        if math.dist(p, center) >= dist:
            return p
    return shape[-1] if math.dist(shape[-1], center) > math.dist(shape[0], center) else shape[0]


def draw_diagram(net_path: Path, out: Path, approach_ids: dict[str, str] | None = None,
                 restricted_vclass: str = "custom1", title: str = "") -> Path:
    """Write an SVG of `net_path`; `approach_ids` maps edge id -> logical approach id for the labels."""
    net = sumolib.net.readNet(str(net_path), withInternal=True, withPrograms=True)
    node = target_node(target_tls(net))
    center = node.getCoord()
    approach_ids = approach_ids or {}
    plt.rcParams["svg.hashsalt"] = "thesis-sumo"  # deterministic SVG ids
    plt.rcParams["svg.fonttype"] = "none"
    fig, ax = plt.subplots(figsize=(9, 9))
    restricted_drawn = False
    for edge in net.getEdges(withInternal=True):
        for lane in edge.getLanes():
            xs, ys = zip(*lane.getShape())
            if edge.isSpecial():
                only = lane.getPermissions() == {restricted_vclass}
                ax.plot(xs, ys, color="red" if only else "0.6", lw=1.6 if only else 0.5, zorder=3 if only else 1,
                        label=f"link allowing only {restricted_vclass}" if only and not restricted_drawn else None)
                restricted_drawn |= only
            else:
                ax.plot(xs, ys, color="0.25", lw=lane.getWidth() * 0.8, solid_capstyle="butt", alpha=0.35, zorder=2)
    for edge in net.getEdges(withInternal=False):
        inbound = edge.getToNode() is node
        far = edge.getFromNode() if inbound else edge.getToNode()
        side = compass8(bearing_deg(center, far.getCoord()))
        shape = edge.getShape()
        px, py = _point_at_distance(shape if not inbound else shape[::-1], center, LABEL_DIST_M)
        r = math.dist((px, py), center) or 1.0
        ux, uy = (px - center[0]) / r, (py - center[1]) / r  # radial unit vector, pointing away
        sign = -1.0 if inbound else 1.0  # the right of travel is (uy, -ux) outbound, (-uy, ux) inbound
        x, y = px + sign * uy * LABEL_OFFSET_M, py - sign * ux * LABEL_OFFSET_M
        text = f"{edge.getID()}\n{'in from' if inbound else 'out to'} {side}"
        if edge.getID() in approach_ids:
            text = f"{approach_ids[edge.getID()]}  {text}"
        ax.annotate(text, (x, y), fontsize=7, ha="center", va="center", zorder=4,
                    color="tab:blue" if inbound else "tab:green",
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85))
    ax.plot(*center, marker="o", ms=5, color="k", zorder=5)
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    ax.annotate("N", xy=(xmax - 30, ymax - 20), xytext=(xmax - 30, ymax - 90), ha="center",
                arrowprops=dict(arrowstyle="->", lw=1.5))
    ax.plot([xmin + 20, xmin + 120], [ymin + 20, ymin + 20], color="k", lw=2)
    ax.text(xmin + 70, ymin + 28, "100 m", ha="center", fontsize=7)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(title or f"{Path(net_path).name}: target junction {node.getID()}", fontsize=9)
    if restricted_drawn:
        ax.legend(loc="lower right", fontsize=7)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, format="svg", metadata={"Date": None}, bbox_inches="tight")
    plt.close(fig)
    return out
