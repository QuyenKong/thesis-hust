"""Config loading: the real site file must never fall back to proxy values (Review focus 1)."""

from pathlib import Path

import pytest
import yaml

from thesis_sumo.config import (
    EVIDENCE,
    EXPERIMENT_EVIDENCE,
    REPO_ROOT,
    MissingFieldDataError,
    allowed_evidence,
    load_experiment,
    load_llm,
    load_site,
)
from thesis_sumo.net.apply_patches import ILLEGAL_LEFT_MODES

SITE = REPO_ROOT / "config" / "site.yaml"
PROXY = REPO_ROOT / "config" / "site.proxy.yaml"
META_SUFFIXES = ("_source", "_evidence", "_transfer_note")


def test_required_null_raises():
    site = load_site(SITE)
    with pytest.raises(MissingFieldDataError) as exc:
        site.require("signal.cycle_s")
    assert "signal.cycle_s" in str(exc.value)


def test_proxy_site_marked():
    assert load_site(PROXY).source == "LITERATURE_PROXY"


def test_real_site_never_reads_proxy():
    site = load_site()  # default path must be the measured file, never the proxy
    assert site.path == SITE
    assert site.source == "MEASURED"
    assert site["signal"]["cycle_s"] is None


def test_require_returns_value_and_walks_lists():
    site = load_site(PROXY)
    assert site.require("signal.cycle_s") == site["signal"]["cycle_s"]
    assert site.require("approaches.0.id") == "LVL_W"
    with pytest.raises(MissingFieldDataError) as exc:
        load_site(SITE).require("approaches.0.lane_widths_m")
    assert "approaches.0.lane_widths_m" in str(exc.value)


def test_unknown_key_is_not_missing_field_data():
    with pytest.raises(KeyError):
        load_site(SITE).require("signal.no_such_key")


def test_bad_or_absent_site_source_rejected(tmp_path: Path):
    for text in ("signal: {cycle_s: null}\n", "site_source: GUESSED\n"):
        f = tmp_path / "site.yaml"
        f.write_text(text, encoding="utf-8")
        with pytest.raises(ValueError, match="site_source"):
            load_site(f)


def _strip_meta(node):
    """Drop `<key>_source` / `<key>_evidence` siblings of an existing `<key>`, keep structure."""
    if isinstance(node, dict):
        meta = {f"{k}{s}" for k in node for s in META_SUFFIXES}
        return {k: _strip_meta(v) for k, v in node.items() if k not in meta}
    if isinstance(node, list):
        return [_strip_meta(v) for v in node]
    return node


def _structure_diffs(measured, proxy, prefix=""):
    """Key mismatches, descending only where site.yaml has structure (a null may be filled freely)."""
    if isinstance(measured, dict):
        if not isinstance(proxy, dict) or set(measured) != set(proxy):
            return [prefix or "<root>"]
        return [d for k in measured for d in _structure_diffs(measured[k], proxy[k], f"{prefix}{k}.")]
    if isinstance(measured, list) and any(isinstance(v, dict) for v in measured):
        if not isinstance(proxy, list) or len(proxy) != len(measured):
            return [prefix]
        return [d for i, (m, p) in enumerate(zip(measured, proxy))
                for d in _structure_diffs(m, p, f"{prefix}{i}.")]
    return []


def test_proxy_has_same_structure_as_site():
    measured = yaml.safe_load(SITE.read_text(encoding="utf-8"))
    proxy = _strip_meta(yaml.safe_load(PROXY.read_text(encoding="utf-8")))
    assert _structure_diffs(measured, proxy) == []


def _filled_without_citation(measured, proxy, prefix=""):
    """Keys null (TODO_MEASURE / TODO_DECIDE) in site.yaml but filled in the proxy need _source and an _evidence
    allowed for that key (`config.allowed_evidence`)."""
    bad = []
    if isinstance(measured, dict):
        for key, m_val in measured.items():
            p_val = proxy.get(key)
            path = f"{prefix}{key}"
            if m_val is None and p_val is not None and key != "edge":  # edge ids come from Task 2 mapping
                src = proxy.get(f"{key}_source")
                ev = proxy.get(f"{key}_evidence")
                note = proxy.get(f"{key}_transfer_note")
                if (not (isinstance(src, str) and src.strip()) or ev not in allowed_evidence(path)
                        or (ev == "literature_transferred") != (isinstance(note, str) and bool(note.strip()))):
                    bad.append(path)
            else:
                bad += _filled_without_citation(m_val, p_val, f"{path}.")
    elif isinstance(measured, list) and isinstance(proxy, list):
        for i, (m_val, p_val) in enumerate(zip(measured, proxy)):
            bad += _filled_without_citation(m_val, p_val, f"{prefix}{i}.")
    return bad


def test_every_proxy_value_cites_source_and_evidence():
    measured = yaml.safe_load(SITE.read_text(encoding="utf-8"))
    proxy = yaml.safe_load(PROXY.read_text(encoding="utf-8"))
    assert _filled_without_citation(measured, proxy) == []


def test_experiment_evidence_only_for_allowed_keys():
    """`experiment` evidence is accepted only on the keys of config.EXPERIMENT_EVIDENCE_KEYS."""
    assert EXPERIMENT_EVIDENCE not in EVIDENCE
    assert EXPERIMENT_EVIDENCE in allowed_evidence("illegal_left.mode")
    assert allowed_evidence("signal.cycle_s") == EVIDENCE
    measured = {"signal": {"cycle_s": None}, "illegal_left": {"mode": None}}
    proxy = {"signal": {"cycle_s": 120, "cycle_s_source": "x", "cycle_s_evidence": EXPERIMENT_EVIDENCE},
             "illegal_left": {"mode": "native", "mode_source": "x", "mode_evidence": EXPERIMENT_EVIDENCE}}
    assert _filled_without_citation(measured, proxy) == ["signal.cycle_s"]


def test_illegal_left_mode_is_an_experiment_choice():
    """Phase 3 decision: a modelling choice in the proxy file (evidence `experiment`), TODO_DECIDE in site.yaml."""
    assert load_site(SITE)["illegal_left"]["mode"] is None
    proxy = load_site(PROXY)["illegal_left"]
    assert proxy["mode"] in ILLEGAL_LEFT_MODES
    assert proxy["mode_evidence"] == EXPERIMENT_EVIDENCE
    assert "experiments/phase3" in proxy["mode_source"]


def test_proxy_signal_phases_sum_to_cycle():
    site = load_site(PROXY)
    phases = site.require("signal.phases")
    assert sum(p["duration_s"] for p in phases) == site.require("signal.cycle_s")
    for p in phases:
        assert set(p) == {"name", "duration_s", "green_movements", "yellow_movements"}


def test_experiment_and_llm_load():
    assert load_experiment()["sim"]["step_length_s"] == 0.1
    assert load_llm()["max_retries"] == 3
