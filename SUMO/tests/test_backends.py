"""libsumo and traci must give identical trajectories for the same scenario and seed."""

import subprocess

import pytest
import sumolib

STEPS = 300


@pytest.fixture(scope="module")
def tiny_scenario(tmp_path_factory):
    d = tmp_path_factory.mktemp("tiny")
    net = d / "net.net.xml"
    subprocess.run([sumolib.checkBinary("netgenerate"), "--grid", "--grid.number", "3",
                    "--grid.length", "100", "-o", str(net)], check=True, capture_output=True)
    routes = d / "routes.rou.xml"
    routes.write_text(
        '<routes><flow id="f" from="A0B0" to="B0C0" begin="0" end="60" number="20"/></routes>',
        encoding="utf-8")
    return net, routes


def _trajectory(backend, net, routes, seed):
    backend.start([sumolib.checkBinary("sumo"), "-n", str(net), "-r", str(routes),
                   "--seed", str(seed), "--no-step-log", "true", "--no-warnings", "true"])
    try:
        out = []
        for _ in range(STEPS):
            backend.simulationStep()
            for vid in backend.vehicle.getIDList():
                out.append((backend.simulation.getTime(), vid, backend.vehicle.getPosition(vid)))
        return out
    finally:
        backend.close()


def test_libsumo_matches_traci(tiny_scenario):
    import libsumo
    import traci

    net, routes = tiny_scenario
    via_libsumo = _trajectory(libsumo, net, routes, seed=7)
    via_traci = _trajectory(traci, net, routes, seed=7)
    assert via_libsumo, "no vehicles were simulated"
    assert via_libsumo == via_traci
