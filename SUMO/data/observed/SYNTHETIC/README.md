# SYNTHETIC — pipeline test data only

**These counts are made up.** They are not field observations and not literature values. They exist only
to run the pipeline end to end (PLAN Phase 2.2) before real or proxy counts exist. Never use them in
results, calibration or validation; results come from `data/observed/<day>/` with measured data, or from
the labelled `PROXY_D*` days.

`turn_counts.csv` follows the PLAN 5.1 schema
`interval_start, interval_end, approach, movement, vclass, count`:

- `interval_start` / `interval_end`: simulation seconds, 15-min intervals (0–3600 s).
- `approach`: logical approach ids of the site file (`LVL_W`, `LVL_E`, `HDT_N`, `HDT_S`).
- `movement`: `s`, `r`, `l`, `u`, `illegal_l` (`illegal_l` = motorcycle left turn on the banned LVL_W
  approach; it becomes vehicle type `moto_violator`). LVL_W has no legal `l` (banned in the proxy site).
- `vclass`: `car`, `moto`.

Recipe (arbitrary round numbers, chosen so the 3-lane arms are loaded but not gridlocked over 3600 s,
motorcycle-dominated):

| approach | veh/h (all) | moto share |
|---|---|---|
| LVL_W | 1600 | 0.80 |
| LVL_E | 1200 | 0.80 |
| HDT_N | 800 | 0.85 |
| HDT_S | 700 | 0.85 |

- Movement split: s 0.70, r 0.15, l 0.10, u 0.05; on LVL_W moto s 0.72, r 0.15, illegal_l 0.08,
  u 0.05 and car s 0.80, r 0.15, u 0.05.
- 15-min profile factors 0.90, 1.05, 1.10, 0.95.
- `count = round(veh_per_h * class_share * movement_share * profile / 4)`.

Routes: `.venv/Scripts/python -m thesis_sumo.demand.build_demand --net scenario/net/site.proxy.net.xml
--counts data/observed/SYNTHETIC/turn_counts.csv --seed 1` → `scenario/demand/routes_SYNTHETIC.rou.xml`.
