# Ledger — proxy-benchmark-loop, continued on Linux (2026-10-26)

The original ledger (`.superpowers/sdd/2026-10-25-proxy-benchmark-loop/progress.md`) stays on the Windows machine
(it was git-ignored). Source of truth: `PLAN.md` (repo root, new version with custom2, M9–M11, Phase 3A–3D,
E1/E2, policy evaluation), then `docs/PROGRESS.md` rulings R1–R34. Old commit hashes in PROGRESS do not resolve
(SUMO/.git was removed).

## Environment (Linux)
- `SUMO/scripts/setup_env.py` -> `.venv` (uv, Python 3.12.3), eclipse-sumo 1.27.0 wheel, libsumo/sumo-data 1.27.0
  --no-deps, `sumo_tools.pth` sets SUMO_HOME. git-lfs 3.4.1 in ~/.local/bin (no sudo). Full suite after Task 10:
  242 passed, 1 xfailed.
- No Ollama: the LLM stand-in is a Claude Sonnet subagent; provenance.model "claude-sonnet (stand-in)".
- Foreign process: sumo-gui PID 1132137 from another Claude session (~/sumo-venv, SUMO 1.28) — not ours, not killed.

## Order
Task 10 (distance) -> R28 re-run on Linux (9 runs; thresholds NOT frozen: F2 changes the network) -> Task F2-net
-> Phase 3A/3B/3C/3D experiments -> STOP (Viktor decides 3C, 3D) -> F2 rules (queue_space_seeking) + M9–M11 ->
R28 freeze on the F2 network -> Task 11–15 (P1/P2/B2/H, E1/E2, policy/evaluate.py).

## Task F2-net brief (PLAN §0 "Hạ tầng đã xác nhận", Phase 1.4, Phase 2.1)
Field fact from Viktor: every approach has a continuous right-turn lane (outermost right lane, not signal
controlled); LVL has a hard median only for a short stretch before the stop line.

Build (net + site + B0 vTypes; no TraCI rules yet — those follow Phase 3):
1. Site files: per approach `continuous_right_lane` (site.yaml: `true`, field-confirmed; site.proxy.yaml: `true`
   with evidence `field_observation`, a new label allowed only on this key), `right_lane_separator`,
   `sidewalk_width_m`, `hard_median_length_m` (site.yaml `null # TODO_MEASURE`; proxy: assumed values with source or
   left null where no source), top-level `violator_classes: {moto: custom1, car: custom2}`, `f2_measured_approaches`.
   `lane_movements` lane 0 becomes `[r]` on continuous-right approaches.
2. `turns.con.xml`: on continuous-right approaches the straight connection(s) from lane 0 are deleted and re-added
   with `allow="custom1 custom2"` (compliant traffic turns right only from lane 0).
3. `signal.tll.xml`: right-turn links of continuous-right approaches are `g` (green, yield) in every phase; right
   turn on red is not a violation.
4. Sidewalk lane (`sidewalk.edg.xml`/`.con.xml`) on `f2_measured_approaches` only: right-edge lane,
   width `sidewalk_width_m`, `allow="custom1"`, low speed, joining the right turn and the outermost lane before the
   stop line. Null width -> MissingFieldDataError (no default).
5. B0: add `car_violator` (vClass custom2, passenger defaults copied explicitly, SL2015) like `moto_violator`.
6. Proxy days regenerated (lane markings changed); demand rebuilt.
Tests: right links never `r`; non-right link states unchanged char-by-char; lane-0 straight only custom1/custom2;
null site values raise; byte-identical rebuild; custom2 defaults equal passenger.

## Status
- Task 10: distance.py + experiment.yaml (metric_window_s, equal group weights) — implemented, 242 passed; in review.
- R28 Linux run: running (logs experiments/operator/task9/linux_run_PROXY_D*.txt).

## Status 2026-10-27 ~12:00
- Committed: Task 10 (94f29f4), R28 Linux (7dc93ae), F2-net (a8385e5), Phase 3 (cf4f55f), F2-behaviours (f557c2c),
  F2-metrics (8acc85c), R28 frozen on F2 net lane 4 / junction 142 (cfd86ba), Task 11 (d24a13b), Task 12 (481ea06),
  Task 14 code (ccb7520).
- Rulings since: R35–R44 (see docs/PROGRESS.md). R44: each spec = 3 runs (D1–D3, seed 1); budget 36 per method.
- Running: campaign B2 detached (nohup, `pgrep -af optuna_search`), log experiments/campaigns/B2_run.log; resumable:
  rerun the same command (docs/PROGRESS.md Task 14 entry) if it died. experiments/campaigns/B2_aborted = first attempt
  killed after 3 charged runs (do not use, do not commit).
- In progress: Task 13 loop code (agent). Then: review → commit → campaigns P1 (params_only, base B1) and P2 (full)
  with Sonnet stand-in answering `python -m thesis_sumo.llm.loop pending --campaign X` requests → H = Optuna on P2_best
  structure → Task 15 benchmark (B0, B1, B2, P1, P2, H on D4–D5, ≥ 20 seeds, allow_validation) → LaTeX → video.

## Campaign procedure (2026-10-27 ~12:40) — Task 13 committed 81a9362
Running detached (setsid nohup): B2 (Optuna, log experiments/campaigns/B2_run.log), P1 (llm.loop params_only base
B1, nproc 9, log P1_run.log), P2 (llm.loop full, nproc 3, log P2_run.log). Check: `pgrep -af "llm.loop|optuna_search"`,
`cat experiments/campaigns/<c>/budget.json`, `tail experiments/campaigns/<c>_run.log`.
When a loop process has exited: if its log ends with "LLM response(s) pending" (exit 3) → for EACH listed request
spawn one background Agent (model sonnet) with the stand-in prompt: read ONLY that request file, reply with ONE JSON
object valid against its `schema` (fix listed validator issues on retries), write {"content": spec, "reasoning": "..."}
to the response path, touch nothing else. When all are answered, rerun the same loop command (same flags) detached:
  P1: .venv/bin/python -m thesis_sumo.llm.loop --campaign P1 --mode params_only --base rules/specs/B1_manual.json --budget 36 --site config/site.proxy.yaml --b0-lane-collisions 1.333 --nproc 9
  P2: .venv/bin/python -m thesis_sumo.llm.loop --campaign P2 --mode full --budget 36 --site config/site.proxy.yaml --b0-lane-collisions 1.333 --nproc 3
If finished (budget/max_iter): rerun once with `--write-best rules/specs/P1_best.json` (P2_best) — no new runs.
B2 finished → B2_best.json written by its CLI. Then H = optuna_search --structure rules/specs/P2_best.json --campaign H.
iteration 1 validity: P1 4/4 valid first attempt; P2 1/4 first attempt (3 × lcPushy+lcPushyGap logic error), retried.

## Status 2026-10-27 ~17:00 — PAUSED by Viktor
- P1/P2 loops (iteration 3 running) suspended with SIGSTOP on their process groups (not killed); supervisor stopped;
  hourly reminder disabled (enabled=false). Resume: `kill -CONT -<pgid>` for both loops (pgrep -af llm.loop), rerun
  supervise_llm.sh in background, re-enable the scheduled task. If the machine rebooted: rerun the loop commands above.
- Interim: REF campaign (B0, B1 scored like a spec), LaTeX interim update (agent), demo video + report
  report/2026-10-27/ (record/encode scripts ported to Linux, B2_best).
