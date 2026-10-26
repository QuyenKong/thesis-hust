#!/usr/bin/env python3
"""
Patch demand files from OpenWebWizard.

Process raw OWZ trip files:
1. Remove original vType references
2. Assign processed vehicle types (car, moto)
3. Save to scenario/demand/

Usage:
    python patch_demand.py
"""

import sys
from pathlib import Path
from lxml import etree


def patch_trips(input_file, output_file, type_mapping):
    """
    Patch trip definitions: replace vType with new mappings.

    Args:
        input_file: Source trips XML
        type_mapping: dict of old_vtype -> new_vtype
        output_file: Output trips XML
    """
    parser = etree.XMLParser(remove_blank_text=False)
    tree = etree.parse(str(input_file), parser)
    root = tree.getroot()

    for trip in root.findall('.//trip'):
        old_type = trip.get('type')
        if old_type in type_mapping:
            trip.set('type', type_mapping[old_type])

    with open(output_file, 'wb') as f:
        tree.write(f, pretty_print=True, xml_declaration=True, encoding='UTF-8')

    print(f"✓ Patched: {output_file}")


def main():
    # Adjust paths as needed
    scenario_raw = Path("scenario_raw")
    scenario_demand = Path("scenario/demand")

    if not scenario_raw.exists():
        print("Error: scenario_raw/ not found. Run from project root.")
        sys.exit(1)

    scenario_demand.mkdir(parents=True, exist_ok=True)

    # Find OWZ output directories
    for raw_dir in sorted(scenario_raw.glob("20*")):
        if not raw_dir.is_dir():
            continue

        print(f"\nProcessing: {raw_dir.name}")

        # Patch motorcycle trips
        moto_trips = raw_dir / "osm.motorcycle.trips.xml"
        if moto_trips.exists():
            patch_trips(
                moto_trips,
                scenario_demand / "moto.trips.xml",
                {"motorcycle": "moto"}
            )

        # Patch passenger trips
        car_trips = raw_dir / "osm.passenger.trips.xml"
        if car_trips.exists():
            patch_trips(
                car_trips,
                scenario_demand / "car.trips.xml",
                {"veh": "car"}
            )

    print("\n✓ Demand patching complete.")


if __name__ == "__main__":
    main()
