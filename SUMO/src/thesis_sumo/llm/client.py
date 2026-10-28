"""LLM client (PLAN Phase 6.1, plan Task 12): one rule spec per call, validated, with up to `max_attempts` tries.

Backends (`cfg["runtime"]`, config/llm.yaml; `llm_config()` returns the active block):
- `openai`: any OpenAI-compatible server (Ollama / vLLM / LM Studio) through the `openai` package. Structured output
  via `response_format = {"type": "json_schema", ...}` with `llm_schema`; if the server rejects it (HTTP 400/422)
  the client switches to plain JSON for the rest of the session and relies on validate + retry. Reasoning text
  (`reasoning_content` (vLLM) / `reasoning` (Ollama) / inline `<think>...</think>`) is kept in the log.
- `file`: the stand-in LLM (Linux has no Ollama; a Claude subagent driven by the controller). The request is
  written to `<log_dir>/requests/<request_id>.json`; the answer is read from `<log_dir>/responses/<request_id>.json`
  (either `{"content": <JSON text or object>, "reasoning": ...}` or the spec object itself). A missing answer raises
  `PendingResponse`: the loop stops, the controller answers, and the same call is repeated later.

Each attempt: parse JSON -> the harness inserts `spec_id`, `source: llm` and `provenance` (model, prompt_version,
iteration, sample_idx, runtime) -> `validator.validate` (+ `validator.structure_issues` in mode params_only) -> on
issues the reply and a retry message with the structured issues are appended and the next attempt starts.
Every attempt is logged in full to `<log_dir>/<request_id>.json` (messages, schema, raw response, reasoning, spec,
issues) and its validity is appended to the ValidityLog `<log_dir>/validity_log.csv` (a thesis metric). Request ids
are deterministic (campaign, iteration, sample, attempt); an attempt whose log exists is replayed from the log
(same messages required), not re-asked and not re-counted, so an interrupted loop resumes exactly.

`llm_schema(mode, base_spec)` is the LLM-facing subset of rule_spec.schema.json (ruling R18: attributes enumerated
from the bounds, one schema per rule type with its params as separate keys, no if/then/propertyNames/uniqueItems/
not/$ref; provenance inserted by the harness). The full schema still validates every spec.

Notes for Tasks 13/14:
- An attempt is replayed only when its log matches the messages AND the LLM setup (runtime, server, model, quant,
  prompt_version); otherwise ValueError, so stand-in answers can never be relabelled as another model's.
- For runtime openai, temperature and quant are required (null = TODO_DECIDE raises); seed is optional.
- `feedback.build_context` trusts its `targets_calib` argument: pass only `feedback.calibration_targets(...)` output
  (it refuses validation days); never targets computed from validation days.
- In mode full the LLM schema offers the full enum of a categorical vType param (latAlignment); params_only locks
  categorical values to the base spec's (structure_locked), so only numeric params and shares are tunable there,
  as in Optuna's fixed-structure search.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from thesis_sumo.config import REPO_ROOT, Site, load_llm
from thesis_sumo.llm.feedback import PROMPTS_DIR, build_retry
from thesis_sumo.rules.schema import DISTRIBUTIONS, TRACI_RULE_PARAMS, VCLASSES, Bound, load_bounds
from thesis_sumo.rules.validator import ValidityLog, structure_issues, validate

LOGS_DIR = REPO_ROOT / "experiments" / "llm_logs"
MODES = ("params_only", "full")
RUNTIMES = ("openai", "file")
HARNESS_KEYS = ("spec_id", "source", "provenance")
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
THINK_RE = re.compile(r"<think>(.*?)</think>", re.DOTALL)
FENCE_RE = re.compile(r"^```[a-zA-Z]*\s*(.*?)\s*```$", re.DOTALL)


class PendingResponse(Exception):
    """The file backend has no answer yet for `request_id`; write it to `path` and call again."""

    def __init__(self, request_id: str, path: Path):
        self.request_id, self.path = request_id, Path(path)
        super().__init__(f"LLM response pending: {request_id} (expected at {path})")


def llm_config(doc: dict | None = None) -> dict:
    """The active block of config/llm.yaml (`active:` selects it), plus the shared top-level keys."""
    doc = doc if doc is not None else load_llm()
    active = doc.get("active")
    if not isinstance(doc.get(active), dict):
        raise ValueError(f"llm.yaml: `active` must name a block of the file, got {active!r}")
    shared = {k: v for k, v in doc.items() if not isinstance(v, dict) and k != "active"}
    return {**shared, **doc[active], "profile": active}


# ---------------------------------------------------------------- LLM-facing schema (R18)


def _attr_schema(b: Bound, vclasses) -> dict:
    if b.values is not None:
        return {"enum": list(b.values)}
    rs = [b.for_vclass(v) for v in vclasses]
    return {"type": "number", "minimum": min(r.min for r in rs), "maximum": max(r.max for r in rs)}


def _rule_schema(rtype: str, names=None, applies_to=None) -> dict:
    params = TRACI_RULE_PARAMS[rtype]
    names = list(names) if names is not None else list(params)
    required = names if applies_to is not None else [n for n in names if not params[n].optional]
    if applies_to is None:
        applies = {"type": "array", "minItems": 1, "items": {"type": "string"}}
    else:
        applies = {"type": "array", "minItems": len(applies_to), "maxItems": len(applies_to),
                   "items": {"enum": list(applies_to)}}
    return {"type": "object", "additionalProperties": False, "required": ["rule_type", "applies_to", "params", "rationale"],
            "properties": {
                "rule_type": {"enum": [rtype]}, "applies_to": applies,
                "params": {"type": "object", "additionalProperties": False, "required": required,
                           "properties": {n: {"type": "number", "minimum": params[n].min, "maximum": params[n].max}
                                          for n in names}},
                "rationale": {"type": "string"}}}


def _archetype_schema(bounds: dict[str, Bound], base: dict | None = None) -> dict:
    props = {"id": {"type": "string"}, "base_vclass": {"enum": list(VCLASSES)}, "distribution": {"enum": list(DISTRIBUTIONS)},
             "share": {"type": "number", "minimum": 0, "maximum": 1}}
    required = ["id", "base_vclass", "share", "params", "rationale"]
    if base is None:
        params = {"type": "object", "additionalProperties": False,
                  "properties": {n: _attr_schema(b, b.vclasses) for n, b in bounds.items() if not b.fixed}}
    else:
        props.update(id={"enum": [base["id"]]}, base_vclass={"enum": [base["base_vclass"]]})
        if "distribution" in base:
            props["distribution"] = {"enum": [base["distribution"]]}
            required.append("distribution")
        else:
            del props["distribution"]
        params = {"type": "object", "additionalProperties": False, "required": list(base["params"]),
                  "properties": {n: _attr_schema(bounds[n], [base["base_vclass"]]) if n in bounds else {}
                                 for n in base["params"]}}
    return {"type": "object", "additionalProperties": False, "required": required,
            "properties": {**props, "params": params, "rationale": {"type": "string"}}}


def llm_schema(mode: str, base_spec: dict | None = None, bounds: dict[str, Bound] | None = None) -> dict:
    """JSON schema of the LLM's answer: `driver_archetypes`, `traci_rules`, optional `description`. params_only locks
    the archetypes and rules of `base_spec` (one schema variant per base archetype / rule)."""
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}, got {mode!r}")
    bounds = bounds if bounds is not None else load_bounds()
    if mode == "full":
        archs = {"type": "array", "minItems": 1, "items": _archetype_schema(bounds)}
        rules = {"type": "array", "items": {"anyOf": [_rule_schema(t) for t in TRACI_RULE_PARAMS]}}
    else:
        if base_spec is None:
            raise ValueError("params_only needs the base spec whose structure is locked")
        a, r = base_spec["driver_archetypes"], base_spec["traci_rules"]
        archs = {"type": "array", "minItems": len(a), "maxItems": len(a),
                 "items": {"anyOf": [_archetype_schema(bounds, x) for x in a]}}
        rules = {"type": "array", "minItems": len(r), "maxItems": len(r),
                 "items": {"anyOf": [_rule_schema(x["rule_type"], x["params"], x["applies_to"]) for x in r]}}
    return {"type": "object", "additionalProperties": False, "required": ["driver_archetypes", "traci_rules"],
            "properties": {"description": {"type": "string"}, "driver_archetypes": archs, "traci_rules": rules}}


# ---------------------------------------------------------------- client


def _parse(text: str | None) -> tuple[dict | None, str | None, list[dict]]:
    """(object, inline reasoning, issues) of a raw answer."""
    text = text or ""
    think = "\n".join(m.strip() for m in THINK_RE.findall(text)) or None
    body = THINK_RE.sub("", text).strip()
    m = FENCE_RE.match(body)
    body = m.group(1) if m else body
    try:
        obj = json.loads(body)
    except json.JSONDecodeError as e:
        return None, think, [{"path": "(response)", "code": "schema",
                              "message": f"the answer is not valid JSON ({e.msg} at line {e.lineno} column {e.colno}); "
                                         f"answer with one JSON object only"}]
    if not isinstance(obj, dict):
        return None, think, [{"path": "(response)", "code": "schema",
                              "message": f"the answer must be a JSON object, got {type(obj).__name__}"}]
    return obj, think, []


def _sha(messages: list[dict]) -> str:
    return hashlib.sha256(json.dumps(messages, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def _write_json(path: Path, doc) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=1, ensure_ascii=False, default=str), encoding="utf-8")


class LLMClient:
    def __init__(self, cfg: dict, *, site: Site, campaign: str, log_root: Path | None = None,
                 validity_log: ValidityLog | None = None, http_client=None, bounds: dict[str, Bound] | None = None):
        self.cfg, self.site, self.campaign = cfg, site, campaign
        if cfg.get("runtime") not in RUNTIMES:
            raise ValueError(f"llm config `runtime` must be one of {RUNTIMES}, got {cfg.get('runtime')!r}")
        openai_keys = ("base_url", "temperature", "quant")  # seed optional: not every runtime supports it
        for key in ("model", "prompt_version", "max_attempts") + (openai_keys if cfg["runtime"] == "openai" else ()):
            if cfg.get(key) is None:
                raise ValueError(f"llm.yaml {cfg.get('profile', '?')}.{key} is null (TODO_DECIDE); no default")
        if not (PROMPTS_DIR / str(cfg["prompt_version"])).is_dir():
            raise ValueError(f"prompt_version {cfg['prompt_version']!r}: no directory {PROMPTS_DIR} / <version>")
        if not NAME_RE.match(campaign):
            raise ValueError(f"campaign {campaign!r}: use letters, digits, '_', '.', '-' (it becomes part of spec ids)")
        self.log_dir = Path(log_root if log_root is not None else LOGS_DIR) / campaign
        self.validity = validity_log or ValidityLog(self.log_dir / "validity_log.csv")
        self.bounds = bounds if bounds is not None else load_bounds()
        self.structured = True
        self._openai = None
        if cfg["runtime"] == "openai":
            import openai
            self._openai = openai.OpenAI(base_url=cfg["base_url"], api_key=cfg.get("api_key") or "unused",
                                         timeout=cfg.get("timeout_s", 600), max_retries=0, http_client=http_client)

    @property
    def runtime_label(self) -> str:
        return str(self.cfg.get("server") or self.cfg["runtime"])

    def _identity(self) -> dict:
        """What an attempt log must match to be replayed (provenance comes from the current config)."""
        return {"runtime": self.cfg["runtime"], "server": self.cfg.get("server"), "model": self.cfg["model"],
                "quant": self.cfg.get("quant"), "prompt_version": self.cfg["prompt_version"]}

    def request_id(self, iteration: int, sample_idx: int, attempt: int) -> str:
        return f"{self.campaign}__it{iteration:02d}_s{sample_idx:02d}_a{attempt}"

    # ------------------------------------------------------------ backends: -> (text, reasoning, raw, request extras)

    def _call_file(self, rid: str, messages: list[dict], schema: dict, mode: str, attempt: int):
        _write_json(self.log_dir / "requests" / f"{rid}.json",
                    {"request_id": rid, "campaign": self.campaign, "mode": mode, "attempt": attempt,
                     "model": self.cfg["model"], "messages": messages, "schema": schema})
        path = self.log_dir / "responses" / f"{rid}.json"
        if not path.is_file():
            raise PendingResponse(rid, path)
        raw = path.read_text(encoding="utf-8")
        try:
            doc = json.loads(raw)
        except json.JSONDecodeError:
            return raw, None, raw, {}
        if isinstance(doc, dict) and "content" in doc:
            c = doc["content"]
            return (c if isinstance(c, str) else json.dumps(c)), doc.get("reasoning"), doc, {}
        return raw, None, doc, {}

    def _call_openai(self, messages: list[dict], schema: dict, sample_idx: int):
        import openai
        kw = {"model": self.cfg["model"], "messages": messages}
        if self.cfg.get("temperature") is not None:
            kw["temperature"] = self.cfg["temperature"]
        if self.cfg.get("seed") is not None:
            kw["seed"] = int(self.cfg["seed"]) + sample_idx  # same seed for every sample = identical samples
        extras = {k: v for k, v in kw.items() if k != "messages"}
        if self.structured:
            fmt = {"type": "json_schema", "json_schema": {"name": "rule_spec", "schema": schema}}
            try:
                resp = self._openai.chat.completions.create(**kw, response_format=fmt)
                extras["response_format"] = "json_schema"
            except (openai.BadRequestError, openai.UnprocessableEntityError) as e:
                self.structured = False
                extras["structured_output_rejected"] = str(e)
        if not self.structured:
            resp = self._openai.chat.completions.create(**kw)
            extras["response_format"] = "none"
        msg = resp.choices[0].message
        extra = msg.model_extra or {}
        reasoning = extra.get("reasoning_content") or extra.get("reasoning")
        return msg.content, reasoning, resp.model_dump(), extras

    # ------------------------------------------------------------ main entry

    def generate_spec(self, messages: list[dict], mode: str, base_spec: dict | None = None, *, iteration: int,
                      sample_idx: int) -> tuple[dict | None, dict]:
        """A valid spec (or None after `max_attempts` invalid answers) and the raw record of the attempts. Raises
        PendingResponse (file backend) when an answer is still missing."""
        if mode == "params_only" and base_spec is None:
            raise ValueError("params_only needs base_spec")
        schema = llm_schema(mode, base_spec, self.bounds)
        spec_id = f"{self.campaign}_it{iteration:02d}_s{sample_idx:02d}"
        provenance = {"model": self.cfg["model"], "prompt_version": self.cfg["prompt_version"], "iteration": iteration,
                      "sample_idx": sample_idx, "runtime": self.runtime_label}
        messages = list(messages)
        record = {"spec_id": spec_id, "campaign": self.campaign, "mode": mode, "attempts": [], "valid": False}
        for attempt in range(1, int(self.cfg["max_attempts"]) + 1):
            rid = self.request_id(iteration, sample_idx, attempt)
            log_path = self.log_dir / f"{rid}.json"
            sha = _sha(messages)
            cached = log_path.is_file()
            if cached:
                log = json.loads(log_path.read_text(encoding="utf-8"))
                if log["messages_sha256"] != sha:
                    raise ValueError(f"{log_path}: logged attempt was asked with other messages; use a new campaign "
                                     f"or remove the log")
                same = {k: (log.get(k), v) for k, v in self._identity().items() if log.get(k) != v}
                if same:
                    raise ValueError(f"{log_path}: logged attempt came from another LLM setup {same} (logged, "
                                     f"config); its answer would be relabelled; use a new campaign or log root")
                text, reasoning = log["response"]["text"], log["response"]["reasoning"]
            elif self.cfg["runtime"] == "file":
                text, reasoning, raw, extras = self._call_file(rid, messages, schema, mode, attempt)
            else:
                text, reasoning, raw, extras = self._call_openai(messages, schema, sample_idx)
            obj, think, issues = _parse(text)
            spec = None
            if obj is not None:
                spec = {"spec_id": spec_id, "source": "llm", "provenance": provenance,
                        **{k: v for k, v in obj.items() if k not in HARNESS_KEYS}}
                issues = validate(spec, self.site, self.bounds)
                if mode == "params_only" and not any(i["code"] == "schema" for i in issues):
                    issues += structure_issues(spec, base_spec)
            if not cached:
                _write_json(log_path, {
                    "request_id": rid, "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "campaign": self.campaign, "iteration": iteration, "sample_idx": sample_idx, "attempt": attempt,
                    "mode": mode, "runtime": self.cfg["runtime"], "server": self.cfg.get("server"),
                    "model": self.cfg["model"], "quant": self.cfg.get("quant"),
                    "prompt_version": self.cfg["prompt_version"], "messages_sha256": sha,
                    "request": {"messages": messages, "schema": schema, **extras},
                    "response": {"text": text, "reasoning": reasoning or think, "raw": raw},
                    "spec": spec, "valid": not issues, "issues": issues})
                self.validity.record(f"{spec_id}#a{attempt}", issues, source=f"llm:{mode}")
            record["attempts"].append({"attempt": attempt, "request_id": rid, "log": str(log_path), "cached": cached,
                                       "valid": not issues, "issues": issues})
            if not issues:
                record["valid"] = True
                return spec, record
            messages += [{"role": "assistant", "content": text or ""},
                         {"role": "user", "content": build_retry(issues, prompt_version=self.cfg["prompt_version"])}]
        return None, record
