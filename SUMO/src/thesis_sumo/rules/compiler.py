"""Rule-spec compiler (PLAN 4.4): a validated spec -> `vtypes.add.xml` + `traci_rules.json`.

    .venv/Scripts/python -m thesis_sumo.rules.compiler rules/specs/B1_manual.json --site config/site.proxy.yaml

`compile_spec(spec, out_dir, site=...)` validates the spec first (`validator.validate`) and raises
`InvalidSpecError` with the issues instead of compiling an invalid spec. Output (default
`rules/compiled/<spec_id>/`):

- `vtypes.add.xml`: one vTypeDistribution per base vclass, ids `car` (passenger), `moto` (motorcycle),
  `moto_violator` (custom1), the ids the demand references (`schema.DISTRIBUTION_OF_VCLASS`). Each archetype is
  one member vType with `id` = archetype id, `probability` = share, `laneChangeModel="SL2015"`. custom1 vTypes
  first get the motorcycle defaults the hand-written B0 file copies (`CUSTOM1_MOTORCYCLE_DEFAULTS`), then the
  spec params override them. Every spec param is written explicitly, also when it equals its default: some SUMO
  defaults are derived from other attributes (lcPushyGap = minGapLat, lcMaxSpeedLatStanding = maxSpeedLat,
  jmDriveRedSpeed = maxSpeed), so dropping a "default-valued" param could change its meaning. Attributes not in
  the spec are omitted (SUMO default), so excluded attributes never appear. The file declares SUMO's
  additional_file.xsd: SUMO's default `--xml-validation local` then rejects an undeclared attribute at load.
- `traci_rules.json` (only if the spec has TraCI rules; the runner requires a controller whenever the file
  exists): the archetype -> vType id / distribution map and each rule with its `applies_to` archetype ids and the
  concrete `vtype_ids`. A vehicle drawn from a vTypeDistribution reports the member vType id via
  `vehicle.getTypeID` (verified in tests/test_compiler.py::test_vehicles_get_member_vtype_id), which is how the
  runtime controller (Task 9) matches vehicles to rules.

Output is deterministic: distributions in vclass order, archetypes and rules in spec order, params in the order
of rules/bounds/param_bounds.yaml (vType) / `TRACI_RULE_PARAMS` (rules), numbers as the shortest round-trip
repr (integral values without ".0"), UTF-8 with `\\n` newlines on every OS.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import quoteattr

from thesis_sumo.config import REPO_ROOT, MissingFieldDataError, Site, load_site
from thesis_sumo.rules.schema import DISTRIBUTION_OF_VCLASS, TRACI_RULE_PARAMS, VCLASSES, Bound, load_bounds
from thesis_sumo.rules.validator import ValidationIssue, validate

COMPILED_DIR = REPO_ROOT / "rules" / "compiled"
VTYPES_NAME = "vtypes.add.xml"
TRACI_RULES_NAME = "traci_rules.json"
LANE_CHANGE_MODEL = "SL2015"
# hand-written compiled dirs the compiler must not overwrite (rules/compiled/B0 is the runner's B0; the spec
# rules/specs/B0.json compiles to the same vTypes, tests/test_compiler.py::test_B0_spec_equivalent_to_handwritten)
HAND_WRITTEN = ("B0",)

# custom1 (moto_violator) has passenger defaults in SUMO; these are the motorcycle defaults of SUMO 1.27.0
# (https://sumo.dlr.de/docs/Vehicle_Type_Parameter_Defaults.html, row motorcycle; personCapacity = 1 as the
# 1.27.0 binary reports), in the order of rules/compiled/B0/vtypes.add.xml. tests/test_compiler.py checks them
# against that file and, loaded in SUMO, against the motorcycle vClass in every vType getter.
CUSTOM1_MOTORCYCLE_DEFAULTS: dict[str, float | str] = {
    "guiShape": "motorcycle", "length": 2.2, "width": 0.9, "height": 1.5, "mass": 200, "minGap": 2.5,
    "accel": 6, "decel": 10, "emergencyDecel": 10, "maxSpeed": 55.55555555555556, "personCapacity": 1,
    "emissionClass": "HBEFA4/MC_4S_gt250cc_preEuro", "speedDev": 0.1,
}


class InvalidSpecError(ValueError):
    """The spec failed validation; `issues` are the validator's issues."""

    def __init__(self, spec_id: str, issues: list[ValidationIssue]):
        self.issues = issues
        lines = "\n".join(f"  [{i['code']}] {i['path']}: {i['message']}" for i in issues)
        super().__init__(f"spec {spec_id!r} is invalid ({len(issues)} issue(s)); not compiled:\n{lines}")


@dataclass(frozen=True)
class CompiledSpec:
    vtypes: Path
    traci_rules: Path | None  # None: the spec has no TraCI rules


def fmt_value(v) -> str:
    """Fixed text form of an attribute value: shortest round-trip float repr, integral values without '.0'."""
    if isinstance(v, str):
        return v
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise TypeError(f"not a number or string: {v!r}")
    f = float(v)
    return str(int(f)) if f.is_integer() and abs(f) < 1e15 else repr(f)


def _vtype_attrs(arch: dict, bounds: dict[str, Bound]) -> dict[str, str]:
    attrs: dict = {"id": arch["id"], "vClass": arch["base_vclass"], "laneChangeModel": LANE_CHANGE_MODEL,
                   "probability": arch["share"]}
    if arch["base_vclass"] == "custom1":
        attrs.update(CUSTOM1_MOTORCYCLE_DEFAULTS)
    params = arch["params"]
    unknown = set(params) - set(bounds)
    if unknown:  # the validator rejects these; guard against a bounds file changed in between
        raise ValueError(f"archetype {arch['id']!r}: params {sorted(unknown)} not in the bounds file")
    for name in bounds:  # bounds-file order; overrides keep the position of a custom1 default
        if name in params:
            attrs[name] = params[name]
    return {k: fmt_value(v) for k, v in attrs.items()}


def render_vtypes(spec: dict, bounds: dict[str, Bound] | None = None) -> str:
    bounds = bounds if bounds is not None else load_bounds()
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             f"<!-- generated by thesis_sumo.rules.compiler from spec {spec['spec_id']}; do not edit.",
             "     vTypeDistribution ids car / moto / moto_violator are referenced by the demand; one vType per",
             "     archetype (id = archetype id, probability = share). -->",
             '<additional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
             'xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/additional_file.xsd">']
    for vc in VCLASSES:
        lines.append(f"    <vTypeDistribution id={quoteattr(DISTRIBUTION_OF_VCLASS[vc])}>")
        for arch in spec["driver_archetypes"]:
            if arch["base_vclass"] == vc:
                attrs = " ".join(f"{k}={quoteattr(v)}" for k, v in _vtype_attrs(arch, bounds).items())
                lines.append(f"        <vType {attrs}/>")
        lines.append("    </vTypeDistribution>")
    lines.append("</additional>")
    return "\n".join(lines) + "\n"


def traci_rules_doc(spec: dict) -> dict:
    archetypes = {a["id"]: {"base_vclass": a["base_vclass"], "distribution": DISTRIBUTION_OF_VCLASS[a["base_vclass"]],
                            "vtype_id": a["id"], "share": float(a["share"])} for a in spec["driver_archetypes"]}
    rules = [{"rule_type": r["rule_type"], "applies_to": list(r["applies_to"]),
              "vtype_ids": [archetypes[a]["vtype_id"] for a in r["applies_to"]],
              "params": {n: float(r["params"][n]) for n in TRACI_RULE_PARAMS[r["rule_type"]]}}
             for r in spec["traci_rules"]]
    return {"spec_id": spec["spec_id"], "archetypes": archetypes, "rules": rules}


def compile_spec(spec: dict, out_dir: Path | None = None, *, site: Site | None = None) -> CompiledSpec:
    """Validate `spec` against `site` (default: the measured config/site.yaml) and write its compiled files to
    `out_dir` (default rules/compiled/<spec_id>/). Raises InvalidSpecError, never compiles an invalid spec."""
    site = site if site is not None else load_site()
    bounds = load_bounds()
    issues = validate(spec, site, bounds)
    spec_id = spec.get("spec_id", "?") if isinstance(spec, dict) else "?"
    if issues:
        raise InvalidSpecError(spec_id, issues)
    out_dir = Path(out_dir) if out_dir is not None else COMPILED_DIR / spec_id
    for name in HAND_WRITTEN:
        if out_dir.resolve() == (COMPILED_DIR / name).resolve():
            raise ValueError(f"{out_dir} holds the hand-written {name} vTypes; compile to another out_dir")
    vtypes_text = render_vtypes(spec, bounds)
    rules_text = json.dumps(traci_rules_doc(spec), indent=2) + "\n" if spec["traci_rules"] else None
    out_dir.mkdir(parents=True, exist_ok=True)
    vtypes = out_dir / VTYPES_NAME
    vtypes.write_bytes(vtypes_text.encode("utf-8"))
    rules_path = out_dir / TRACI_RULES_NAME
    if rules_text is None:
        rules_path.unlink(missing_ok=True)
        return CompiledSpec(vtypes, None)
    rules_path.write_bytes(rules_text.encode("utf-8"))
    return CompiledSpec(vtypes, rules_path)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m thesis_sumo.rules.compiler",
                                 description="Compile a rule spec to vtypes.add.xml + traci_rules.json.")
    ap.add_argument("spec", type=Path, help="rules/specs/<spec_id>.json")
    ap.add_argument("--site", type=Path, default=None, help="site file (default: the measured config/site.yaml)")
    ap.add_argument("--out", type=Path, default=None, help="output dir (default: rules/compiled/<spec_id>/)")
    args = ap.parse_args(argv)
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    try:
        out = compile_spec(spec, args.out, site=load_site(args.site))
    except InvalidSpecError as e:
        print(f"{args.spec}: {e}")
        return 1
    except MissingFieldDataError as e:  # e.g. minGapLat checked against the measured site's null lane widths
        print(f"{args.spec}: {e}", file=sys.stderr)
        return 2
    print(f"{args.spec}: wrote {out.vtypes}" + (f" and {out.traci_rules}" if out.traci_rules else " (no TraCI rules)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
