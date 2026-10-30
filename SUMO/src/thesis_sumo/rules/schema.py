"""The rule-spec space (PLAN 4.1-4.2): vType attribute bounds, TraCI rule parameters and the JSON schema.

- `load_bounds()` reads `rules/bounds/param_bounds.yaml` (every row cites the sumo.dlr.de page of its attribute).
  A row's `min/max/default` apply to every base vclass unless `by_vclass` overrides them; use
  `Bound.for_vclass(vclass)`.
- `TRACI_RULE_PARAMS`: per `rule_type` the parameters the runtime rules (Task 9) read, each with its range. All
  parameters of a rule are required in a spec (no defaults: the LLM / Optuna fills every one), except those marked
  `optional` (queue_space_seeking `t_w`: absent = no waiting-time trigger).
- `RULE_VCLASSES`: which archetype base vclasses a rule may be applied to.
- `DISTRIBUTION_OF_VCLASS`: archetype base vclass -> vTypeDistribution id referenced by the demand
  (`thesis_sumo.demand.build_demand.VEHICLE_TYPES`). `OPTIONAL_VCLASSES`: base vclasses whose distribution no
  demand references yet (custom2 = car_violator, Task F2-net): a spec may leave them out, and then the compiler
  writes no distribution for them.
- `DISTRIBUTIONS_OF_VCLASS`: the distributions an archetype of a base vclass may join (archetype key `distribution`,
  default `DISTRIBUTION_OF_VCLASS`). A violator archetype (custom1 / custom2, PLAN 0) may join the compliant
  distribution of its kind (`moto` / `car`): its riders then drive the legal movements of the demand but may use the
  violator-only space of `queue_space_seeking` (the custom1-only sidewalk; the demand gives custom1 only the illegal
  left, so this is how a straight motorcycle can reach the sidewalk without a TraCI type change, which would copy
  the vType to `typeid@vehid`). The share is then a share of that distribution: PLAN 4.1's `share` is "the share
  within the distribution" (Viktor accepted the `distribution` key, 2026-10-27, F2-behaviours fix round 1).
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from thesis_sumo.config import REPO_ROOT

BOUNDS_PATH = REPO_ROOT / "rules" / "bounds" / "param_bounds.yaml"
SCHEMA_PATH = REPO_ROOT / "rules" / "schema" / "rule_spec.schema.json"

VCLASSES = ("passenger", "motorcycle", "custom1", "custom2")
# archetype base vclass -> vTypeDistribution id (demand references these ids; PLAN 4.4)
DISTRIBUTION_OF_VCLASS = {"passenger": "car", "motorcycle": "moto", "custom1": "moto_violator",
                          "custom2": "car_violator"}
# car_violator (PLAN 2.1) is used only by the F2 rules that come after Phase 3; no demand references it yet
OPTIONAL_VCLASSES = ("custom2",)
DISTRIBUTIONS_OF_VCLASS = {"passenger": ("car",), "motorcycle": ("moto",), "custom1": ("moto_violator", "moto"),
                           "custom2": ("car_violator", "car")}
DISTRIBUTIONS = ("car", "moto", "moto_violator", "car_violator")  # compiler order
OPTIONAL_DISTRIBUTIONS = ("car_violator",)
BEHAVIOR_GROUPS = ("patience", "swarm_pressure", "early_start", "encroachment", "f_risk", "S_cheat", "I_slow",
                   "illegal_left_box")
MODELS = ("vType", "carFollow", "LC", "junction")
RANGE_EVIDENCE = ("docs", "ruling", "literature", "literature_transferred", "assumed")


@dataclass(frozen=True)
class Range:
    min: float | None
    max: float | None
    default: float | str


@dataclass(frozen=True)
class Bound:
    """One tunable vType attribute. `min/max/default` are the generic range (all vclasses without override)."""

    name: str
    min: float | None
    max: float | None
    default: float | str
    unit: str
    model: str
    source_url: str
    behavior_group: tuple[str, ...]
    constrained_by: tuple[str, ...] = ()
    fixed: bool = False
    values: tuple[str, ...] | None = None  # categorical attribute: the allowed strings
    by_vclass: dict[str, Range] = field(default_factory=dict)
    range_source: str | None = None
    range_evidence: str | None = None
    vclasses: tuple[str, ...] = VCLASSES  # base vclasses on which the attribute may be set
    vclasses_reason: str | None = None

    def for_vclass(self, vclass: str) -> Range:
        if vclass not in VCLASSES:
            raise ValueError(f"unknown base vclass {vclass!r}; expected one of {VCLASSES}")
        return self.by_vclass.get(vclass, Range(self.min, self.max, self.default))


@dataclass(frozen=True)
class RuleParam:
    min: float
    max: float
    unit: str
    reason: str
    optional: bool = False


# Ranges are modelling choices (evidence assumed unless stated). Units: s, m, m/s, probability "-", 1/veh.
TRACI_RULE_PARAMS: dict[str, dict[str, RuleParam]] = {
    "early_start": {
        "t_before_green": RuleParam(0.0, 10.0, "s", "window before green onset in which a front-row vehicle may "
                                    "creep over the stop line; 10 s = upper end of the M2 target lead time "
                                    "(data/proxy/targets.yaml early_start_lead_s 4-10 s)"),
        "p": RuleParam(0.0, 1.0, "-", "probability per front-row vehicle and red phase"),
        "v_max": RuleParam(0.5, 5.0, "m/s", "creep speed cap; 5 m/s = 18 km/h, assumed walking-to-slow-rolling range"),
    },
    "swarm_red_running": {
        "p0": RuleParam(0.0, 1.0, "-", "base probability to run the red for a vehicle at the stop line; Saval et al. "
                        "2023 (Sec 4) report 0.5 for front-row motorcycles in Hanoi, so the full [0, 1] is kept"),
        "k": RuleParam(0.0, 0.5, "1/veh", "increase of the probability per vehicle that ran the red on the same "
                       "approach within dt; 0 = no swarm effect; 0.5 assumed upper (two followers saturate p)"),
        "p_max": RuleParam(0.0, 1.0, "-", "cap of p0 + k*n; must be >= p0"),
        "dt": RuleParam(1.0, 30.0, "s", "look-back window for counting red runners; assumed, at most a quarter "
                        "of the 120 s proxy cycle"),
    },
    # PLAN 4.5 (behaviours 5-7; option `opposite` deferred, ruling R38): one draw per vehicle when the trigger first
    # holds, over the options that exist for it, the p_* of absent options redistributed proportionally
    "queue_space_seeking": {
        "q": RuleParam(5.0, 80.0, "m", "queue length on the vehicle's correct lanes (lane_movements) that triggers the "
                       "draw; 80 m = experiment.yaml observation.queue_range_m (queues beyond it are not observed); "
                       "Phase 3A used 50 m (setting)"),
        "t_w": RuleParam(5.0, 120.0, "s", "optional: the draw is also triggered once the vehicle has halted this long "
                         "on its approach (within the controller radius); 120 s = one proxy cycle; assumed",
                         optional=True),
        "t_g_s": RuleParam(0.0, 20.0, "s", "green check (PLAN 4.5 'đèn sắp xanh', Viktor 2026-10-27): this many seconds "
                           "before its approach's next green each queued vehicle not yet drawn estimates whether it "
                           "clears the stop line in that green (vehicles ahead x the approach's discharge headway of "
                           "the previous green, measured live) and draws if not; 0 = off. Viktor's example 7 s; 20 s "
                           "assumed upper bound (twice the 10 s early-start window, data/proxy/targets.yaml)"),
        "est_noise": RuleParam(0.0, 1.0, "-", "sigma of the multiplicative lognormal error of that estimate (median "
                               "unbiased); 1 = a factor e ~ 2.7 at one sigma; assumed"),
        "p_wrong_lane": RuleParam(0.0, 1.0, "-", "probability of the wrong_lane option (S_cheat: an adjacent lane whose "
                                  "markings do not permit the movement but which connects to the vehicle's next "
                                  "edge); inapplicable on the proxy net (ruling R27), so it is redistributed"),
        "p_right_lane": RuleParam(0.0, 1.0, "-", "probability of the right_lane option (behaviour 6, straight vehicles "
                                  "ride the continuous right-turn lane upstream of the bollards, Phase 3A); exists only "
                                  "where straight is not permitted from lane 0 and bollards separate it; not on the "
                                  "proxy net (no bollards, straight from lane 0 legal on green, 2026-10-28), so it is "
                                  "redistributed"),
        "p_sidewalk": RuleParam(0.0, 1.0, "-", "probability of the sidewalk option (behaviour 7, custom1 only, Phase "
                                "3B); p_wrong_lane + p_right_lane + p_sidewalk <= 1"),
        "v_creep": RuleParam(0.5, 5.0, "m/s", "speed cap while in the alternative space (PLAN 4.5 'tốc độ <= v_creep'); "
                             "5 m/s = the proxy sidewalk speed (Phase 3B setting); assumed"),
        "merge_zone_m": RuleParam(3.0, 20.0, "m", "right_lane: the lane-0 request ends this far upstream of the bollard "
                                  "edge and SL2015 merges the vehicle back (Phase 3A: 'a few metres to ~20 m', 15 m "
                                  "tested); assumed; no effect without bollards"),
    },
    "illegal_left_box": {  # rulings R15, R25: the rule only holds, never pushes through foes
        "release_lag_s": RuleParam(0.0, 4.0, "s", "extra hold added to SUMO's native release of box waiters "
                                   "(setSpeed(0) hold, no safety bits changed); ruling R15. R25 dropped the second "
                                   "param max_clear_into_cross_green_s: holding waiters into the crossing green "
                                   "either locks the crossing road or, with foes told to ignore them, collides"),
    },
    "slow_lane_center": {
        "lat_offset": RuleParam(-1.0, 1.0, "m", "lateral offset from the lane centre the slow rider keeps (0 = "
                                "centre); |1 m| keeps a 0.9 m wide motorcycle inside a 3.5 m proxy lane; assumed"),
    },
    "uturn_bypass": {  # Viktor 2026-10-30 (field): most motorcycles pass a standing U-turner, cars rarely
        "p": RuleParam(0.0, 1.0, "-", "probability that a vehicle held behind a standing U-turner on its own green "
                       "passes it (beside it in the lane or in the adjacent lane), one draw per vehicle and blocker"),
        "t_wait": RuleParam(0.0, 10.0, "s", "time the vehicle stands behind the U-turner before the draw; 10 s "
                            "assumed upper bound (the early-start window, data/proxy/targets.yaml)"),
    },
}

# Ruling R19: early start and red running are observed for cars too (targets M2/M3 have car values), so these rules
# apply to passenger and motorcycle archetypes; custom1 (moto_violator, the illegal-left riders) keeps early_start
# and swarm_red_running (they queue at the HDT_N / HDT_S stop lines like other motorcycles). queue_space_seeking (PLAN 4.5,
# which replaces the former wrong_lane_dodge) is a violator behaviour: custom1 (all three options) and custom2
# (wrong_lane, right_lane; the sidewalk is custom1 only), PLAN 0 violator_classes; such archetypes reach the demand's
# legal movements through `distribution` moto / car. The slow-rider rule is a motorcycle behaviour (PLAN 0, I_slow);
# the box rule is defined for custom1 only. uturn_bypass applies to every class (cars with their own, lower p).
RULE_VCLASSES: dict[str, tuple[str, ...]] = {
    "early_start": ("passenger", "motorcycle", "custom1"),
    "swarm_red_running": ("passenger", "motorcycle", "custom1"),
    "queue_space_seeking": ("custom1", "custom2"),
    "illegal_left_box": ("custom1",),
    "slow_lane_center": ("motorcycle",),
    "uturn_bypass": ("passenger", "motorcycle", "custom1", "custom2"),
}


def _num(x, where: str) -> float | None:
    if x is None:
        return None
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"{where}: expected a number, got {x!r}")
    return float(x)


def _range(row: dict, where: str, categorical: bool) -> Range:
    default = row.get("default")
    if default is None:
        raise ValueError(f"{where}: `default` is required")
    if categorical:
        return Range(None, None, default)
    lo, hi = _num(row.get("min"), where), _num(row.get("max"), where)
    if lo is None or hi is None or lo > hi:
        raise ValueError(f"{where}: need numeric min <= max, got min={lo!r} max={hi!r}")
    d = _num(default, where)
    assert d is not None
    if math.isnan(d):
        raise ValueError(f"{where}: default is NaN")
    return Range(lo, hi, d)


def _as_tuple(x) -> tuple[str, ...]:
    if x is None:
        return ()
    return (x,) if isinstance(x, str) else tuple(x)


def load_bounds(path: Path | None = None) -> dict[str, Bound]:
    """Read and check the bounds file; raise ValueError on a malformed row."""
    path = Path(path) if path is not None else BOUNDS_PATH
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    out: dict[str, Bound] = {}
    for name, row in doc["params"].items():
        where = f"{path.name}: params.{name}"
        for key in ("model", "unit", "source_url", "behavior_group"):
            if row.get(key) in (None, "", []):
                raise ValueError(f"{where}: `{key}` is required")
        if row["model"] not in MODELS:
            raise ValueError(f"{where}: model must be one of {MODELS}")
        groups = _as_tuple(row["behavior_group"])
        if not set(groups) <= set(BEHAVIOR_GROUPS):
            raise ValueError(f"{where}: behavior_group {groups} not in {BEHAVIOR_GROUPS}")
        if not str(row["source_url"]).startswith("https://sumo.dlr.de/docs/"):
            raise ValueError(f"{where}: source_url must be a sumo.dlr.de/docs page")
        if row.get("range_source") is not None and row.get("range_evidence") not in RANGE_EVIDENCE:
            raise ValueError(f"{where}: range_evidence must be one of {RANGE_EVIDENCE}")
        values = tuple(row["values"]) if row.get("values") is not None else None
        generic = _range(row, where, values is not None)
        if values is not None and generic.default not in values:
            raise ValueError(f"{where}: default {generic.default!r} not in values {values}")
        by_vclass = {}
        for vc, sub in (row.get("by_vclass") or {}).items():
            if vc not in VCLASSES:
                raise ValueError(f"{where}: by_vclass key {vc!r} not in {VCLASSES}")
            by_vclass[vc] = _range(sub, f"{where}.by_vclass.{vc}", values is not None)
        vclasses = _as_tuple(row.get("vclasses")) or VCLASSES
        if not set(vclasses) <= set(VCLASSES):
            raise ValueError(f"{where}: vclasses {vclasses} not in {VCLASSES}")
        if vclasses != VCLASSES and not row.get("vclasses_reason"):
            raise ValueError(f"{where}: a vclass-restricted attribute needs `vclasses_reason`")
        fixed = bool(row.get("fixed", False))
        if fixed:
            for vc in VCLASSES:
                r = by_vclass.get(vc, generic)
                if not (r.min == r.max == r.default):
                    raise ValueError(f"{where}: a fixed attribute needs min = max = default ({vc})")
        out[name] = Bound(name=name, min=generic.min, max=generic.max, default=generic.default,
                          unit=str(row["unit"]), model=row["model"], source_url=row["source_url"],
                          behavior_group=groups, constrained_by=_as_tuple(row.get("constrained_by")), fixed=fixed,
                          values=values, by_vclass=by_vclass, range_source=row.get("range_source"),
                          range_evidence=row.get("range_evidence"), vclasses=vclasses,
                          vclasses_reason=" ".join(str(row["vclasses_reason"]).split())
                          if row.get("vclasses_reason") else None)
    return out


def load_excluded(path: Path | None = None) -> dict[str, str]:
    """Attributes deliberately left out of the space -> reason (reported to the LLM)."""
    path = Path(path) if path is not None else BOUNDS_PATH
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    return {k: " ".join(str(v).split()) for k, v in (doc.get("excluded") or {}).items()}


def load_json_schema(path: Path | None = None) -> dict:
    path = Path(path) if path is not None else SCHEMA_PATH
    return json.loads(path.read_text(encoding="utf-8"))
