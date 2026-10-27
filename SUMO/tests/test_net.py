"""Network build (PLAN Phase 1): base net from OSM, site patches, signal program, edge table.

One CLI run (session fixture) builds base + proxy site net into a temp dir; tests read its outputs.
"""

import gzip
import math
import subprocess
import sys
import warnings
from pathlib import Path

import pytest
import sumolib
from lxml import etree

from thesis_sumo.config import REPO_ROOT, MissingFieldDataError, Site, load_site
from thesis_sumo.net.apply_patches import (
    ProxySiteWarning,
    build_site_net,
    movement_of,
    phase_states,
    site_net_name,
)
from thesis_sumo.net.build_net import (
    approach_edges,
    approach_segments,
    edge_table,
    exit_edges,
    inbound_edges,
    outbound_edges,
    sidewalk_edges,
    target_node,
    target_tls,
)

PROXY = REPO_ROOT / "config" / "site.proxy.yaml"
MEASURED = REPO_ROOT / "config" / "site.yaml"
OSM = REPO_ROOT / "scenario_raw" / "2026-10-02-06-34-26" / "osm_bbox.osm.xml.gz"
COMMITTED = REPO_ROOT / "scenario" / "net"


def _cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "thesis_sumo.net.build", *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=REPO_ROOT,
    )


@pytest.fixture(scope="session")
def built(tmp_path_factory):
    out_dir = tmp_path_factory.mktemp("net")
    proc = _cli("--site", str(PROXY), "--out-dir", str(out_dir))
    return out_dir, proc


@pytest.fixture(scope="session")
def site_net(built):
    out_dir, proc = built
    assert proc.returncode == 0, proc.stderr[-3000:]
    return sumolib.net.readNet(str(out_dir / "site.proxy.net.xml"), withInternal=True, withPrograms=True)


@pytest.fixture(scope="session")
def proxy():
    return load_site(PROXY)


def _strip_header(path: Path) -> str:
    """Net file text without the leading netconvert comment (it holds the date and input paths)."""
    text = path.read_text(encoding="utf-8")
    end = text.index("-->") + 3
    return text[end:]


# --- tests named in the task brief -------------------------------------------------------------

def test_base_net_builds(built):
    out_dir, proc = built
    assert proc.returncode == 0, proc.stderr[-3000:]
    for name in ("base.net.xml", "site.proxy.net.xml", "edge_table.csv", "diagram.svg",
                 "removed_nodes.csv", "patches/site.proxy/lanes.edg.xml",
                 "patches/site.proxy/turns.con.xml", "patches/site.proxy/signal.tll.xml"):
        assert (out_dir / name).is_file(), name


def test_target_tls_static(site_net):
    tls = target_tls(site_net)
    programs = tls.getPrograms()
    assert programs, "target junction has no tlLogic"
    assert {p.getType() for p in programs.values()} == {"static"}
    # the only signal left in the cut network is the target one (arm signals removed, PLAN 1.1)
    assert [t.getID() for t in site_net.getTrafficLights()] == [tls.getID()]


def test_banned_left_only_custom1(site_net, proxy):
    banned = [a for a in proxy["approaches"] if a["left_turn_banned"]]
    assert banned, "proxy site must ban at least one left turn"
    vclass = proxy["illegal_left"]["vclass"]
    for a in banned:
        lefts = [c for c in _conns_from(site_net, a["edge"]) if movement_of(c.getDirection()) == "l"]
        assert lefts, f"{a['id']}: no left connection left for {vclass}"
        for c in lefts:
            via = site_net.getLane(c.getViaLaneID())
            assert via.getPermissions() == {vclass}, (a["id"], via.getID(), via.getPermissions())
            assert c.allows(vclass) and not c.allows("motorcycle") and not c.allows("passenger")
    # approaches without a ban keep their ordinary left turns
    for a in proxy["approaches"]:
        if not a["left_turn_banned"]:
            lefts = [c for c in _conns_from(site_net, a["edge"]) if movement_of(c.getDirection()) == "l"]
            assert lefts and all(c.allows("motorcycle") and c.allows("passenger") for c in lefts)


def test_signal_matches_site(site_net, proxy):
    (program,) = target_tls(site_net).getPrograms().values()
    phases = program.getPhases()
    assert sum(p.duration for p in phases) == proxy["signal"]["cycle_s"]
    assert [p.duration for p in phases] == [p["duration_s"] for p in proxy["signal"]["phases"]]
    # every link shows the colour the site file asks for, by movement
    approach_of = {a["edge"]: a["id"] for a in proxy["approaches"]} | sidewalk_edges(site_net)
    continuous = {f"{a['id']}:r" for a in proxy["approaches"] if a["continuous_right_lane"]}
    for k, (ph, spec) in enumerate(zip(phases, proxy["signal"]["phases"])):
        for conn in target_tls(site_net).getConnections():
            in_lane, _, idx = conn
            c = _link(site_net, idx)
            mv = f"{approach_of[in_lane.getEdge().getID()]}:{movement_of(c.getDirection())}"
            ch = ph.state[idx]
            if mv in continuous:  # continuous right turn: not signal controlled (PLAN 1.4)
                assert ch == "g", (k, mv, ch)
            elif mv in spec["green_movements"]:
                assert ch in "Gg", (k, mv, ch)
            elif mv in spec["yellow_movements"]:
                assert ch == "y", (k, mv, ch)
            else:
                assert ch == "r", (k, mv, ch)


# --- further behaviour ---------------------------------------------------------------------------

def test_illegal_left_green_in_own_through_phase(site_net, proxy):
    """PLAN 1.4: the illegal (custom1) left link is `g` in the through-green phase of its approach."""
    (program,) = target_tls(site_net).getPrograms().values()
    for app_id in proxy["illegal_left"]["approaches"]:
        edge = next(a["edge"] for a in proxy["approaches"] if a["id"] == app_id)
        conns = _conns_from(site_net, edge)
        through = {c.getTLLinkIndex() for c in conns if movement_of(c.getDirection()) == "s"}
        lefts = {c.getTLLinkIndex() for c in conns if movement_of(c.getDirection()) == "l"}
        through_green = [p for p in program.getPhases() if all(p.state[i] in "Gg" for i in through)]
        assert through_green
        for p in through_green:
            assert all(p.state[i] == "g" for i in lefts)


def test_edges_mapped_and_inbound(site_net, proxy):
    incoming = {e.getID() for e in inbound_edges(target_node(target_tls(site_net)))}
    edges = [a["edge"] for a in proxy["approaches"]]
    sidewalks = {f"{a['edge']}.sidewalk": a["id"] for a in proxy["approaches"] if a["id"] in
                 proxy["f2_measured_approaches"]}
    assert sidewalk_edges(site_net) == sidewalks and len(sidewalks) == 1
    assert len(set(edges)) == 4 and set(edges) | set(sidewalks) == incoming
    assert approach_edges(site_net) == {a["id"]: a["edge"] for a in proxy["approaches"]}


def test_measured_site_edges_match_proxy():
    """Edge ids are geometry, not field data: both site files carry the same mapping."""
    m, p = load_site(MEASURED), load_site(PROXY)
    for key in ("approaches", "exits"):
        assert [(a["id"], a["edge"]) for a in m[key]] == [(a["id"], a["edge"]) for a in p[key]], key
    assert all(x["lane_widths_m"] is None for x in m["exits"])


def test_lane_widths_from_site(site_net, proxy):
    for a in [*proxy["approaches"], *proxy["exits"]]:
        lanes = site_net.getEdge(a["edge"]).getLanes()
        assert [round(l.getWidth(), 2) for l in lanes] == a["lane_widths_m"], a["id"]


def test_exits_mapped_and_outbound(site_net, proxy):
    outgoing = {e.getID() for e in outbound_edges(target_node(target_tls(site_net)))}
    edges = [x["edge"] for x in proxy["exits"]]
    assert len(set(edges)) == 4 and set(edges) == outgoing
    assert exit_edges(site_net) == {x["id"]: x["edge"] for x in proxy["exits"]}
    # an exit lies on the arm of the approach with the same prefix: the approach's turnaround leads into it
    approach = {a["id"]: a["edge"] for a in proxy["approaches"]}
    for x in proxy["exits"]:
        turns = [c for c in _conns_from(site_net, approach[x["id"].removesuffix("_out")])
                 if movement_of(c.getDirection()) == "t"]
        assert {c.getTo().getID() for c in turns} == {x["edge"]}, x["id"]


def test_internal_lanes_as_wide_as_outbound_lane(site_net, proxy):
    """R21: no width step inside the box. netconvert gives an internal lane the width of its outbound lane
    (Task 4 operator report); with exit widths = approach widths every link keeps the approach width."""
    node = target_node(target_tls(site_net))
    widths = {a["edge"]: a["lane_widths_m"] for a in [*proxy["approaches"], *proxy["exits"]]}
    n_internal = 0
    for edge in inbound_edges(node):
        if edge.getID() in sidewalk_edges(site_net):  # not a road approach: own width, checked in the sidewalk test
            n_internal += len(_conns_from(site_net, edge.getID()))
            continue
        for c in _conns_from(site_net, edge.getID()):
            out = c.getToLane()
            assert round(out.getWidth(), 2) == widths[out.getEdge().getID()][out.getIndex()]
            assert round(c.getFromLane().getWidth(), 2) == widths[edge.getID()][c.getFromLane().getIndex()]
            via = site_net.getLane(c.getViaLaneID())
            while via is not None:  # a link may run over several internal lanes (internal junctions)
                assert math.isclose(via.getWidth(), out.getWidth()), (via.getID(), via.getWidth(), out.getID())
                n_internal += 1
                (nxt,) = via.getOutgoing()
                via = site_net.getLane(nxt.getViaLaneID()) if nxt.getViaLaneID() else None
    assert n_internal >= len(target_tls(site_net).getConnections())


def test_exit_widths_required_and_checked(built, proxy, tmp_path):
    """R7: a null exit width raises MissingFieldDataError naming the key; a wrong lane count raises."""
    out_dir, _ = built
    for widths, err, match in ((None, MissingFieldDataError, r"exits\.2\.lane_widths_m"),
                               ([3.5, 3.5], ValueError, "2 lane widths for 3 lanes")):
        data = dict(proxy)
        data["exits"] = [dict(x) for x in proxy["exits"]]
        data["exits"][2]["lane_widths_m"] = widths
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ProxySiteWarning)
            with pytest.raises(err, match=match):
                build_site_net(Site(data, proxy.path), out_dir / "base.net.xml", tmp_path / "x.net.xml")
        assert not (tmp_path / "x.net.xml").exists()


def test_unnamed_osm_way_is_hoang_dao_thuy(site_net):
    """PLAN 1.2: OSM way 1071601648 has no name; its wikidata id is Hoang Dao Thuy's."""
    tags = {}
    with gzip.open(OSM) as f:
        for _, el in etree.iterparse(f, tag="way"):
            if el.get("id") in ("1071601648", "953158817", "37871458"):
                tags[el.get("id")] = {t.get("k"): t.get("v") for t in el.findall("tag")}
            el.clear()
    assert "name" not in tags["1071601648"]
    hdt = tags["37871458"]["name:etymology:wikidata"]
    assert tags["1071601648"]["name:etymology:wikidata"] == hdt == tags["953158817"]["name:etymology:wikidata"]
    assert tags["953158817"]["name"] == "Phố Hoàng Đạo Thúy"
    # in the built net the HDT_N approach carries the HĐT name
    assert site_net.getEdge(approach_edges(site_net)["HDT_N"]).getName() == "Phố Hoàng Đạo Thúy"


def test_edge_table_columns(built):
    out_dir, _ = built
    df = edge_table(out_dir / "base.net.xml")
    assert list(df.columns) == ["edge_id", "name", "direction", "n_lanes", "length_m", "connections"]
    assert len(df) == 8
    inbound = df[df["direction"].str.startswith("in")]
    assert len(inbound) == 4 and all(inbound["connections"].str.len() > 0)


def test_removed_nodes_reported(built):
    out_dir, _ = built
    text = (out_dir / "removed_nodes.csv").read_text(encoding="utf-8")
    assert "cluster_2291072471_443393357" in text  # the signal on the HĐT north arm


def test_measured_site_raises(built):
    out_dir, _ = built
    with pytest.raises(MissingFieldDataError):
        build_site_net(load_site(MEASURED), out_dir / "base.net.xml", out_dir / "site.net.xml")
    assert not (out_dir / "site.net.xml").exists()
    proc = _cli("--site", str(MEASURED), "--out-dir", str(out_dir / "measured"))
    assert proc.returncode != 0 and "TODO_MEASURE" in proc.stderr
    assert not (out_dir / "measured" / "site.net.xml").exists()


def test_proxy_build_warns(built, proxy, tmp_path):
    out_dir, proc = built
    assert "LITERATURE_PROXY" in proc.stderr
    with pytest.warns(ProxySiteWarning):
        build_site_net(proxy, out_dir / "base.net.xml", tmp_path / "site.proxy.net.xml")


def test_site_net_name(proxy):
    assert site_net_name(proxy) == "site.proxy.net.xml"
    assert site_net_name(load_site(MEASURED)) == "site.net.xml"


def test_phase_states_rules():
    links = [("A", "s"), ("A", "l"), ("A", "r"), ("A", "t"), ("B", "s")]
    phases = [
        {"name": "g", "duration_s": 10, "green_movements": ["A:s", "A:l", "A:r", "A:t"], "yellow_movements": []},
        {"name": "y", "duration_s": 3, "green_movements": [], "yellow_movements": ["A:s", "A:l"]},
        {"name": "b", "duration_s": 7, "green_movements": ["B:s"], "yellow_movements": []},
    ]
    assert phase_states(links, phases, cycle_s=20) == ["GgGgr", "yyrrr", "rrrrG"]
    with pytest.raises(ValueError, match="cycle"):
        phase_states(links, phases, cycle_s=21)
    bad = [dict(phases[0], green_movements=["A:x"])]
    with pytest.raises(ValueError, match="A:x"):
        phase_states(links, bad, cycle_s=10)
    missing = [dict(phases[0], green_movements=["C:s"])]
    with pytest.raises(ValueError, match="C:s"):
        phase_states(links, missing, cycle_s=10)


def test_movement_codes():
    assert [movement_of(d) for d in ("s", "l", "L", "r", "R", "t")] == ["s", "l", "l", "r", "r", "t"]
    with pytest.raises(ValueError):
        movement_of("invalid")


def test_u_turn_ban_and_unbanned_illegal_left_rejected(built, proxy, tmp_path):
    out_dir, _ = built
    data = dict(proxy)
    data["approaches"] = [dict(a) for a in proxy["approaches"]]
    data["approaches"][1]["u_turn_banned"] = True
    site = Site(data, proxy.path)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ProxySiteWarning)
        net_path = build_site_net(site, out_dir / "base.net.xml", tmp_path / "u.net.xml")
    net = sumolib.net.readNet(str(net_path), withInternal=True)
    turns = [c for c in _conns_from(net, data["approaches"][1]["edge"]) if movement_of(c.getDirection()) == "t"]
    assert turns and all(net.getLane(c.getViaLaneID()).getPermissions() == {"custom1"} for c in turns)

    data["illegal_left"] = dict(proxy["illegal_left"], approaches=["LVL_E"])
    with pytest.raises(ValueError, match="LVL_E"):
        build_site_net(Site(data, proxy.path), out_dir / "base.net.xml", tmp_path / "v.net.xml")


def test_illegal_left_mode_checked(built, proxy, tmp_path):
    """`illegal_left.mode` (Phase 3 decision) is required and must be native | box_edge."""
    out_dir, _ = built
    for mode, err, match in ((None, MissingFieldDataError, "illegal_left.mode"),
                             ("teleport", ValueError, "illegal_left.mode"),
                             ("box_edge", NotImplementedError, "box_edge")):
        data = dict(proxy)
        data["illegal_left"] = dict(proxy["illegal_left"], mode=mode)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ProxySiteWarning)
            with pytest.raises(err, match=match):
                build_site_net(Site(data, proxy.path), out_dir / "base.net.xml", tmp_path / "m.net.xml")
        assert not (tmp_path / "m.net.xml").exists()


def test_committed_outputs_match_build(built):
    """scenario/net/*.net.xml are exactly what the script produces (no hand edits); stopline_shift.csv logs how far
    the sidewalk moved each stop line (F2-behaviours review: within 0.2 m on LVL_W / HDT_S, the junction is not
    blown up by the sidewalk corner)."""
    out_dir, _ = built
    for name in ("base.net.xml", "site.proxy.net.xml"):
        assert _strip_header(COMMITTED / name) == _strip_header(out_dir / name), name
    import pandas as pd
    shift = pd.read_csv(out_dir / "stopline_shift.csv").set_index("approach")["shift_m"]
    assert abs(shift["LVL_W"]) <= 0.2 and abs(shift["HDT_S"]) <= 0.2 and shift.abs().max() <= 2.0, shift
    for name in ("edge_table.csv", "removed_nodes.csv", "stopline_shift.csv", "patches/site.proxy/signal.tll.xml",
                 "patches/site.proxy/turns.con.xml", "patches/site.proxy/lanes.edg.xml",
                 "patches/site.proxy/split.edg.xml", "patches/site.proxy/bollards.edg.xml",
                 "patches/site.proxy/sidewalk.edg.xml", "patches/site.proxy/sidewalk.con.xml"):
        assert (COMMITTED / name).read_text(encoding="utf-8") == (out_dir / name).read_text(encoding="utf-8"), name


# --- continuous right-turn lane (Task F2-net, PLAN 0 / 1.4) ---------------------------------------------

def _continuous(proxy):
    return [a for a in proxy["approaches"] if a["continuous_right_lane"]]


def _states(net):
    (program,) = target_tls(net).getPrograms().values()
    return [p.state for p in program.getPhases()]


def test_continuous_right_turn_never_red(site_net, proxy):
    """The right turn from the continuous right-turn lane is `g` (green, yield) in every phase: no right on red."""
    assert len(_continuous(proxy)) == 4  # PLAN 0: every approach
    for a in _continuous(proxy):
        rights = [c.getTLLinkIndex() for c in _conns_from(site_net, a["edge"]) if movement_of(c.getDirection()) == "r"]
        assert rights, a["id"]
        assert all(state[i] == "g" for state in _states(site_net) for i in rights), a["id"]


def _lane0_check(net, approaches, expected: set):
    """Lane 0 straight carries `expected` vClasses only; lane 0 right and lanes 1-2 straight stay open to all."""
    for a in approaches:
        conns = _conns_from(net, a["edge"])
        lane0_s = [c for c in conns if c.getFromLane().getIndex() == 0 and movement_of(c.getDirection()) == "s"]
        assert lane0_s, a["id"]  # kept, never deleted: TLS link indices must not move
        for c in lane0_s:
            assert net.getLane(c.getViaLaneID()).getPermissions() == expected, a["id"]
            assert not c.allows("passenger") and not c.allows("motorcycle")
        for c in conns:
            if c not in lane0_s and movement_of(c.getDirection()) in ("r", "s"):
                assert c.allows("passenger") and c.allows("motorcycle"), (a["id"], c.getTLLinkIndex())


def test_lane0_straight_closed_by_bollards(site_net, proxy):
    """Viktor: the continuous right lane is separated by bollards, so nobody goes straight from lane 0."""
    assert {a["right_lane_separator"] for a in _continuous(proxy)} == {"bollards"}
    _lane0_check(site_net, _continuous(proxy), set())


def test_lane0_straight_only_violators_with_paint(built, site_net, proxy, tmp_path):
    """With a painted separator, lane 0 straight is open to custom1 + custom2 only (PLAN behaviour 6); the link
    indices are the same as with bollards."""
    out_dir, _ = built
    data = dict(proxy)
    data["approaches"] = [dict(a, right_lane_separator="paint") for a in proxy["approaches"]]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ProxySiteWarning)
        paint = sumolib.net.readNet(str(build_site_net(Site(data, proxy.path), out_dir / "base.net.xml",
                                                       tmp_path / "paint.net.xml")), withInternal=True)
    violators = {proxy["violator_classes"]["moto"], proxy["violator_classes"]["car"]}
    assert violators == {"custom1", "custom2"}
    _lane0_check(paint, _continuous(proxy), violators)
    key = lambda c: (c.getFromLane().getIndex(), c.getTo().getID(), c.getTLLinkIndex())
    for a in proxy["approaches"]:
        assert sorted(map(key, _conns_from(paint, a["edge"]))) == sorted(map(key, _conns_from(site_net, a["edge"])))


def test_non_right_states_unchanged_without_continuous_lane(built, site_net, proxy, tmp_path):
    """Switching continuous_right_lane off changes only the right-turn links (char by char) and gives the lane-0
    straight back to everyone; link indices are the same."""
    out_dir, _ = built
    data = dict(proxy)
    data["approaches"] = [dict(a, continuous_right_lane=False) for a in proxy["approaches"]]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ProxySiteWarning)
        off = sumolib.net.readNet(str(build_site_net(Site(data, proxy.path), out_dir / "base.net.xml",
                                                     tmp_path / "off.net.xml")), withPrograms=True)
    rights = {c.getTLLinkIndex() for e in [a["edge"] for a in proxy["approaches"]] + list(sidewalk_edges(site_net))
              for c in _conns_from(site_net, e) if movement_of(c.getDirection()) == "r"}
    on_states, off_states = _states(site_net), _states(off)
    assert len(on_states) == len(off_states)
    for on, of in zip(on_states, off_states):
        assert len(on) == len(of)  # G vs g: the closed lane-0 straight next to a sidewalk yields (apply_patches)
        assert [ch.upper() for i, ch in enumerate(on) if i not in rights] == \
            [ch.upper() for i, ch in enumerate(of) if i not in rights]
    assert any(on[i] != of[i] for on, of in zip(on_states, off_states) for i in rights)  # off: red in HDT/LVL phases
    for a in proxy["approaches"]:
        key = lambda c: (c.getFromLane().getIndex(), c.getTo().getID(), c.getTLLinkIndex())
        assert sorted(map(key, _conns_from(off, a["edge"]))) == sorted(map(key, _conns_from(site_net, a["edge"])))
        assert all(c.allows("passenger") for c in _conns_from(off, a["edge"]) if movement_of(c.getDirection()) == "s")


def test_phase_states_uncontrolled_links():
    links = [("A", "s"), ("A", "r"), ("B", "s"), ("B", "r")]
    phases = [{"name": "a", "duration_s": 10, "green_movements": ["A:s", "A:r"], "yellow_movements": []},
              {"name": "b", "duration_s": 10, "green_movements": ["B:s", "B:r"], "yellow_movements": ["A:r"]}]
    assert phase_states(links, phases, 20) == ["GGrr", "ryGG"]
    assert phase_states(links, phases, 20, frozenset({("A", "r")})) == ["Ggrr", "rgGG"]


@pytest.mark.parametrize("key, value, err, match", [
    ("continuous_right_lane", None, MissingFieldDataError, r"approaches\.1\.continuous_right_lane"),
    ("right_lane_separator", None, MissingFieldDataError, r"approaches\.1\.right_lane_separator"),
    ("right_lane_separator", "cones", ValueError, "right_lane_separator"),
    ("f2_measured_approaches", ["HDT_S"], MissingFieldDataError, r"approaches\.3\.sidewalk_width_m"),
    ("f2_measured_approaches", ["NOPE"], ValueError, "NOPE"),
    ("bollard_length_m", None, MissingFieldDataError, r"approaches\.1\.bollard_length_m"),
    ("bollard_length_m", -5, ValueError, r"approaches\.1\.bollard_length_m must be a positive number"),
    ("sidewalk_start_m", None, MissingFieldDataError, r"approaches\.0\.sidewalk_start_m"),
    ("sidewalk_start_m", 20, ValueError, "must exceed bollard_length_m"),
    ("sidewalk_speed_mps", None, MissingFieldDataError, r"approaches\.0\.sidewalk_speed_mps"),
    ("violator_classes", {"moto": "custom2", "car": "custom2"}, ValueError, "violator_classes.moto"),
    ("violator_classes", {"moto": "custom1", "car": None}, MissingFieldDataError, r"violator_classes\.car"),
])
def test_f2_site_values_checked(built, proxy, tmp_path, key, value, err, match):
    """A required null raises naming the key; nothing is written."""
    out_dir, _ = built
    data = dict(proxy)
    if key in ("continuous_right_lane", "right_lane_separator", "bollard_length_m"):
        data["approaches"] = [dict(a) for a in proxy["approaches"]]
        data["approaches"][1][key] = value
    elif key.startswith("sidewalk_"):
        data["approaches"] = [dict(a) for a in proxy["approaches"]]
        data["approaches"][0][key] = value  # LVL_W, the proxy f2 approach
    else:
        data[key] = value
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ProxySiteWarning)
        with pytest.raises(err, match=match):
            build_site_net(Site(data, proxy.path), out_dir / "base.net.xml", tmp_path / "f.net.xml")
    assert not (tmp_path / "f.net.xml").exists()


def _lane_attrs(path: Path, lane_ids: set[str]) -> dict[str, dict]:
    """Raw attributes of some lanes of a net file (sumolib does not read changeLeft / changeRight)."""
    out = {}
    for _, el in etree.iterparse(str(path), tag="lane"):
        if el.get("id") in lane_ids:
            out[el.get("id")] = dict(el.attrib)
    return out


def test_bollard_edge_bans_lane_change_0_1(built, site_net, proxy):
    """Phase 3A / R39: every bollards approach is split at stop line - bollard_length_m; the stop-line part keeps the
    approach id and bans lane changes between lane 0 and 1 (`emergency` only: netconvert drops `ignoring`); upstream
    and between lanes 1-2 lane changes stay free; R37's closed lane-0 straight is kept."""
    out_dir, _ = built
    for a in proxy["approaches"]:
        segs = [e.getID() for e in approach_segments(site_net, a["edge"])]
        assert segs[0] == a["edge"] and segs[-1] == a["edge"] + ".up", segs
        assert len(segs) == (3 if a["id"] in proxy["f2_measured_approaches"] else 2)
        assert site_net.getEdge(a["edge"]).getFromNode().getID() == a["edge"] + ".bollard"
        for ln in site_net.getEdge(a["edge"]).getLanes():
            assert abs(ln.getLength() - a["bollard_length_m"]) <= 0.2, (a["id"], ln.getLength())
        for s in segs[1:]:
            assert [round(ln.getWidth(), 2) for ln in site_net.getEdge(s).getLanes()] == a["lane_widths_m"]
        ids = {f"{e}_{k}" for e in segs for k in range(3)}
        attrs = _lane_attrs(out_dir / "site.proxy.net.xml", ids)
        e = a["edge"]
        assert attrs[f"{e}_0"].get("changeLeft") == "emergency" and attrs[f"{e}_1"].get("changeRight") == "emergency"
        assert "changeRight" not in attrs[f"{e}_0"] and "changeLeft" not in attrs[f"{e}_1"]
        assert not any(k in attrs[f"{e}_2"] for k in ("changeLeft", "changeRight"))
        for s in segs[1:]:
            assert not any(k in attrs[f"{s}_{i}"] for i in range(3) for k in ("changeLeft", "changeRight")), s


def test_sidewalk_edge_custom1_only_with_pinned_links(built, site_net, proxy):
    """Phase 3B topology c + priority (R39) on f2_measured_approaches: a separate custom1-only edge from
    stop line - sidewalk_start_m to the junction, entered from lane 0 of the upstream segment only, with its own TLS
    links appended after the unchanged road links: right = g always, straight = the approach's straight state."""
    out_dir, _ = built
    (app,) = [a for a in proxy["approaches"] if a["id"] in proxy["f2_measured_approaches"]]
    sw = site_net.getEdge(app["edge"] + ".sidewalk")
    (lane,) = sw.getLanes()
    assert lane.getPermissions() == {"custom1"} and not sw.getName()
    assert round(lane.getWidth(), 2) == app["sidewalk_width_m"] and round(lane.getSpeed(), 2) == app["sidewalk_speed_mps"]
    assert sw.getFromNode().getID() == app["edge"] + ".sidewalk_start"
    mid, up = site_net.getEdge(app["edge"] + ".mid"), site_net.getEdge(app["edge"] + ".up")
    start = sum(e.getLanes()[0].getLength() for e in (site_net.getEdge(app["edge"]), mid)) + 0.1  # + bollard node
    assert abs(start - app["sidewalk_start_m"]) <= 0.25
    into_sw = [c for c in up.getOutgoing()[sw]]
    assert [(c.getFromLane().getIndex(), c.getToLane().getIndex()) for c in into_sw] == [(0, 0)]
    assert sorted((c.getFromLane().getIndex(), c.getToLane().getIndex()) for c in up.getOutgoing()[mid]) == \
        [(0, 0), (1, 1), (2, 2)]
    # road links keep the base net's link indices; the two sidewalk links come last
    base = sumolib.net.readNet(str(out_dir / "base.net.xml"), withPrograms=True)
    key = lambda il, ol: (il.getEdge().getID(), il.getIndex(), ol.getEdge().getID(), ol.getIndex())
    before = sorted((i, key(il, ol)) for il, ol, i in target_tls(base).getConnections())
    after = sorted((i, key(il, ol)) for il, ol, i in target_tls(site_net).getConnections())
    assert after[:len(before)] == before and len(after) == len(before) + 2
    exits = {movement_of(c.getDirection()): (i, c.getTo().getID()) for i, (_, k) in enumerate(after[len(before):])
             for c in sw.getOutgoing()[site_net.getEdge(k[2])]}
    conns = _conns_from(site_net, app["edge"])
    road = {movement_of(c.getDirection()): c.getTo().getID() for c in conns if movement_of(c.getDirection()) in "rs"}
    assert {m: e for m, (_, e) in exits.items()} == road
    straight = next(c.getTLLinkIndex() for c in conns if c.getFromLane().getIndex() == 1 and movement_of(c.getDirection()) == "s")
    for state in _states(site_net):  # exits[mv][0] = offset after the road links
        assert state[len(before) + exits["r"][0]] == "g"
        assert state[len(before) + exits["s"][0]] == state[straight]
    assert "G" in {s[len(before) + exits["s"][0]] for s in _states(site_net)}  # priority over the road (3B)
    for c in sw.getOutgoing().values():
        for x in c:
            assert site_net.getLane(x.getViaLaneID()).getPermissions() == {"custom1"}
    assert sorted(p.name for p in (out_dir / "patches" / "site.proxy").iterdir()) == [
        "bollards.edg.xml", "lanes.edg.xml", "sidewalk.con.xml", "sidewalk.edg.xml", "signal.tll.xml",
        "split.edg.xml", "turns.con.xml"]


def test_short_run_on_new_net(built):
    """120 s of PROXY_D1 with the B0 vTypes (incl. car_violator) loads and runs on the new net: no passenger /
    motorcycle ever drives the violator-only lane-0 straight, and right turns move while their approach is red."""
    import libsumo

    out_dir, _ = built
    net = sumolib.net.readNet(str(out_dir / "site.proxy.net.xml"), withInternal=True, withPrograms=True)
    vio_lanes, right_lanes = set(), {}
    for edge in (a["edge"] for a in load_site(PROXY)["approaches"]):
        for c in _conns_from(net, edge):
            if c.getFromLane().getIndex() == 0 and movement_of(c.getDirection()) == "s":
                vio_lanes.add(c.getViaLaneID())
            if movement_of(c.getDirection()) == "r":
                straight = next(x.getTLLinkIndex() for x in _conns_from(net, edge)
                                if x.getFromLane().getIndex() == 1 and movement_of(x.getDirection()) == "s")
                right_lanes[c.getViaLaneID()] = straight
    libsumo.start([sumolib.checkBinary("sumo"), "-n", str(out_dir / "site.proxy.net.xml"),
                   "-r", str(REPO_ROOT / "scenario" / "demand" / "routes_PROXY_D1.rou.xml"),
                   "-a", str(REPO_ROOT / "rules" / "compiled" / "B0" / "vtypes.add.xml"),
                   "--step-length", "0.1", "--lateral-resolution", "0.4", "--seed", "1", "--end", "120",
                   "--no-step-log", "true"])
    tls = target_tls(net).getID()
    on_red = teleports = 0
    try:
        assert "car_violator_B0" in libsumo.vehicletype.getIDList()
        while libsumo.simulation.getTime() < 120:
            libsumo.simulationStep()
            teleports += libsumo.simulation.getStartingTeleportNumber()
            state = libsumo.trafficlight.getRedYellowGreenState(tls)
            for v in libsumo.vehicle.getIDList():
                lane = libsumo.vehicle.getLaneID(v)
                if lane in vio_lanes:
                    assert libsumo.vehicle.getVehicleClass(v) in ("custom1", "custom2"), (v, lane)
                if lane in right_lanes and state[right_lanes[lane]] == "r":
                    on_red += 1
    finally:
        libsumo.close()
    assert on_red > 0 and teleports == 0


# --- helpers ---------------------------------------------------------------------------------------

def _conns_from(net, edge_id):
    edge = net.getEdge(edge_id)
    return [c for conns in edge.getOutgoing().values() for c in conns]


def _link(net, idx):
    tls = target_tls(net)
    for in_lane, out_lane, i in tls.getConnections():
        if i == idx:
            for c in in_lane.getOutgoing():
                if c.getToLane() == out_lane:
                    return c
    raise KeyError(idx)
