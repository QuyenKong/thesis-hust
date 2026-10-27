# CLAUDE.md

Thesis project: a local LLM generates and iteratively refines driver-behaviour rules (vType params +
TraCI conditional rules) for SUMO, to make a micro-simulation of mixed car/motorcycle traffic at
**Le Van Luong x Hoang Dao Thuy** (Thanh Xuan, Hanoi), AM peak 07:30–09:00, more realistic.
The scenario covers all 11 behaviours in PLAN §0; illegal left turns that wait inside the junction box
are one of them, not a separate focus. Goal: reproduce road-user behaviour at the junction as closely as possible.

`PLAN.md` is the source of truth (scope, decisions, phases). Work phase by phase; after each phase
report what was done, commands to reproduce, criteria met/unmet, assumptions, remaining `TODO_MEASURE`,
and wait for confirmation. Phase 3 and the end of Phase 5 are hard stops.

## Writing documents

Before any action that writes or edits prose (reports, LaTeX chapters, README, notes, long commit/PR
text), load the `writing-docs-viktor` skill and follow it strictly. It does not apply to code or prompts.
Run its checklist before delivering the text.

## Rules (PLAN §1)

- **Never invent field data.** Measured values (lane widths, signal cycle/phases, turn bans, flows) come
  only from `config/site.yaml`. Unknown → `null  # TODO_MEASURE`. Code raises a clear error on a required
  `null`; never fill a default. Design choices still open are `null  # TODO_DECIDE`.
- **Never guess SUMO names.** Check every vType attribute / sumo / netconvert option with `--help` or
  sumo.dlr.de/docs before use. Every row of `rules/bounds/param_bounds.yaml` cites its source URL.
- **`scenario_raw/` is immutable.** The OWZ export lives in `scenario_raw/2026-10-02-06-34-26/`.
- **Reproducible:** network = script + plain-XML patches (never hand-edit `.net.xml`), fixed seeds,
  every run writes `manifest.json`.
- Windows: use `pathlib`, no hardcoded `\`; readers accept `.xml` and `.xml.gz`.
- Python ≥ 3.10 in `.venv`. `pytest` tests for validator, compiler and metrics on small synthetic data.
- Unsure how SUMO behaves → write a small experiment to check; don't assume.
- Out of scope: wrong-way driving, sidewalk riding, illegal parking, route choice (`U_route`),
  pedestrians/buses/trucks. The LLM never generates or edits the network.
- `legacy/` holds the pre-PLAN skeleton for reference only; don't build on it.

## Environment

- Two machines, same SUMO 1.27.0: Windows (installed at `C:\Program Files (x86)\Eclipse\Sumo`, `SUMO_HOME` set)
  and Linux (`eclipse-sumo==1.27.0` wheel inside `.venv`, no system SUMO). `scripts/setup_env.py` builds `.venv` on
  either; venv python is `.venv/Scripts/python` (Windows) or `.venv/bin/python` (Linux).
- `traci`/`sumolib` come from `<SUMO_HOME>/tools` via `sumo_tools.pth` in the venv site-packages (not from PyPI)
  so they match the binary; the same `.pth` sets `SUMO_HOME` inside the venv when it is not set.
- Large files are Git LFS (`git lfs pull` after cloning). Run records (`experiments/runs/**/manifest.json`,
  `collisions.xml`) and the SDD ledger (`.superpowers/sdd/`) are tracked; other raw output is not.
- Linux has no Ollama yet: the LLM loop's stand-in is a Claude Sonnet subagent; specs it writes carry
  `provenance.model` "claude-sonnet (stand-in)" and are not results of the local-LLM method.
- `libsumo` 1.27.0 + `sumo-data` 1.27.0 (its DLLs) are pip-installed with `--no-deps`: their declared
  deps pull traci/sumolib 1.28 from PyPI, which would shadow the SUMO_HOME copies. Never `pip install
  libsumo` without `--no-deps`. `tests/test_backends.py` checks libsumo and traci give identical runs.
  libsumo cannot drive sumo-gui; use the `traci` backend for GUI debugging.

## Commands

```bash
git lfs pull                                 # after cloning: scenario_raw/*.gz etc. are LFS objects
py -3.12 scripts/setup_env.py                # Windows, from SUMO/ (Linux: python3.12 scripts/setup_env.py)
.venv/Scripts/python -m pytest               # Linux: .venv/bin/python -m pytest
bash experiments/operator/task9/run_b0.sh    # operator scripts run as-is on both (Git Bash on Windows)
```

## Layout

- `config/` — `site.yaml` (field data), `experiment.yaml` (seeds, step-length, budget, split), `llm.yaml`
- `scenario/net/` — `base.net.xml` (from OSM by script), `patches/`, `site.net.xml`
- `scenario/demand/` — candidate routes, routeSampler output per day
- `data/observed/<day>/` — CSVs in the Phase 5.1 schema (`SYNTHETIC/` = pipeline test only, never in results)
- `rules/` — `schema/`, `bounds/`, `specs/<spec_id>.json`, `compiled/<spec_id>/`
- `src/thesis_sumo/` — `net`, `demand`, `rules`, `runtime`, `sim`, `metrics`, `llm`, `baselines`
- `experiments/runs/<run_id>/seed_XX/` — raw SUMO output (git-ignored)
- `results/` — `metrics.csv`, `figures/`
