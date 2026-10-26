# Proxy-data end-to-end run (PLAN Phase 1–7, 3 LLM rounds) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build PLAN Phase 1–7 far enough to run the full methodology loop (metrics → LLM rule spec → compile → SUMO → distance → diagnosis → feedback) for exactly 3 rounds on literature-based proxy data, then benchmark B0/B1/B2/P and write a report.

**Architecture:** Python package `thesis_sumo` drives SUMO 1.27 (libsumo for batch, traci for GUI). Observed data and simulation output share one CSV schema (PLAN §5.1), so the same metric functions run on both. Proxy inputs are isolated in `config/site.proxy.yaml`, `data/proxy/targets.yaml` and `data/observed/PROXY_D*/`; swapping in real data means swapping files only.

**Tech Stack:** Python 3.12 venv, SUMO 1.27.0 (netconvert, routeSampler.py, libsumo/traci), numpy/pandas/scipy, jsonschema, openai client → Ollama 0.40.10 (`qwen3.5:9b`), optuna, matplotlib, pytest.

**Spec:** `docs/superpowers/specs/2026-10-25-proxy-benchmark-loop-design.md` (read with `PLAN.md` and `CLAUDE.md`).

## Global Constraints

- All CLAUDE.md rules hold. Exception 1: unmeasured values may come from literature, but only in proxy files, each value with `source:` and `evidence: literature | assumed`; `config/site.yaml` stays `null # TODO_MEASURE`.
- Exception 2: no stop for confirmation between phases; every decision taken at a former stop point (Phase 3 a/b, end of Phase 5) is logged in `docs/PROGRESS.md` with its reason.
- Every SUMO attribute/option is checked with `--help` or sumo.dlr.de/docs before use; `rules/bounds/param_bounds.yaml` rows carry `source_url`.
- `scenario_raw/` is never modified; `.net.xml` is never hand-edited (script + plain-XML patches only).
- Fixed seeds; every run writes `manifest.json` incl. `site_source` (`MEASURED` or `LITERATURE_PROXY`).
- `pathlib` only; readers accept `.xml` and `.xml.gz`.
- Proxy observed data is generated independently of any SUMO output (never fitted to B0).
- Budget counted in SUMO runs (1 spec × 1 seed = 1 run): LLM loop 3 rounds × 4 specs × 3 seeds = 36; Optuna 36 (12 trials × 3 seeds); invalid specs cost 0 runs.
- Calibration days PROXY_D1–D3, validation days PROXY_D4–D5; LLM and Optuna never see D4–D5 statistics.
- R = d_sim_obs / d_day_day; "realistic" when R ≤ 1; on proxy data R is reported as illustrative only.
- LLM: Ollama at `http://localhost:11434/v1`, model `qwen3.5:9b`, fallback `qwen3:8b`; models live in `D:\ollama\models`.
- Run commands with `.venv/Scripts/python`. Heavy outputs go under `experiments/runs/` (git-ignored).
- `docs/PROGRESS.md` gets one entry per task finished: what was done, commands, criteria met/unmet, assumptions, open TODO_MEASURE.

## Review Focus

1. A required `null` in the site file (real `site.yaml`) must raise `MissingFieldDataError` naming the key, never silently fall back to proxy values — test in Task 1.
2. LLM returns malformed/out-of-bounds JSON or a non-existent attribute: validator returns structured errors, retry ≤ 3, and the run counter does not increase — tests in Tasks 7 and 12.
3. A TraCI intervention that SUMO ignores (speed/lane-change mode overridden) must be logged with `executed: false`, and modes restored afterwards — test in Task 9.
4. A run with teleports, collisions or GEH-gate failure must be flagged in the manifest and excluded from "best spec" selection, never hidden by options — tests in Tasks 4 and 11.
5. A metric with no events in a run (e.g. zero red-light violations, zero box waiters) must yield a defined distance (not NaN/crash) — test in Task 10.

---

### Task 1: Config loading and proxy site file (research)

**Files:**
- Create: `src/thesis_sumo/config.py`, `config/site.proxy.yaml`, `docs/research/proxy_sources.md`, `docs/PROGRESS.md`
- Test: `tests/test_config.py`

**Interfaces:**
- Produces: `load_site(path: Path | None = None) -> Site` (default `config/site.yaml`; `Site` is a dict-like with `.source` = `"MEASURED"` or `"LITERATURE_PROXY"` read from a top-level `site_source:` key); `Site.require(dotted_key: str)` raises `MissingFieldDataError(key)` on `None`; `load_experiment() -> dict`; `load_llm() -> dict`; `REPO_ROOT: Path`.

- [ ] **Step 1:** Research (web) Hanoi/Vietnam values for: typical cycle and phase split at large 4-arm signalised intersections in Hanoi (and LVL × HĐT specifically if any source exists), lane widths of Le Van Luong / Hoang Dao Thuy, left/U-turn bans at this junction (street-view / news), AM-peak volumes and motorcycle share. Write each value with citation into `docs/research/proxy_sources.md`.
- [ ] **Step 2:** Write `config/site.proxy.yaml`: same structure as `site.yaml`, `site_source: LITERATURE_PROXY`, every filled value followed by `source` and `evidence` (use sibling keys `<key>_source`, `<key>_evidence`). `edge:` fields stay `null` until Task 2 fills them.
- [ ] **Step 3: Write failing tests**: `test_required_null_raises` (real `site.yaml`, `require("signal.cycle_s")` → `MissingFieldDataError` with `"signal.cycle_s"` in message); `test_proxy_site_marked` (`load_site(config/site.proxy.yaml).source == "LITERATURE_PROXY"`); `test_real_site_never_reads_proxy` (loading `site.yaml` returns `.source == "MEASURED"` and `signal.cycle_s is None`).
- [ ] **Step 4:** Implement `config.py`; run `pytest tests/test_config.py -v` → PASS.
- [ ] **Step 5:** Create `docs/PROGRESS.md` (header: goal, link to spec/plan, legend) with the Task 1 entry. Commit.

### Task 2: Network (Phase 1)

**Files:**
- Create: `src/thesis_sumo/net/build_net.py`, `src/thesis_sumo/net/apply_patches.py`, `src/thesis_sumo/net/diagram.py`, `scenario/net/patches/` (generated), `scenario/net/edge_table.csv`, `scenario/net/diagram.svg`
- Test: `tests/test_net.py`

**Interfaces:**
- Consumes: `load_site`.
- Produces: `build_base(site: Site, out: Path = scenario/net/base.net.xml) -> Path`; `edge_table(net: Path) -> pandas.DataFrame` (columns `edge_id, name, direction, n_lanes, length_m, connections`); `build_site_net(site: Site, base: Path, out: Path) -> Path` (proxy site → `scenario/net/site.proxy.net.xml`, measured → `site.net.xml`); CLI `python -m thesis_sumo.net.build --site <path>` builds everything in one command.

- [ ] **Step 1:** Check options with `netconvert --help` (geo-boundary cut, tls type, `--keep-edges.by-vclass`/`--remove-edges.by-type`, junction removal) and connection-level `permissions` in netconvert docs; record findings in PROGRESS.
- [ ] **Step 2: Failing tests**: `test_base_net_builds` (one command, netconvert exit 0); `test_target_tls_static` (target junction tlLogic `type="static"`); `test_banned_left_only_custom1` (on the proxy-banned approach, every `l` connection's lane allows only `custom1`); `test_signal_matches_site` (sum of phase durations == `signal.cycle_s` from site file).
- [ ] **Step 3:** Implement `build_base` and `edge_table`; print table; verify the unnamed edge `1071601648#4` (PLAN Phase 1.2); fill `approaches[].edge` in `site.proxy.yaml`. Report minor-node/TLS removals in PROGRESS before removing them.
- [ ] **Step 4:** Implement `build_site_net` (generates `lanes.edg.xml`, `turns.con.xml`, `signal.tll.xml` from the site file; warns loudly when using proxy values) and `diagram.py` (sumolib + matplotlib, labelled edge ids and directions).
- [ ] **Step 5:** `pytest tests/test_net.py -v` → PASS. Commit.

### Task 3: B0 vTypes, demand and sumocfg (Phase 2 part 1)

**Files:**
- Create: `rules/compiled/B0/vtypes.add.xml`, `src/thesis_sumo/demand/build_demand.py`, `src/thesis_sumo/sim/sumocfg.py`, `data/observed/SYNTHETIC/turn_counts.csv`, `scenario/demand/candidate_routes.rou.xml`
- Test: `tests/test_demand.py`

**Interfaces:**
- Consumes: `build_site_net` output, site file.
- Produces: `build_candidate_routes(net: Path, out: Path) -> Path`; `build_demand(turn_counts: Path, candidates: Path, out: Path, seed: int) -> Path` (calls `%SUMO_HOME%/tools/routeSampler.py`, options checked with `--help`; vehicle `type` attribute references distribution ids `car`, `moto`, `moto_violator`; `illegal_l` movement → `moto_violator`); `write_sumocfg(run_dir: Path, net: Path, routes: Path, additionals: list[Path], seed: int, exp: dict) -> Path` with step-length 0.1, lateral-resolution 0.4, tripinfo, tlsStates, instantInductionLoops at each entry stop line and exit, fcd filtered to 60 m with lateral position, lanechange-output, SSM PET (all attribute names checked against docs), rerouting off, no `ignore-route-errors`.

- [ ] **Step 1:** B0 vtypes: `car` (passenger), `moto` (motorcycle), `moto_violator` (custom1 with motorcycle default dims/speed/kinematics from the vClass defaults doc page); all `laneChangeModel="SL2015"`.
- [ ] **Step 2: Failing tests**: `test_candidate_routes_cover_all_movements` (every inbound→outbound pair allowed by the net appears once); `test_routesampler_matches_counts` (synthetic counts → sampled routes per 15-min cell within ±1 vehicle of input); `test_violator_type_mapping`.
- [ ] **Step 3:** Implement; `pytest tests/test_demand.py -v` → PASS. Commit.

### Task 4: Runner and manifest (Phase 2 part 2)

**Files:**
- Create: `src/thesis_sumo/sim/runner.py`, `src/thesis_sumo/sim/outputs.py`
- Test: `tests/test_runner.py`

**Interfaces:**
- Consumes: `write_sumocfg`, compiled spec dir (`rules/compiled/<spec_id>/vtypes.add.xml` + optional `traci_rules.json`), `Controller` (Task 9; runner accepts `controller_factory=None` until then).
- Produces: `run(spec_id: str, day: str, seed: int, use_gui: bool = False, site_path: Path | None = None, sim_end_s: float | None = None) -> RunResult` where `RunResult` has `run_dir: Path`, `manifest: dict` (git hash, SUMO version, spec hash, net hash, seed, config, `site_source`, `n_teleports`, `n_collisions`, `insertion_backlog`, `valid: bool`); `run_many(jobs: list[tuple[str,str,int]], n_proc: int) -> list[RunResult]` (multiprocessing, one SUMO per process); `to_observed_schema(run_dir: Path) -> dict[str, pandas.DataFrame]` writing `turn_counts.csv, signal_events.csv, stopline_crossings.csv, queue_snapshots.csv, lateral_snapshots.csv, box_queue.csv` into `run_dir/observed_schema/` with the exact PLAN §5.1 columns.
- Output path: `experiments/runs/<run_id>/seed_XX/`; `run_id = f"{spec_id}__{day}"`.

- [ ] **Step 1: Failing tests**: `test_manifest_fields` (all keys above present); `test_teleport_marks_invalid` (tiny scenario with forced teleport → `valid is False`); `test_schema_columns` (each CSV has exactly the §5.1 columns).
- [ ] **Step 2:** Implement; `pytest tests/test_runner.py -v` → PASS.
- [ ] **Step 3:** Run B0 3600 s × seeds 1,2,3 on proxy site + SYNTHETIC demand; record wall time per run, teleports, collisions, backlog in PROGRESS. If teleports: find cause and report (no hiding options). If one run > ~5 min, set `sim.calib_end_s: 1800` in `experiment.yaml` and log it.
- [ ] **Step 4:** Operator agent opens one run in sumo-gui (traci backend) and records observations/screenshot in PROGRESS. Commit.

### Task 5: In-box waiting experiment (Phase 3, decision logged, no stop)

**Files:**
- Create: `experiments/phase3/box_capacity.py`, `docs/research/phase3_box_capacity.md`

**Interfaces:**
- Consumes: `runner`, proxy net. Produces: decision `illegal_left.mode: native | box_edge` written to `config/site.proxy.yaml` (as modelling choice, `evidence: experiment`), and, for `box_edge`, an extra patch in `build_site_net`.

- [ ] **Step 1:** Scenario per PLAN Phase 3: dense opposing through flow, many `moto_violator` from the banned approach; per step log count on the left-turn internal lanes, lateral positions, discharge time vs opposing yellow/red onset, deadlocks/teleports, interaction with crossing flow.
- [ ] **Step 2:** Compare max native capacity with the proxy target for vehicles waiting in box (Task 6 `targets.yaml` M7a). Choose (a) native if capacity ≥ target mean, else (b) box edge. Write numbers + decision in the md and PROGRESS. If (b): implement the patch, add `test_box_edge_signal` to `tests/test_net.py` (box link green only while opposing through is red). Commit.

### Task 6: Proxy observed data (targets + generator)

**Files:**
- Create: `data/proxy/targets.yaml`, `src/thesis_sumo/proxy/generate.py`, `data/observed/PROXY_D1..D5/*.csv`
- Test: `tests/test_proxy.py`

**Interfaces:**
- Consumes: site proxy (cycle/phases, approaches).
- Produces: `generate_day(targets: dict, site: Site, day_id: str, seed: int, out_dir: Path) -> None` writing the six §5.1 CSVs; CLI `python -m thesis_sumo.proxy.generate` writes D1–D5 with seeds 101–105.

- [ ] **Step 1:** Research (web) and write `targets.yaml`: per metric M1–M8 + G0 counts, the distribution family, parameters, between-day variation, `source`, `evidence: literature | assumed`. Minimum coverage: motorcycle and car discharge headway (Vietnam/Hanoi saturation-flow studies), red-light violation rate and per-cycle dispersion, early-start share, lateral position of motorcycles at stop line, queue length/density at green onset, traversal time, illegal-left box queue size and clearing time, PET, wrong-lane share. Missing literature → assumed value, labelled.
- [ ] **Step 2: Failing tests**: `test_generator_deterministic` (same seed → identical files); `test_days_differ` (D1 vs D2 not identical); `test_generated_means_match_targets` (over 5 days, mean of each scalar within 15% of target mean); `test_schema_columns`.
- [ ] **Step 3:** Implement; generate D1–D5; set `data_split` in `experiment.yaml` (calibration D1–D3, validation D4–D5). `pytest tests/test_proxy.py -v` → PASS. Commit.

### Task 7: Param bounds, rule schema, validator (Phase 4.1–4.3)

**Files:**
- Create: `rules/bounds/param_bounds.yaml`, `rules/schema/rule_spec.schema.json`, `src/thesis_sumo/rules/schema.py`, `src/thesis_sumo/rules/validator.py`
- Test: `tests/test_validator.py`

**Interfaces:**
- Produces: `load_bounds() -> dict[str, Bound]` (`min, max, default, unit, model, source_url, behavior_group`); `validate(spec: dict, site: Site) -> list[ValidationIssue]` where `ValidationIssue = {path: str, code: str, message: str}` (codes: `schema`, `unknown_attr`, `out_of_bounds`, `share_sum`, `rule_params`, `logic`); `ValidityLog.record(spec_id, issues)` appending to `experiments/validity_log.csv`.
- `TRACI_RULE_PARAMS` dict in `schema.py`: per rule_type its params with min/max (early_start: `t_before_green, p, v_max`; swarm_red_running: `p0, k, p_max, dt`; wrong_lane_dodge: `q_min, v_creep`; illegal_left_box: per Task 5; slow_lane_center: `lat_offset`).

- [ ] **Step 1:** Check every candidate attribute (PLAN 4.2 list) on sumo.dlr.de docs; keep only those that exist in 1.27 with their docs URL; drop/mark the rest in PROGRESS.
- [ ] **Step 2: Failing tests**: `test_valid_spec_passes` (`rules/specs/B1_manual.json` → `[]`); `test_unknown_attr` (`code == "unknown_attr"`); `test_out_of_bounds`; `test_share_sum` (shares 0.6+0.6 → `share_sum`); `test_minGapLat_wider_than_lane` (→ `logic`); `test_rule_params_invalid`.
- [ ] **Step 3:** Write `B1_manual.json` from Saval et al. (2023) (e.g. front-row motorcycles stop at red with p = 0.5) as the fixed structure for E1; implement; tests PASS. Commit.

### Task 8: Compiler (Phase 4.4)

**Files:**
- Create: `src/thesis_sumo/rules/compiler.py`
- Test: `tests/test_compiler.py`, `tests/snapshots/B1_vtypes.add.xml`

**Interfaces:**
- Consumes: validated spec. Produces: `compile_spec(spec: dict, out_dir: Path = rules/compiled/<spec_id>/) -> CompiledSpec(vtypes: Path, traci_rules: Path)`; distributions named exactly `car`, `moto`, `moto_violator`.

- [ ] **Step 1: Failing tests**: `test_snapshot_B1` (byte-equal to snapshot); `test_distribution_ids`; `test_sumo_loads_compiled` (sumo with `--additional-files` on the compiled file exits 0 for 10 s).
- [ ] **Step 2:** Implement; tests PASS. Commit.

### Task 9: TraCI runtime controller and rules (Phase 4.5)

**Files:**
- Create: `src/thesis_sumo/runtime/controller.py`, `src/thesis_sumo/runtime/rules/{early_start,swarm_red_running,wrong_lane_dodge,illegal_left_box,slow_lane_center}.py`
- Test: `tests/test_runtime.py`

**Interfaces:**
- Produces: `Controller(rules: list[dict], backend, site: Site, log_path: Path)` with `on_step() -> None` (uses subscriptions; only vehicles within the junction radius); `RULE_REGISTRY: dict[str, type[Rule]]`; `Rule.on_step(state) -> list[Intervention]`; intervention log CSV columns `t, veh_id, rule, action, executed`.
- Runner (Task 4) constructs the Controller when `traci_rules.json` is non-empty.

- [ ] **Step 1: Failing tests** (one scenario per rule, tiny net): `test_early_start_fires` (vehicle crosses stop line before green; log `executed == True`); `test_swarm_probability_rises`; `test_wrong_lane_dodge_fires` (or reports unsupported connection clearly); `test_illegal_left_box_fires`; `test_ignored_command_logged` (command SUMO overrides → `executed == False`); `test_modes_restored` (speed/lane-change mode back to original after intervention).
- [ ] **Step 2:** Implement; tests PASS; run `B1_manual` once via runner on proxy D1 (3600 s or calib length) and log intervention counts. Commit.

### Task 10: Metrics M1–M8, G0 and distance (Phase 5)

**Files:**
- Create: `src/thesis_sumo/metrics/{m1_headway,m2_early_start,m3_red_running,m4_lateral,m5_queue,m6_traversal,m7_illegal_left,m8_wrong_lane,g0_geh,distance}.py`
- Test: `tests/test_metrics.py`

**Interfaces:**
- Consumes: `dict[str, DataFrame]` in §5.1 schema (from `to_observed_schema` or `data/observed/<day>/`).
- Produces: each `mX.compute(tables) -> MetricValue` (`kind: "dist" | "scalar"`, `values: np.ndarray | float`, sub-keys allowed, e.g. `M7a/M7b/M7c`); `g0_geh.gate(sim, obs, threshold=5, min_share=0.85) -> (bool, float)`; `distance.compare(sim_tables: list[dict], obs_days: list[dict], weights: dict) -> DistanceReport` with per metric `d`, `d_day_day`, `R`, `direction` (`sim>obs` / `sim<obs`), and `S`; `DistanceReport.to_row() -> dict` for `results/metrics.csv`.
- Distances: W1 normalised by observed IQR for dist metrics, relative error for scalars; `d_day_day` = mean pairwise distance among the given observed days. Weights: equal across M1–M8 (write to `experiment.yaml score.weights`, log as my call).

- [ ] **Step 1: Failing tests** with hand-built tables and known answers: `test_m1_headway_known`, `test_m3_violations_per_cycle`, `test_m7_box_count`, `test_geh_gate`, `test_w1_iqr_normalised`, `test_R_ratio`, `test_empty_events_defined_distance` (zero events in sim → finite d, documented rule).
- [ ] **Step 2:** Implement; tests PASS. Run all metrics on B0 output vs PROXY D1–D3; write first `DistanceReport` to PROGRESS (this is the end-of-Phase-5 checkpoint; continue without stopping). Commit.

### Task 11: Experiment harness (shared evaluation + budget counter)

**Files:**
- Create: `src/thesis_sumo/evaluate.py`
- Test: `tests/test_evaluate.py`

**Interfaces:**
- Produces: `RunBudget(total: int)` with `.consume(n)`, `.remaining`, persisted to `experiments/<campaign>/budget.json`; `evaluate_spec(spec: dict, days: list[str], seeds: list[int], budget: RunBudget) -> EvalResult` (validate → compile → `run_many` → `to_observed_schema` → GEH gate → `distance.compare`; invalid spec costs 0; runs with `valid=False` or failing gate are excluded and reported); `EvalResult = {spec_id, S, report: DistanceReport, n_runs, excluded_runs, interventions_summary}`.

- [ ] **Step 1: Failing tests**: `test_invalid_spec_costs_nothing`; `test_budget_exhausted_raises`; `test_gate_failure_excluded`.
- [ ] **Step 2:** Implement; tests PASS. Commit.

### Task 12: LLM client, prompts v001, feedback

**Files:**
- Create: `src/thesis_sumo/llm/client.py`, `src/thesis_sumo/llm/prompts/v001/{system,context,feedback}.md`, `src/thesis_sumo/llm/feedback.py`; Modify: `config/llm.yaml`
- Test: `tests/test_llm.py`

**Interfaces:**
- Produces: `LLMClient(cfg: dict)`; `.generate_spec(messages: list[dict], schema: dict) -> tuple[dict, dict]` (spec, raw record); tries `/v1` `response_format` json_schema, falls back to native `/api/chat` with `format=schema`; validate + retry ≤ 3 feeding validator issues back; logs full request/response (incl. thinking) to `experiments/llm_logs/<ts>.json`. `build_context(bounds, site, targets_calib) -> str` (parameter dictionary auto-generated from `param_bounds.yaml`); `build_feedback(prev: list[EvalResult], issues, interventions) -> str` (per-metric d, R, direction, validator errors, TraCI log summary; never validation-day data).
- `config/llm.yaml`: `base_url: http://localhost:11434/v1`, `runtime: ollama`, `model: qwen3.5:9b`, `quant: Q4_K_M` (verify with `ollama show`), `temperature: 0.7`, `seed: 42`, `n_samples: 4`, comment marking these as provisional choices.

- [ ] **Step 1:** Check Ollama docs for structured outputs on `/v1` vs `/api/chat`; record in PROGRESS.
- [ ] **Step 2: Failing tests** (mock HTTP): `test_retry_on_invalid_then_success` (2 bad + 1 good → spec, 3 calls); `test_gives_up_after_3`; `test_feedback_has_no_validation_days` (feedback text contains no `PROXY_D4`/`PROXY_D5` values); `test_context_lists_only_bounds_attrs`.
- [ ] **Step 3:** Implement; tests PASS; smoke-test one real call to Ollama and record latency and validity in PROGRESS. Commit.

### Task 13: LLM loop — 3 rounds

**Files:**
- Create: `src/thesis_sumo/llm/loop.py`, `experiments/llm_loop/` (outputs)

**Interfaces:**
- Consumes: `LLMClient`, `evaluate_spec`, `RunBudget(36)`, `build_feedback`.
- Produces: `run_loop(n_iter: int = 3, n_samples: int = 4, seeds: list[int] = [1, 2, 3], days: list[str] = calibration_days) -> LoopResult` saving each spec to `rules/specs/llm_it{i}_s{j}.json`, per-iteration summary `experiments/llm_loop/iter_{i}.json`, best spec across all iterations as `rules/specs/P_best.json`; convergence series (runs used vs best S).

- [ ] **Step 1:** Implement (iteration 1 prompt: system + context + calibration targets; iterations 2–3 add feedback of the previous iteration's specs).
- [ ] **Step 2:** Run the 3 rounds. After each round the coordinator writes a diagnosis note into PROGRESS (which metrics moved, why the remaining gaps likely exist — SUMO mechanism, proxy data, LLM behaviour); the note is NOT fed to the LLM. Commit outputs (specs, summaries; not raw runs).

### Task 14: Optuna baseline B2

**Files:**
- Create: `src/thesis_sumo/baselines/optuna_search.py`

**Interfaces:**
- Produces: `run_optuna(n_trials: int = 12, seeds=[1,2,3], structure="B1_manual") -> OptunaResult`; same search space (bounds + TraCI rule params of the B1 structure), same objective (`evaluate_spec(...).S`), own `RunBudget(36)`, TPE sampler seed 0; best spec → `rules/specs/B2_best.json`; convergence series.

- [ ] **Step 1:** Implement and run; record result in PROGRESS. Commit.

### Task 15: Benchmark and report

**Files:**
- Create: `src/thesis_sumo/benchmark.py`, `results/metrics.csv`, `results/figures/*.png`, `docs/reports/2026-10-proxy-run-report.md`

**Interfaces:**
- Produces: `run_benchmark(specs=["B0","B1_manual","B2_best","P_best", "llm best of iter 1/2/3"], days=validation_days, n_seeds=20) -> DataFrame` (one row per spec × seed × day into `results/metrics.csv`); figures: sim vs obs distribution per metric, convergence LLM vs Optuna; stats: Mann–Whitney per pair with Holm correction and Cliff's delta.

- [ ] **Step 1:** Implement and run (20 seeds × D4–D5; if runtime too long, log the reduced count used).
- [ ] **Step 2:** Optional if time permits (log which were done): ablation per TraCI rule/parameter group; illegal-left 0/50/100% scenario; Morris sensitivity.
- [ ] **Step 3:** Write the report per spec §6 (what improved after 3 rounds per metric vs B0, literature vs assumed groups separately, convergence, rule quality, blockers, what changes once video data arrives). Publish it as a page for Viktor. Update README status and PROGRESS. Commit.
