"""Site network (PLAN Phase 1.4): base net + plain-XML patches generated from the site file.

`netconvert -s base.net.xml -e lanes.edg.xml -x turns.con.xml -i signal.tll.xml -o <site net>`

- `lanes.edg.xml`: `approaches[].lane_widths_m` on each approach edge and `exits[].lane_widths_m` on each
  outbound edge (lane index 0 = rightmost). netconvert gives an internal lane the width of its outbound lane
  (Task 4 operator report), so the exit widths also set the widths inside the junction box (ruling R21).
- `turns.con.xml`: for `left_turn_banned: true` every left (`dir` l/L) connection of the approach is
  deleted and re-added with `allow="<illegal_left.vclass>"` (connection-level permissions, PlainXML docs:
  "set custom permissions independent of from-lane and to-lane permissions"). Same for
  `u_turn_banned: true` with the turnaround (`dir` t).
  `continuous_right_lane: true` (PLAN 0: every approach has a continuous right-turn lane, the outermost one;
  modelled as the existing lane 0, no lane added): every straight connection from lane 0 is deleted and
  re-added: with `right_lane_separator` `none` or `paint` with `allow="<violator_classes.moto>
  <violator_classes.car>"` (custom1 custom2: PLAN behaviour 6, violators going straight from the right-turn lane);
  with `bollards` (Viktor, field visit: a physical separator) with `disallow="all"`, i.e. nobody goes straight
  from lane 0. The connection is kept (not deleted) so no TLS link index moves (checked: its internal lane then
  has no permissions). The right turn from lane 0 stays open to everyone.
- `signal.tll.xml`: static program from `signal.phases`. Every link is listed with an explicit
  `linkIndex`, so the delete/re-add above cannot shuffle the state string. A movement in
  `green_movements` is `G` for straight/right and `g` (yield) for left/turnaround; `yellow_movements`
  are `y`; everything else is `r`. The right-turn links of `continuous_right_lane` approaches are not signal
  controlled: `g` (green, yield to foes) in every phase, whatever the phase lists say (a right turn on red is
  no violation, PLAN 0).
- `split.edg.xml` + `bollards.edg.xml` (Phase 3A, ruling R39): with `right_lane_separator: bollards` the approach
  edge is split at `stop line - bollard_length_m`; the downstream part keeps the approach edge id (so every
  stop-line lookup, TLS link and turns.con.xml entry stays valid), the upstream part is `<edge>.up`, the split node
  `<edge>.bollard`. On the bollard edge lane 0 gets `changeLeft="emergency"` and lane 1 `changeRight="emergency"`:
  no lane change between the continuous right-turn lane and the through lanes (`"ignoring"`, the documented
  strongest value, is dropped silently by netconvert 1.27; no emergency vehicle exists here; Phase 3A).
- Sidewalk (PLAN 1.4, Phase 3B topology c with priority, ruling R39) on the approaches of `f2_measured_approaches`
  (null or empty: none): the approach is also split at `stop line - sidewalk_start_m` (node `<edge>.sidewalk_start`,
  `<edge>.up` upstream of it, `<edge>.mid` between it and the bollard node); `sidewalk.edg.xml` adds the one-lane
  edge `<edge>.sidewalk` from that node to the target junction (`allow="custom1"`, width `sidewalk_width_m`, speed
  `sidewalk_speed_mps`, priority one above the approach, unnamed so it is never taken for an approach, geometry =
  lane 0 shifted right, ending edge to edge beside lane 0 at the stop line, see SIDEWALK_JOG_M; the build checks
  that the sidewalk links are foes of the lane-0 right turn). `sidewalk.con.xml`: `<edge>.up` lanes i -> i
  onwards, lane 0 also -> the sidewalk; sidewalk -> lane 0 of the approach's right and straight exits. The two
  sidewalk links are TLS links appended after the road links (pinned in signal.tll.xml, so no road link index
  moves): right = the approach's right-turn state (`g` in every phase on a continuous right lane), straight = the
  approach's straight state (`G` in its green: the road yields to riders at the stop line; a yielding `g` jams, 3B).
  Use of the sidewalk is a TraCI route choice only (`queue_space_seeking`, option `sidewalk`).
- Split positions are measured along the raw edge geometry from the stop line. Junction shapes change with the
  patched widths and with the sidewalk node, so the build reruns netconvert (at most `SPLIT_PASSES` times), each
  time shifting every split by the remaining error, until every realised distance (stop line to the start of the
  segment downstream of the split) is within `SPLIT_TOL_M` of the site value; otherwise it raises.
- `illegal_left.mode` (PLAN Phase 3 decision, `native | box_edge`): `native` = the illegal lefts wait at the
  internal junction netconvert builds on their link (no extra patch). `box_edge` (an explicit waiting edge
  with its own signal link) is not implemented: Phase 3 measured enough native capacity
  (docs/research/phase3_box_capacity.md), so it raises.

A required `null` in the site file raises `MissingFieldDataError` before anything is written. A
literature-proxy site file builds, with a loud `ProxySiteWarning`.
"""

from __future__ import annotations

import math
import warnings
from pathlib import Path

import sumolib
from lxml import etree
from sumolib.geomhelper import move2side, polygonOffsetWithMinimumDistanceToPoint, positionAtShapeOffset

from thesis_sumo.config import Site
from thesis_sumo.net.build_net import (
    inbound_edges,
    netconvert,
    outbound_edges,
    target_node,
    target_tls,
    write_xml,
)

SITE_NET_NAMES = {"MEASURED": "site.net.xml", "LITERATURE_PROXY": "site.proxy.net.xml"}
MOVEMENTS = ("r", "s", "l", "t")
ILLEGAL_LEFT_MODES = ("native", "box_edge")
RIGHT_LANE_SEPARATORS = ("none", "paint", "bollards")  # PLAN 0 site template
DIR_TO_MOVEMENT = {"s": "s", "r": "r", "R": "r", "l": "l", "L": "l", "t": "t"}  # SUMO connection dir codes
PRIORITY_MOVEMENTS = ("s", "r")  # green = G; other movements yield (g)
UNCONTROLLED_STATE = "g"  # continuous right turn: green in every phase, yields to foes (PLAN 1.4)
NO_CHANGE = "emergency"  # changeLeft/changeRight value: only vClass emergency (absent) may change (Phase 3A)
SPLIT_TOL_M = 0.2  # realised bollard / sidewalk-start distance vs the site value
SPLIT_PASSES = 5  # netconvert passes at most: moving a split node reshapes the junctions, so the lengths are coupled
# Sidewalk geometry (not field data): its centre runs SIDEWALK_JOG_M further out than "beside lane 0" and jogs back
# over the last SIDEWALK_JOG_LEN_M to end exactly beside lane 0 at the stop line. Checked on LVL_W (F2-behaviours
# review): ending parallel at the corner without the jog (0 m) lets the sidewalk take netconvert's turnaround pairing of
# the approach's own exit (>= 160 deg; the road U-turn then gets dir "r"); a bend that ended ~0.25 m from lane 0's end
# overlapped lane 0 and the sidewalk links were no foes of the lane-0 right turn (junction collisions); 3-4 m moved the
# LVL_W stop line 3.6 m. 1-2 m: links of the sidewalk and of lane 0 are foes (checked in _check_site_net), every road
# link keeps its dir, stop lines within 0.1 m of the unpatched net for LVL_W / HDT_S (LVL_E -0.7 m, HDT_N +1.6 m:
# scenario/net/stopline_shift.csv written by thesis_sumo.net.build). With the second sidewalk on LVL_E (2026-10-28)
# 2.0 m moved the LVL_E stop line +3.9 m; 1.0 and 1.5 m give -0.7 m there and leave the other three unchanged.
SIDEWALK_JOG_M, SIDEWALK_JOG_LEN_M = 1.5, 6.0
UP, MID, SIDEWALK = ".up", ".mid", ".sidewalk"  # suffixes of the split / added edges
# sumo-gui highlight of the continuous right-turn lanes (write_gui_highlight; display only). Layer checked in sumo-gui
# 1.27 (2026-10-28 screenshots): at 1 the polygon is drawn under the road and only shows beside lane 0, at 10 it covers
# lane 0 and the vehicles stay on top
GUI_HIGHLIGHT_SUFFIX, GUI_HIGHLIGHT_COLOR, GUI_HIGHLIGHT_LAYER = ".gui.add.xml", "255,215,0", "10"
BOLLARD_NODE, SIDEWALK_NODE = ".bollard", ".sidewalk_start"


class ProxySiteWarning(UserWarning):
    """The network is being built from literature-proxy values, not field measurements."""


def site_net_name(site: Site) -> str:
    return SITE_NET_NAMES[site.source]


def movement_of(direction: str) -> str:
    """SUMO connection `dir` -> movement code used in the site file (r, s, l, t)."""
    try:
        return DIR_TO_MOVEMENT[direction]
    except KeyError:
        raise ValueError(f"connection dir {direction!r} has no movement code (expected one of "
                         f"{sorted(DIR_TO_MOVEMENT)})") from None


def site_values(site: Site) -> dict:
    """Every site value the network needs; raises MissingFieldDataError on the first required null."""
    approaches = []
    for i, a in enumerate(site.require("approaches")):
        approaches.append({
            "id": site.require(f"approaches.{i}.id"),
            "edge": site.require(f"approaches.{i}.edge"),
            "lane_widths_m": site.require(f"approaches.{i}.lane_widths_m"),
            "left_turn_banned": site.require(f"approaches.{i}.left_turn_banned"),
            "u_turn_banned": site.require(f"approaches.{i}.u_turn_banned"),
            "continuous_right_lane": site.require(f"approaches.{i}.continuous_right_lane"),
        })
        approaches[-1]["bollard_length_m"] = approaches[-1]["sidewalk"] = None
        if approaches[-1]["continuous_right_lane"]:
            sep = approaches[-1]["right_lane_separator"] = site.require(f"approaches.{i}.right_lane_separator")
            if sep not in RIGHT_LANE_SEPARATORS:
                raise ValueError(f"{site.path}: approaches.{i}.right_lane_separator must be one of "
                                 f"{RIGHT_LANE_SEPARATORS}, got {sep!r}")
            if sep == "bollards":
                approaches[-1]["bollard_length_m"] = _positive(site, f"approaches.{i}.bollard_length_m")
    exits = [{"id": site.require(f"exits.{i}.id"), "edge": site.require(f"exits.{i}.edge"),
              "lane_widths_m": site.require(f"exits.{i}.lane_widths_m")} for i in range(len(site.require("exits")))]
    vals = {
        "approaches": approaches,
        "exits": exits,
        "signal_type": site.require("signal.type"),
        "cycle_s": site.require("signal.cycle_s"),
        "phases": site.require("signal.phases"),
        "illegal_left": site.require("illegal_left.approaches"),
        "vclass": site.require("illegal_left.vclass"),
        "illegal_left_mode": site.require("illegal_left.mode"),
        "violators": (site.require("violator_classes.moto"), site.require("violator_classes.car")),
    }
    if vals["vclass"] != vals["violators"][0]:
        raise ValueError(f"{site.path}: illegal_left.vclass {vals['vclass']!r} must be violator_classes.moto "
                         f"{vals['violators'][0]!r}")
    ids = [a["id"] for a in approaches]
    for app in site.get("f2_measured_approaches") or []:  # null = none chosen yet: no sidewalk
        if app not in ids:
            raise ValueError(f"{site.path}: f2_measured_approaches {app!r} is not an approach id {ids}")
        i = ids.index(app)
        sw = approaches[i]["sidewalk"] = {k: _positive(site, f"approaches.{i}.{k}")
                                          for k in ("sidewalk_width_m", "sidewalk_start_m", "sidewalk_speed_mps")}
        if sw["sidewalk_start_m"] <= (approaches[i]["bollard_length_m"] or 0.0):
            raise ValueError(f"{site.path}: approaches.{i}.sidewalk_start_m {sw['sidewalk_start_m']} must exceed "
                             f"bollard_length_m {approaches[i]['bollard_length_m']} (the sidewalk starts upstream)")
    if vals["signal_type"] != "static":
        raise ValueError(f"{site.path}: signal.type must be 'static' (PLAN 1.1), got {vals['signal_type']!r}")
    if vals["illegal_left_mode"] not in ILLEGAL_LEFT_MODES:
        raise ValueError(f"{site.path}: illegal_left.mode must be one of {ILLEGAL_LEFT_MODES}, "
                         f"got {vals['illegal_left_mode']!r}")
    if vals["illegal_left_mode"] == "box_edge":
        raise NotImplementedError(f"{site.path}: illegal_left.mode box_edge (explicit waiting edge, PLAN Phase 3 b) "
                                  f"is not implemented; Phase 3 chose native (docs/research/phase3_box_capacity.md)")
    banned = {a["id"] for a in approaches if a["left_turn_banned"]}
    unbanned = [a for a in vals["illegal_left"] if a not in banned]
    if unbanned:
        raise ValueError(f"{site.path}: illegal_left.approaches {unbanned} are not left_turn_banned; "
                         f"an illegal left needs a ban on that approach")
    return vals


def _positive(site: Site, key: str) -> float:
    value = site.require(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise ValueError(f"{site.path}: {key} must be a positive number, got {value!r}")
    return float(value)


def _parse_movement(mv: str) -> tuple[str, str]:
    app, sep, code = mv.partition(":")
    if not sep or code not in MOVEMENTS:
        raise ValueError(f"movement {mv!r} must be '<approach_id>:<dir>' with dir in {MOVEMENTS}")
    return app, code


def phase_states(links: list[tuple[str, str]], phases: list[dict], cycle_s: float,
                 uncontrolled: frozenset[tuple[str, str]] = frozenset()) -> list[str]:
    """State string per phase; `links[i]` = (approach_id, movement) of tl link index i. Links in `uncontrolled`
    (continuous right turns) are `g` in every phase."""
    total = sum(p["duration_s"] for p in phases)
    if not math.isclose(total, cycle_s):
        raise ValueError(f"signal phase durations sum to {total} s, signal.cycle_s is {cycle_s} s")
    existing = set(links)
    states = []
    for p in phases:
        green = {_parse_movement(m) for m in p["green_movements"]}
        yellow = {_parse_movement(m) for m in p["yellow_movements"]}
        for app, code in green | yellow:
            if (app, code) not in existing:
                raise ValueError(f"phase {p['name']!r}: movement {app}:{code} matches no link at the target junction")
        both = green & yellow
        if both:
            raise ValueError(f"phase {p['name']!r}: {sorted(both)} listed as both green and yellow")
        states.append("".join(
            UNCONTROLLED_STATE if (app, code) in uncontrolled
            else ("G" if code in PRIORITY_MOVEMENTS else "g") if (app, code) in green
            else "y" if (app, code) in yellow else "r"
            for app, code in links))
    return states


def _links(net, approach_of: dict[str, str]) -> list:
    """Connections of the target TLS ordered by link index, checked to be 0..n-1."""
    tls = target_tls(net)
    by_index = {}
    for in_lane, out_lane, idx in tls.getConnections():
        (conn,) = [c for c in in_lane.getOutgoing() if c.getToLane() == out_lane]
        if in_lane.getEdge().getID() not in approach_of:
            raise ValueError(f"link {idx} comes from edge {in_lane.getEdge().getID()}, which is no approach edge")
        by_index[idx] = conn
    if sorted(by_index) != list(range(len(by_index))):
        raise ValueError(f"traffic light {tls.getID()} link indices are not contiguous: {sorted(by_index)}")
    return [by_index[i] for i in range(len(by_index))]


def _lane_patch(net, vals: dict) -> etree._Element:
    root = etree.Element("edges")
    for kind, a in [("approach", a) for a in vals["approaches"]] + [("exit", x) for x in vals["exits"]]:
        n = net.getEdge(a["edge"]).getLaneNumber()
        if len(a["lane_widths_m"]) != n:
            raise ValueError(f"{kind} {a['id']}: {len(a['lane_widths_m'])} lane widths for {n} lanes on {a['edge']}")
        e = etree.SubElement(root, "edge", id=a["edge"])
        for i, w in enumerate(a["lane_widths_m"]):
            etree.SubElement(e, "lane", index=str(i), width=f"{float(w):.2f}")
    return root


def _turn_patch(net, vals: dict) -> etree._Element:
    root = etree.Element("connections")
    for a in vals["approaches"]:
        conns = sorted((c for cs in net.getEdge(a["edge"]).getOutgoing().values() for c in cs),
                       key=lambda c: (c.getFromLane().getIndex(), c.getTo().getID()))
        banned = {"l"} if a["left_turn_banned"] else set()
        banned |= {"t"} if a["u_turn_banned"] else set()
        if banned:
            root.append(etree.Comment(f" {a['id']}: banned {sorted(banned)}; re-added for {vals['vclass']} only "))
            _readd(root, a["edge"], [c for c in conns if movement_of(c.getDirection()) in banned], allow=vals["vclass"])
        if a["continuous_right_lane"]:
            closed = a["right_lane_separator"] == "bollards"
            perm = {"disallow": "all"} if closed else {"allow": " ".join(vals["violators"])}
            root.append(etree.Comment(f" {a['id']}: lane 0 = continuous right-turn lane, separator "
                                      f"{a['right_lane_separator']}; straight re-added with {perm} "))
            _readd(root, a["edge"], [c for c in conns if c.getFromLane().getIndex() == 0
                                     and movement_of(c.getDirection()) == "s"], **perm)
    return root


def _readd(root: etree._Element, edge: str, conns: list, **perm: str) -> None:
    """Delete `conns` and add them back with connection-level permissions `perm` (allow= or disallow=)."""
    for c in conns:
        key = dict(**{"from": edge}, to=c.getTo().getID(),
                   fromLane=str(c.getFromLane().getIndex()), toLane=str(c.getToLane().getIndex()))
        etree.SubElement(root, "delete", **key)
        etree.SubElement(root, "connection", **key, **perm)


def segments(a: dict) -> list[str]:
    """Edge ids of a patched approach from upstream to the stop line (the last one keeps the approach edge id)."""
    e = a["edge"]
    return [e + UP] * bool(a["sidewalk"] or a["bollard_length_m"]) + [e + MID] * bool(
        a["sidewalk"] and a["bollard_length_m"]) + [e]


def _cuts(a: dict) -> list[tuple[str, float]]:
    """(split node id, distance from the stop line), upstream first; cut k separates segments k and k + 1."""
    cuts = [(a["edge"] + SIDEWALK_NODE, a["sidewalk"]["sidewalk_start_m"])] if a["sidewalk"] else []
    return cuts + ([(a["edge"] + BOLLARD_NODE, a["bollard_length_m"])] if a["bollard_length_m"] else [])


def _split_patch(net, vals: dict, shift: dict[str, float]) -> etree._Element:
    """`<split>`s at the site distances (+ `shift`) upstream of the stop line, with negative positions measured from
    the end of the raw edge geometry (which reaches into the junction)."""
    root = etree.Element("edges")
    for a in vals["approaches"]:
        e = net.getEdge(a["edge"])
        raw = e.getRawShape()
        tail = sumolib.geomhelper.polyLength(raw) - polygonOffsetWithMinimumDistanceToPoint(e.getShape()[-1], raw)
        segs = segments(a)
        for k, (node, dist) in enumerate(_cuts(a)):
            el = etree.SubElement(root, "edge", id=a["edge"] if k == 0 else segs[k])
            etree.SubElement(el, "split", pos=f"{-(tail + dist + shift.get(node, 0.0)):.2f}", id=node,
                             idBefore=segs[k], idAfter=segs[k + 1])
    return root


def _bollard_patch(vals: dict) -> etree._Element:
    root = etree.Element("edges")
    for a in vals["approaches"]:
        if a["bollard_length_m"]:
            e = etree.SubElement(root, "edge", id=a["edge"])
            etree.SubElement(e, "lane", index="0", changeLeft=NO_CHANGE)
            etree.SubElement(e, "lane", index="1", changeRight=NO_CHANGE)
    return root


def _exit_of(net, a: dict, movement: str) -> str:
    (to,) = {c.getTo().getID() for cs in net.getEdge(a["edge"]).getOutgoing().values() for c in cs
             if movement_of(c.getDirection()) == movement}
    return to


def _sidewalk_patches(net, vals: dict, node_id: str,
                      shift: dict[str, float]) -> tuple[etree._Element, etree._Element, list[tuple]]:
    """(sidewalk.edg.xml, sidewalk.con.xml, sidewalk TLS links as (approach, movement, from, to, fromLane, toLane));
    the sidewalk shape starts where the (shifted) sidewalk_start split is."""
    edges, cons, links = etree.Element("edges"), etree.Element("connections"), []
    for a in vals["approaches"]:
        sw = a["sidewalk"]
        if not sw:
            continue
        shape = net.getEdge(a["edge"]).getLane(0).getShape()
        start = sumolib.geomhelper.polyLength(shape) - sw["sidewalk_start_m"] - shift.get(a["edge"] + SIDEWALK_NODE, 0.0)
        acc, pts = 0.0, [positionAtShapeOffset(shape, start)]
        for p0, p1 in zip(shape, shape[1:]):
            acc += math.dist(p0, p1)
            if acc > start:
                pts.append(p1)
        beside = a["lane_widths_m"][0] / 2 + sw["sidewalk_width_m"] / 2  # centre offset: edge to edge with lane 0
        end = move2side(pts[-2:], beside)[-1]  # positive = to the right
        pts = move2side(pts, beside + SIDEWALK_JOG_M)
        (x0, y0), (x1, y1) = pts[-2], pts[-1]
        d = math.dist(pts[-2], pts[-1])
        pts[-1:] = [(x1 - SIDEWALK_JOG_LEN_M * (x1 - x0) / d, y1 - SIDEWALK_JOG_LEN_M * (y1 - y0) / d), end]
        swe = a["edge"] + SIDEWALK
        edges.append(etree.Comment(f" {a['id']}: sidewalk (Phase 3B topology c), custom1 only "))
        etree.SubElement(edges, "edge", id=swe, **{"from": a["edge"] + SIDEWALK_NODE}, to=node_id, numLanes="1",
                         priority=str(net.getEdge(a["edge"]).getPriority() + 1), allow="custom1",
                         width=f"{sw['sidewalk_width_m']:.2f}", speed=f"{sw['sidewalk_speed_mps']:.2f}",
                         spreadType="center", shape=" ".join(f"{x:.2f},{y:.2f}" for x, y in pts))
        up, nxt = segments(a)[0], segments(a)[1]
        for i in range(net.getEdge(a["edge"]).getLaneNumber()):
            etree.SubElement(cons, "connection", **{"from": up}, to=nxt, fromLane=str(i), toLane=str(i))
        etree.SubElement(cons, "connection", **{"from": up}, to=swe, fromLane="0", toLane="0")
        for mv in ("r", "s"):
            to = _exit_of(net, a, mv)
            etree.SubElement(cons, "connection", **{"from": swe}, to=to, fromLane="0", toLane="0")
            links.append((a["id"], mv, swe, to, 0, 0))
    return edges, cons, links


def _signal_patch(tls_id: str, links: list[tuple], vals: dict, states: list[str]) -> etree._Element:
    """`links[i]` = (from edge, to edge, fromLane, toLane) of TLS link index i."""
    root = etree.Element("tlLogics")
    logic = etree.SubElement(root, "tlLogic", id=tls_id, type="static", programID="0", offset="0")
    for p, state in zip(vals["phases"], states):
        etree.SubElement(logic, "phase", duration=str(p["duration_s"]), state=state, name=p["name"])
    for i, (frm, to, fl, tl) in enumerate(links):
        etree.SubElement(root, "connection", **{"from": frm}, to=to, fromLane=str(fl), toLane=str(tl),
                         tl=tls_id, linkIndex=str(i))
    return root


def _key(c) -> tuple:
    return c.getFrom().getID(), c.getTo().getID(), c.getFromLane().getIndex(), c.getToLane().getIndex()


def _realised(net, vals: dict) -> dict[str, tuple[float, float]]:
    """split node -> (site distance, distance from the stop line to the start of the segment downstream of it)."""
    out = {}
    for a in vals["approaches"]:
        segs, d, start = segments(a), 0.0, {}
        for j in range(len(segs) - 1, -1, -1):
            d += net.getEdge(segs[j]).getLane(0).getLength()
            start[j] = d
            if j:
                (c,) = [c for c in net.getEdge(segs[j - 1]).getOutgoing()[net.getEdge(segs[j])]
                        if c.getFromLane().getIndex() == 0]
                d += net.getLane(c.getViaLaneID()).getLength() if c.getViaLaneID() else 0.0
        for k, (node, dist) in enumerate(_cuts(a)):
            out[node] = (dist, start[k + 1])
    return out


def _check_site_net(out: Path, links_before: list[tuple], dirs_before: list[str], states: list[str],
                    vals: dict) -> None:
    net = sumolib.net.readNet(str(out), withPrograms=True, withInternal=True)
    approach_of = {a["edge"]: a["id"] for a in vals["approaches"]}
    approach_of.update({a["edge"] + SIDEWALK: a["id"] for a in vals["approaches"] if a["sidewalk"]})
    after = _links(net, approach_of)
    if [_key(c) for c in after] != links_before:
        raise RuntimeError(f"{out}: link indices changed while patching")
    changed = [(i, d, c.getDirection()) for i, (c, d) in enumerate(zip(after, dirs_before)) if c.getDirection() != d]
    if changed:
        raise RuntimeError(f"{out}: link directions changed while patching (index, before, after): {changed}")
    node = target_node(target_tls(net))
    for sw in (c for c in after if c.getFrom().getID().endswith(SIDEWALK)):  # riders leave beside lane 0: its links
        for road in (c for c in after if c.getFrom().getID() + SIDEWALK == sw.getFrom().getID()  # are their foes
                     and c.getFromLane().getIndex() == 0 and movement_of(c.getDirection()) == "r"):
            if not node.areFoes(node.getLinkIndex(sw), node.getLinkIndex(road)):
                raise RuntimeError(f"{out}: sidewalk link {_key(sw)} is no foe of the lane-0 right turn {_key(road)}")
    (program,) = target_tls(net).getPrograms().values()
    got = [p.state for p in program.getPhases()]
    if program.getType() != "static" or got != states:
        raise RuntimeError(f"{out}: program {program.getType()} {got} differs from the generated one {states}")


def gui_highlight_name(site: Site) -> str:
    return site_net_name(site).removesuffix(".net.xml") + GUI_HIGHLIGHT_SUFFIX


def write_gui_highlight(site: Site, net_path: Path, out: Path) -> Path:
    """sumo-gui only: paints lane 0 yellow where it is the continuous right-turn lane, i.e. beside the separator (lane 0
    of the bollard segment, the approach edge after the split), and its right-turn path through the junction. No lane is
    added: filled `<poly>` additionals over the existing lane 0 (sumo.dlr.de/docs/Simulation/Shapes.html: fill, layer);
    the simulation never loads them, so they cannot change a run."""
    vals = site_values(site)
    net = sumolib.net.readNet(str(net_path), withInternal=True)
    root = etree.Element("additional")
    for a in vals["approaches"]:
        if not (a["continuous_right_lane"] and a["bollard_length_m"]):
            continue
        lane0 = net.getEdge(a["edge"]).getLane(0)
        lanes = [lane0]
        for c in lane0.getOutgoing():
            if movement_of(c.getDirection()) != "r" or not c.getViaLaneID():
                continue
            via = net.getLane(c.getViaLaneID())
            while via.getEdge().getFunction() == "internal":  # the turn may run over an internal junction
                lanes.append(via)
                via = via.getOutgoing()[0].getToLane()
        for lane in lanes:  # filled outline of the lane: its centre line shifted half a width to each side
            shape, half = lane.getShape(), lane.getWidth() / 2
            outline = move2side(shape, -half) + move2side(shape, half)[::-1]
            etree.SubElement(root, "poly", id=f"continuous_right_{lane.getID()}", type="continuous_right",
                             color=GUI_HIGHLIGHT_COLOR, fill="1", layer=GUI_HIGHLIGHT_LAYER,
                             shape=" ".join(f"{x:.2f},{y:.2f}" for x, y in outline))
    write_xml(root, out)
    return out


def build_site_net(site: Site, base: Path, out: Path) -> Path:
    """Generate the patches from `site`, apply them to `base`, write `out`; return `out`."""
    vals = site_values(site)
    if site.source == "LITERATURE_PROXY":
        warnings.warn(ProxySiteWarning(
            f"building {Path(out).name} from LITERATURE_PROXY site file {site.path}: lane widths, turn bans "
            f"and the signal plan are literature/assumed values, NOT field measurements"), stacklevel=2)
    base, out = Path(base), Path(out)
    net = sumolib.net.readNet(str(base), withPrograms=True)
    tls = target_tls(net)
    inbound = {e.getID() for e in inbound_edges(target_node(tls))}
    approach_of = {a["edge"]: a["id"] for a in vals["approaches"]}
    if set(approach_of) != inbound or len(approach_of) != len(vals["approaches"]):
        raise ValueError(f"{site.path}: approach edges {sorted(approach_of)} must be exactly the inbound "
                         f"edges of the target junction {sorted(inbound)}")
    outbound = {e.getID() for e in outbound_edges(target_node(tls))}
    exit_ids = [x["edge"] for x in vals["exits"]]
    if set(exit_ids) != outbound or len(exit_ids) != len(outbound):
        raise ValueError(f"{site.path}: exit edges {sorted(exit_ids)} must be exactly the outbound "
                         f"edges of the target junction {sorted(outbound)}")
    links = _links(net, approach_of)
    sw_links = _sidewalk_patches(net, vals, target_node(tls).getID(), {})[2]
    continuous = frozenset((a["id"], "r") for a in vals["approaches"] if a["continuous_right_lane"])
    states = phase_states([(approach_of[c.getFrom().getID()], movement_of(c.getDirection())) for c in links]
                          + [lk[:2] for lk in sw_links], vals["phases"], vals["cycle_s"], continuous)
    # the closed lane-0 straight (bollards, R37: allowed for nobody) targets the exit lane of the sidewalk straight; SUMO
    # warns on two G links into one lane ("unsafe green"), so the closed one is g (yield): no vehicle drives it
    closed = {i for i, c in enumerate(links) if c.getFromLane().getIndex() == 0 and movement_of(c.getDirection()) == "s"
              and any(a["edge"] == c.getFrom().getID() and a["sidewalk"] and a["bollard_length_m"]
                      for a in vals["approaches"])}
    states = ["".join("g" if i in closed and ch == "G" else ch for i, ch in enumerate(s)) for s in states]
    all_links = [_key(c) for c in links] + [lk[2:] for lk in sw_links]

    patch_dir = out.parent / "patches" / out.name.removesuffix(".net.xml")
    files = {"lanes.edg.xml": _lane_patch(net, vals), "turns.con.xml": _turn_patch(net, vals),
             "signal.tll.xml": _signal_patch(tls.getID(), all_links, vals, states)}
    edg, con = ["lanes.edg.xml"], ["turns.con.xml"]
    if any(_cuts(a) for a in vals["approaches"]):  # order matters: splits, then lane attributes of the parts
        edg += ["split.edg.xml", "bollards.edg.xml"]
        files["bollards.edg.xml"] = _bollard_patch(vals)
    if sw_links:
        edg.append("sidewalk.edg.xml")
        con.append("sidewalk.con.xml")
    shift: dict[str, float] = {}
    for attempt in range(SPLIT_PASSES):  # each pass corrects the split positions by the previous pass's error
        if "split.edg.xml" in edg:
            files["split.edg.xml"] = _split_patch(net, vals, shift)
        if sw_links:
            files["sidewalk.edg.xml"], files["sidewalk.con.xml"], _ = _sidewalk_patches(
                net, vals, target_node(tls).getID(), shift)
        for name, root in files.items():
            write_xml(root, patch_dir / name)
        netconvert([
            "-s", str(base),
            "-e", ",".join(str(patch_dir / f) for f in edg),
            "-x", ",".join(str(patch_dir / f) for f in con),
            "-i", str(patch_dir / "signal.tll.xml"),
            "--output.street-names", "--output.original-names",
            "-o", str(out),
        ], out.parent / "logs" / f"netconvert_{out.name.removesuffix('.net.xml')}.log")
        real = _realised(sumolib.net.readNet(str(out), withInternal=True), vals)
        if all(abs(r - d) <= SPLIT_TOL_M for d, r in real.values()):
            break
        if attempt == SPLIT_PASSES - 1:
            raise RuntimeError(f"{out}: split distances from the stop line {real} (site, realised) differ by more "
                               f"than {SPLIT_TOL_M} m after {SPLIT_PASSES} netconvert passes")
        shift = {n: shift.get(n, 0.0) + d - r for n, (d, r) in real.items()}
    _check_site_net(out, all_links, [c.getDirection() for c in links] + [mv for _, mv, *_ in sw_links], states, vals)
    return out
