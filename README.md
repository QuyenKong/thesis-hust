# thesis-sumo

LLM-generated driver-behaviour rules for SUMO: mixed car/motorcycle traffic at Le Van Luong x
Hoang Dao Thuy (Hanoi), AM peak. See `PLAN.md` for scope and phases, `CLAUDE.md` for working rules.

## Setup (Windows)

Requires SUMO 1.27.x with `SUMO_HOME` set, and Python ≥ 3.10.

```bash
py -3.12 -m venv .venv
# make traci/sumolib from SUMO_HOME importable inside the venv (matches the SUMO binary)
.venv/Scripts/python -c "import os,sysconfig,pathlib; pathlib.Path(sysconfig.get_paths()['purelib'],'sumo_tools.pth').write_text(os.path.join(os.environ['SUMO_HOME'],'tools')+'\n')"
.venv/Scripts/python -m pip install -e ".[dev]"
# libsumo (fast in-process backend). --no-deps is required: its deps would pull traci/sumolib 1.28
# from PyPI and shadow the SUMO_HOME 1.27 copies. sumo-data supplies the DLLs libsumo links against.
.venv/Scripts/python -m pip install --no-deps libsumo==1.27.0 sumo-data==1.27.0
.venv/Scripts/python -m pytest
```

Optional extras: `.[llm]` (Phase 6), `.[optuna]` (Phase 7).

## Status

- [x] Phase 0 — environment and repo skeleton
- [ ] Phase 1 — network
- [ ] Phase 2 — baseline B0
- [ ] Phase 3 — in-box waiting feasibility (stop: choose a/b)
- [ ] Phase 4 — rule spec, validator, compiler, TraCI runtime
- [ ] Phase 5 — metrics and distance
- [ ] Phase 6 — LLM loop
- [ ] Phase 7 — Optuna baseline and benchmark
