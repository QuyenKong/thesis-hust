"""Demand (PLAN Phase 2.1-2.2): B0 vTypes, candidate routes, routeSampler from turn counts.

Runs on the committed proxy network `scenario/net/site.proxy.net.xml` (built by Task 2).
"""

from collections import Counter
from pathlib import Path

import pandas as pd
import pytest
import sumolib
from lxml import etree

from thesis_sumo.config import REPO_ROOT
from thesis_sumo.demand.build_demand import (
    MOVEMENTS,
    TURN_COUNT_COLUMNS,
    VEHICLE_TYPES,
    build_candidate_routes,
    build_demand,
    read_candidates,
)
from thesis_sumo.net.build_net import approach_edges, inbound_edges, target_node, target_tls

NET = REPO_ROOT / "scenario" / "net" / "site.proxy.net.xml"
B0_VTYPES = REPO_ROOT / "rules" / "compiled" / "B0" / "vtypes.add.xml"
SYNTHETIC = REPO_ROOT / "data" / "observed" / "SYNTHETIC"
INTERVAL_S = 900

# small synthetic count table: two 15-min intervals, both vclasses, every movement kind
SMALL_COUNTS = [
    # interval_start, interval_end, approach, movement, vclass, count
    (0, 900, "LVL_W", "s", "moto", 40), (0, 900, "LVL_W", "s", "car", 12),
    (0, 900, "LVL_W", "r", "moto", 9), (0, 900, "LVL_W", "illegal_l", "moto", 5),
    (0, 900, "LVL_W", "u", "moto", 2), (0, 900, "LVL_E", "l", "car", 3),
    (0, 900, "LVL_E", "s", "moto", 30), (0, 900, "HDT_N", "l", "moto", 6),
    (0, 900, "HDT_S", "r", "car", 4),
    (900, 1800, "LVL_W", "s", "moto", 55), (900, 1800, "LVL_W", "illegal_l", "moto", 8),
    (900, 1800, "LVL_E", "s", "car", 10), (900, 1800, "HDT_N", "s", "moto", 20),
    (900, 1800, "HDT_S", "u", "car", 1),
]


def _write_counts(path: Path, rows) -> Path:
    pd.DataFrame(rows, columns=TURN_COUNT_COLUMNS).to_csv(path, index=False, lineterminator="\n")
    return path


@pytest.fixture(scope="module")
def net():
    return sumolib.net.readNet(str(NET))


@pytest.fixture(scope="module")
def candidates(tmp_path_factory):
    return build_candidate_routes(NET, tmp_path_factory.mktemp("cand") / "candidate_routes.rou.xml")


@pytest.fixture(scope="module")
def sampled(tmp_path_factory, candidates):
    d = tmp_path_factory.mktemp("demand")
    counts = _write_counts(d / "turn_counts.csv", SMALL_COUNTS)
    return build_demand(counts, candidates, d / "routes.rou.xml", seed=7)


def _vehicles(routes: Path) -> list[dict]:
    out = []
    for v in etree.parse(str(routes)).getroot().iter("vehicle"):
        (r,) = v.findall("route")
        out.append({"id": v.get("id"), "depart": float(v.get("depart")), "type": v.get("type"),
                    "edges": tuple(r.get("edges").split())})
    return out


# --- tests named in the task brief -------------------------------------------------------------

def test_candidate_routes_cover_all_movements(net, candidates):
    """Every inbound -> outbound pair the net connects (for any vClass) appears exactly once."""
    node = target_node(target_tls(net))
    expected = {(e.getID(), to.getID()) for e in inbound_edges(node) for to in e.getOutgoing()}
    routes = etree.parse(str(candidates)).getroot().findall("route")
    pairs = [tuple(r.get("edges").split()) for r in routes]
    assert Counter(pairs) == Counter(expected)  # each once, nothing else
    assert len(expected) == 16  # 4 arms x (r, s, l, u)

    cands = read_candidates(candidates)
    approach_of = {e: a for a, e in approach_edges(net).items()}
    for (app, mv), edges in cands.items():
        assert approach_of[edges[0]] == app
        assert mv in MOVEMENTS
    # LVL_W left is banned and re-added for custom1 only (Task 2) -> the illegal left movement
    assert ("LVL_W", "illegal_l") in cands and ("LVL_W", "l") not in cands
    for app in ("LVL_E", "HDT_N", "HDT_S"):
        assert {(app, m) for m in ("l", "s", "r", "u")} <= set(cands)


def test_routesampler_matches_counts(sampled, candidates):
    """Sampled vehicles per 15-min cell (approach x movement x vclass) within +-1 of the input."""
    edges_to_mv = {edges: key for key, edges in read_candidates(candidates).items()}
    vclass_of = {"car": "car", "moto": "moto", "moto_violator": "moto"}
    got = Counter()
    for v in _vehicles(sampled):
        app, mv = edges_to_mv[v["edges"]]
        start = int(v["depart"] // INTERVAL_S) * INTERVAL_S
        got[(start, app, mv, vclass_of[v["type"]])] += 1
    want = {(s, a, m, c): n for s, _, a, m, c, n in SMALL_COUNTS}
    for cell in set(got) | set(want):
        assert abs(got[cell] - want.get(cell, 0)) <= 1, (cell, got[cell], want.get(cell, 0))
    # totals are exact (routeSampler matched every count; only interval edges may shift by rounding)
    assert sum(got.values()) == sum(want.values())


def test_violator_type_mapping(sampled, candidates):
    """`illegal_l` -> type `moto_violator`; other moto -> `moto`; car -> `car`; ids unique, departs sorted."""
    cands = read_candidates(candidates)
    illegal = {edges for (_, mv), edges in cands.items() if mv == "illegal_l"}
    vehs = _vehicles(sampled)
    assert {v["type"] for v in vehs} == set(VEHICLE_TYPES)
    for v in vehs:
        assert (v["type"] == "moto_violator") == (v["edges"] in illegal), v
    want = Counter()
    for _, _, _, mv, vc, n in SMALL_COUNTS:
        want["moto_violator" if mv == "illegal_l" else vc] += n
    assert Counter(v["type"] for v in vehs) == want
    assert len({v["id"] for v in vehs}) == len(vehs)
    departs = [v["depart"] for v in vehs]
    assert departs == sorted(departs)


# --- further behaviour ---------------------------------------------------------------------------

def test_car_illegal_left_rejected(tmp_path, candidates):
    counts = _write_counts(tmp_path / "c.csv", [(0, 900, "LVL_W", "illegal_l", "car", 1)])
    with pytest.raises(ValueError, match="illegal_l"):
        build_demand(counts, candidates, tmp_path / "r.rou.xml", seed=1)


def test_banned_movement_rejected(tmp_path, candidates):
    """A legal `l` count on the banned approach has no route; it must fail, not be dropped."""
    counts = _write_counts(tmp_path / "c.csv", [(0, 900, "LVL_W", "l", "moto", 1)])
    with pytest.raises(ValueError, match="LVL_W"):
        build_demand(counts, candidates, tmp_path / "r.rou.xml", seed=1)


def test_bad_columns_rejected(tmp_path, candidates):
    path = tmp_path / "c.csv"
    pd.DataFrame([(0, 900, "LVL_W", "s", "moto", 1)],
                 columns=["start", "end", "approach", "movement", "vclass", "count"]).to_csv(path, index=False)
    with pytest.raises(ValueError, match="columns"):
        build_demand(path, candidates, tmp_path / "r.rou.xml", seed=1)


def test_interval_not_15_min_rejected(tmp_path, candidates):
    counts = _write_counts(tmp_path / "c.csv", [(0, 600, "LVL_W", "s", "moto", 1)])
    with pytest.raises(ValueError, match="900"):
        build_demand(counts, candidates, tmp_path / "r.rou.xml", seed=1)


def test_demand_deterministic(tmp_path, candidates):
    counts = _write_counts(tmp_path / "c.csv", SMALL_COUNTS)
    a = build_demand(counts, candidates, tmp_path / "a.rou.xml", seed=3)
    b = build_demand(counts, candidates, tmp_path / "b.rou.xml", seed=3)
    c = build_demand(counts, candidates, tmp_path / "c.rou.xml", seed=4)
    assert _vehicles(a) == _vehicles(b)
    assert _vehicles(a) != _vehicles(c)


def test_b0_distribution_ids():
    root = etree.parse(str(B0_VTYPES)).getroot()
    dists = {d.get("id"): d.findall("vType") for d in root.iter("vTypeDistribution")}
    assert set(dists) == set(VEHICLE_TYPES) | {"car_violator"}  # car_violator: no demand references it yet (F2-net)
    vclass = {k: [t.get("vClass") for t in v] for k, v in dists.items()}
    assert vclass == {"car": ["passenger"], "moto": ["motorcycle"], "moto_violator": ["custom1"],
                      "car_violator": ["custom2"]}
    for types in dists.values():
        assert all(t.get("laneChangeModel") == "SL2015" for t in types)


@pytest.mark.parametrize("base, violator, vclass", [("moto_B0", "moto_violator_B0", "custom1"),
                                                     ("car_B0", "car_violator_B0", "custom2")])
def test_violator_matches_base_defaults(base, violator, vclass):
    """Loaded in SUMO, moto_violator (custom1) equals the motorcycle defaults and car_violator (custom2) the
    passenger defaults in every vType getter."""
    import libsumo

    libsumo.start([sumolib.checkBinary("sumo"), "-n", str(NET), "-a", str(B0_VTYPES), "--end", "1",
                   "--no-step-log", "true"])
    try:
        vt = libsumo.vehicletype
        skip = {"getIDList", "getIDCount", "getVehicleClass"}
        getters = [g for g in dir(vt) if g.startswith("get") and g not in skip
                   and "Subscription" not in g and "Parameter" not in g]
        assert len(getters) > 20
        diffs = {g: (getattr(vt, g)(base), getattr(vt, g)(violator)) for g in getters
                 if getattr(vt, g)(base) != getattr(vt, g)(violator)}
        assert diffs == {}
        assert vt.getVehicleClass(violator) == vclass
    finally:
        libsumo.close()


def test_synthetic_counts_marked_and_valid(candidates):
    """data/observed/SYNTHETIC is a pipeline test input, clearly marked, in the Phase 5.1 schema."""
    assert (SYNTHETIC / "SYNTHETIC").is_file()
    # README.md moved to docs/SYNTHETIC_README.md; the marker file itself carries the warning
    assert "Never use in results" in (SYNTHETIC / "SYNTHETIC").read_text(encoding="utf-8")
    df = pd.read_csv(SYNTHETIC / "turn_counts.csv")
    assert list(df.columns) == TURN_COUNT_COLUMNS
    assert set(df["vclass"]) == {"car", "moto"}
    assert (df["interval_end"] - df["interval_start"] == INTERVAL_S).all()
    cands = read_candidates(candidates)
    assert set(zip(df["approach"], df["movement"])) <= set(cands)
    assert df.loc[df["vclass"] == "moto", "count"].sum() > df.loc[df["vclass"] == "car", "count"].sum()
