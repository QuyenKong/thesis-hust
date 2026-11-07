"""Scratch: validate an Ollama response the way LLMClient.generate_spec does (parse, insert harness keys, validate).
usage: validate_resp.py <tag>   (reads <tag>_response.json, writes <tag>_validation.json)"""
import json
import sys
from pathlib import Path

from thesis_sumo.llm.client import _parse
from thesis_sumo.rules.schema import load_bounds
from thesis_sumo.rules.validator import load_site, validate

OUT = Path(r"D:/hust-master/Thesis/report/2026-11-03/data/ollama")
SITE = Path(r"D:/hust-master/Thesis/SUMO/config/site.proxy.yaml")  # the P2 loops ran with --site config/site.proxy.yaml
tag = sys.argv[1]
resp = json.loads((OUT / f"{tag}_response.json").read_text(encoding="utf-8"))
text = resp["choices"][0]["message"].get("content")
obj, think, issues = _parse(text)
rec = {"tag": tag, "parsed": obj is not None, "parse_issues": issues if obj is None else []}
if obj is not None:
    spec = {"spec_id": f"ollama_{tag}", "source": "llm",
            "provenance": {"model": "qwen3.5:9b (ollama)", "prompt_version": "v002", "iteration": 2, "sample_idx": 3,
                           "runtime": "openai"},
            **{k: v for k, v in obj.items() if k not in ("spec_id", "source", "provenance")}}
    issues = validate(spec, load_site(SITE), load_bounds())
    rec.update(site=str(SITE), valid=not issues, n_issues=len(issues), issues=issues,
               n_archetypes=len(obj.get("driver_archetypes", [])), n_rules=len(obj.get("traci_rules", [])),
               rule_types=sorted({r.get("rule_type") for r in obj.get("traci_rules", [])}))
else:
    rec["valid"] = False
(OUT / f"{tag}_validation.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
print(json.dumps({k: v for k, v in rec.items() if k != "issues"}, ensure_ascii=False))
for i in rec.get("issues", []) or rec["parse_issues"]:
    print(f"  [{i['code']}] {i['path']}: {i['message']}")
