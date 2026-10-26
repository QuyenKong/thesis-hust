#!/usr/bin/env python3
"""
Runtime rule enforcement via TraCI.

Applies dynamic rules during simulation: speed limits, lane changes, etc.
Runs simulation with traci while enforcing rules from compiled rule files.

Usage:
    python dynamic_rules.py configs/rules_v001.sumocfg outputs/rules_v001/seed_01 42
"""

import sys
import os
from pathlib import Path

# Add SUMO tools to path if needed
if "SUMO_HOME" in os.environ:
    sys.path.append(os.path.join(os.environ["SUMO_HOME"], "tools"))

import traci
import traci.constants as tc


def apply_rules(traci_rules, vehicles):
    """
    Apply dynamic rules to all vehicles at this timestep.

    Args:
        traci_rules: List of rule dicts with 'condition' and 'action' fields
        vehicles: List of vehicle IDs in simulation
    """
    for vehicle_id in vehicles:
        try:
            speed = traci.vehicle.getSpeed(vehicle_id)
            # Add other accessible vehicle state as needed

            for rule in traci_rules:
                # Evaluate rule condition
                if eval(rule["condition"]):
                    # Execute rule action
                    eval(rule["action"])
        except traci.TraCIException:
            # Vehicle left simulation
            pass


def run_simulation_with_rules(config_file, output_dir, seed, traci_rules):
    """
    Run SUMO simulation with TraCI rule enforcement.

    Args:
        config_file: Path to SUMO .sumocfg
        output_dir: Output directory
        seed: Random seed
        traci_rules: List of rule definitions
    """
    sumo_cmd = [
        "sumo",
        "-c", str(config_file),
        "--seed", str(seed),
        "--output-prefix", str(output_dir),
    ]

    traci.start(sumo_cmd)

    step = 0
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()

        # Apply rules every step
        vehicles = traci.vehicle.getIDList()
        apply_rules(traci_rules, vehicles)

        step += 1
        if step % 100 == 0:
            print(f"  Step {step}: {len(vehicles)} vehicles")

    traci.close()
    print(f"✓ Simulation complete: {step} steps, {len(vehicles)} final vehicles")


def main():
    if len(sys.argv) < 4:
        print("Usage: dynamic_rules.py <config.sumocfg> <output_dir> <seed>")
        sys.exit(1)

    config_file = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    seed = int(sys.argv[3])

    output_dir.mkdir(parents=True, exist_ok=True)

    # TODO: Load compiled TraCI rules from rules/compiled/
    traci_rules = []

    print(f"Running: {config_file}")
    run_simulation_with_rules(config_file, output_dir, seed, traci_rules)


if __name__ == "__main__":
    main()
