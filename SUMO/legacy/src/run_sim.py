#!/usr/bin/env python3
"""
Run SUMO simulations with optional TraCI dynamic rules.

Executes simulations with multiple random seeds and collects outputs.

Usage:
    python run_sim.py --version baseline --seeds 1 2 3
    python run_sim.py --version rules_v001 --seeds 1 2 3 --traci
"""

import subprocess
import sys
from pathlib import Path
import argparse


def run_simulation(config_file, output_dir, seed, use_traci=False):
    """
    Run one SUMO simulation instance.

    Args:
        config_file: Path to .sumocfg
        output_dir: Output directory for this seed
        seed: Random seed
        use_traci: If True, run with TraCI (dynamic rules)
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    if use_traci:
        # Run with TraCI via run_with_traci.py
        cmd = [
            sys.executable, "src/dynamic_rules.py",
            str(config_file),
            str(output_dir),
            str(seed),
        ]
    else:
        # Standard SUMO headless run
        cmd = [
            "sumo",
            "-c", str(config_file),
            "--seed", str(seed),
            "--output-prefix", str(output_dir / f"seed_{seed:02d}_"),
        ]

    print(f"  Running seed {seed:02d}...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"    Error: {result.stderr}")
        return False

    print(f"  ✓ Seed {seed:02d} complete")
    return True


def main():
    parser = argparse.ArgumentParser(description="Run SUMO simulations")
    parser.add_argument("--version", required=True, help="Rule version (baseline, rules_v001, ...)")
    parser.add_argument("--seeds", type=int, nargs="+", required=True, help="Random seeds")
    parser.add_argument("--traci", action="store_true", help="Use TraCI dynamic rules")

    args = parser.parse_args()

    # Locate config file
    config_file = Path(f"configs/{args.version}.sumocfg")
    if not config_file.exists():
        print(f"Error: {config_file} not found.")
        sys.exit(1)

    print(f"Configuration: {config_file}")
    print(f"Version: {args.version}")
    print(f"Seeds: {args.seeds}")
    print(f"TraCI: {args.traci}\n")

    output_base = Path(f"outputs/{args.version}")

    for seed in args.seeds:
        output_dir = output_base / f"seed_{seed:02d}"
        success = run_simulation(config_file, output_dir, seed, use_traci=args.traci)

        if not success:
            print(f"Warning: Seed {seed:02d} failed.")

    print(f"\n✓ Simulation run complete.")


if __name__ == "__main__":
    main()
