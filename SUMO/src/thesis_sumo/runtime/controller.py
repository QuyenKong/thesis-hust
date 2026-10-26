"""TraCI runtime controller (PLAN 4.5): runs the compiled TraCI rules of a spec during a SUMO run.

`Controller(rules, backend, site, log_path, radius_m=..., seed=...)`:

- `rules` = the `rules` list of `rules/compiled/<spec_id>/traci_rules.json` (thesis_sumo.rules.compiler): each
  entry has `rule_type`, `vtype_ids` (the member vType ids a vehicle reports via `vehicle.getTypeID`) and `params`
  (exactly `schema.TRACI_RULE_PARAMS[rule_type]`). One `RULE_REGISTRY` class per entry.
- The junction is read once through TraCI + the site file (`state.JunctionInfo`); each step one junction context
  subscription (radius `radius_m` around the target junction) and one TLS subscription feed a `state.Step` to every
  rule; vehicles outside the radius are never handled and no per-vehicle getter runs every step.
- Randomness: each rule draws from its own `random.Random("<seed>:<index>:<rule_type>")` (fixed by the run seed;
  string seeds are hashed with SHA-512 by `random`, independent of PYTHONHASHSEED). Vehicles are visited in sorted
  id order, so libsumo and traci give the same draws and the same log.
- `interventions.csv` (`base.LOG_COLUMNS`: t, veh_id, rule, action, executed, reason, t_end) gets one row per
  intervention once SUMO's response decided its outcome; `summary()` -> per rule_type attempted / executed, the
  reasons of the not-executed ones and the rule's counters (manifest `interventions`); `wall_s` = time spent in
  `on_step` (manifest `controller_wall_s`).
- `intervened(vid, t)`: was `vid` inside an intervention window at `t` (runner.count_intervened, rulings R10/R30:
  the window lasts until the vehicle is past the junction, `base.Commands`).

`make_controller(backend, inputs, run_dir, *, seed, radius_m)` is the runner's factory.
"""

from __future__ import annotations

import csv
import json
import random
import time
from collections import Counter
from pathlib import Path

from thesis_sumo.config import Site
from thesis_sumo.rules.schema import TRACI_RULE_PARAMS
from thesis_sumo.runtime.rules import RULE_REGISTRY
from thesis_sumo.runtime.rules.base import LOG_COLUMNS, Commands, Intervention
from thesis_sumo.runtime.state import JunctionInfo, StepReader

LOG_NAME = "interventions.csv"


def load_rules(path: Path) -> list[dict]:
    """The rule list of a compiled `traci_rules.json`; raises ValueError on anything else."""
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(doc, dict) or not isinstance(doc.get("rules"), list) or not doc["rules"]:
        raise ValueError(f"{path}: expected the compiler's traci_rules.json ({{'spec_id', 'archetypes', 'rules': "
                         f"[...]}}) with at least one rule")
    for i, r in enumerate(doc["rules"]):
        rtype = r.get("rule_type")
        if rtype not in RULE_REGISTRY:
            raise ValueError(f"{path}: rules[{i}].rule_type {rtype!r} not in {sorted(RULE_REGISTRY)}")
        if set(r.get("params", {})) != set(TRACI_RULE_PARAMS[rtype]):
            raise ValueError(f"{path}: rules[{i}] ({rtype}) params {sorted(r.get('params', {}))} != "
                             f"{sorted(TRACI_RULE_PARAMS[rtype])}")
        if not r.get("vtype_ids"):
            raise ValueError(f"{path}: rules[{i}] ({rtype}) has no vtype_ids")
    return doc["rules"]


class Controller:
    def __init__(self, rules: list[dict], backend, site: Site, log_path: Path, *, radius_m: float, seed: int = 0):
        types = {r["rule_type"] for r in rules}
        self.info = JunctionInfo.build(backend, site, need_lane_movements="wrong_lane_dodge" in types,
                                       need_box="illegal_left_box" in types)
        self.cmd = Commands(backend, self.info.lane_approach)
        self.rules = [RULE_REGISTRY[r["rule_type"]]({k: float(v) for k, v in r["params"].items()}, r["vtype_ids"],
                                                    self.info, self.cmd, random.Random(f"{seed}:{i}:{r['rule_type']}"))
                      for i, r in enumerate(rules)]
        self.reader = StepReader(backend, self.info, radius_m)
        self.log_path = Path(log_path)
        self._file = self.log_path.open("w", encoding="utf-8", newline="")
        self._csv = csv.writer(self._file, lineterminator="\n")
        self._csv.writerow(LOG_COLUMNS)
        self._stats = {r.rule_type: {"attempted": 0, "executed": 0, "not_executed": Counter()} for r in self.rules}
        self._t = 0.0
        self.wall_s = 0.0  # time spent in on_step (controller overhead)

    def on_step(self, t: float | None = None) -> None:
        t0 = time.perf_counter()
        step = self.reader.read()
        self._t = step.t
        self.cmd.update_windows(step)
        for rule in self.rules:
            self._log(rule.on_step(step))
        self.wall_s += time.perf_counter() - t0

    def _log(self, records: list[Intervention]) -> None:
        for rec in records:
            st = self._stats[rec.rule]
            st["attempted"] += 1
            if rec.executed:
                st["executed"] += 1
            else:
                st["not_executed"][rec.reason.split(":")[0]] += 1
            self._csv.writerow(rec.row())

    def intervened(self, vid: str, t: float) -> bool:
        return self.cmd.intervened(vid, t)

    def close(self) -> None:
        """Log interventions still running as `run_ended` and close the log (idempotent)."""
        if self._file.closed:
            return
        for rule in self.rules:
            self._log(rule.close(self._t))
        self._file.close()

    def summary(self) -> dict:
        out = {}
        for rule in self.rules:
            st = self._stats[rule.rule_type]
            prev = out.get(rule.rule_type, {"attempted": 0, "executed": 0, "not_executed": {}, "counters": {}})
            out[rule.rule_type] = {
                "attempted": st["attempted"], "executed": st["executed"],
                "not_executed": dict(sorted(st["not_executed"].items())),
                "counters": dict(sorted((Counter(prev["counters"]) + rule.counters).items())),
            }
        return out


def make_controller(backend, inputs, run_dir: Path, *, seed: int, radius_m: float) -> Controller:
    """Runner factory: the Controller for `inputs.traci_rules`, logging to `run_dir/interventions.csv`."""
    return Controller(load_rules(inputs.traci_rules), backend, inputs.site, Path(run_dir) / LOG_NAME,
                      radius_m=radius_m, seed=seed)
