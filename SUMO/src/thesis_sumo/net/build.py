"""One command for the whole network (PLAN Phase 1):

    .venv/Scripts/python -m thesis_sumo.net.build --site config/site.proxy.yaml

writes into `scenario/net/` (or `--out-dir`): `base.net.xml`, `removed_nodes.csv`, `edge_table.csv`,
`patches/base/*`, `patches/<site net stem>/*`, `site.proxy.net.xml` (proxy) or `site.net.xml`
(measured), `stopline_shift.csv` (stop line to junction centre, site net without / with the sidewalk), `diagram.svg`,
`<site net stem>.gui.add.xml` (sumo-gui only: continuous right-turn lanes drawn in yellow), and netconvert logs in `logs/`. A required null in the site file stops the
build before anything is written.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
import warnings
from pathlib import Path

import pandas as pd
import sumolib

from thesis_sumo.config import MissingFieldDataError, Site, load_site
from thesis_sumo.net.apply_patches import (
    ProxySiteWarning,
    build_site_net,
    gui_highlight_name,
    site_net_name,
    site_values,
    write_gui_highlight,
)
from thesis_sumo.net.build_net import NET_DIR, approach_edges, build_base, edge_table, exit_edges
from thesis_sumo.net.diagram import draw_diagram

BANNER = "#" * 100


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):  # street names are Vietnamese; never crash on a cp1252 console
        stream.reconfigure(errors="replace")
    ap = argparse.ArgumentParser(prog="python -m thesis_sumo.net.build", description=__doc__.split("\n\n")[0])
    ap.add_argument("--site", type=Path, default=None, help="site file (default: config/site.yaml)")
    ap.add_argument("--out-dir", type=Path, default=NET_DIR)
    args = ap.parse_args(argv)

    site = load_site(args.site)
    try:
        site_values(site)  # fail fast on a required null, before any file is written
    except MissingFieldDataError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if site.source == "LITERATURE_PROXY":
        print(f"{BANNER}\n# WARNING: site_source LITERATURE_PROXY ({site.path})\n# Lane widths, turn bans "
              f"and signal plan are literature/assumed values, NOT field measurements.\n{BANNER}", file=sys.stderr)

    out_dir = args.out_dir
    base = build_base(site, out_dir / "base.net.xml")
    removed = (out_dir / "removed_nodes.csv").read_text(encoding="utf-8")
    print(f"Nodes removed from the arms ({out_dir / 'removed_nodes.csv'}):\n{removed}")

    table = edge_table(base)
    table.to_csv(out_dir / "edge_table.csv", index=False, lineterminator="\n")
    print(f"Edge table ({out_dir / 'edge_table.csv'}):\n{table.to_string(index=False)}\n")

    base_net = sumolib.net.readNet(str(base))
    for key, derive in (("approaches", approach_edges), ("exits", exit_edges)):
        listed = {a["id"]: a["edge"] for a in site[key]}
        derived = derive(base_net)
        print(f"{key} mapping (site file / derived from geometry):")
        for item_id, edge in listed.items():
            print(f"  {item_id:9s} {edge:16s} {derived.get(item_id)}")
        if listed != derived:
            print(f"ERROR: {key}[].edge in {site.path} differ from the geometry: {derived}", file=sys.stderr)
            return 3
    mapping = {a["id"]: a["edge"] for a in site["approaches"]}

    with warnings.catch_warnings():  # the banner above already said it, loudly
        warnings.simplefilter("ignore", ProxySiteWarning)
        net = build_site_net(site, base, out_dir / site_net_name(site))
    # the sidewalk edge reshapes the junction: log how far each stop line moved from the centre against the same site
    # net without sidewalk (the bollard splits leave the junction as it is)
    from thesis_sumo.sim.outputs import junction_geometry  # (outputs imports this package)
    with tempfile.TemporaryDirectory() as tmp, warnings.catch_warnings():
        warnings.simplefilter("ignore", ProxySiteWarning)
        plain = build_site_net(Site({**site, "f2_measured_approaches": None}, site.path), base, Path(tmp) / "n.net.xml")
        before = junction_geometry(plain).stopline_from_centre
    after = junction_geometry(net).stopline_from_centre
    shift = pd.DataFrame([{"approach": a, "no_sidewalk_m": round(before[a], 2), "site_m": round(after[a], 2),
                           "shift_m": round(after[a] - before[a], 2)} for a in before])
    shift.to_csv(out_dir / "stopline_shift.csv", index=False, lineterminator="\n")
    print(f"Stop line distance from the junction centre, without / with the sidewalk ({out_dir / 'stopline_shift.csv'}):"
          f"\n{shift.to_string(index=False)}")
    draw_diagram(net, out_dir / "diagram.svg", {e: a for a, e in mapping.items()},
                 (site.require("violator_classes.moto"), site.require("violator_classes.car")),
                 title=f"{site['intersection']['name']} - {net.name} ({site.source})")
    gui = write_gui_highlight(site, net, out_dir / gui_highlight_name(site))
    print(f"Wrote {net}, {out_dir / 'diagram.svg'} and {gui} (sumo-gui: continuous right-turn lanes in yellow)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
