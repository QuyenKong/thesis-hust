"""TraCI rules (PLAN 4.5): one class per `rule_type`, registered in `RULE_REGISTRY`."""

from thesis_sumo.runtime.rules.base import Intervention, Rule
from thesis_sumo.runtime.rules.early_start import EarlyStart
from thesis_sumo.runtime.rules.illegal_left_box import IllegalLeftBox
from thesis_sumo.runtime.rules.slow_lane_center import SlowLaneCenter
from thesis_sumo.runtime.rules.swarm_red_running import SwarmRedRunning
from thesis_sumo.runtime.rules.wrong_lane_dodge import WrongLaneDodge

RULE_REGISTRY: dict[str, type[Rule]] = {r.rule_type: r for r in (
    EarlyStart, SwarmRedRunning, WrongLaneDodge, IllegalLeftBox, SlowLaneCenter)}

__all__ = ["RULE_REGISTRY", "Intervention", "Rule"]
