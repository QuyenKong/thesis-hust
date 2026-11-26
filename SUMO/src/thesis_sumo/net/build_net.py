"""Base network (PLAN Phase 1.1-1.2): cut the OSM export around the target junction.

Two netconvert passes, both from the immutable OSM file, no hand edits:

1. **cut**: OSM -> temporary net. Keeps edges inside a circle of `intersection.cut_radius_m` around
   `intersection.center_lonlat` (`--keep-edges.in-geo-boundary`, polygon form), only edges that allow
   passenger or motorcycle (`--keep-edges.by-vclass`), minus service roads and slip roads (`--remove-edges.by-type`).
   LVL, HMG and NT are dual carriageways near the junction, so OSM draws it as several nodes; the plain-XML patch
   `patches/base/join_target.nod.xml` (`<join nodes=.../>` with `intersection.join_nodes`) merges them into one node,
   and `--tls.set` puts the only signal of the study on it (`static`). OSM has no signal tag at these nodes; the
   pedestrian crossing signals on the arms are dropped in pass 2 (owner 2026-11-26).
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
from pathlib import Path

import pandas as pd
import sumolib
from lxml import etree

from thesis_sumo.config import REPO_ROOT, Site

NET_DIR = REPO_ROOT / "scenario" / "net"
KEEP_VCLASSES = ("passenger", "motorcycle")
# highway.tertiary_link: the slip roads of LVL x HMG x NT; continuous right turns are modelled as lane 0 of the
# approach (PLAN 0, apply_patches), not as separate edges
REMOVE_TYPES = ("highway.service", "highway.footway", "railway.subway", "highway.tertiary_link")
TARGET_MAX_DIST_M = 50.0  # the target TLS must lie this close to intersection.center_lonlat
CIRCLE_VERTICES = 36
M_PER_DEG_LAT = 111_320.0

# logical approach id -> compass bearing (deg) from the junction to the arm (LVL x HMG x NT, 2026-11-26): LVL runs
# SW-NE, Hoang Minh Giam leaves to the NW, Nguyen Tuan to the SE. An edge belongs to the arm whose bearing is nearest
# to the bearing of its far end; each arm must get exactly one edge, within ARM_MAX_DEV_DEG.
ARM_BEARINGS = {"LVL_W": 225.0, "LVL_E": 45.0, "HMG": 315.0, "NT": 135.0}
ARM_MAX_DEV_DEG = 40.0


def opposing_arm(approach: str, approaches) -> str:
    """The approach across the junction: the one whose ARM_BEARINGS bearing differs by 180 deg (LVL_W <-> LVL_E,
    HMG <-> NT). Raises if `approach` or its opposite is not among `approaches`."""
    approaches = list(approaches)
    if approach not in ARM_BEARINGS:
        raise ValueError(f"approach {approach!r} is not an arm of {sorted(ARM_BEARINGS)}")
    opp = [a for a in approaches if a in ARM_BEARINGS and a != approach
           and _angle_diff(ARM_BEARINGS[a], ARM_BEARINGS[approach] + 180.0) < 1.0]
    if len(opp) != 1:
        raise ValueError(f"approach {approach}: no unique opposing approach (bearing + 180 deg) in {approaches}")
    return opp[0]
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


def bearing_deg(frm: tuple[float, float], to: tuple[float, float]) -> float:
    """Compass bearing from `frm` to `to` (0 = north, 90 = east); net y points north."""
    return math.degrees(math.atan2(to[0] - frm[0], to[1] - frm[1])) % 360


def compass8(bearing: float) -> str:
    return COMPASS8[int(((bearing + 22.5) % 360) // 45)]


def approach_edges(net: sumolib.net.Net) -> dict[str, str]:
    """Logical approach id -> inbound edge id at the target junction.

    Rule: each inbound edge goes to the arm of `ARM_BEARINGS` nearest to the bearing from the junction to the
    edge's far (upstream) end. The cross street has two names (Hoang Minh Giam, Nguyen Tuan), so names cannot pair
    the arms; the bearing rule does not depend on them.
    """
    node = target_node(target_tls(net))
    return _arm_edges(node, inbound_edges(node),
                      lambda e: _straight_chain(e, upstream=True)[-1].getFromNode().getCoord(), "inbound")


def exit_edges(net: sumolib.net.Net) -> dict[str, str]:
    """Logical exit id (`<approach id of the same arm>_out`) -> outbound edge id; same bearing rule as
    `approach_edges`, applied to the far (downstream) end of each outbound edge."""
    node = target_node(target_tls(net))
    arms = _arm_edges(node, outbound_edges(node),
                      lambda e: _straight_chain(e, upstream=False)[-1].getToNode().getCoord(), "outbound")
    return {f"{k}_out": v for k, v in arms.items()}


def _angle_diff(a: float, b: float) -> float:
    return abs((a - b + 180.0) % 360.0 - 180.0)


def _arm_edges(node, edges: list, far_coord, kind: str) -> dict[str, str]:
    """The four named edges matched to the four arms in cyclic order (both sorted by bearing), choosing the rotation
    with the smallest total deviation from ARM_BEARINGS; each deviation must stay within ARM_MAX_DEV_DEG + 5. A tie
    (an axis-aligned cross, every edge 45 deg off: the tests' tiny nets) goes to the clockwise rotation, so W -> LVL_W,
    N -> HMG, E -> LVL_E, S -> NT. Unnamed edges (the sidewalks of apply_patches) are never arms."""
    named = [e for e in edges if e.getName()]
    if len(named) != len(ARM_BEARINGS):
        raise ValueError(f"expected {len(ARM_BEARINGS)} named {kind} edges at the target junction, found "
                         f"{[e.getID() for e in named]}")
    eb = sorted((bearing_deg(node.getCoord(), far_coord(e)), e.getID()) for e in named)
    arms = sorted(ARM_BEARINGS, key=ARM_BEARINGS.get)
    best = None
    for k in range(len(arms)):
        pairs = [(arms[(m + k) % len(arms)], b, eid) for m, (b, eid) in enumerate(eb)]
        signed = [((b - ARM_BEARINGS[a] + 180.0) % 360.0) - 180.0 for a, b, _ in pairs]
        key = (round(sum(abs(d) for d in signed), 6), 0 if sum(signed) >= 0 else 1)
        if best is None or key < best[0]:
            best = (key, pairs, signed)
    _, pairs, signed = best
    if max(abs(d) for d in signed) > ARM_MAX_DEV_DEG + 5.0:
        raise ValueError(f"{kind} edges {[(eid, round(b)) for _, b, eid in pairs]} do not fit the arms {ARM_BEARINGS}")
    out = {a: eid for a, _, eid in pairs}
    return {k: out[k] for k in ARM_BEARINGS}


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

    # signals off the arms vanish with their edges; those on the arms (inside, or at an arm's fringe end) are the
    # pedestrian crossing signals of OSM: the study keeps only the target signal (owner 2026-11-26), so all go priority
    arm_nodes = {n.getID() for e_id in keep for n in (net.getEdge(e_id).getFromNode(), net.getEdge(e_id).getToNode())}
    unset = etree.Element("nodes")
    for nid in sorted(tls_nodes & (set(removed) | arm_nodes)):
        etree.SubElement(unset, "node", id=nid, type="priority")

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
    # LVL x HMG x NT: HMG and NT turn from a dual carriageway into a two-way street a few tens of metres out, and the
    # LVL_W exit gains a lane where a side street joined; netconvert keeps those nodes. Allowed: nodes that only join
    # consecutive edges of the arm chains (straight through, no side street left) and the chains' fringe ends.
    chain_edges = {e.getID() for _, chain in _arms(net, node) for e in chain}
    left = [n.getID() for n in net.getNodes() if n is not node and n.getType() != "dead_end"
            and not all(e.getID() in chain_edges for e in n.getIncoming() + n.getOutgoing())]
    if left:
        raise RuntimeError(f"{base}: nodes left on the arms that are not part of an arm chain: {left}")
    types = {p.getType() for p in tls.getPrograms().values()}
    if types != {"static"}:
        raise RuntimeError(f"{base}: target tlLogic type {types}, expected static")


def build_base(site: Site, out: Path = NET_DIR / "base.net.xml") -> Path:
    """Build `out` (base net) from the OSM file named in the site file; return its path."""
    out = Path(out)
    osm = REPO_ROOT / site.require("source.osm_file")
    lon, lat = site.require("intersection.center_lonlat")
    radius = site.require("intersection.cut_radius_m")
    join_nodes = [str(n) for n in site.require("intersection.join_nodes")]
    typemap = Path(os.environ["SUMO_HOME"]) / "data" / "typemap" / "osmNetconvert.typ.xml"
    logs = out.parent / "logs"
    patch_dir = out.parent / "patches" / "base"

    join = etree.Element("nodes")
    etree.SubElement(join, "join", nodes=" ".join(join_nodes))
    join_file = patch_dir / "join_target.nod.xml"
    write_xml(join, join_file)
    cluster_id = "cluster_" + "_".join(sorted(join_nodes))  # netconvert's id for a joined node set

    with tempfile.TemporaryDirectory() as tmp:
        cut = Path(tmp) / "cut.net.xml"
        netconvert([
            "--osm-files", str(osm), "--type-files", str(typemap), "-n", str(join_file),
            "--keep-edges.in-geo-boundary", geo_circle(lon, lat, radius),
            "--keep-edges.by-vclass", ",".join(KEEP_VCLASSES),
            "--remove-edges.by-type", ",".join(REMOVE_TYPES),
            "--geometry.remove", "--junctions.join",
            "--tls.set", cluster_id, "--tls.default-type", "static",
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
    _set_lane_counts(site, out, patch_dir, logs)
    return out


MOVE_OFFSET_DEG = {"r": -90.0, "s": 180.0, "l": 90.0, "u": 0.0}  # exit arm bearing = approach arm bearing + offset


def _exit_arm(approach: str, move: str) -> str:
    """Arm id of the exit for `move` (r/s/l/u) from `approach`, right-hand traffic (ARM_BEARINGS)."""
    target = ARM_BEARINGS[approach] + MOVE_OFFSET_DEG[move]
    (arm,) = [a for a, b in ARM_BEARINGS.items() if _angle_diff(b, target) < ARM_MAX_DEV_DEG]
    return arm


def _site_lane_layout(net, site: Site) -> tuple[dict[str, int], etree._Element, etree._Element]:
    """numLanes per arm-chain edge and the lane-to-lane connections of every approach edge, from the site file.

    - Every edge of an arm chain gets len(lane_widths_m) lanes (OSM lane tags here predate the 2025-26 widening; owner
      counts 2026-11-26), so no lane drop sits next to the box.
    - Approach edges get explicit lane-level connections from `lane_movements` (netconvert then guesses nothing for
      them, PlainXML docs): straight lanes map in order onto the straight exit's lanes (from the right), a right turn
      onto exit lane 0, a left or U-turn onto the exit's leftmost lane. A `left_turn_banned` approach also gets its left
      from its leftmost lane, which apply_patches re-adds for `illegal_left.vclass` only (the illegal left).
    - Consecutive chain edges (same lane count) get lane k -> lane k.
    Returns (numLanes per edge, `<delete>` file for every existing connection of those edges, connection file); a
    loaded .net.xml keeps its connections, so they are deleted in one pass and re-added in the next."""
    app_map, exit_map = approach_edges(net), exit_edges(net)
    lanes: dict[str, int] = {}
    for key, mapped, upstream in (("approaches", app_map, True), ("exits", exit_map, False)):
        for i, item in enumerate(site.require(key)):
            n = len(site.require(f"{key}.{i}.lane_widths_m"))
            for edge in _straight_chain(net.getEdge(mapped[item["id"]]), upstream=upstream):
                lanes[edge.getID()] = n
    exit_lanes = {x["id"][:-len("_out")]: (exit_map[x["id"]], len(x["lane_widths_m"])) for x in site.require("exits")}
    con, delete = etree.Element("connections"), etree.Element("connections")
    for key, mapped, upstream in (("approaches", app_map, True), ("exits", exit_map, False)):
        for item in site.require(key):
            chain = _straight_chain(net.getEdge(mapped[item["id"]]), upstream=upstream)
            for a, b in zip(chain, chain[1:]):
                frm, to = (b, a) if upstream else (a, b)
                for k in range(lanes[frm.getID()]):
                    etree.SubElement(con, "connection", **{"from": frm.getID(), "to": to.getID(),
                                                           "fromLane": str(k), "toLane": str(k)})
    for eid in sorted(lanes):
        for to in net.getEdge(eid).getOutgoing():
            etree.SubElement(delete, "delete", **{"from": eid, "to": to.getID()})
    for i, a in enumerate(site.require("approaches")):
        moves = site.require(f"approaches.{i}.lane_movements")
        n = len(site.require(f"approaches.{i}.lane_widths_m"))
        if len(moves) != n:
            raise ValueError(f"{site.path}: approaches.{i}.lane_movements has {len(moves)} lanes, lane_widths_m {n}")
        if a["left_turn_banned"] and any("l" in m for m in moves):
            raise ValueError(f"{site.path}: approach {a['id']} is left_turn_banned but lane_movements lists l")
        frm = app_map[a["id"]]
        pairs = []  # (from lane, move)
        for move in ("r", "s", "l", "u"):
            pairs += [(k, move) for k in range(n) if move in moves[k]]
        if a["left_turn_banned"]:
            pairs.append((n - 1, "l"))
        for move in ("r", "s", "l", "u"):
            from_lanes = [k for k, m in pairs if m == move]
            if not from_lanes:
                continue
            to_edge, n_out = exit_lanes[_exit_arm(a["id"], move)]
            for rank, k in enumerate(from_lanes):
                to_lane = 0 if move == "r" else n_out - 1 if move in ("l", "u") else min(rank, n_out - 1)
                etree.SubElement(con, "connection", **{"from": frm, "to": to_edge, "fromLane": str(k),
                                                       "toLane": str(to_lane)})
    return lanes, delete, con


def _two_way_centre(a, b) -> list[tuple[float, float]]:
    """Centre line of a two-way street from its two directed edges, in the direction of `a`: sumolib gives each
    edge's shape at its own lane centres (spreadType right shifts them by half the OSM roadway), so the street's centre
    is the midpoint of `a` and the nearest point of `b`."""
    from sumolib.geomhelper import polygonOffsetWithMinimumDistanceToPoint, positionAtShapeOffset
    out = []
    for x, y in a.getShape():
        off = polygonOffsetWithMinimumDistanceToPoint((x, y), b.getShape(), perpendicular=False)
        qx, qy = positionAtShapeOffset(b.getShape(), off)
        out.append(((x + qx) / 2.0, (y + qy) / 2.0))
    return out


def _inner_boundary(carriageway, other) -> list[tuple[float, float]]:
    """Inner (median-side) boundary of a one-way carriageway, in its direction: each point of the OSM centre line moved
    towards the other carriageway by half the OSM roadway width (its lanes as netconvert built them from OSM), at most
    half the distance between them. The median between the two boundaries is then as wide as OSM draws it (the gap
    between the two OSM roadways), tapering to 0 where the carriageways join the two-way street."""
    from sumolib.geomhelper import polygonOffsetWithMinimumDistanceToPoint, positionAtShapeOffset
    half_w = sum(ln.getWidth() for ln in carriageway.getLanes()) / 2.0
    out = []
    for x, y in carriageway.getShape():
        off = polygonOffsetWithMinimumDistanceToPoint((x, y), other.getShape(), perpendicular=False)
        qx, qy = positionAtShapeOffset(other.getShape(), off)
        d = math.hypot(qx - x, qy - y)
        k = 0.0 if d == 0 else min(half_w, d / 2.0) / d
        out.append((x + (qx - x) * k, y + (qy - y) * k))
    return out


def _merge_transitions(net) -> etree._Element | None:
    """Edge patch that removes the nodes where an arm turns from two one-way carriageways into a two-way street (HMG
    83 m, NT 70 m from the centre at LVL x HMG x NT): such a node carries both the inbound and the outbound chain, so
    netconvert kept it as a junction of its own (a second junction in sumo-gui; the study models one, owner
    2026-11-26). Each direction becomes one edge: the edge at the target junction keeps its id (the site file names
    it) and runs from the arm's fringe. Its shape is its inner (median-side) boundary with `spreadType="right"`: the
    two-way street's line upstream, the OSM carriageway moved to its median edge near the junction (`_inner_boundary`),
    so the median OSM draws over the last stretch stays (owner 2026-11-26: HMG and NT have one) and the 3 + 3 lanes do
    not overlap. With `center` on the OSM lines they overlapped by 1.2 m at the HMG stop line and fully on the two-way
    part, and the HMG illegal lefts waited inside the NT through lanes (B0 REF_n1126: 165 collisions/h)."""
    node = target_node(target_tls(net))
    ins = {e.getID() for e in inbound_edges(node) for e in _straight_chain(e, upstream=True)}
    outs = {e.getID() for e in outbound_edges(node) for e in _straight_chain(e, upstream=False)}
    root, found = etree.Element("edges"), False
    for n in net.getNodes():
        ids = {e.getID() for e in n.getIncoming() + n.getOutgoing()}
        if n is node or not ids <= ins | outs:
            continue
        through = all(sum(e.getID() in c for e in side) == 1 for c in (ins, outs)
                      for side in (n.getIncoming(), n.getOutgoing()))
        if not through:  # e.g. the fringe end of a two-way street: one direction starts there, the other ends
            continue
        (a_in,) = [e for e in n.getIncoming() if e.getID() in ins]     # two-way part, fringe -> n
        (b_in,) = [e for e in n.getOutgoing() if e.getID() in ins]     # carriageway, n -> junction
        (a_out,) = [e for e in n.getIncoming() if e.getID() in outs]   # carriageway, junction -> n
        (b_out,) = [e for e in n.getOutgoing() if e.getID() in outs]   # two-way part, n -> fringe
        # inner boundaries (spreadType right: lanes to the right of the shape): the two-way street's line upstream,
        # then each OSM carriageway moved to its median edge, so the median of the last stretch stays (owner
        # 2026-11-26: HMG and NT both have a median near the junction)
        street = _two_way_centre(a_in, b_out)                                  # fringe -> n
        in_shape = street + _inner_boundary(b_in, a_out)[1:]                    # fringe -> junction
        out_shape = _inner_boundary(a_out, b_in)[:-1] + street[::-1]            # junction -> fringe
        shape = lambda pts: " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)
        etree.SubElement(root, "delete", id=a_in.getID())
        etree.SubElement(root, "delete", id=b_out.getID())
        etree.SubElement(root, "edge", id=b_in.getID(), **{"from": a_in.getFromNode().getID(),
                                                          "to": b_in.getToNode().getID()},
                         shape=shape(in_shape), spreadType="right")
        etree.SubElement(root, "edge", id=a_out.getID(), **{"from": a_out.getFromNode().getID(),
                                                           "to": b_out.getToNode().getID()},
                         shape=shape(out_shape), spreadType="right")
        found = True
    return root if found else None


def _set_lane_counts(site: Site, base: Path, patch_dir: Path, logs: Path) -> None:
    """Pass 3: lane counts and approach lane connections from the site file (`_site_lane_layout`), then pass 4:
    `--geometry.remove` again (a lane-count change left near-zero-length edges, e.g. 0.2 m on the LVL_W exit)."""
    merge = _merge_transitions(sumolib.net.readNet(str(base), withPrograms=True))
    if merge is not None:  # pass 3a: one edge per arm direction, no second junction on HMG / NT
        merge_file = patch_dir / "merge_transitions.edg.xml"
        write_xml(merge, merge_file)
        with tempfile.TemporaryDirectory() as tmp:
            merged = Path(tmp) / "merged.net.xml"
            netconvert(["-s", str(base), "-e", str(merge_file), "--output.street-names", "--output.original-names",
                        "--no-internal-links", "false", "-o", str(merged)], logs / "netconvert_merge.log")
            base.write_bytes(merged.read_bytes())
    net = sumolib.net.readNet(str(base), withPrograms=True)
    tls_id = target_tls(net).getID()  # deleting every approach connection drops the program; pass b sets it again
    lanes, delete, con = _site_lane_layout(net, site)
    root = etree.Element("edges")
    for eid, n in sorted(lanes.items()):
        if net.getEdge(eid).getLaneNumber() != n:
            etree.SubElement(root, "edge", id=eid, numLanes=str(n))
    lanes_file, del_file, con_file = (patch_dir / "lane_counts.edg.xml", patch_dir / "lane_layout_delete.con.xml",
                                      patch_dir / "lane_layout.con.xml")
    write_xml(root, lanes_file)
    write_xml(delete, del_file)
    write_xml(con, con_file)
    # internal lanes must exist (junction_geometry, box waiting): a pass that saw an edge without connections records
    # no-internal-links=true in the net and the next -s pass inherits it (checked 2026-11-26), so set it every pass
    names = ["--output.street-names", "--output.original-names", "--no-internal-links", "false"]
    with tempfile.TemporaryDirectory() as tmp:
        a, b, tmp_out = Path(tmp) / "a.net.xml", Path(tmp) / "b.net.xml", Path(tmp) / "base.net.xml"
        netconvert(["-s", str(base), "-e", str(lanes_file), "-x", str(del_file), *names, "-o", str(a)],
                   logs / "netconvert_lanes.log")
        netconvert(["-s", str(a), "-x", str(con_file), "--tls.set", tls_id, "--tls.default-type", "static", *names,
                    "-o", str(b)], logs / "netconvert_lanes_con.log")
        netconvert(["-s", str(b), "--geometry.remove", *names, "-o", str(tmp_out)], logs / "netconvert_lanes_merge.log")
        base.write_bytes(tmp_out.read_bytes())
    _check_base(base)
    got = sumolib.net.readNet(str(base))
    for key, derive in (("approaches", approach_edges), ("exits", exit_edges)):
        mapped = derive(got)
        for i, item in enumerate(site.require(key)):
            n = len(site.require(f"{key}.{i}.lane_widths_m"))
            if got.getEdge(mapped[item["id"]]).getLaneNumber() != n:
                raise RuntimeError(f"{base}: {item['id']} has {got.getEdge(mapped[item['id']]).getLaneNumber()} lanes, "
                                   f"site file {n}")


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
    inbound_chain = {x.getID() for e in inbound_edges(node) for x in _straight_chain(e, upstream=True)}
    rows = []
    for e in n.getEdges(withInternal=False):
        inbound = e.getID() in inbound_chain  # an arm may be several edges long (HMG, NT)
        far = e.getFromNode() if inbound else e.getToNode()
        side = compass8(bearing_deg(node.getCoord(), far.getCoord()))
        rows.append(((not inbound, COMPASS8.index(side), e.getID()), {
            "edge_id": e.getID(), "name": e.getName(),
            "direction": f"in from {side}" if inbound else f"out to {side}",
            "n_lanes": e.getLaneNumber(), "length_m": round(e.getLength(), 1),
            "connections": _conn_summary(n, e) if e.getToNode() is node else "",
        }))
    return pd.DataFrame([r for _, r in sorted(rows, key=lambda kv: kv[0])], columns=EDGE_TABLE_COLUMNS)

