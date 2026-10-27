"""Base network (PLAN Phase 1.1-1.2): cut the OSM export around the target junction.

Two netconvert passes, both from the immutable OSM file, no hand edits:

1. **cut**: OSM -> temporary net. Keeps edges inside a circle of `intersection.cut_radius_m` around
   `intersection.center_lonlat` (`--keep-edges.in-geo-boundary`, polygon form), only edges that allow
   passenger or motorcycle (`--keep-edges.by-vclass`), minus service roads (`--remove-edges.by-type`).
   Signals at the target junction are built as `static` (`--tls.default-type static`).
2. **base**: cut net -> `base.net.xml`. Keeps only the four arms of the target junction (chains of
   straight connections from the junction to the cut fringe). Side streets carry no demand (turn counts
   are only observed at the target), and the nodes they create on the arms would split or block queues
   (PLAN 1.1), so they are dropped. Signals on the arms are switched to `priority` by a generated
   plain-XML node patch, and `--geometry.remove` then merges each arm into one edge. Every removed node
   is listed in `removed_nodes.csv` (and printed) with the reason.

All option names checked with `netconvert --help` (SUMO 1.27.0).
"""

from __future__ import annotations

import csv
import math
import os
import subprocess
import tempfile
import unicodedata
from pathlib import Path

import pandas as pd
import sumolib
from lxml import etree

from thesis_sumo.config import REPO_ROOT, Site

NET_DIR = REPO_ROOT / "scenario" / "net"
KEEP_VCLASSES = ("passenger", "motorcycle")
REMOVE_TYPES = ("highway.service", "highway.footway", "railway.subway")
TARGET_MAX_DIST_M = 50.0  # the target TLS must lie this close to intersection.center_lonlat
CIRCLE_VERTICES = 36
M_PER_DEG_LAT = 111_320.0

# logical approach ids (site file) -> street name (accents stripped) and the axis that tells the arms apart
ROAD_AXES = {"LVL": ("le van luong", "x"), "HDT": ("hoang dao thuy", "y")}
ARM_SIDE = {("x", False): "W", ("x", True): "E", ("y", False): "S", ("y", True): "N"}
COMPASS8 = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")
EDGE_TABLE_COLUMNS = ["edge_id", "name", "direction", "n_lanes", "length_m", "connections"]
REMOVED_COLUMNS = ["node_id", "node_type", "signal", "dist_to_center_m", "arms", "side_streets", "reason"]


def netconvert(args: list[str], log: Path) -> None:
    """Run netconvert; write its output to `log`; raise with the output tail on a non-zero exit."""
    log.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run([sumolib.checkBinary("netconvert"), *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    log.write_text(proc.stdout + proc.stderr, encoding="utf-8")
    if proc.returncode != 0:
        raise RuntimeError(f"netconvert failed (exit {proc.returncode}), see {log}:\n{proc.stderr[-2000:]}")


def geo_circle(lon: float, lat: float, radius_m: float, n: int = CIRCLE_VERTICES) -> str:
    """`lon0,lat0,lon1,lat1,...` polygon approximating a circle (local equirectangular, fine at < 1 km)."""
    m_per_deg_lon = M_PER_DEG_LAT * math.cos(math.radians(lat))
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / n
        pts += [f"{lon + radius_m * math.cos(a) / m_per_deg_lon:.7f}", f"{lat + radius_m * math.sin(a) / M_PER_DEG_LAT:.7f}"]
    return ",".join(pts)


def target_tls(net: sumolib.net.Net, center_lonlat: tuple[float, float] | None = None):
    """The target traffic light: the only one in the net, or the one nearest `center_lonlat`."""
    tlss = net.getTrafficLights()
    if center_lonlat is None:
        if len(tlss) != 1:
            raise ValueError(f"expected exactly one traffic light, found {[t.getID() for t in tlss]}")
        return tlss[0]
    cx, cy = net.convertLonLat2XY(*center_lonlat)
    dist = {t.getID(): math.dist(target_node(t).getCoord(), (cx, cy)) for t in tlss}
    best = min(tlss, key=lambda t: dist[t.getID()])
    if dist[best.getID()] > TARGET_MAX_DIST_M:
        raise ValueError(f"no traffic light within {TARGET_MAX_DIST_M} m of {center_lonlat} "
                         f"(nearest {best.getID()} at {dist[best.getID()]:.0f} m)")
    return best


def target_node(tls) -> sumolib.net.node.Node:
    nodes = {in_lane.getEdge().getToNode() for in_lane, _, _ in tls.getConnections()}
    if len(nodes) != 1:
        raise ValueError(f"traffic light {tls.getID()} controls {len(nodes)} junctions, expected 1")
    return nodes.pop()


def inbound_edges(node) -> list:
    """Normal (non-internal) edges ending at `node`."""
    return [e for e in node.getIncoming() if not e.isSpecial()]


def outbound_edges(node) -> list:
    """Normal (non-internal) edges starting at `node`."""
    return [e for e in node.getOutgoing() if not e.isSpecial()]


def _plain(name: str) -> str:
    """Street name lower-cased with Vietnamese accents stripped ("Đường Lê Văn Lương" -> "duong le van luong")."""
    s = unicodedata.normalize("NFKD", name.replace("Đ", "D").replace("đ", "d"))
    return "".join(ch for ch in s if not unicodedata.combining(ch)).lower()


def bearing_deg(frm: tuple[float, float], to: tuple[float, float]) -> float:
    """Compass bearing from `frm` to `to` (0 = north, 90 = east); net y points north."""
    return math.degrees(math.atan2(to[0] - frm[0], to[1] - frm[1])) % 360


def compass8(bearing: float) -> str:
    return COMPASS8[int(((bearing + 22.5) % 360) // 45)]


def approach_edges(net: sumolib.net.Net) -> dict[str, str]:
    """Logical approach id -> inbound edge id at the target junction.

    Rule: the two inbound arms of Le Van Luong are told apart by x (smaller = W), those of
    Hoang Dao Thuy by y (larger = N). Both roads run diagonally (LVL SW-NE, HDT NW-SE), so the
    nearest-compass label would not be unique; the axis rule matches the site file's naming.
    """
    node = target_node(target_tls(net))
    return _arm_edges(inbound_edges(node), lambda e: e.getFromNode().getCoord(), "inbound")


def exit_edges(net: sumolib.net.Net) -> dict[str, str]:
    """Logical exit id (`<approach id of the same arm>_out`) -> outbound edge id; same axis rule as
    `approach_edges`, applied to the far (downstream) end of each outbound edge."""
    node = target_node(target_tls(net))
    arms = _arm_edges(outbound_edges(node), lambda e: e.getToNode().getCoord(), "outbound")
    return {f"{k}_out": v for k, v in arms.items()}


def _arm_edges(edges: list, far_coord, kind: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for prefix, (street, axis) in ROAD_AXES.items():
        arms = [e for e in edges if street in _plain(e.getName())]
        if len(arms) != 2:
            raise ValueError(f"expected 2 {kind} edges named like {street!r}, found {[e.getID() for e in arms]}")
        k = 0 if axis == "x" else 1
        lo, hi = sorted(arms, key=lambda e: far_coord(e)[k])
        for edge, high in ((hi, True), (lo, False)):
            out[f"{prefix}_{ARM_SIDE[(axis, high)]}"] = edge.getID()
    return {k: out[k] for k in ("LVL_W", "LVL_E", "HDT_N", "HDT_S")}


def approach_segments(net: sumolib.net.Net, edge_id: str) -> list:
    """The approach edge `edge_id` (ends at the stop line) and its straight upstream continuation, stop line first:
    one edge in the base net, `[<edge>, <edge>.mid, <edge>.up]` or `[<edge>, <edge>.up]` once the site patches split
    it (thesis_sumo.net.apply_patches)."""
    return _straight_chain(net.getEdge(edge_id), upstream=True)


def sidewalk_edges(net: sumolib.net.Net) -> dict[str, str]:
    """Sidewalk edge id -> approach id: the inbound edges of the target junction that are no approach edge and start
    at a node of an approach's segment chain (apply_patches, Phase 3B topology c)."""
    node = target_node(target_tls(net))
    approaches = approach_edges(net)
    nodes = {s.getFromNode().getID(): a for a, e in approaches.items() for s in approach_segments(net, e)}
    out = {}
    for e in inbound_edges(node):
        if e.getID() in approaches.values():
            continue
        if e.getFromNode().getID() not in nodes:
            raise ValueError(f"inbound edge {e.getID()} is neither an approach edge nor a sidewalk of one")
        out[e.getID()] = nodes[e.getFromNode().getID()]
    return out


def _straight_chain(edge, upstream: bool) -> list:
    """`edge` plus its straight (`dir="s"`) continuation away from the junction, to the cut fringe."""
    chain = [edge]
    while True:
        cur = chain[-1]
        links = cur.getIncoming() if upstream else cur.getOutgoing()
        nxt = [e for e, conns in links.items() if not e.isSpecial() and any(c.getDirection() == "s" for c in conns)]
        if len(nxt) > 1:
            raise ValueError(f"edge {cur.getID()} has {len(nxt)} straight continuations: {[e.getID() for e in nxt]}")
        if not nxt or nxt[0] in chain:
            return chain
        chain.append(nxt[0])


def _arms(net, node) -> list[tuple[bool, list]]:
    """(inbound, chain) for every edge at `node`; chain[0] touches the junction."""
    return ([(True, _straight_chain(e, upstream=True)) for e in inbound_edges(node)]
            + [(False, _straight_chain(e, upstream=False)) for e in node.getOutgoing()])


def write_xml(root: etree._Element, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    etree.ElementTree(root).write(str(path), pretty_print=True, xml_declaration=True, encoding="UTF-8")


def _plan_base(cut: Path, site: Site, patch_dir: Path) -> tuple[Path, Path, Path, list[dict]]:
    """From the cut net: which edges to keep, which arm signals to unset, which names to fill."""
    net = sumolib.net.readNet(str(cut), withPrograms=True)
    center = tuple(site.require("intersection.center_lonlat"))
    tls = target_tls(net, center)
    node = target_node(tls)
    cx, cy = net.convertLonLat2XY(*center)
    arms = _arms(net, node)
    keep = {e.getID() for _, chain in arms for e in chain}
    tls_nodes = {target_node(t).getID() for t in net.getTrafficLights() if t is not tls}

    removed: dict[str, dict] = {}
    names = etree.Element("edges")
    for inbound, chain in arms:
        named = {e.getName() for e in chain if e.getName()}
        far = chain[-1].getFromNode() if inbound else chain[-1].getToNode()
        side = compass8(bearing_deg(node.getCoord(), far.getCoord()))
        arm = f"{' / '.join(sorted(named)) or '(unnamed)'} {'in from' if inbound else 'out to'} {side}"
        # interior nodes: between consecutive chain edges
        for e in chain[:-1]:
            n = e.getFromNode() if inbound else e.getToNode()
            streets = sorted({f"{x.getID()} ({x.getName() or 'unnamed'}, {x.getType()})"
                              for x in n.getIncoming() + n.getOutgoing() if x.getID() not in keep})
            row = removed.setdefault(n.getID(), {
                "node_id": n.getID(), "node_type": n.getType(), "signal": n.getID() in tls_nodes,
                "dist_to_center_m": round(math.dist(n.getCoord(), (cx, cy)), 1), "arms": [], "side_streets": streets})
            row["arms"].append(arm)
        # an unnamed arm edge takes the arm's single street name, so --geometry.remove can merge it
        if len(named) == 1:
            (street,) = named
            for e in chain:
                if not e.getName():
                    etree.SubElement(names, "edge", id=e.getID(), name=street)

    unset = etree.Element("nodes")
    for nid in sorted(n for n in tls_nodes if n in removed):
        etree.SubElement(unset, "node", id=nid, type="priority")
    # signals off the arms vanish with their edges; one at an arm's fringe end would survive unnoticed
    arm_nodes = {n.getID() for e_id in keep for n in (net.getEdge(e_id).getFromNode(), net.getEdge(e_id).getToNode())}
    stray = (tls_nodes - set(removed)) & arm_nodes
    if stray:
        raise ValueError(f"signals {sorted(stray)} sit at the fringe end of an arm; widen or shrink the cut")

    keep_file = patch_dir / "keep_edges.txt"
    keep_file.parent.mkdir(parents=True, exist_ok=True)
    keep_file.write_text("".join(f"{e}\n" for e in sorted(keep)), encoding="utf-8")
    nod_file, edg_file = patch_dir / "unset_arm_tls.nod.xml", patch_dir / "street_names.edg.xml"
    write_xml(unset, nod_file)
    write_xml(names, edg_file)

    rows = []
    for r in sorted(removed.values(), key=lambda r: r["dist_to_center_m"]):
        reason = "side street junction on an arm (side streets dropped, no demand)"
        if r["signal"]:
            reason = "signal on an arm, would meter queues/discharge upstream of the target (PLAN 1.1); set to priority"
        rows.append({**r, "arms": "; ".join(r["arms"]), "side_streets": "; ".join(r["side_streets"]),
                     "signal": "yes" if r["signal"] else "no", "reason": reason})
    return keep_file, nod_file, edg_file, rows


def _check_base(base: Path) -> None:
    net = sumolib.net.readNet(str(base), withPrograms=True)
    tls = target_tls(net)
    node = target_node(tls)
    n_in, n_out = len(inbound_edges(node)), len(node.getOutgoing())
    if (n_in, n_out) != (4, 4):
        raise RuntimeError(f"{base}: target junction has {n_in} in / {n_out} out edges, expected 4 / 4")
    left = [n.getID() for n in net.getNodes() if n is not node and n.getType() != "dead_end"]
    if left:
        raise RuntimeError(f"{base}: nodes left on the arms after --geometry.remove: {left}")
    types = {p.getType() for p in tls.getPrograms().values()}
    if types != {"static"}:
        raise RuntimeError(f"{base}: target tlLogic type {types}, expected static")


def build_base(site: Site, out: Path = NET_DIR / "base.net.xml") -> Path:
    """Build `out` (base net) from the OSM file named in the site file; return its path."""
    out = Path(out)
    osm = REPO_ROOT / site.require("source.osm_file")
    lon, lat = site.require("intersection.center_lonlat")
    radius = site.require("intersection.cut_radius_m")
    typemap = Path(os.environ["SUMO_HOME"]) / "data" / "typemap" / "osmNetconvert.typ.xml"
    logs = out.parent / "logs"
    patch_dir = out.parent / "patches" / "base"

    with tempfile.TemporaryDirectory() as tmp:
        cut = Path(tmp) / "cut.net.xml"
        netconvert([
            "--osm-files", str(osm), "--type-files", str(typemap),
            "--keep-edges.in-geo-boundary", geo_circle(lon, lat, radius),
            "--keep-edges.by-vclass", ",".join(KEEP_VCLASSES),
            "--remove-edges.by-type", ",".join(REMOVE_TYPES),
            "--geometry.remove", "--junctions.join",
            "--tls.guess-signals", "--tls.discard-simple", "--tls.join", "--tls.default-type", "static",
            "--output.street-names", "--output.original-names",
            "-o", str(cut),
        ], logs / "netconvert_cut.log")
        keep_file, nod_file, edg_file, removed = _plan_base(cut, site, patch_dir)
        _write_removed(removed, out.parent / "removed_nodes.csv")
        netconvert([
            "-s", str(cut), "--keep-edges.input-file", str(keep_file),
            "-n", str(nod_file), "-e", str(edg_file),
            "--geometry.remove", "--output.street-names", "--output.original-names",
            "-o", str(out),
        ], logs / "netconvert_base.log")
    _check_base(out)
    return out


def _write_removed(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=REMOVED_COLUMNS, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def _conn_summary(net, edge) -> str:
    """`dir>to[lanes]` per outgoing movement; `{only:vclasses}` when the link narrows permissions."""
    groups: dict[tuple[str, str, str], list[int]] = {}
    for to, conns in edge.getOutgoing().items():
        for c in conns:
            via = c.getViaLaneID()
            perms = net.getLane(via).getPermissions() if via else set()
            only = "" if not via or perms >= c.getFromLane().getPermissions() else "{only:" + ",".join(sorted(perms)) + "}"
            groups.setdefault((c.getDirection(), to.getID(), only), []).append(c.getFromLane().getIndex())
    order = {d: i for i, d in enumerate("rRsLlt")}
    return " ".join(f"{d}>{to}[{','.join(map(str, sorted(lanes)))}]{only}"
                    for (d, to, only), lanes in sorted(groups.items(), key=lambda kv: (order.get(kv[0][0], 9), kv[0][1])))


def edge_table(net: Path) -> pd.DataFrame:
    """One row per edge of `net`: id, street name, side of the junction, lanes, length, connections."""
    n = sumolib.net.readNet(str(net), withInternal=True, withPrograms=True)
    node = target_node(target_tls(n))
    rows = []
    for e in n.getEdges(withInternal=False):
        inbound = e.getToNode() is node
        far = e.getFromNode() if inbound else e.getToNode()
        side = compass8(bearing_deg(node.getCoord(), far.getCoord()))
        rows.append(((not inbound, COMPASS8.index(side), e.getID()), {
            "edge_id": e.getID(), "name": e.getName(),
            "direction": f"in from {side}" if inbound else f"out to {side}",
            "n_lanes": e.getLaneNumber(), "length_m": round(e.getLength(), 1),
            "connections": _conn_summary(n, e) if inbound else "",
        }))
    return pd.DataFrame([r for _, r in sorted(rows, key=lambda kv: kv[0])], columns=EDGE_TABLE_COLUMNS)

