"""Site network (PLAN Phase 1.4): base net + plain-XML patches generated from the site file.

`netconvert -s base.net.xml -e lanes.edg.xml -x turns.con.xml -i signal.tll.xml -o <site net>`

- `lanes.edg.xml`: `approaches[].lane_widths_m` on each approach edge and `exits[].lane_widths_m` on each
  outbound edge (lane index 0 = rightmost). netconvert gives an internal lane the width of its outbound lane
  (Task 4 operator report), so the exit widths also set the widths inside the junction box (ruling R21).
- `turns.con.xml`: for `left_turn_banned: true` every left (`dir` l/L) connection of the approach is
  deleted and re-added with `allow="<illegal_left.vclass>"` (connection-level permissions, PlainXML docs:
  "set custom permissions independent of from-lane and to-lane permissions"). Same for
  `u_turn_banned: true` with the turnaround (`dir` t).
- `signal.tll.xml`: static program from `signal.phases`. Every link is listed with an explicit
  `linkIndex`, so the delete/re-add above cannot shuffle the state string. A movement in
  `green_movements` is `G` for straight/right and `g` (yield) for left/turnaround; `yellow_movements`
  are `y`; everything else is `r`.
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
DIR_TO_MOVEMENT = {"s": "s", "r": "r", "R": "r", "l": "l", "L": "l", "t": "t"}  # SUMO connection dir codes
PRIORITY_MOVEMENTS = ("s", "r")  # green = G; other movements yield (g)


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
        })
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
    }
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


def _parse_movement(mv: str) -> tuple[str, str]:
    app, sep, code = mv.partition(":")
    if not sep or code not in MOVEMENTS:
        raise ValueError(f"movement {mv!r} must be '<approach_id>:<dir>' with dir in {MOVEMENTS}")
    return app, code


def phase_states(links: list[tuple[str, str]], phases: list[dict], cycle_s: float) -> list[str]:
    """State string per phase; `links[i]` = (approach_id, movement) of tl link index i."""
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
            ("G" if code in PRIORITY_MOVEMENTS else "g") if (app, code) in green
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
        banned = {"l"} if a["left_turn_banned"] else set()
        banned |= {"t"} if a["u_turn_banned"] else set()
        if not banned:
            continue
        root.append(etree.Comment(f" {a['id']}: banned {sorted(banned)}; re-added for {vals['vclass']} only "))
        conns = [c for cs in net.getEdge(a["edge"]).getOutgoing().values() for c in cs]
        for c in sorted(conns, key=lambda c: (c.getFromLane().getIndex(), c.getTo().getID())):
            if movement_of(c.getDirection()) in banned:
                key = dict(**{"from": a["edge"]}, to=c.getTo().getID(),
                           fromLane=str(c.getFromLane().getIndex()), toLane=str(c.getToLane().getIndex()))
                etree.SubElement(root, "delete", **key)
                etree.SubElement(root, "connection", **key, allow=vals["vclass"])
    return root


def _signal_patch(tls_id: str, links: list, vals: dict, states: list[str]) -> etree._Element:
    root = etree.Element("tlLogics")
    logic = etree.SubElement(root, "tlLogic", id=tls_id, type="static", programID="0", offset="0")
    for p, state in zip(vals["phases"], states):
        etree.SubElement(logic, "phase", duration=str(p["duration_s"]), state=state, name=p["name"])
    for i, c in enumerate(links):
        etree.SubElement(root, "connection", **{"from": c.getFrom().getID()}, to=c.getTo().getID(),
                         fromLane=str(c.getFromLane().getIndex()), toLane=str(c.getToLane().getIndex()),
                         tl=tls_id, linkIndex=str(i))
    return root


def _check_site_net(out: Path, links_before: list, states: list[str], vals: dict) -> None:
    net = sumolib.net.readNet(str(out), withPrograms=True)
    approach_of = {a["edge"]: a["id"] for a in vals["approaches"]}
    after = [(c.getFrom().getID(), c.getFromLane().getIndex(), c.getTo().getID(), c.getToLane().getIndex())
             for c in _links(net, approach_of)]
    before = [(c.getFrom().getID(), c.getFromLane().getIndex(), c.getTo().getID(), c.getToLane().getIndex())
              for c in links_before]
    if after != before:
        raise RuntimeError(f"{out}: link indices changed while patching")
    (program,) = target_tls(net).getPrograms().values()
    got = [p.state for p in program.getPhases()]
    if program.getType() != "static" or got != states:
        raise RuntimeError(f"{out}: program {program.getType()} {got} differs from the generated one {states}")


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
    states = phase_states([(approach_of[c.getFrom().getID()], movement_of(c.getDirection())) for c in links],
                          vals["phases"], vals["cycle_s"])

    patch_dir = out.parent / "patches" / out.name.removesuffix(".net.xml")
    files = {"lanes.edg.xml": _lane_patch(net, vals), "turns.con.xml": _turn_patch(net, vals),
             "signal.tll.xml": _signal_patch(tls.getID(), links, vals, states)}
    for name, root in files.items():
        write_xml(root, patch_dir / name)
    netconvert([
        "-s", str(base),
        "-e", str(patch_dir / "lanes.edg.xml"),
        "-x", str(patch_dir / "turns.con.xml"),
        "-i", str(patch_dir / "signal.tll.xml"),
        "--output.street-names", "--output.original-names",
        "-o", str(out),
    ], out.parent / "logs" / f"netconvert_{out.name.removesuffix('.net.xml')}.log")
    _check_site_net(out, links, states, vals)
    return out
