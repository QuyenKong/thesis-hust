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
