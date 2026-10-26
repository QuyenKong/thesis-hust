#!/usr/bin/env python3
"""
Compile rules JSON → SUMO ADD files and TraCI initialization code.

Reads rules/generated/*.json and produces:
- rules/compiled/*.add.xml (vehicle type definitions)
- Python code for dynamic_rules.py

Usage:
    python rule_compiler.py [rule_json_file]
    python rule_compiler.py rules/generated/rules_v001.json
"""

import json
import sys
from pathlib import Path
from lxml import etree


def load_rule_schema(rule_file):
    """Load and validate rule JSON."""
    with open(rule_file) as f:
        return json.load(f)


def compile_vehicle_types(rules, output_add_file):
    """
    Compile vehicle type definitions to SUMO ADD XML.

    Args:
        rules: Parsed rule schema dict
        output_add_file: Path to output .add.xml
    """
    root = etree.Element("additional")

    for vtype in rules.get("vehicle_types", []):
        vtype_elem = etree.SubElement(root, "vType", id=vtype["id"], vClass=vtype["vClass"])

        # Copy attributes
        for key in ["length", "width", "maxSpeed", "accel", "decel", "sigma", "tau", "minGap"]:
            if key in vtype:
                vtype_elem.set(key, str(vtype[key]))

        # Lane change parameters
        if "laneChangeParams" in vtype:
            for param, value in vtype["laneChangeParams"].items():
                vtype_elem.set(param, str(value))

    tree = etree.ElementTree(root)
    tree.write(output_add_file, pretty_print=True, xml_declaration=True, encoding='UTF-8')
    print(f"✓ Compiled: {output_add_file}")


def compile_traci_rules(rules, output_py_file):
    """
    Generate TraCI rule code from rule schema.

    Args:
        rules: Parsed rule schema dict
        output_py_file: Path to output Python file (for dynamic_rules.py to import)
    """
    traci_rules = rules.get("traci_rules", [])

    code_lines = [
        "# Auto-generated TraCI rules",
        "# DO NOT EDIT - regenerate with rule_compiler.py",
        "",
        "TRACI_RULES = [",
    ]

    for rule in traci_rules:
        code_lines.append(f"    {{")
        code_lines.append(f"        'name': {repr(rule['name'])},")
        code_lines.append(f"        'condition': {repr(rule['condition'])},")
        code_lines.append(f"        'action': {repr(rule['action'])},")
        code_lines.append(f"    }},")

    code_lines.append("]")

    with open(output_py_file, 'w') as f:
        f.write('\n'.join(code_lines))

    print(f"✓ Generated: {output_py_file}")


def main():
    if len(sys.argv) > 1:
        rule_file = Path(sys.argv[1])
    else:
        # Find latest rule file
        rule_dir = Path("rules/generated")
        rule_files = sorted(rule_dir.glob("rules_*.json"))
        if not rule_files:
            print("Error: No rule files found in rules/generated/")
            sys.exit(1)
        rule_file = rule_files[-1]

    if not rule_file.exists():
        print(f"Error: {rule_file} not found.")
        sys.exit(1)

    print(f"Compiling: {rule_file}")
    rules = load_rule_schema(rule_file)

    version = rules.get("version", "unknown")

    # Compile to ADD file
    add_file = Path(f"rules/compiled/{version}.add.xml")
    add_file.parent.mkdir(parents=True, exist_ok=True)
    compile_vehicle_types(rules, add_file)

    # Generate TraCI rules
    traci_file = Path(f"rules/compiled/{version}_traci_rules.py")
    compile_traci_rules(rules, traci_file)

    print(f"\n✓ Rule compilation complete.")


if __name__ == "__main__":
    main()
