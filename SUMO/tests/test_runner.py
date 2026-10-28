"""Runner, manifest and conversion of SUMO output to the PLAN 5.1 observed-data schema (PLAN Phase 2.4)."""

import copy
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import sumolib

from thesis_sumo.config import REPO_ROOT, load_experiment, load_site
from thesis_sumo.schema_observed import TABLES, cycle_id_at, cycle_table, green_onsets
from thesis_sumo.sim import outputs, runner
from thesis_sumo.sim.sumocfg import violator_ids

PROXY_SITE = REPO_ROOT / "config" / "site.proxy.yaml"
PROXY_NET = REPO_ROOT / "scenario" / "net" / "site.proxy.net.xml"
SHORT_END_S = 300
MANIFEST_KEYS = {"git_hash", "sumo_version", "spec_hash", "net_hash", "seed", "config", "site_source",
                 "n_teleports", "n_collisions", "insertion_backlog", "valid", "valid_strict",
                 "n_teleports_noncollision", "collisions_by_class", "n_collisions_intervened"}


def _cfg_options(cfg: Path) -> dict[str, str]:
    from lxml import etree
    return {el.tag: el.get("value") for sec in etree.parse(str(cfg)).getroot() for el in sec if isinstance(el.tag, str)}


@pytest.fixture(scope="module")
def proxy_run(tmp_path_factory):
    root = tmp_path_factory.mktemp("runs")
    return runner.run("B0", "SYNTHETIC", seed=1, site_path=PROXY_SITE, sim_end_s=SHORT_END_S, runs_root=root)


# ---------------------------------------------------------------- manifest


def test_manifest_fields(proxy_run):
    m = proxy_run.manifest
    assert MANIFEST_KEYS <= set(m)
    assert proxy_run.run_dir.name == "seed_01" and proxy_run.run_dir.parent.name == "B0__SYNTHETIC"
    assert json.loads((proxy_run.run_dir / "manifest.json").read_text(encoding="utf-8")) == m
    assert m["seed"] == 1 and m["site_source"] == "LITERATURE_PROXY"
    assert "1.27.0" in m["sumo_version"]
    assert m["net_hash"] == hashlib.sha256(PROXY_NET.read_bytes()).hexdigest()
    assert len(m["git_hash"]) == 40 and len(m["spec_hash"]) == 64
    assert m["config"]["sim"]["end_s"] == SHORT_END_S
    assert isinstance(m["n_teleports"], int) and isinstance(m["n_collisions"], int)
    assert isinstance(m["insertion_backlog"], int)
    assert m["valid_strict"] == m["valid"] == (m["n_teleports"] == 0 and m["n_collisions"] == 0)
    assert set(m["collisions_by_class"]) == {"rear_end", "lateral", "junction", "other"}
    assert sum(m["collisions_by_class"].values()) == m["collisions"]["collision_output_records"]
    assert m["n_collisions_intervened"] == 0  # no controller
    assert m["interventions"] is None and m["interventions_log"] is None  # B0: no traci_rules.json, no controller
    # R28: junction collisions are checked and counted apart
    assert m["sumo_options"]["collision.check-junctions"] == "true"
    assert m["n_collisions_lane"] + m["n_collisions_junction"] == m["n_collisions"]
    assert not (proxy_run.run_dir / "interventions.csv").exists()
    # R22 defaults: no SSM device, warnings aggregated
    assert m["config"]["sim"]["ssm"]["mode"] == "off"
    assert not [k for k in m["sumo_options"] if k.startswith("device.ssm")]
    assert not (proxy_run.run_dir / "ssm.xml").exists()
    assert m["sumo_options"]["aggregate-warnings"] == "20"
    assert m["ssm_n_explicit"] == 0


def _tiny_cross(d: Path) -> Path:
    """One signalised single-lane cross junction whose arms carry the site street names."""
    (d / "n.nod.xml").write_text(
        '<nodes><node id="C" x="0" y="0" type="traffic_light"/><node id="W" x="-150" y="0"/>'
        '<node id="E" x="150" y="0"/><node id="S" x="0" y="-150"/><node id="N" x="0" y="150"/></nodes>',
        encoding="utf-8")
    edges = [("WC", "W", "C", "Le Van Luong"), ("CE", "C", "E", "Le Van Luong"), ("EC", "E", "C", "Le Van Luong"),
             ("CW", "C", "W", "Le Van Luong"), ("SC", "S", "C", "Hoang Dao Thuy"), ("CN", "C", "N", "Hoang Dao Thuy"),
             ("NC", "N", "C", "Hoang Dao Thuy"), ("CS", "C", "S", "Hoang Dao Thuy")]
    (d / "n.edg.xml").write_text("<edges>" + "".join(
        f'<edge id="{i}" from="{f}" to="{t}" name="{n}" numLanes="1" speed="13.9"/>' for i, f, t, n in edges)
        + "</edges>", encoding="utf-8")
    net = d / "tiny.net.xml"
    subprocess.run([sumolib.checkBinary("netconvert"), "-n", str(d / "n.nod.xml"), "-e", str(d / "n.edg.xml"),
                    "-o", str(net)], check=True, capture_output=True)
    return net


def test_teleport_marks_invalid(tmp_path):
    net = _tiny_cross(tmp_path)
    routes = tmp_path / "jam.rou.xml"
    # the leader stops on the single lane for longer than the run; the follower cannot pass and is
    # teleported after the SUMO default time-to-teleport (300 s)
    routes.write_text(
        '<routes><vehicle id="leader" type="car" depart="0"><route edges="WC CE"/>'
        '<stop lane="WC_0" endPos="100" duration="2000"/></vehicle>'
        '<vehicle id="follower" type="car" depart="2"><route edges="WC CE"/></vehicle></routes>',
        encoding="utf-8")
    inputs = runner.RunInputs(spec_id="B0", day="TINY", site=load_site(PROXY_SITE), net=net, routes=routes,
                              spec_dir=REPO_ROOT / "rules" / "compiled" / "B0")
    res = runner.run("B0", "TINY", seed=1, sim_end_s=400, runs_root=tmp_path / "runs", inputs=inputs)
    assert res.manifest["n_teleports"] >= 1 and res.manifest["n_teleports_noncollision"] == res.manifest["n_teleports"]
    assert res.manifest["n_collisions"] == 0
    assert res.manifest["valid_strict"] is False and res.manifest["valid"] is False
    assert any("teleport" in r for r in res.manifest["invalid_reasons"])


def test_malformed_traci_rules_raise(tmp_path):
    """A spec dir with traci_rules.json always gets the runtime controller (Task 9); a file that is not the
    compiler's format stops the run instead of silently dropping the rules."""
    spec = tmp_path / "spec"
    spec.mkdir()
    (spec / "vtypes.add.xml").write_bytes((REPO_ROOT / "rules" / "compiled" / "B0" / "vtypes.add.xml").read_bytes())
    (spec / "traci_rules.json").write_text("[]", encoding="utf-8")
    inputs = runner.RunInputs(spec_id="X", day="SYNTHETIC", site=load_site(PROXY_SITE), net=PROXY_NET,
                              routes=REPO_ROOT / "scenario" / "demand" / "routes_SYNTHETIC.rou.xml", spec_dir=spec)
    with pytest.raises(RuntimeError, match="expected the compiler's traci_rules.json"):
        runner.run("X", "SYNTHETIC", seed=1, sim_end_s=10, runs_root=tmp_path / "runs", inputs=inputs)


def test_missing_routes_raise(tmp_path):
    with pytest.raises(FileNotFoundError, match="routes_NO_SUCH_DAY"):
        runner.resolve_inputs("B0", "NO_SUCH_DAY", PROXY_SITE)


def test_run_many_parallel(tmp_path):
    res = runner.run_many([("B0", "SYNTHETIC", 1), ("B0", "SYNTHETIC", 2)], n_proc=2, site_path=PROXY_SITE,
                          sim_end_s=30, runs_root=tmp_path, ssm_mode="violators")
    assert [r.manifest["seed"] for r in res] == [1, 2]
    assert all((r.run_dir / "manifest.json").is_file() for r in res)
    n_viol = len(violator_ids(REPO_ROOT / "scenario" / "demand" / "routes_SYNTHETIC.rou.xml"))
    for r in res:  # the mode reaches every worker and is recorded as the effective config
        assert r.manifest["config"]["sim"]["ssm"]["mode"] == "violators"
        # the manifest keeps the count, the id list stays in run.sumocfg only
        assert r.manifest["ssm_n_explicit"] == n_viol > 0
        assert "," not in r.manifest["sumo_options"]["device.ssm.explicit"]
        cfg_ids = _cfg_options(r.run_dir / "run.sumocfg")["device.ssm.explicit"].replace(",", " ").split()
        assert len(cfg_ids) == n_viol


def test_cli_ssm_flag(tmp_path, monkeypatch, capsys):
    seen = {}

    def fake_run_many(jobs, n_proc, **kw):
        seen.update(kw)
        return []

    monkeypatch.setattr(runner, "run_many", fake_run_many)
    assert runner.main(["--spec", "B0", "--day", "SYNTHETIC", "--seeds", "1", "--ssm", "all"]) == 0
    assert seen["ssm_mode"] == "all"
    assert runner.main(["--spec", "B0", "--day", "SYNTHETIC", "--seeds", "1"]) == 0
    assert seen["ssm_mode"] is None  # -> experiment.yaml sim.ssm.mode
    with pytest.raises(SystemExit):
        runner.main(["--spec", "B0", "--day", "SYNTHETIC", "--seeds", "1", "--ssm", "some"])


# ---------------------------------------------------------------- observed schema on a real run


@pytest.fixture(scope="module")
def observed(proxy_run):
    return {name: pd.read_csv(proxy_run.run_dir / outputs.OBSERVED_DIR / f"{name}.csv") for name in TABLES}


def test_schema_columns(proxy_run, observed):
    for name, cols in TABLES.items():
        assert list(observed[name].columns) == cols, name
    assert set(outputs.to_observed_schema(proxy_run.run_dir)) == set(TABLES)


def test_signal_events_follow_program(observed):
    ev = observed["signal_events"]
    lvl = ev[ev["approach_group"] == "LVL_W"][["t", "state"]].values.tolist()  # the LVL straight head (3 stages)
    assert lvl == [[0, "G"], [42, "y"], [46, "r"], [120, "G"], [162, "y"], [166, "r"], [240, "G"], [282, "y"], [286, "r"]]
    hdt = ev[ev["approach_group"] == "HDT_N"][["t", "state"]].values.tolist()
    assert hdt == [[0, "r"], [70, "G"], [114, "y"], [118, "r"], [190, "G"], [234, "y"], [238, "r"]]
    assert sorted(ev["approach_group"].unique()) == ["HDT_N", "HDT_S", "LVL_E", "LVL_W"]
    assert list(green_onsets(ev, "LVL_W")) == [120, 240]  # t=0 is the start of the record, not an onset


def test_crossings_and_turn_counts(proxy_run, observed):
    cr, tc = observed["stopline_crossings"], observed["turn_counts"]
    assert len(cr) > 100 and cr["track_id"].is_unique
    assert set(cr["vclass"]) <= {"car", "moto"} and set(cr["signal_state_at_t"]) <= {"G", "y", "r"}
    widths = {a["id"]: sum(a["lane_widths_m"]) for a in load_site(PROXY_SITE)["approaches"]}
    lat_ok = cr.apply(lambda r: -0.5 <= r["lane_or_lat_m"] <= widths[r["approach"]] + 0.5, axis=1)
    assert lat_ok.all()
    assert (tc["interval_end"] - tc["interval_start"] == 900).all()
    assert tc["count"].sum() == len(cr)
    assert {"illegal_l"} <= set(tc["movement"]) and not ((tc["movement"] == "illegal_l") & (tc["vclass"] == "car")).any()


def test_snapshots_at_green_onsets(observed):
    q, lat = observed["queue_snapshots"], observed["lateral_snapshots"]
    lvl = q[q["approach"] == "LVL_W"]
    assert lvl["t_green_onset"].tolist() == [120, 240] and lvl["cycle_id"].tolist() == [0, 1]
    assert (q["queue_length_m"] >= 0).all() and (q["area_m2"] == q["queue_length_m"] * 10.5).all()
    assert (q["n_car"] + q["n_moto"] > 0).any()
    rng = load_experiment()["observation"]["queue_range_m"]
    assert (q["queue_length_m"] <= rng).all()
    assert set(lat["cycle_id"]) <= set(q["cycle_id"]) and (lat["long_m_from_stopline"] <= rng).all()


def test_box_queue_rows(observed):
    b = observed["box_queue"]
    # illegal lefts on HDT_N and HDT_S; the opposing (HDT_S / HDT_N) straight green ends at 114 s and 234 s
    assert sorted(b["approach"].unique()) == ["HDT_N", "HDT_S"]
    for _, rows in b.groupby("approach"):
        assert rows["t"].tolist() == [114, 234] and rows["cycle_id"].tolist() == [0, 1]
    assert (b["n_waiting_in_box"] >= 0).all()
    # B0: the cycle-0 box waiters have all left before the next HDT green onset (190 s)
    c0 = b[(b["cycle_id"] == 0) & b["t_clear_start"].notna()]
    assert len(c0) and (c0["t_clear_start"] <= c0["t_clear_end"]).all() and (c0["t_clear_end"] < 190).all()


def test_shared_green_check_needs_both_greens():
    """A record shorter than the first HDT green (70 s on the proxy program) cannot tell whether HDT_N and HDT_S
    share a green: no error (and no box_queue row)."""
    ev = pd.DataFrame([(0, "HDT_N", "r"), (0, "HDT_S", "r"), (0, "LVL_W", "G")], columns=["t", "approach_group", "state"])
    outputs.check_shared_green(ev, "HDT_N", "HDT_S")


def test_crossing_state_is_own_link():
    """signal_state_at_t = the state of the crossing vehicle's own TLS link (proxy net, its program): the LVL left in
    the LVL_left stage is G while the LVL straight head is red; the HDT illegal left follows the HDT green; the
    continuous right turn is G in every stage; a sidewalk straight follows the LVL straight."""
    geo = outputs.junction_geometry(PROXY_NET)
    (prog,) = sumolib.net.readNet(str(PROXY_NET), withPrograms=True).getTrafficLights()[0].getPrograms().values()
    starts = np.cumsum([0] + [p.duration for p in prog.getPhases()])[:-1]
    tls = pd.DataFrame({"t": starts, "state": [p.state for p in prog.getPhases()]})
    w, n, e = "711526326#1", "953158817#2", "37876499#0"
    cr = pd.DataFrame([(50, f"{w}_2", "LVL_W", "408823207#0"), (50, f"{w}_2", "LVL_W", "37877893#0"),
                       (80, f"{n}_2", "HDT_N", "37877893#0"), (50, f"{n}_2", "HDT_N", "37877893#0"),
                       (50, f"{w}_0", "LVL_W", "37871458#0"), (10, f"{e}.sidewalk_0", "LVL_E", "711526328#0"),
                       (50, f"{e}.sidewalk_0", "LVL_E", "711526328#0")], columns=["t", "lane", "approach", "exit_edge"])
    assert list(outputs.crossing_states(cr, tls, geo)) == ["G", "r", "G", "r", "G", "G", "r"]


# ---------------------------------------------------------------- derivations on hand-made data


def _tls(records):
    return pd.DataFrame(records, columns=["t", "state"])


def test_signal_events_definition():
    tls = _tls([(0.0, "GGr"), (0.1, "GGr"), (0.2, "yyr"), (0.3, "rrG"), (0.4, "GgR")])
    ev = outputs.signal_events(tls, {"A": [0, 1], "B": [2]})
    assert ev.values.tolist() == [[0.0, "A", "G"], [0.0, "B", "r"], [0.2, "A", "y"], [0.3, "A", "r"],
                                  [0.3, "B", "G"], [0.4, "A", "G"], [0.4, "B", "r"]]
    assert list(green_onsets(ev, "A")) == [0.4] and list(green_onsets(ev, "B")) == [0.3]
    assert cycle_id_at(green_onsets(ev, "A"), [0.1, 0.4, 0.5]).tolist() == [-1, 0, 0]
    with pytest.raises(ValueError, match="disagree"):
        outputs.signal_events(_tls([(0.0, "Gyr")]), {"A": [0, 1]})


def test_cycle_table():
    ev = pd.DataFrame([(0, "A", "r"), (10, "A", "G"), (40, "A", "y"), (44, "A", "r"), (60, "A", "G"), (90, "A", "y")],
                      columns=["t", "approach_group", "state"])
    ct = cycle_table(ev, "A")
    assert ct["t_green_onset"].tolist() == [10, 60] and ct["t_red_onset"].tolist()[0] == 44
    assert ct["t_next_green_onset"].tolist()[0] == 60 and np.isnan(ct["t_next_green_onset"].tolist()[1])
    assert np.isnan(ct["t_red_onset"].tolist()[1]) and ct["t_yellow_onset"].tolist()[1] == 90


def test_queue_definition():
    frame = pd.DataFrame([  # front distance upstream of the stop line, length, speed
        ("m1", "moto", 0.5, 2.2, 0.0), ("m2", "moto", 0.5, 2.2, 0.0), ("c1", "car", 3.0, 5.0, 0.2),
        ("m3", "moto", 15.0, 2.2, 0.0),   # 15 <= 8 + 10 (jam gap): queued, tail 17.2
        ("c2", "car", 20.0, 5.0, 5.0),    # moving: not part of the queue, does not break it
        ("m4", "moto", 30.0, 2.2, 0.0),   # 30 > 17.2 + 10: queue ends before it
    ], columns=["track_id", "vclass", "dist_m", "length", "speed"])
    assert outputs.queue_at(frame, 40.0) == pytest.approx((17.2, 1, 3))
    assert outputs.queue_at(frame, 16.0) == pytest.approx((16.0, 1, 3))  # censored: capped at the range
    assert outputs.queue_at(frame[frame["track_id"] == "m4"], 40.0) == (0.0, 0, 0)  # first halted vehicle too far
    assert outputs.queue_at(frame.iloc[0:0], 40.0) == (0.0, 0, 0)


def test_box_queue_definition():
    box_rows = pd.DataFrame([
        (10.0, "v1", 0.0), (10.0, "v2", 0.5),  # halting in the box at the opposing green end t=10
        (8.0, "v3", 5.0),                       # entered in cycle 0, leaves early through a gap
        (12.0, "v5", 0.0),                      # halts later in the same cycle
        (9.0, "v6", 0.0),                       # removed (collision teleport) while in the box
        (30.0, "v4", 0.0),                      # cycle 1, never leaves before the record ends
    ], columns=["t", "track_id", "speed"])
    exits = pd.DataFrame([("v1", 13.0, "exit"), ("v2", 15.5, "exit"), ("v3", 8.5, "exit"), ("v5", 16.0, "exit"),
                          ("v6", 9.5, "removed"), ("v1", 2.0, "exit")], columns=["track_id", "t", "kind"])
    b = outputs.box_queue_rows("A", opposing_ends=[10.0, 30.0, 45.0], onsets=[5.0, 25.0, 40.0],
                               box_rows=box_rows, box_exits=exits)
    assert list(b.columns) == TABLES["box_queue"]
    assert b["cycle_id"].tolist() == [0, 1, 2] and b["n_waiting_in_box"].tolist() == [2, 1, 0]
    # clearing = first / last box exit of every vehicle that entered the box in the cycle (v1, v2, v3, v5);
    # the removed v6 is left out and does not make t_clear_end NaN; t_clear_start precedes t
    assert b.iloc[0][["t_clear_start", "t_clear_end"]].tolist() == [8.5, 16.0]
    assert b.iloc[1][["t_clear_start", "t_clear_end"]].isna().all()  # v4 still in the box at the end
    assert b.iloc[2][["t_clear_start", "t_clear_end"]].isna().all()  # nobody entered in cycle 2


# ---------------------------------------------------------------- validity / eligibility


def _manifest(**kw):
    m = {"config": {"sim": {"begin_s": 0, "end_s": 1800}}, "n_teleports_noncollision": 0, "insertion_backlog": 0,
         "n_collisions": 1, "n_collisions_lane": 1, "n_collisions_junction": 0, "n_collisions_intervened": 0}
    m.update(kw)
    return m


LIMITS = {"max_noncollision_teleports": 0, "max_end_backlog": 0, "max_collisions_per_hour": 2,
          "max_junction_collisions_per_hour": 4, "max_intervened_collisions": 1}


@pytest.mark.parametrize("key", ["max_collisions_per_hour", "max_junction_collisions_per_hour"])
def test_is_eligible_needs_collision_threshold(key):
    with pytest.raises(ValueError, match=f"validity.{key}.* is null"):
        runner.is_eligible(_manifest(), {"validity": {**LIMITS, key: None}})


def test_real_collision_thresholds_pending_R28():
    """R28: both caps are re-derived by the operator with --collision.check-junctions on; until then they are null
    (is_eligible raises), afterwards integers >= 2 (R24 procedure, floor 2)."""
    v = load_experiment()["validity"]
    for key in ("max_collisions_per_hour", "max_junction_collisions_per_hour"):
        assert key in v
        assert v[key] is None or (isinstance(v[key], int) and not isinstance(v[key], bool) and v[key] >= 2), key


def test_is_eligible_thresholds():
    """Lane collisions against max_collisions_per_hour, junction collisions against
    max_junction_collisions_per_hour (R28)."""
    exp = {"validity": LIMITS}
    assert runner.is_eligible(_manifest(), exp) == (True, [])        # 1 lane collision in 0.5 h = 2 per hour
    assert runner.is_eligible(_manifest(n_collisions=3, n_collisions_junction=2), exp) == (True, [])  # 4/h junction
    ok, why = runner.is_eligible(_manifest(n_collisions=5, n_collisions_lane=2, n_collisions_junction=3,
                                           n_teleports_noncollision=1, insertion_backlog=3,
                                           n_collisions_intervened=2), exp)
    assert not ok and len(why) == 5
    assert any("lane collisions per hour: 4" in w for w in why) and any("junction collisions per hour: 6" in w
                                                                      for w in why)


def test_junction_collision_split():
    coll = [{"type": "collision", "lane": "e_0"}, {"type": "junction", "lane": ":c_1_0"},
            {"type": "side", "lane": ":c_2_0"}, {"type": "side", "lane": "e_1"}]
    assert [runner.is_junction_collision(c) for c in coll] == [False, True, True, False]


def test_default_end_is_calib_end(tmp_path, monkeypatch):
    """R31: without sim_end_s / --end the run ends at sim.calib_end_s; an explicit end overrides it."""
    exp = load_experiment()
    assert exp["sim"]["calib_end_s"] == 1800
    fake = copy.deepcopy(exp)
    fake["sim"]["calib_end_s"] = 20
    monkeypatch.setattr(runner, "load_experiment", lambda: copy.deepcopy(fake))
    res = runner.run("B0", "SYNTHETIC", seed=1, site_path=PROXY_SITE, runs_root=tmp_path / "a")
    assert res.manifest["config"]["sim"]["end_s"] == 20
    assert float(_cfg_options(res.run_dir / "run.sumocfg")["end"]) == 20
    res = runner.run("B0", "SYNTHETIC", seed=1, site_path=PROXY_SITE, sim_end_s=10, runs_root=tmp_path / "b")
    assert res.manifest["config"]["sim"]["end_s"] == 10
    seen = {}
    monkeypatch.setattr(runner, "run_many", lambda jobs, n_proc, **kw: seen.update(kw) or [])
    runner.main(["--spec", "B0", "--day", "SYNTHETIC", "--seeds", "1"])
    assert seen["sim_end_s"] is None  # -> calib_end_s inside run()
    runner.main(["--spec", "B0", "--day", "SYNTHETIC", "--seeds", "1", "--end", "3600"])
    assert seen["sim_end_s"] == 3600


def test_summarise_log_counts_aggregated_warnings(tmp_path):
    """--aggregate-warnings (R22): SUMO prints the first lines of a type, then at the end one line
    `Warning: N total messages of type: <format>` where N includes the printed lines (checked on PROXY_D1 B0 300 s,
    SSM on all: 119468 = the line count without aggregation). Counts must be the totals."""
    geo = ("Cannot compute SSM due to bad internal lane geometry at junction '{j}'. Crossing point between traffic "
           "from links {a} and {b} not found.")
    lines = [f"Warning: {geo.format(j='c1', a=10, b=22)}"] * 3 + [
        "Warning: Vehicle 'car_0_14' performs emergency braking on lane '9531#2_2' with decel=9.00, wished=4.50, "
        "severity=1.00, time=206.50.",
        "Error: something",
        "Simulation ended at time: 300.00.",
        f"Warning: 119468 total messages of type: {geo.format(j='%', a='%', b='%')}",
    ]
    log = tmp_path / "sumo.log"
    log.write_text("\n".join(lines) + "\n", encoding="utf-8")
    n_warn, n_err, top = runner.summarise_log(log)
    assert n_warn == 119468 + 1 and n_err == 1
    key = "Warning: " + geo.format(j="*", a="#", b="#")
    assert top[key] == 119468 and list(top)[0] == key
    assert sum(top.values()) == n_warn and len(top) == 2


def test_summarise_log_plain_warnings(tmp_path):
    """No aggregation line (every run with < sim.aggregate_warnings lines per type): each line counts once,
    quoted names -> '*', numbers -> #, errors counted apart, non-message lines ignored."""
    log = tmp_path / "sumo.log"
    log.write_text("\n".join([
        "Loading done.",
        "Warning: Vehicle 'car_0_14' performs emergency braking on lane 'e#2_2' with decel=9.00, wished=4.50, "
        "severity=1.00, time=206.50.",
        "Warning: Vehicle 'moto_1_3' performs emergency braking on lane 'x_0' with decel=7.50, wished=4.00, "
        "severity=0.70, time=12.00.",
        "Warning: Teleporting vehicle 'car_0_9'; collision with vehicle 'moto_0_2', lane='e_1', gap=-0.50, "
        "latGap=-0.20, time=33.10, stage=move.",
        "Warning: Vehicle 'car_0_9' ends teleporting on edge 'f', time=33.20.",
        "Error: one",
        "Error: two",
    ]) + "\n", encoding="utf-8")
    n_warn, n_err, top = runner.summarise_log(log)
    assert (n_warn, n_err) == (4, 2)
    assert top == {
        "Warning: Vehicle '*' performs emergency braking on lane '*' with decel=#, wished=#, severity=#, time=#.": 2,
        "Warning: Teleporting vehicle '*'; collision with vehicle '*', lane='*', gap=-#, latGap=-#, time=#, "
        "stage=move.": 1,
        "Warning: Vehicle '*' ends teleporting on edge '*', time=#.": 1,
    }


def test_summarise_log_aggregate_keeps_other_types(tmp_path):
    """An aggregated format made mostly of placeholders must absorb only its own printed lines: a placeholder
    matches within one quoted name ('%') or one whitespace-free token (%), and the whole line must match."""
    fmt = "Vehicle '%' %."  # mostly placeholders
    log = tmp_path / "sumo.log"
    log.write_text("\n".join([
        "Warning: Vehicle 'a' stopped.",
        "Warning: Vehicle 'b' stopped.",
        "Warning: Vehicle 'c' ends teleporting on edge 'f', time=3.00.",     # another type: must stay
        "Warning: Vehicle 'd' performs emergency braking on lane 'x' with decel=9.00, wished=4.50, "
        "severity=1.00, time=2.00.",                                          # another type: must stay
        f"Warning: 50 total messages of type: {fmt}",
    ]) + "\n", encoding="utf-8")
    n_warn, _, top = runner.summarise_log(log)
    assert top == {
        "Warning: Vehicle '*' #.": 50,
        "Warning: Vehicle '*' ends teleporting on edge '*', time=#.": 1,
        "Warning: Vehicle '*' performs emergency braking on lane '*' with decel=#, wished=#, severity=#, time=#.": 1,
    }
    assert n_warn == 52


def test_relative_runs_root(tmp_path, monkeypatch):
    """Tasks 11/13 pass runs_root; a relative one must work (write_sumocfg resolves the run dir)."""
    monkeypatch.chdir(tmp_path)
    res = runner.run("B0", "SYNTHETIC", seed=1, site_path=PROXY_SITE, sim_end_s=10, runs_root=Path("rel_runs"))
    assert (tmp_path / "rel_runs" / "B0__SYNTHETIC" / "seed_01" / "manifest.json").is_file()


def test_collision_classes_and_intervened():
    coll = [{"time": "1.0", "type": "collision", "collider": "a", "victim": "b"},
            {"time": "2.0", "type": "side", "collider": "c", "victim": "d"},
            {"time": "3.0", "type": "junction", "collider": "e", "victim": "a"},
            {"time": "4.0", "type": "frontal", "collider": "f", "victim": "g"}]
    assert runner.collision_classes(coll) == {"rear_end": 1, "lateral": 1, "junction": 1, "other": 1}
    with pytest.raises(ValueError, match="not a documented SUMO collision type"):
        runner.collision_classes([{"type": "bump"}])

    class Ctl:
        def intervened(self, vid, t):
            return vid == "a" and t < 2.5

    assert runner.count_intervened(coll, Ctl()) == 1 and runner.count_intervened(coll, object()) == 0
    assert runner.count_intervened(coll, None) == 0


def test_same_seed_same_observed_tables(tmp_path):
    hashes = []
    for k in (1, 2):
        res = runner.run("B0", "SYNTHETIC", seed=3, site_path=PROXY_SITE, sim_end_s=150, runs_root=tmp_path / str(k))
        hashes.append({p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in sorted((res.run_dir / outputs.OBSERVED_DIR).glob("*.csv"))})
    assert hashes[0] == hashes[1] and len(hashes[0]) == len(TABLES)
