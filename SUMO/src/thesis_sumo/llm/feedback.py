"""Prompt texts of the LLM loop (PLAN Phase 6.2, plan Task 12), rendered from the versioned templates in
`prompts/<version>/` (`system.md`, `context.md`, `feedback.md`, `retry.md`; `string.Template` `$name` fields).

- `build_context`: intersection from the (proxy) site file, the 10 behaviours in scope (wrong-way driving deferred,
  ruling R38), the parameter dictionary generated from rules/bounds/param_bounds.yaml (fixed attributes left out:
  they can only take their default) and `TRACI_RULE_PARAMS`, calibration targets, output schema.
- `build_feedback`: per spec of the previous iteration S, eligibility, run summary, `DistanceReport.summary_lines`
  and intervention counts; validator errors of rejected specs.
- `calibration_targets`: pooled observed means of the calibration days (refuses validation days, PLAN 5.4).
- Every text passes `assert_no_day_data` (PLAN 5.4 / Phase 6.2): no day name at all, so no validation-day value
  can be attributed and nothing leaks by name.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from string import Template

import numpy as np

from thesis_sumo.config import Site, load_experiment
from thesis_sumo.rules.schema import RULE_VCLASSES, TRACI_RULE_PARAMS, VCLASSES, Bound

PROMPTS_DIR = Path(__file__).parent / "prompts"
DAY_NAME_RE = re.compile(r"PROXY_D\d+")

MODE_RULES = {
    "params_only": "The structure is locked (experiment E1, P1): keep exactly the archetypes of the base spec below "
                   "(ids, base_vclass, distribution, the names of their params) and exactly its rules (rule_type, "
                   "applies_to, the names of their params). Change only `share` values and numeric param values; any "
                   "other change is rejected with code structure_locked.",
    "full": "You may change the structure (experiment E2, P2): add, remove or redefine archetypes and rules, as well "
            "as all values.",
}


class DayDataLeak(ValueError):
    """A prompt text names an observed day (PLAN 5.4: the LLM never sees validation-day data)."""


def load_prompt(name: str, version: str = "v002") -> Template:
    return Template((PROMPTS_DIR / version / f"{name}.md").read_text(encoding="utf-8"))


def system_prompt(version: str = "v002") -> str:
    return load_prompt("system", version).template.strip()


def assert_no_day_data(text: str, exp: dict | None = None) -> str:
    split = (exp if exp is not None else load_experiment()).get("data_split") or {}
    names = set(split.get("calibration_days") or []) | set(split.get("validation_days") or [])
    found = sorted({n for n in names if n in text} | set(DAY_NAME_RE.findall(text)))
    if found:
        raise DayDataLeak(f"prompt text names observed day(s) {found}; feedback must never contain day names or "
                          f"validation-day data")
    return text


# ---------------------------------------------------------------- context


def _ev(d: dict, key: str) -> str:
    ev = d.get(f"{key}_evidence")
    return f" [{ev}]" if ev else ""


def _site_text(site: Site) -> str:
    lines = [f"{site['intersection']['name']} (Hanoi), signalised, AM peak. Site file source: {site.source}."]
    for a in site["approaches"]:
        widths = a.get("lane_widths_m")
        parts = [f"- Approach {a['id']}: {len(widths) if widths else '?'} lanes (index 0 = rightmost), widths "
                 f"{widths} m{_ev(a, 'lane_widths_m')}, lane movements {a.get('lane_movements')}"
                 f"{_ev(a, 'lane_movements')} (r right, s straight, l left, u U-turn)"]
        if a.get("left_turn_banned"):
            parts.append(f"left turn banned{_ev(a, 'left_turn_banned')}")
        if a.get("continuous_right_lane") and a.get("right_lane_separator") == "open":
            extra = [m for m, banned in (("left", a.get("left_turn_banned")), ("U-turn", a.get("u_turn_banned")))
                     if not banned]
            parts.append(f"lane 0 is a continuous right-turn lane over the last {a.get('right_lane_length_m')} m before "
                         f"the stop line{_ev(a, 'right_lane_length_m')} (an ordinary lane upstream of it): right turn at "
                         f"any time (not signal controlled), straight from it legal on the approach's straight green "
                         f"(no separator){_ev(a, 'right_lane_separator')}; standing in it at red while going straight, "
                         f"left or U-turn is a violation"
                         + (f"; violator classes may also {' / '.join(extra)} from it on the arrow (wrong lane)"
                            if extra else ""))
        elif a.get("continuous_right_lane"):
            parts.append(f"lane 0 is a continuous right-turn lane (not signal controlled), separated by "
                         f"{a.get('right_lane_separator')} over the last {a.get('bollard_length_m')} m"
                         f"{_ev(a, 'bollard_length_m')}")
        if a.get("sidewalk_start_m") is not None:
            parts.append(f"rideable sidewalk from {a['sidewalk_start_m']} m before the stop line, "
                         f"{a.get('sidewalk_width_m')} m wide{_ev(a, 'sidewalk_start_m')}")
        lines.append("; ".join(parts) + ".")
    sig = site["signal"]
    il = site.get("illegal_left") or {}
    apps = {a["id"]: a for a in site["approaches"]}

    def green(p) -> str:
        out = []
        for m in p.get("green_movements") or []:
            a = apps.get(m.split(":")[0], {})
            if m.endswith(":r") and a.get("continuous_right_lane"):
                continue   # that right turn is green in every phase (stated per approach above)
            out.append(m + (f" (banned, {il.get('vclass')} only)" if m.endswith(":l") and a.get("left_turn_banned")
                            else ""))
        return f" (green {', '.join(out)})" if out else ""

    phases = ", ".join(f"{p['name']} {p['duration_s']} s{green(p)}" for p in sig["phases"])
    lines.append(f"- Signal: fixed time, cycle {sig['cycle_s']} s{_ev(sig, 'cycle_s')}; phases {phases}"
                 f"{_ev(sig, 'phases')} (movement <approach>:<r right, s straight, l left, t U-turn>; not listed = "
                 f"red).")
    if il.get("approaches"):
        lines.append(f"- Illegal left turns ({il.get('vclass')} riders, distribution moto_violator) from "
                     f"{', '.join(il['approaches'])}: they enter the junction on their own green, wait inside the box "
                     f"and turn when the opposing straight green ends{_ev(il, 'approaches')}.")
    return "\n".join(lines)


def _fmt(x) -> str:
    return f"{x:g}" if isinstance(x, (int, float)) else str(x)


def vtype_dictionary(bounds: dict[str, Bound]) -> str:
    out = []
    for name, b in bounds.items():
        if b.fixed:
            continue
        if b.values is not None:
            rng = f"one of {', '.join(b.values)}; SUMO default {b.default}"
        else:
            rng = f"[{b.min:g}, {b.max:g}] {b.unit}, SUMO default {_fmt(b.default)}"
            over = "; ".join(f"{v}: [{r.min:g}, {r.max:g}], default {_fmt(r.default)}"
                             for v, r in b.by_vclass.items() if v in b.vclasses)
            rng += f" (except {over})" if over else ""
        where = "" if b.vclasses == VCLASSES else f"; only on base_vclass {', '.join(b.vclasses)}"
        out.append(f"- `{name}` ({b.model}): {rng}{where}; behaviour {', '.join(b.behavior_group)}; observed "
                   f"through {', '.join(b.constrained_by) or '-'}")
    return "\n".join(out)


def rule_dictionary() -> str:
    out = []
    for rtype, params in TRACI_RULE_PARAMS.items():
        out.append(f"- `{rtype}` (applies to base_vclass {', '.join(RULE_VCLASSES[rtype])}):")
        out += [f"  - `{n}` [{p.min:g}, {p.max:g}] {p.unit}{' (optional)' if p.optional else ''}: "
                f"{' '.join(p.reason.split())}" for n, p in params.items()]
    return "\n".join(out)


def _targets_text(targets_calib: dict) -> str:
    out = []
    for k, t in sorted(targets_calib.items()):
        m = t["obs_mean"]
        obs = f"observed mean {m:.4g} {t.get('unit', '')}".rstrip() if m == m else "no observed events"  # m != m: NaN
        note = "" if t.get("scored", True) else ", reported only"
        out.append(f"- {k}: {t.get('label', k)}: {obs} (target evidence {t.get('evidence') or '-'}{note})")
    return "\n".join(out)


def build_context(mode: str, base_spec: dict | None, site: Site, bounds: dict[str, Bound], targets_calib: dict,
                  *, schema: dict, prompt_version: str = "v002", exp: dict | None = None) -> str:
    """The context message. `targets_calib` = `calibration_targets(...)` (key -> label, unit, obs_mean, evidence,
    scored); `schema` = `client.llm_schema(mode, base_spec)`."""
    if mode not in MODE_RULES:
        raise ValueError(f"mode must be one of {tuple(MODE_RULES)}, got {mode!r}")
    rules = MODE_RULES[mode]
    if mode == "params_only":
        if base_spec is None:
            raise ValueError("params_only needs the base spec whose structure is locked")
        base = {k: base_spec[k] for k in ("driver_archetypes", "traci_rules")}
        rules += "\n\nBase spec (structure to keep, values to tune):\n\n```json\n" + json.dumps(base, indent=1) + "\n```"
    text = load_prompt("context", prompt_version).substitute(
        mode=mode, mode_rules=rules, site=_site_text(site), vtype_params=vtype_dictionary(bounds),
        rule_params=rule_dictionary(), targets=_targets_text(targets_calib), schema=json.dumps(schema))
    return assert_no_day_data(text, exp)


def calibration_targets(days: list[str], *, exp: dict | None = None, site: Site | None = None) -> dict:
    """Pooled observed means of the calibration `days` per metric key (PLAN 5.4: validation days raise)."""
    from thesis_sumo.evaluate import OBSERVED_DIR, check_days
    from thesis_sumo.metrics.common import MetricContext, read_tables
    from thesis_sumo.metrics.distance import compute_all, evidence
    exp = exp if exp is not None else load_experiment()
    check_days(days, exp)
    ctx = MetricContext.from_config(exp, site=site)
    per_day = [compute_all(read_tables(OBSERVED_DIR / d), ctx) for d in days]
    out = {}
    for key, m in per_day[0].items():
        vals = [v.values if v.kind == "dist" else np.atleast_1d(v.values) for v in (r[key] for r in per_day)]
        pooled = np.concatenate(vals) if vals else np.array([])
        pooled = pooled[~np.isnan(pooled)]
        out[key] = {"label": m.label, "unit": m.unit, "obs_mean": float(pooled.mean()) if pooled.size else float("nan"),
                    "evidence": evidence(m.target), "scored": m.scored}
    return out


# ---------------------------------------------------------------- feedback


def _issues_text(issues: list[dict]) -> str:
    return "\n".join(f"- {i['path']} [{i['code']}]: {i['message']}" for i in issues)


def _interventions_text(summary: dict) -> str:
    if not summary:
        return "  (no TraCI interventions)"
    out = []
    for rule, st in sorted(summary.items()):
        line = f"  - {rule}: attempted {st.get('attempted', 0)}, executed {st.get('executed', 0)}"
        if st.get("not_executed"):
            line += f", not executed {dict(sorted(st['not_executed'].items()))}"
        if st.get("counters"):
            line += f", counters {dict(sorted(st['counters'].items()))}"
        out.append(line)
    return "\n".join(out)


def _result_text(r, interventions: dict | None) -> str:
    head = f"## Spec {r.spec_id}"
    if not r.valid:
        return f"{head}: rejected by the validator, not simulated."
    rep = r.report
    reasons = Counter(x.split(":")[0] for run in r.runs for x in run["reasons"])
    lines = [f"{head}: S = {r.S:.4f} (sourced targets {rep.S_sourced:.4f}, assumed targets {rep.S_assumed:.4f})",
             f"Runs: {r.n_runs}; eligibility {r.eligibility} ({len(r.eligible_runs)} eligible, "
             f"{len(r.excluded_runs)} excluded); mean collisions/h {r.collisions_per_hour:.1f} (lane "
             f"{r.lane_collisions_per_hour:.1f}); mean jam+yield teleports/h {r.jam_yield_teleports_per_hour:.1f}"
             + (f"; exclusion reasons (runs): {dict(sorted(reasons.items()))}" if reasons else ""),
             "Metrics:", *[f"- {s}" for s in rep.summary_lines()],
             "TraCI interventions (all runs):",
             _interventions_text(interventions if interventions is not None else r.interventions_summary)]
    return "\n".join(lines)


def build_feedback(prev_results: list, issues: dict[str, list[dict]] | None = None,
                   interventions: dict[str, dict] | None = None, *, prompt_version: str = "v002",
                   exp: dict | None = None) -> str:
    """Feedback message on the previous iteration. `prev_results`: `evaluate.EvalResult`s (calibration days only);
    `issues`: spec_id -> validator issues of specs that never reached evaluation (the client gave up), merged with
    those of invalid `prev_results`; `interventions`: spec_id -> intervention summary overriding
    `EvalResult.interventions_summary`. Raises DayDataLeak if a day name gets into the text."""
    exp = exp if exp is not None else load_experiment()
    val = set((exp.get("data_split") or {}).get("validation_days") or [])
    leaked = sorted({run["day"] for r in prev_results for run in r.runs if run["day"] in val})
    if leaked:
        raise DayDataLeak(f"previous results include runs on validation days {leaked}; feedback uses calibration "
                          f"days only")
    interventions = interventions or {}
    rejected = dict(issues or {})
    for r in prev_results:
        if not r.valid and r.issues:
            rejected.setdefault(r.spec_id, r.issues)
    results = "\n\n".join(_result_text(r, interventions.get(r.spec_id)) for r in prev_results) or "(no simulated specs)"
    iss = "\n\n".join(f"### {sid}\n{_issues_text(v)}" for sid, v in rejected.items()) or "(none)"
    text = load_prompt("feedback", prompt_version).substitute(results=results, issues=iss)
    return assert_no_day_data(text, exp)


def build_retry(issues: list[dict], *, prompt_version: str = "v002") -> str:
    return load_prompt("retry", prompt_version).substitute(issues=_issues_text(issues))
