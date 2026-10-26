# SUMO Thesis - Traffic Simulation with Dynamic Rules

This project investigates traffic flow dynamics and vehicle interactions using SUMO (Simulation of Urban MObility) with dynamic rule generation and validation.

## Project Structure

```
thesis-sumo/
├── scenario_raw/          # Original OpenWebWizard exports (read-only)
├── scenario/              # Processed network & demand files
│   ├── net/              # Network topology
│   └── demand/           # Vehicle trips (processed)
├── rules/                # Rule definitions & compilation
│   ├── schema/           # JSON schema for AI-generated rules
│   ├── generated/        # AI-generated rules (versioned)
│   └── compiled/         # Compiled to SUMO ADD files
├── configs/              # SUMO configuration files
├── src/                  # Python processing & simulation scripts
├── data/observed/        # Real-world observed data
├── outputs/              # Simulation results by version & seed
├── results/              # Analysis metrics & visualizations
├── requirements.txt
└── README.md
```

## Quick Start

### 1. Setup Environment
```bash
pip install -r requirements.txt
```

### 2. Prepare Scenario
```bash
python src/patch_demand.py
```

### 3. Generate Rules (optional)
```bash
python src/rule_compiler.py rules/generated/rules_v001.json
```

### 4. Run Simulation
```bash
python src/run_sim.py --version baseline --seeds 1 2 3
python src/run_sim.py --version rules_v001 --seeds 1 2 3 --traci
```

### 5. Evaluate Results
```bash
python src/evaluate.py
```

## Key Scripts

- **patch_demand.py** — Process OWZ trips, remove original vType, assign new types
- **rule_compiler.py** — Convert rule JSON → SUMO ADD files + TraCI initialization
- **dynamic_rules.py** — Runtime rule enforcement via TraCI
- **run_sim.py** — Execute simulations with multiple seeds
- **evaluate.py** — Compute GEH, MAPE, lane-change counts, TTC

## Data Flow

```
OpenWebWizard → scenario_raw/
                    ↓
            patch_demand.py
                    ↓
            scenario/demand/ + scenario/net/
                    ↓
            rule_compiler.py (if rules)
                    ↓
            configs/ + rules/compiled/
                    ↓
            run_sim.py (+ dynamic_rules.py via TraCI)
                    ↓
            outputs/{version}/seed_XX/
                    ↓
            evaluate.py
                    ↓
            results/metrics.csv + figures/
```

## Rule Versioning

Keep all generated rule versions:
- `rules/generated/rules_v001.json` — First generation
- `rules/generated/rules_v002.json` — Second iteration
- `outputs/` and `results/` track results per version

## Output Files

Each simulation run produces:
- `tripinfos.xml` — Per-vehicle trip details
- `stats.xml` — Aggregate statistics
- `edgeData.xml` — Per-road segment data
- Optional: `laneChangeEvents.xml`, `tripData.xml`

Parse these with `sumolib` or standard XML tools.

## References

- SUMO Documentation: https://sumo.dlr.de/
- TraCI Python API: https://sumo.dlr.de/docs/TraCI/Interfacing_TraCI_from_Python.html
