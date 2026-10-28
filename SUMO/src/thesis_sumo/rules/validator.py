"""Rule-spec validator (PLAN 4.3) and the validity log (share of valid specs is a thesis metric).

`validate(spec, site)` returns a list of issues `{path, code, message}`; an empty list means valid. Messages
are written to be fed back to the LLM verbatim: each states the allowed range or the allowed names.

Codes:
- `schema`        the JSON structure (rules/schema/rule_spec.schema.json) is violated (incl. an archetype id starting
                  with the reserved prefix DEFAULT_); other checks are skipped
- `unknown_attr`  an archetype param is not in rules/bounds/param_bounds.yaml (or is deliberately excluded)
- `out_of_bounds` a param value is outside its range for the archetype's base vclass, has the wrong type, or
                  changes an attribute that is fixed at its default
- `share_sum`     the shares of one vTypeDistribution do not sum to 1 (tolerance 1e-6); an archetype joins the
                  distribution of its base vclass or the one its `distribution` key names (custom1 -> moto, custom2
                  -> car; Viktor 2026-10-27: share = share within the distribution)
- `rule_params`   a TraCI rule's params are missing (optional ones may be), unknown, out of range or inconsistent
                  (p0 > p_max; queue_space_seeking p_wrong_lane + p_right_lane + p_sidewalk > 1)
- `logic`         contradictions: an attribute set on a base vclass it is not tunable for (jmTimegapMinor is
                  custom1-only, R15), minGapLat wider than the narrowest site lane, lcPushy together with
                  lcPushyGap (SUMO ignores the latter) or lcPushyGap > minGapLat, a vTypeDistribution without
                  archetype, duplicate / reserved archetype ids, an archetype in a distribution its base vclass may
                  not join (`schema.DISTRIBUTIONS_OF_VCLASS`), a rule applied to an unknown archetype or to one of
                  the wrong base vclass, the same rule twice on one archetype, a queue_space_seeking rule on an
                  archetype for which none of the options with p > 0 exists on this site's net (ruling R27: "rule
                  inapplicable on this site"; an absent option with p > 0 is no issue: the runtime redistributes its
                  probability, PLAN 4.5). Options per archetype: wrong_lane = `runtime.wrong_lane.usable_dodges` with
                  the site's lane_movements and the net's connections and their vClass permissions; right_lane = an
                  approach with a bollard edge (split node `<edge>.bollard`, net.apply_patches) whose upstream lane 0
                  allows the vclass (none on the proxy net since 2026-10-28, `right_lane_separator: open`: p_right_lane
                  is then redistributed like any absent option); sidewalk = a sidewalk edge allowing the vclass. An
                  archetype in moto_violator
                  drives only the illegal left (build_demand), so only wrong_lane counts for it
- `structure_locked` (`structure_issues`, LLM loop mode params_only = P1, PLAN 7.2) the spec changes the structure
                  of the locked base spec: archetype ids, base_vclass, distribution, the param names of an archetype
                  or a rule, a non-numeric param value, or the rule types and their applies_to

`minGapLat` is compared with the site file's lane widths via `Site.require`, so the measured site file with
`lane_widths_m: null # TODO_MEASURE` raises MissingFieldDataError instead of validating against a default.
"""

from __future__ import annotations

import argparse
import csv
import difflib
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict

import sumolib
from jsonschema import Draft202012Validator

from thesis_sumo.config import REPO_ROOT, Site, load_site
from thesis_sumo.net.apply_patches import BOLLARD_NODE, site_net_name
from thesis_sumo.net.build_net import approach_edges, approach_segments, sidewalk_edges
from thesis_sumo.rules.schema import (DISTRIBUTION_OF_VCLASS, DISTRIBUTIONS, DISTRIBUTIONS_OF_VCLASS,
                                      OPTIONAL_DISTRIBUTIONS, RULE_VCLASSES, TRACI_RULE_PARAMS, VCLASSES, Bound,
                                      load_bounds, load_excluded, load_json_schema)

ISSUE_CODES = ("schema", "unknown_attr", "out_of_bounds", "share_sum", "rule_params", "logic", "structure_locked")
SHARE_TOL = 1e-6
VALIDITY_LOG_PATH = REPO_ROOT / "experiments" / "validity_log.csv"
NET_DIR = REPO_ROOT / "scenario" / "net"


class ValidationIssue(TypedDict):
    path: str
    code: str
    message: str


def _issue(path: str, code: str, message: str) -> ValidationIssue:
    assert code in ISSUE_CODES, code
    return {"path": path, "code": code, "message": message}


def _is_number(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _fmt_path(parts) -> str:
    out = ""
    for p in parts:
        out += f"[{p}]" if isinstance(p, int) else (f".{p}" if out else str(p))
    return out or "(spec)"


# ---------------------------------------------------------------- checks


def _schema_issues(spec) -> list[ValidationIssue]:
    validator = Draft202012Validator(load_json_schema())
    errors = sorted(validator.iter_errors(spec), key=lambda e: (list(map(str, e.absolute_path)), e.message))
    return [_issue(_fmt_path(e.absolute_path), "schema", e.message) for e in errors]


def _param_issues(path: str, name: str, value, vclass: str, bounds: dict[str, Bound],
                  excluded: dict[str, str]) -> list[ValidationIssue]:
    b = bounds.get(name)
    if b is None:
        if name in excluded:
            return [_issue(path, "unknown_attr", f"'{name}' is not a tunable attribute: {excluded[name]}")]
        close = difflib.get_close_matches(name, list(bounds), n=1)
        hint = f" Did you mean '{close[0]}'?" if close else ""
        return [_issue(path, "unknown_attr", f"'{name}' is not a tunable vType attribute.{hint} "
                                             f"Allowed attributes: {', '.join(sorted(bounds))}.")]
    if vclass not in b.vclasses:
        return [_issue(path, "logic", f"{name} may be set only on archetypes with base_vclass "
                                      f"{' or '.join(b.vclasses)} ({b.vclasses_reason}); remove it from this "
                                      f"{vclass} archetype.")]
    r = b.for_vclass(vclass)
    if b.values is not None:
        if not isinstance(value, str) or value not in b.values:
            return [_issue(path, "out_of_bounds", f"{name} must be one of {', '.join(b.values)} "
                                                  f"(got {value!r}).")]
        return []
    if not _is_number(value) or not math.isfinite(value):
        return [_issue(path, "out_of_bounds", f"{name} must be a finite number in [{r.min:g}, {r.max:g}] {b.unit} "
                                              f"for base_vclass {vclass} (got {value!r}).")]
    if b.fixed:
        if value != r.default:
            return [_issue(path, "out_of_bounds", f"{name} is fixed at its SUMO default {r.default:g} {b.unit} "
                                                  f"(no metric M1-M8 constrains it); remove it from params.")]
        return []
    if not r.min <= value <= r.max:
        return [_issue(path, "out_of_bounds", f"{name} = {value:g} is outside [{r.min:g}, {r.max:g}] {b.unit} "
                                              f"for base_vclass {vclass}.")]
    return []


def _archetype_issues(spec: dict, bounds: dict[str, Bound], excluded: dict[str, str]) -> list[ValidationIssue]:
    issues = []
    for i, arch in enumerate(spec["driver_archetypes"]):
        vc, params = arch["base_vclass"], arch["params"]
        for name, value in params.items():
            issues += _param_issues(f"driver_archetypes[{i}].params.{name}", name, value, vc, bounds, excluded)
        # SUMO 1.27 (SL2015): lcPushyGap g sets lcPushy = 1 - g/minGapLat; with both given, lcPushy wins and
        # lcPushyGap is ignored silently (experiment in the Task 7 report)
        if "lcPushy" in params and "lcPushyGap" in params:
            issues.append(_issue(f"driver_archetypes[{i}].params.lcPushyGap", "logic",
                                 "set either lcPushy or lcPushyGap, not both: SUMO ignores lcPushyGap when lcPushy "
                                 "is given (lcPushyGap = alternative way to define lcPushy)."))
        gap, lat = params.get("lcPushyGap"), params.get("minGapLat", bounds["minGapLat"].for_vclass(vc).default)
        if _is_number(gap) and _is_number(lat) and gap > lat:
            issues.append(_issue(f"driver_archetypes[{i}].params.lcPushyGap", "logic",
                                 f"lcPushyGap = {gap:g} m exceeds this archetype's minGapLat = {lat:g} m; SUMO's "
                                 f"range for lcPushyGap is 0 to minGapLat."))
    return issues


def distribution_of(arch: dict) -> str:
    """The vTypeDistribution an archetype joins (`distribution`, default by base vclass)."""
    return arch.get("distribution", DISTRIBUTION_OF_VCLASS[arch["base_vclass"]])


def _distribution_issues(spec: dict) -> list[ValidationIssue]:
    issues = []
    by_dist: dict[str, list[dict]] = defaultdict(list)
    for i, arch in enumerate(spec["driver_archetypes"]):
        ok = DISTRIBUTIONS_OF_VCLASS[arch["base_vclass"]]
        if distribution_of(arch) not in ok:
            issues.append(_issue(f"driver_archetypes[{i}].distribution", "logic",
                                 f"an archetype with base_vclass {arch['base_vclass']} may join vTypeDistribution "
                                 f"{' or '.join(ok)}, not '{distribution_of(arch)}'."))
            continue
        by_dist[distribution_of(arch)].append(arch)
    for dist in DISTRIBUTIONS:
        archs = by_dist.get(dist, [])
        if not archs:
            if dist in OPTIONAL_DISTRIBUTIONS:  # no demand references it: leaving it out is fine
                continue
            issues.append(_issue("driver_archetypes", "logic",
                                 f"no archetype in vTypeDistribution '{dist}': the demand uses it, so it needs at "
                                 f"least one archetype (base_vclass passenger -> 'car', motorcycle -> 'moto', custom1 "
                                 f"-> 'moto_violator' or, with distribution 'moto', the motorcycle distribution; "
                                 f"custom2 -> 'car_violator' (optional) or 'car')."))
            continue
        total = math.fsum(a["share"] for a in archs)
        if abs(total - 1.0) > SHARE_TOL:
            ids = ", ".join(f"{a['id']}={a['share']:g}" for a in archs)
            issues.append(_issue("driver_archetypes", "share_sum",
                                 f"shares of vTypeDistribution '{dist}' sum to {round(total, 6):g}; they must sum to "
                                 f"1 ({ids})."))
    seen = Counter(a["id"] for a in spec["driver_archetypes"])
    for i, arch in enumerate(spec["driver_archetypes"]):
        if arch["id"] in DISTRIBUTION_OF_VCLASS.values():
            issues.append(_issue(f"driver_archetypes[{i}].id", "logic",
                                 f"archetype id '{arch['id']}' clashes with a vTypeDistribution id (car, moto, "
                                 f"moto_violator, car_violator are reserved); choose another id."))
        if seen[arch["id"]] > 1:
            issues.append(_issue(f"driver_archetypes[{i}].id", "logic",
                                 f"archetype id '{arch['id']}' is used {seen[arch['id']]} times; ids must be unique."))
    return issues


def narrowest_lane(site: Site) -> tuple[float, str, int]:
    best = None
    for i, appr in enumerate(site.require("approaches")):
        for j, w in enumerate(site.require(f"approaches.{i}.lane_widths_m")):
            if best is None or w < best[0]:
                best = (float(w), appr.get("id", f"approaches[{i}]"), j)
    if best is None:
        raise ValueError(f"{site.path}: no lane widths in approaches")
    return best


_narrowest_lane = narrowest_lane  # former private name


def _lane_width_issues(spec: dict, site: Site) -> list[ValidationIssue]:
    issues, narrowest = [], None
    for i, arch in enumerate(spec["driver_archetypes"]):
        v = arch["params"].get("minGapLat")
        if not _is_number(v):
            continue
        narrowest = narrowest or narrowest_lane(site)
        w, appr, lane = narrowest
        if v > w:
            issues.append(_issue(f"driver_archetypes[{i}].params.minGapLat", "logic",
                                 f"minGapLat = {v:g} m is wider than the narrowest lane of the site ({w:g} m, "
                                 f"approach {appr} lane {lane}); use a value below {w:g} m."))
    return issues


def _rule_issues(spec: dict) -> list[ValidationIssue]:
    issues = []
    archs = {a["id"]: a for a in spec["driver_archetypes"]}
    applied: dict[tuple[str, str], int] = {}
    for i, rule in enumerate(spec["traci_rules"]):
        rtype, params = rule["rule_type"], rule["params"]
        allowed = TRACI_RULE_PARAMS[rtype]
        names = ", ".join(f"{n} [{p.min:g}, {p.max:g}] {p.unit}" for n, p in allowed.items())
        for name, p in allowed.items():
            if name not in params and not p.optional:
                issues.append(_issue(f"traci_rules[{i}].params", "rule_params",
                                     f"rule_type {rtype}: missing parameter '{name}' ({p.unit}, allowed "
                                     f"[{p.min:g}, {p.max:g}]). Required parameters: {names}."))
        for name, value in params.items():
            path = f"traci_rules[{i}].params.{name}"
            p = allowed.get(name)
            if p is None:
                issues.append(_issue(path, "rule_params", f"rule_type {rtype}: unknown parameter '{name}'. "
                                                          f"Allowed parameters: {names}."))
            elif not math.isfinite(value) or not p.min <= value <= p.max:
                issues.append(_issue(path, "rule_params", f"rule_type {rtype}: {name} = {value:g} is outside "
                                                          f"[{p.min:g}, {p.max:g}] {p.unit}."))
        if rtype == "swarm_red_running" and _is_number(params.get("p0")) and _is_number(params.get("p_max")) \
                and params["p0"] > params["p_max"]:
            issues.append(_issue(f"traci_rules[{i}].params.p_max", "rule_params",
                                 f"rule_type swarm_red_running: p_max = {params['p_max']:g} is below p0 = "
                                 f"{params['p0']:g}; the probability p0 + k*n is capped at p_max, so p_max >= p0."))
        if rtype == "queue_space_seeking":
            total = math.fsum(params[f"p_{o}"] for o in SEEK_OPTIONS if _is_number(params.get(f"p_{o}")))
            if total > 1 + 1e-9:
                issues.append(_issue(f"traci_rules[{i}].params", "rule_params",
                                     f"rule_type queue_space_seeking: p_wrong_lane + p_right_lane + p_sidewalk = "
                                     f"{total:g}; they are the probabilities of exclusive choices, so their sum must "
                                     f"be <= 1 (the rest = the vehicle does not seek space)."))
        dups = []
        for j, aid in enumerate(rule["applies_to"]):
            path = f"traci_rules[{i}].applies_to[{j}]"
            arch = archs.get(aid)
            if arch is None:
                issues.append(_issue(path, "logic", f"applies_to references '{aid}', which is not an archetype id; "
                                                    f"archetype ids: {', '.join(archs)}."))
                continue
            ok = RULE_VCLASSES[rtype]
            if arch["base_vclass"] not in ok:
                issues.append(_issue(path, "logic", f"rule_type {rtype} applies only to archetypes with base_vclass "
                                                    f"{' or '.join(ok)}; '{aid}' has base_vclass "
                                                    f"{arch['base_vclass']}."))
            if (rtype, aid) in applied:
                dups.append(aid)
            applied.setdefault((rtype, aid), i)
        if dups:
            issues.append(_issue(f"traci_rules[{i}]", "logic",
                                 f"rule_type {rtype} is applied more than once to {', '.join(dups)} (also in "
                                 f"traci_rules[{applied[(rtype, dups[0])]}]); use one rule per archetype."))
    return issues


SEEK_OPTIONS = ("wrong_lane", "right_lane", "sidewalk")  # runtime.rules.queue_space_seeking.OPTIONS
_DODGE_CACHE: dict[tuple, frozenset[str]] = {}
_SPACE_CACHE: dict[str, dict[str, frozenset[str]]] = {}


def _dodge_vclasses(net_path: str, site_key: tuple, site: Site) -> frozenset[str]:
    """Base vclasses that have at least one usable wrong-lane dodge on the net (cached per net and site content)."""
    key = (net_path, site_key)
    if key not in _DODGE_CACHE:
        _DODGE_CACHE[key] = _compute_dodge_vclasses(net_path, site)
    return _DODGE_CACHE[key]


def _compute_dodge_vclasses(net_path: str, site: Site) -> frozenset[str]:
    from thesis_sumo.runtime.wrong_lane import LaneLink, usable_dodges
    net = sumolib.net.readNet(net_path)
    links, marks = {}, {}
    for i, a in enumerate(site["approaches"]):
        app = site.require(f"approaches.{i}.id")
        lanes = sorted(net.getEdge(str(site.require(f"approaches.{i}.edge"))).getLanes(), key=lambda ln: ln.getIndex())
        links[app] = [[LaneLink(c.getTo().getID(), c.getDirection(), frozenset(v for v in VCLASSES if c.allows(v)))
                       for c in lane.getOutgoing()] for lane in lanes]
        marks[app] = [list(m) for m in site.require(f"approaches.{i}.lane_movements")]
    return frozenset(v for v in VCLASSES if usable_dodges(links, marks, v))


def _space_vclasses(net_path: str) -> dict[str, frozenset[str]]:
    """right_lane / sidewalk -> base vclasses for which the option exists somewhere on the net (cached per net)."""
    if net_path not in _SPACE_CACHE:
        net = sumolib.net.readNet(net_path)
        right, side = set(), set()
        for e in approach_edges(net).values():
            segs = approach_segments(net, e)
            if len(segs) > 1 and segs[0].getFromNode().getID() == e + BOLLARD_NODE:
                right |= {v for v in VCLASSES if segs[-1].getLanes()[0].allows(v)}
        for sw in sidewalk_edges(net):
            side |= {v for v in VCLASSES if net.getEdge(sw).getLanes()[0].allows(v)}
        _SPACE_CACHE[net_path] = {"right_lane": frozenset(right), "sidewalk": frozenset(side)}
    return _SPACE_CACHE[net_path]


def _site_rule_issues(spec: dict, site: Site, net: Path | None) -> list[ValidationIssue]:
    rules = [(i, r) for i, r in enumerate(spec["traci_rules"]) if r["rule_type"] == "queue_space_seeking"]
    if not rules:
        return []
    net = Path(net) if net is not None else NET_DIR / site_net_name(site)
    site_key = json.dumps(site["approaches"], sort_keys=True, default=str)
    ok = {"wrong_lane": _dodge_vclasses(str(net), (site_key,), site), **_space_vclasses(str(net))}
    archs = {a["id"]: a for a in spec["driver_archetypes"]}
    issues = []
    for i, rule in rules:
        wanted = [o for o in SEEK_OPTIONS if _is_number(rule["params"].get(f"p_{o}")) and rule["params"][f"p_{o}"] > 0]
        for j, aid in enumerate(rule["applies_to"]):
            arch = archs.get(aid)
            if arch is None or not wanted:
                continue
            vc = arch["base_vclass"]
            exist = [o for o in SEEK_OPTIONS
                     if vc in ok[o] and (o == "wrong_lane" or distribution_of(arch) != "moto_violator")]
            if not set(wanted) & set(exist):
                issues.append(_issue(f"traci_rules[{i}].applies_to[{j}]", "logic",
                                     f"rule_type queue_space_seeking is inapplicable on this site for '{aid}' "
                                     f"(base_vclass {vc}, distribution {distribution_of(arch)}): the options with "
                                     f"p > 0 ({', '.join(wanted)}) do not exist for it here (existing: "
                                     f"{', '.join(exist) or 'none'}), so the rule could never execute; give p > 0 to "
                                     f"an existing option or remove the rule."))
    return issues


def validate(spec, site: Site, bounds: dict[str, Bound] | None = None, *, net: Path | None = None) -> list[ValidationIssue]:
    """All issues of `spec` (empty = valid). Structural errors stop further checks. `net` (default: the site's net in
    scenario/net/) is read only for a queue_space_seeking rule (ruling R27)."""
    issues = _schema_issues(spec)
    if issues:
        return issues
    bounds = bounds if bounds is not None else load_bounds()
    return (_archetype_issues(spec, bounds, load_excluded()) + _distribution_issues(spec)
            + _lane_width_issues(spec, site) + _rule_issues(spec) + _site_rule_issues(spec, site, net))


def structure_issues(spec: dict, base: dict) -> list[ValidationIssue]:
    """params_only lock (P1): `spec` may differ from `base` only in archetype `share`, numeric param values and
    free text (rationale, description). Run after `validate` (expects a schema-valid spec)."""
    issues = []
    archs = {a["id"]: a for a in spec["driver_archetypes"]}
    base_archs = {a["id"]: a for a in base["driver_archetypes"]}
    if set(archs) != set(base_archs):
        issues.append(_issue("driver_archetypes", "structure_locked",
                             f"structure is locked: the archetype ids must be exactly {', '.join(base_archs)} "
                             f"(got {', '.join(archs)}); change only share and numeric param values."))
    for i, arch in enumerate(spec["driver_archetypes"]):
        b = base_archs.get(arch["id"])
        if b is None:
            continue
        for key, get in (("base_vclass", lambda a: a["base_vclass"]), ("distribution", distribution_of)):
            if get(arch) != get(b):
                issues.append(_issue(f"driver_archetypes[{i}].{key}", "structure_locked",
                                     f"structure is locked: {arch['id']}.{key} must stay '{get(b)}'."))
        issues += _params_locked(f"driver_archetypes[{i}].params", arch["id"], arch["params"], b["params"])
    def rkey(r):
        return r["rule_type"], tuple(sorted(r["applies_to"]))
    base_rules = {rkey(r): r for r in base["traci_rules"]}
    if sorted(map(rkey, spec["traci_rules"])) != sorted(base_rules):
        want = "; ".join(f"{t} on {', '.join(a)}" for t, a in sorted(base_rules)) or "none"
        issues.append(_issue("traci_rules", "structure_locked",
                             f"structure is locked: the rules (rule_type, applies_to) must be exactly: {want}."))
    for i, rule in enumerate(spec["traci_rules"]):
        b = base_rules.get(rkey(rule))
        if b is not None:
            issues += _params_locked(f"traci_rules[{i}].params", rule["rule_type"], rule["params"], b["params"])
    return issues


def _params_locked(path: str, owner: str, params: dict, base: dict) -> list[ValidationIssue]:
    if set(params) != set(base):
        return [_issue(path, "structure_locked", f"structure is locked: {owner} must have exactly the params "
                                                 f"{', '.join(base)} (got {', '.join(params) or 'none'}).")]
    return [_issue(f"{path}.{k}", "structure_locked", f"structure is locked: {owner}.{k} is not numeric and must stay "
                                                      f"{base[k]!r}.")
            for k, v in params.items() if not (_is_number(v) and _is_number(base[k])) and v != base[k]]


# ---------------------------------------------------------------- validity log


class ValidityLog:
    """Append-only CSV of validation outcomes (runtime output, not committed)."""

    COLUMNS = ["timestamp", "spec_id", "source", "valid", "n_issues", "codes"]

    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path is not None else VALIDITY_LOG_PATH

    def record(self, spec_id: str, issues: list[ValidationIssue], *, source: str = "") -> None:
        counts = Counter(i["code"] for i in issues)
        row = {"timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"), "spec_id": spec_id,
               "source": source, "valid": not issues, "n_issues": len(issues),
               "codes": ";".join(f"{c}:{counts[c]}" for c in ISSUE_CODES if counts[c])}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        new = not self.path.is_file() or self.path.stat().st_size == 0
        with self.path.open("a", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=self.COLUMNS)
            if new:
                w.writeheader()
            w.writerow(row)

    def rows(self) -> list[dict]:
        if not self.path.is_file():
            return []
        with self.path.open(encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))

    def valid_rate(self, source: str | None = None) -> float | None:
        """Share of recorded specs that were valid (None if nothing recorded)."""
        rows = [r for r in self.rows() if source is None or r["source"] == source]
        return sum(r["valid"] == "True" for r in rows) / len(rows) if rows else None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m thesis_sumo.rules.validator", description="Validate rule specs.")
    ap.add_argument("specs", type=Path, nargs="+", help="rules/specs/<spec_id>.json")
    ap.add_argument("--site", type=Path, default=None, help="site file (default: the measured config/site.yaml)")
    ap.add_argument("--log", action="store_true", help=f"append the outcome to {VALIDITY_LOG_PATH.name}")
    args = ap.parse_args(argv)
    site, log, n_bad = load_site(args.site), ValidityLog(), 0
    for path in args.specs:
        spec = json.loads(path.read_text(encoding="utf-8"))
        issues = validate(spec, site)
        spec_id = spec.get("spec_id", path.stem) if isinstance(spec, dict) else path.stem
        if args.log:
            log.record(spec_id, issues, source=spec.get("source", "") if isinstance(spec, dict) else "")
        print(f"{path}: {'valid' if not issues else f'{len(issues)} issue(s)'}")
        for i in issues:
            print(f"  [{i['code']}] {i['path']}: {i['message']}")
        n_bad += bool(issues)
    return 1 if n_bad else 0


if __name__ == "__main__":
    sys.exit(main())
