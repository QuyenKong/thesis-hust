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
  modelled as the existing lane 0, no lane added): with `right_lane_separator` `open` (Viktor 2026-10-28, field:
  going straight from the right-turn lane on green is legal, no separator) the straight connections from lane 0 are
  left as netconvert builds them (the lane's permissions, everyone) and follow the approach's straight signal.
  Lane 0 is the right-turn lane only over the last `right_lane_length_m` (Viktor 2026-10-29, field: 30 m; upstream
  all lanes are ordinary): the approach is split there (node `<edge>.right_lane`, see `split.edg.xml` below) and
  `lane0_extras` adds, on the stop-line edge only, links for the violators (`violator_classes`, custom1 custom2):
  a left from lane 0 (not on an approach whose left is banned) and a U-turn from lanes 0 and 1. Each copies the exit
  and exit lane of the approach's existing left / U-turn and follows its signal state, so a U-turn on a red left
  arrow is a red-light run of the TraCI rules, not a signal state. With
  the other values every straight connection from lane 0 is deleted and re-added: with `none` or `paint` with
  `allow="<violator_classes.moto> <violator_classes.car>"` (custom1 custom2: PLAN behaviour 6, violators going
  straight from the right-turn lane); with `bollards` (Viktor 2026-10-26: a physical separator) with
  `disallow="all"`, i.e. nobody goes straight from lane 0. The connection is kept (not deleted) so no TLS link index
  moves (checked: its internal lane then has no permissions). The right turn from lane 0 stays open to everyone.
- `signal.tll.xml`: static program from `signal.phases`. Every link is listed with an explicit
  `linkIndex`, so the delete/re-add above cannot shuffle the state string. A movement in
  `green_movements` is `G` for straight/right and `g` (yield) for left/turnaround; `yellow_movements`
  are `y`; everything else is `r`. The right-turn links of `continuous_right_lane` approaches are not signal
  controlled: `g` (green, yield to foes) in every phase, whatever the phase lists say (a right turn on red is
  no violation, PLAN 0); their lane-0 straight is an ordinary straight link (`G` in the approach's green).
- `split.edg.xml` + `bollards.edg.xml` (Phase 3A, ruling R39): with `right_lane_separator: bollards` the approach
  edge is split at `stop line - bollard_length_m`; the downstream part keeps the approach edge id (so every
  stop-line lookup, TLS link and turns.con.xml entry stays valid), the upstream part is `<edge>.up`, the split node
  `<edge>.bollard`. On the bollard edge lane 0 gets `changeLeft="emergency"` and lane 1 `changeRight="emergency"`:
  no lane change between the continuous right-turn lane and the through lanes (`"ignoring"`, the documented
  strongest value, is dropped silently by netconvert 1.27; no emergency vehicle exists here; Phase 3A). Any other
  separator: no `bollards.edg.xml`, lane changes free (`bollard_length_m` is not read); `open` splits at
  `stop line - right_lane_length_m` (node `<edge>.right_lane`) with the same machinery.
- Sidewalk (PLAN 1.4, Phase 3B topology c with priority, ruling R39) on the approaches of `f2_measured_approaches`
  (null or empty: none): the approach is also split at `stop line - sidewalk_start_m` (node `<edge>.sidewalk_start`,
  `<edge>.up` upstream of it, `<edge>.mid` between it and the bollard node if there is one; without bollards the
  approach edge starts at the sidewalk node); `sidewalk.edg.xml` adds the one-lane
  edge `<edge>.sidewalk` from that node to the target junction (`allow="custom1"`, width `sidewalk_width_m`, speed
  `sidewalk_speed_mps`, priority one above the approach, unnamed so it is never taken for an approach, geometry =
  lane 0 shifted right, ending edge to edge beside lane 0 at the stop line, see SIDEWALK_JOG_M; the build checks
  that the sidewalk links are foes of the lane-0 right turn). `sidewalk.con.xml`: `<edge>.up` lanes i -> i
  onwards, lane 0 also -> the sidewalk; sidewalk -> lane 0 of the approach's right and straight exits, plus a
  `<prohibition>` per approach whose straight enters the sidewalk's right exit: the sidewalk right turn yields to
  that straight and it does not yield back (the edge priority alone made the two mutual foes: an HDT red runner
  waiting at its stop line and a rider then waited for each other, and the lane-0 right turn behind the rider,
  until the run ended; D3 2026-10-28; the build checks it). The two
  sidewalk links are TLS links appended after the road links (pinned in signal.tll.xml, so no road link index
  moves): right = the approach's right-turn state (`g` in every phase on a continuous right lane), straight = the
  approach's straight state (`G` in its green: the road yields to riders at the stop line; a yielding `g` jams, 3B);
  the road link into the same exit lane (the lane-0 straight beside the sidewalk) is `g` in that green instead of
  `G` (SUMO: "unsafe green" for two G links into one lane).
  Use of the sidewalk is a TraCI route choice only (`queue_space_seeking`, option `sidewalk`).
- Split positions are measured along the raw edge geometry from the stop line. Junction shapes change with the
  patched widths and with the sidewalk node, so the build reruns netconvert (at most `SPLIT_PASSES` times), each
  time shifting every split by the remaining error, until every realised distance (stop line to the start of the
  segment downstream of the split) is within `SPLIT_TOL_M` of the site value; otherwise it raises.
- `illegal_left.mode` (PLAN Phase 3 decision, `native | box_edge`): `native` = the illegal lefts wait at the
  internal junction netconvert builds on their link. The final netconvert pass places it for a vehicle as wide as the
  internal lane (`--internal-junctions.vehicle-width`, default 1.8 m = a centred car): the sublane model lets a waiter
  stand anywhere across the 3.5 m lane, and at the default point the HDT_N / HDT_S waiters stood up to 0.8 m inside
  the opposing through lane 2 (green at the same time) and were hit (D2 2026-10-28, B0 PROXY_D1 1800 s: 10-27 such
  collisions per seed, 0 after). `box_pins.con.xml` pins every other internal junction (compliant U-turns /
  turnarounds) at its default position with `contPos`: unpinned, the HDT U-turn waiting points moved too (B0 62
  collisions vs 32). Pinning the box links themselves with `contPos` instead is not equivalent: netconvert then
  makes their internal junctions yield to the LVL approaches as well, and waiters and LVL through blocked each other
  until teleported (5-6 per run). Side effect of the option: the LVL_E left (link 4) now yields to the LVL_W left
  (link 16; no foe relation before; paths 3.05 m apart, < one lane width). `box_edge` (an explicit waiting edge
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
RIGHT_LANE_SEPARATORS = ("none", "paint", "bollards", "open")  # PLAN 0 site template + open (Viktor 2026-10-28)
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
# lane 0 and the vehicles stay on top. Colour: pale yellow (#FFF3B0) at half alpha so vehicles on lane 0 stay easy to
# see (Viktor 2026-10-28; <COLOR> takes an optional 4th alpha component, sumo.dlr.de/docs/Basics/Notation.html)
GUI_HIGHLIGHT_SUFFIX, GUI_HIGHLIGHT_COLOR, GUI_HIGHLIGHT_LAYER = ".gui.add.xml", "255,243,176,128", "10"
BOLLARD_NODE, SIDEWALK_NODE, RIGHT_LANE_NODE = ".bollard", ".sidewalk_start", ".right_lane"


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
        approaches[-1]["bollard_length_m"] = approaches[-1]["sidewalk"] = approaches[-1]["right_lane_length_m"] = None
        if approaches[-1]["continuous_right_lane"]:
            sep = approaches[-1]["right_lane_separator"] = site.require(f"approaches.{i}.right_lane_separator")
            if sep not in RIGHT_LANE_SEPARATORS:
                raise ValueError(f"{site.path}: approaches.{i}.right_lane_separator must be one of "
                                 f"{RIGHT_LANE_SEPARATORS}, got {sep!r}")
            if sep == "bollards":
                approaches[-1]["bollard_length_m"] = _positive(site, f"approaches.{i}.bollard_length_m")
            if sep == "open":  # Viktor 2026-10-29: lane 0 is the right-turn lane only over the last stretch
                approaches[-1]["right_lane_length_m"] = _positive(site, f"approaches.{i}.right_lane_length_m")
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
        if sw["sidewalk_start_m"] <= (split_m(approaches[i]) or 0.0):
            raise ValueError(f"{site.path}: approaches.{i}.sidewalk_start_m {sw['sidewalk_start_m']} must exceed "
                             f"{'bollard_length_m' if approaches[i]['bollard_length_m'] else 'right_lane_length_m'} "
                             f"{split_m(approaches[i])} (the sidewalk starts upstream)")
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
        if a["continuous_right_lane"] and a["right_lane_separator"] == "open":
            root.append(etree.Comment(f" {a['id']}: lane 0 = continuous right-turn lane over the last "
                                      f"{a['right_lane_length_m']} m, separator open; straight kept as built (everyone, "
                                      f"approach straight signal); violator-only left / U-turn links follow "))
            for _, _, frm, to, fl, tl, _, allow in (x for x in lane0_extras(net, {**vals, "approaches": [a]})):
                etree.SubElement(root, "connection", **{"from": frm}, to=to, fromLane=str(fl), toLane=str(tl),
                                 allow=allow)
        elif a["continuous_right_lane"]:
            closed = a["right_lane_separator"] == "bollards"
            perm = {"disallow": "all"} if closed else {"allow": " ".join(vals["violators"])}
            root.append(etree.Comment(f" {a['id']}: lane 0 = continuous right-turn lane, separator "
                                      f"{a['right_lane_separator']}; straight re-added with {perm} "))
            _readd(root, a["edge"], [c for c in conns if c.getFromLane().getIndex() == 0
                                     and movement_of(c.getDirection()) == "s"], **perm)
    return root


def lane0_extras(net, vals: dict) -> list[tuple]:
    """Violator-only links added on the stop-line edge of an `open` continuous-right-lane approach (Viktor 2026-10-29):
    a left from lane 0 (approaches whose left is not banned) and a U-turn from lanes 0 and 1. They copy the exit and
    exit lane of the approach's existing left / U-turn (the one from the highest lane) and follow its signal state.
    Tuples (approach, movement, from edge, to edge, fromLane, toLane, dir, allow)."""
    out = []
    for a in vals["approaches"]:
        if not (a["continuous_right_lane"] and a["right_lane_separator"] == "open"):
            continue
        conns = [c for cs in net.getEdge(a["edge"]).getOutgoing().values() for c in cs]
        for mv, lanes, banned in (("l", (0,), a["left_turn_banned"]), ("t", (0, 1), a["u_turn_banned"])):
            src = [c for c in conns if movement_of(c.getDirection()) == mv]
            if not src:
                continue
            c = max(src, key=lambda c: c.getFromLane().getIndex())
            if mv == "l" and banned:
                continue  # a banned left has no lane-0 version: only the box waiters of lane 2 exist
            allow = vals["vclass"] if banned else " ".join(vals["violators"])
            out += [(a["id"], mv, a["edge"], c.getTo().getID(), i, c.getToLane().getIndex(), c.getDirection(), allow)
                    for i in lanes]
    return out


def _readd(root: etree._Element, edge: str, conns: list, **perm: str) -> None:
    """Delete `conns` and add them back with connection-level permissions `perm` (allow= or disallow=)."""
    for c in conns:
        key = dict(**{"from": edge}, to=c.getTo().getID(),
                   fromLane=str(c.getFromLane().getIndex()), toLane=str(c.getToLane().getIndex()))
        etree.SubElement(root, "delete", **key)
        etree.SubElement(root, "connection", **key, **perm)


def split_m(a: dict) -> float | None:
    """Distance from the stop line of the split that ends the stretch where lane 0 is the continuous right-turn lane
    (`bollard_length_m` with bollards, `right_lane_length_m` with an open lane 0), or None."""
    return a["bollard_length_m"] or a["right_lane_length_m"]


def segments(a: dict) -> list[str]:
    """Edge ids of a patched approach from upstream to the stop line (the last one keeps the approach edge id)."""
    e = a["edge"]
    return [e + UP] * bool(a["sidewalk"] or split_m(a)) + [e + MID] * bool(a["sidewalk"] and split_m(a)) + [e]


def _cuts(a: dict) -> list[tuple[str, float]]:
    """(split node id, distance from the stop line), upstream first; cut k separates segments k and k + 1."""
    cuts = [(a["edge"] + SIDEWALK_NODE, a["sidewalk"]["sidewalk_start_m"])] if a["sidewalk"] else []
    node = BOLLARD_NODE if a["bollard_length_m"] else RIGHT_LANE_NODE
    return cuts + ([(a["edge"] + node, split_m(a))] if split_m(a) else [])


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
        right = _exit_of(net, a, "r")  # sumo.dlr.de/docs/Networks/PlainXML.html#setting_connection_priorities
        for b in (b for b in vals["approaches"] if b is not a and _exit_of(net, b, "s") == right):
            etree.SubElement(cons, "prohibition", prohibitor=f"{b['edge']}->{right}", prohibited=f"{swe}->{right}")
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


def _box_pins(net_path: Path, vals: dict, extras: list[tuple] = ()) -> tuple[float | None, etree._Element]:
    """(internal lane width of the banned links that wait in the box, or None if none has an internal junction;
    `<connection contPos>` for every other link with an internal junction at its default position in `net_path`; a
    pinned `extras` link (lane0_extras) repeats its `allow`, since a later `<connection>` replaces the earlier one)."""
    allow = {(x[2], x[3], x[4], x[5]): x[7] for x in extras}
    net = sumolib.net.readNet(str(net_path), withInternal=True)
    banned = {a["edge"]: {m for m, b in (("l", a["left_turn_banned"]), ("t", a["u_turn_banned"])) if b}
              for a in vals["approaches"]}
    box, pins = [], etree.Element("connections")
    for e in (net.getEdge(a["edge"]) for a in vals["approaches"]):
        for c in (c for cs in e.getOutgoing().values() for c in cs if c.getViaLaneID()):
            via = net.getLane(c.getViaLaneID())
            if not via.getOutgoing()[0].getViaLaneID():
                continue  # no internal junction
            if movement_of(c.getDirection()) in banned[e.getID()]:
                box.append(via.getWidth())
            else:
                k = _key(c)
                perm = {"allow": allow[k]} if k in allow else {}
                etree.SubElement(pins, "connection", **{"from": k[0]}, to=k[1], fromLane=str(k[2]), toLane=str(k[3]),
                                 contPos=f"{via.getLength():.2f}", **perm)
    return (max(box) if box else None), pins


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
        # only the lane-0 right turn beside it yields to a sidewalk right turn (prohibitions: no mutual right of way)
        back = [_key(c) for c in after if node.forbids(sw, c) and not (c.getFrom().getID() + SIDEWALK ==
                sw.getFrom().getID() and c.getFromLane().getIndex() == 0 and movement_of(c.getDirection()) == "r")]
        if movement_of(sw.getDirection()) == "r" and back:
            raise RuntimeError(f"{out}: links {back} yield to the sidewalk right turn {_key(sw)}")
    (program,) = target_tls(net).getPrograms().values()
    got = [p.state for p in program.getPhases()]
    if program.getType() != "static" or got != states:
        raise RuntimeError(f"{out}: program {program.getType()} {got} differs from the generated one {states}")


def gui_highlight_name(site: Site) -> str:
    return site_net_name(site).removesuffix(".net.xml") + GUI_HIGHLIGHT_SUFFIX


def write_gui_highlight(site: Site, net_path: Path, out: Path) -> Path:
    """sumo-gui only: paints lane 0 of every continuous_right_lane approach pale yellow on its stop-line edge (the
    bollard segment with bollards; else the approach edge downstream of any split, e.g. from the sidewalk start) and its
    right-turn path through the junction. No lane is added: filled `<poly>` additionals over the existing lane 0
    (sumo.dlr.de/docs/Simulation/Shapes.html: fill, layer); the simulation never loads them, so they cannot change a
    run."""
    vals = site_values(site)
    net = sumolib.net.readNet(str(net_path), withInternal=True)
    root = etree.Element("additional")
    for a in vals["approaches"]:
        if not a["continuous_right_lane"]:
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
    extras = lane0_extras(net, vals)
    states = phase_states([(approach_of[c.getFrom().getID()], movement_of(c.getDirection())) for c in links]
                          + [lk[:2] for lk in sw_links] + [x[:2] for x in extras], vals["phases"], vals["cycle_s"],
                          continuous)
    # the lane-0 straight of a sidewalk approach targets the exit lane of the sidewalk straight; SUMO warns on two G
    # links into one lane ("unsafe green"), so the road link is g (yield): closed (bollards, R37) nobody drives it; open
    # (2026-10-28) it yields to the riders leaving the sidewalk, as netconvert's foe matrix already has it
    sw_targets = {(to, tl) for _, mv, _, to, _, tl in sw_links if mv == "s"}
    merging = {i for i, c in enumerate(links) if (c.getTo().getID(), c.getToLane().getIndex()) in sw_targets}
    states = ["".join("g" if i in merging and ch == "G" else ch for i, ch in enumerate(s)) for s in states]
    all_links = [_key(c) for c in links] + [lk[2:] for lk in sw_links] + [lk[2:6] for lk in extras]

    patch_dir = out.parent / "patches" / out.name.removesuffix(".net.xml")
    files = {"lanes.edg.xml": _lane_patch(net, vals), "turns.con.xml": _turn_patch(net, vals),
             "signal.tll.xml": _signal_patch(tls.getID(), all_links, vals, states)}
    edg, con = ["lanes.edg.xml"], ["turns.con.xml"]
    if any(_cuts(a) for a in vals["approaches"]):  # order matters: splits, then lane attributes of the parts
        edg.append("split.edg.xml")
    if any(a["bollard_length_m"] for a in vals["approaches"]):  # only bollards stop lane changes; open: free
        edg.append("bollards.edg.xml")
        files["bollards.edg.xml"] = _bollard_patch(vals)
    if sw_links:
        edg.append("sidewalk.edg.xml")
        con.append("sidewalk.con.xml")
    log = out.parent / "logs" / f"netconvert_{out.name.removesuffix('.net.xml')}.log"

    def convert(*extra: str) -> None:
        for name, root in files.items():
            write_xml(root, patch_dir / name)
        netconvert([
            "-s", str(base),
            "-e", ",".join(str(patch_dir / f) for f in edg),
            "-x", ",".join(str(patch_dir / f) for f in con),
            "-i", str(patch_dir / "signal.tll.xml"),
            "--output.street-names", "--output.original-names", *extra,
            "-o", str(out),
        ], log)

    shift: dict[str, float] = {}
    for attempt in range(SPLIT_PASSES):  # each pass corrects the split positions by the previous pass's error
        if "split.edg.xml" in edg:
            files["split.edg.xml"] = _split_patch(net, vals, shift)
        if sw_links:
            files["sidewalk.edg.xml"], files["sidewalk.con.xml"], _ = _sidewalk_patches(
                net, vals, target_node(tls).getID(), shift)
        convert()
        real = _realised(sumolib.net.readNet(str(out), withInternal=True), vals)
        if all(abs(r - d) <= SPLIT_TOL_M for d, r in real.values()):
            break
        if attempt == SPLIT_PASSES - 1:
            raise RuntimeError(f"{out}: split distances from the stop line {real} (site, realised) differ by more "
                               f"than {SPLIT_TOL_M} m after {SPLIT_PASSES} netconvert passes")
        shift = {n: shift.get(n, 0.0) + d - r for n, (d, r) in real.items()}
    width, pins = _box_pins(out, vals, extras)
    if width:  # moves internal junctions only, no junction shape, so no split moves
        files["box_pins.con.xml"] = pins
        con.append("box_pins.con.xml")
        convert("--internal-junctions.vehicle-width", f"{width:.2f}")
    _check_site_net(out, all_links, [c.getDirection() for c in links] + [mv for _, mv, *_ in sw_links]
                     + [x[6] for x in extras], states, vals)
    return out
