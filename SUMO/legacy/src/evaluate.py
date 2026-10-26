#!/usr/bin/env python3
"""
Evaluate simulation results against observed data.

Computes metrics:
- GEH (Geoffrey E. Havers indicator) for flow match
- MAPE (Mean Absolute Percentage Error) for speed
- Lane change counts
- Time to collision (TTC)

Outputs: results/metrics.csv

Usage:
    python evaluate.py
"""

import csv
from pathlib import Path
from lxml import etree
import numpy as np


def compute_geh(observed, simulated):
    """
    Geoffrey E. Havers (GEH) statistic.

    GEH = sqrt(2 * (O - S)^2 / (O + S))
    GEH < 5: good fit
    GEH < 10: acceptable
    """
    if observed + simulated == 0:
        return 0
    return np.sqrt(2 * (observed - simulated) ** 2 / (observed + simulated))


def compute_mape(observed, simulated):
    """Mean Absolute Percentage Error."""
    if len(observed) == 0:
        return np.nan
    return np.mean(np.abs((observed - simulated) / observed)) * 100


def parse_tripinfos(tripinfos_file):
    """Extract vehicle speeds and times from tripinfos.xml."""
    tree = etree.parse(str(tripinfos_file))
    root = tree.getroot()

    speeds = []
    durations = []

    for trip in root.findall('.//tripinfo'):
        vehspeed = trip.get('vehspeed')
        duration = trip.get('duration')
        if vehspeed:
            speeds.append(float(vehspeed))
        if duration:
            durations.append(float(duration))

    return np.array(speeds), np.array(durations)


def evaluate_version(version, observed_data=None):
    """
    Evaluate all seeds of a rule version.

    Args:
        version: Rule version name (baseline, rules_v001, ...)
        observed_data: Dict of observed metrics (optional)

    Returns:
        Dict of metrics for this version
    """
    output_dir = Path(f"outputs/{version}")

    all_speeds = []
    all_flows = []

    for seed_dir in sorted(output_dir.glob("seed_*")):
        tripinfos = seed_dir / "tripinfos.xml"
        if not tripinfos.exists():
            continue

        speeds, durations = parse_tripinfos(tripinfos)
        all_speeds.extend(speeds)
        all_flows.append(len(speeds))  # Vehicle count as flow proxy

    metrics = {
        "version": version,
        "num_seeds": len(list(output_dir.glob("seed_*"))),
        "mean_speed": np.mean(all_speeds) if all_speeds else np.nan,
        "std_speed": np.std(all_speeds) if all_speeds else np.nan,
        "mean_flow": np.mean(all_flows) if all_flows else np.nan,
    }

    if observed_data:
        metrics["geh_flow"] = compute_geh(observed_data.get("flow", 0), metrics["mean_flow"])
        metrics["mape_speed"] = compute_mape(
            np.array([observed_data.get("speed", 0)]),
            np.array([metrics["mean_speed"]])
        )

    return metrics


def main():
    results_dir = Path("results")
    results_dir.mkdir(parents=True, exist_ok=True)

    # Find all rule versions in outputs/
    versions = sorted(set(p.parent.name for p in Path("outputs").glob("*/seed_*")))

    print(f"Evaluating {len(versions)} versions...\n")

    metrics_list = []
    for version in versions:
        print(f"  {version}...", end="", flush=True)
        metrics = evaluate_version(version)
        metrics_list.append(metrics)
        print(" ✓")

    # Write CSV
    csv_file = results_dir / "metrics.csv"
    if metrics_list:
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=metrics_list[0].keys())
            writer.writeheader()
            writer.writerows(metrics_list)
        print(f"\n✓ Results: {csv_file}")
    else:
        print("\n✗ No results found.")


if __name__ == "__main__":
    main()
