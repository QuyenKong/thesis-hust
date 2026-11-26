"""Observed days VIDEO_V2 (calibration) and VIDEO_V1 (validation) from the video targets (decisions D17-D19).

    .venv/Scripts/python video/make_video_days.py

Generates data/observed/VIDEO_V*/ with thesis_sumo.proxy.generate on config/site.yaml (measured site, cycle 160 s)
and data/video_targets/targets_video.yaml, then the routes scenario/demand/routes_VIDEO_V*.rou.xml on site.net.xml
(candidates scenario/demand/candidate_routes_site.rou.xml)."""
from pathlib import Path

from thesis_sumo.config import REPO_ROOT, load_site
from thesis_sumo.demand.build_demand import DEMAND_DIR, build_candidate_routes, build_demand
from thesis_sumo.proxy.generate import OBSERVED_ROOT, campaign_day_factors, generate_day, load_targets

DAYS = {"VIDEO_V2": 201, "VIDEO_V1": 202}

if __name__ == "__main__":
    site = load_site(REPO_ROOT / "config" / "site.yaml")
    targets = load_targets(REPO_ROOT / "data" / "video_targets" / "targets_video.yaml")
    factors = campaign_day_factors(targets, DAYS)
    cands = build_candidate_routes(REPO_ROOT / "scenario" / "net" / "site.net.xml",
                                   DEMAND_DIR / "candidate_routes_site.rou.xml")
    for day, seed in DAYS.items():
        out = OBSERVED_ROOT / day
        generate_day(targets, site, day, seed, out, day_factors=factors[day])
        routes = build_demand(out / "turn_counts.csv", cands, DEMAND_DIR / f"routes_{day}.rou.xml", seed)
        print(day, seed, out, routes)
