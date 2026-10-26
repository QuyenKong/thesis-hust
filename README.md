# thesis-sumo

LLM-generated driver-behaviour rules for SUMO: mixed car/motorcycle traffic at Le Van Luong x
Hoang Dao Thuy (Hanoi), AM peak. See `PLAN.md` for scope and phases, `CLAUDE.md` for working rules.

## Setup (Windows and Linux)

Needs Python ≥ 3.10 and Git LFS (`git lfs pull`: `scenario_raw/*.gz` and other binaries are LFS objects). Run
from `SUMO/`:

```bash
py -3.12 scripts/setup_env.py      # Windows: uses the installed SUMO 1.27 at %SUMO_HOME%
python3.12 scripts/setup_env.py    # Linux: no SUMO_HOME -> installs the eclipse-sumo 1.27.0 wheel into .venv
.venv/Scripts/python -m pytest     # Windows
.venv/bin/python -m pytest         # Linux
```

The script creates `.venv` (with `uv` when available), installs the project with all extras and
`libsumo`/`sumo-data` 1.27.0 with `--no-deps` (their deps would pull traci/sumolib 1.28 from PyPI), and writes
`sumo_tools.pth` so traci/sumolib come from `<SUMO_HOME>/tools` and `SUMO_HOME` is set inside the venv. The operator
shell scripts (`experiments/operator/*/*.sh`) source `experiments/operator/env.sh` and run on both (Git Bash on
Windows). Each run's `manifest.json` and `collisions.xml` and the SDD ledger (`.superpowers/sdd/`) are tracked in git
so either machine can pick up the work; the rest of `experiments/runs/` is not.

## Status

- [x] Phase 0 — environment and repo skeleton
- [ ] Phase 1 — network
- [ ] Phase 2 — baseline B0
- [ ] Phase 3 — in-box waiting feasibility (stop: choose a/b)
- [ ] Phase 4 — rule spec, validator, compiler, TraCI runtime
- [ ] Phase 5 — metrics and distance
- [ ] Phase 6 — LLM loop
- [ ] Phase 7 — Optuna baseline and benchmark
