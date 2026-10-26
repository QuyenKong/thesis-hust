# Phase 3: waiting in the junction box (native SUMO capacity)

> **Superseded by R21 (exit lanes 3.5 m); re-check by operator pending.** The measurements below were made on the 3.2 m box lanes.

**Question (PLAN Phase 3).** How many motorcycles can SUMO 1.27.0 (sublane model, SL2015) hold waiting at the
internal junction of the illegal left turn? On the proxy net this is the left turn of LVL_W (TLS link 16).

**Decision: (a) `native`.**
- Measured native capacity: **8** halting `moto_violator` with the B0 vTypes. This is at least the M7 target
  mean of **6**.
- The target **p90 of 10** is not reached with B0 values. It is reached by lowering the `custom1` archetype's
  `minGap`. Measured: minGap 1.8 m gives 10, minGap 1.0 m gives 12.
- Early leaving through gaps depends on the opposing flow. Measured: none under dense opposing flow; 62 % of box
  entrants at a flow near the proxy days' LVL_E through. The M7 target is 20 %.
- The decision is written to `config/site.proxy.yaml` as `illegal_left.mode: native` (`mode_evidence: experiment`).
  `config/site.yaml` keeps `mode: null # TODO_DECIDE`.
- The PLAN stop at this point was waived for the proxy run (global constraints, exception 2). The decision is
  recorded here, not asked.

All numbers below come from LITERATURE_PROXY inputs (the proxy net and the proxy signal plan) and a synthetic
test demand. They describe SUMO's behaviour on this geometry, not field data.

## Setup

- **Network.** `scenario/net/site.proxy.net.xml` (built by `python -m thesis_sumo.net.build --site
  config/site.proxy.yaml`, unchanged by this task).
  - The illegal left `711526326#1_2 -> 408823207#0_2` allows `custom1` only. It is green (`g`) in the LVL
    phase, together with the opposing LVL_E through (`G`).
  - Its internal-lane chain is `:…_16_0` (18.89 m, width 3.2 m). That lane ends at the internal junction
    `:…_28_0`, the waiting point. After it comes `:…_28_0` (17.58 m).
  - These are the "box lanes" of `thesis_sumo.sim.outputs.junction_geometry`.
- **Signal.** Proxy plan, 120 s cycle: LVL green 64 s, yellow 4 s, all-red 2 s; HDT green 44 s, yellow 4 s,
  all-red 2 s.
- **Demand.** `experiments/phase3/box_capacity.py`, one route file per seed. Arrivals are Poisson, with the rng
  seeded by (scenario, seed). Vehicles use `departLane="best"` and `departSpeed="max"`.
  - Opposing LVL_E through, per scenario:
    - dense: 4000 moto/h + 700 car/h, so no gap is left during the green;
    - moderate: 1300 moto/h + 200 car/h, close to the LVL_E through volume of the generated proxy days
      (PROXY_D1–D3 `turn_counts.csv`: 1204–1498 moto/h, 157–221 car/h).
  - Crossing HDT_N and HDT_S through: 1200 moto/h + 250 car/h each.
  - Illegal left (`moto_violator`), by scenario:
    - `sat`: 1500/h, about 50 per cycle. This saturates the box.
    - `target`: 225/h = 7.5 entrants per cycle, the M7 entrant mean.
    - `sat_tight`: 1500/h, with a `moto_violator` vType of `minGap` 1.0 m and `minGapLat` 0.3 m. Everything
      else is B0. This is a sensitivity case.
    - `sat_mg18`: 1500/h, `moto_violator` `minGap` 1.8 m. This checks the capacity of 10 predicted by the row
      formula below.
    - `target_modopp`: 225/h, as `target`, but against the moderate opposing flow. This shows early leaving
      through gaps.
  - The opposing flow is dense in every scenario except `target_modopp`.
- **Runs.** 5 scenarios x seeds 1–5 = 25 runs, 900 s each (7 opposing green ends per run).
  - The first 15 runs (`sat`, `target`, `sat_tight`) date from the initial round; `target_modopp` and
    `sat_mg18` were added in fix round 1.
  - New scenarios are appended to `SCENARIOS`, so the earlier scenarios' demand streams are unchanged.
  - `sat_mg18` seeds 1, 3 and 5 failed with "bad allocation" when 10 runs shared the machine with an operator
    campaign. They were re-run with 3 processes. Each run goes through
  `thesis_sumo.sim.runner.run`, which writes `manifest.json`, all SUMO outputs and the observed-schema tables
  (incl. `box_queue.csv`).
  - The vTypes are B0 (`rules/compiled/B0`), or a B0 copy with the scenario's overrides. SUMO itself was queried for the
    loaded `minGap` and `minGapLat` (`vehicletype.getMinGap` / `getMinGapLat`).
  - A TraCI observer, which never intervenes, logs every 0.1 s step:
    - each vehicle on the box lanes (pos, posLat, speed, waiting time);
    - the TLS state;
    - halting vehicles on LVL_W lane 2;
    - teleports and colliding vehicles.
- **Reproduce.**

  ```bash
  .venv/Scripts/python experiments/phase3/box_capacity.py --nproc 4 --tag native   # 25 runs
  .venv/Scripts/python experiments/phase3/box_capacity.py --tag native --reanalyse # tables/figures only
  ```

  Outputs:
  - per-seed summary: `experiments/phase3/results_native.csv`;
  - per-run data: `experiments/runs/phase3/native/<spec>__PHASE3_<scenario>/seed_XX/` (`cycles.csv`,
    `waiters.csv`, `box_steps.csv`, git-ignored);
  - figures: `docs/research/figures/phase3_box_*_native.png`.
- **Definitions.**
  - Halting = speed < 5 km/h (`HALT_SPEED_MPS`, as `box_queue`).
  - Opposing green end `t_e` = G -> y of the LVL_E through link.
  - Box exit = first step off the box lanes.
  - Abreast = another waiter whose front is within 2.2 m longitudinally and whose centre is ≥ 0.9 m away
    laterally.
  - "HDT_N lane 2 first crossing" = first stop-line crossing on `953158817#2_2` after the HDT green onset.
    It is the only crossing lane whose internal lane passes over the waiting point (centre line 0.03 m
    away); the script computes this from the geometry. On the other HDT lanes the first crossing is
    0.30–0.35 s after the onset in every run.

## Results per seed

| scenario | seed | max halting in box | mean waiting at opp. green end | abreast at max | lat. span (m) | early leavers / cycle | first exit (s) | last exit (s) | in box at HDT green | HDT_N lane 2 first crossing (s) | stuck > 1 cycle | non-coll. teleports | collisions (all) | backlog end |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sat | 1 | 8 | 7.71 | 8 | 1.89 | 0.43 | 4.74 | 8.50 | 4.57 | 0.82 | 0 | 0 | 13 | 165 |
| sat | 2 | 8 | 7.71 | 8 | 2.20 | 0.14 | 4.89 | 8.71 | 4.43 | 0.83 | 0 | 0 | 21 | 176 |
| sat | 3 | 8 | 7.71 | 8 | 1.85 | 0.43 | 4.99 | 8.69 | 5.14 | 1.02 | 0 | 0 | 16 | 191 |
| sat | 4 | 8 | 7.57 | 8 | 1.85 | 0.29 | 4.63 | 8.11 | 4.43 | 0.70 | 0 | 0 | 9 | 164 |
| sat | 5 | 8 | 7.43 | 8 | 1.85 | 0.29 | 4.26 | 7.80 | 3.71 | 0.39 | 0 | 0 | 13 | 195 |
| target | 1 | 8 | 6.57 | 8 | 1.89 | 0.14 | 4.00 | 7.11 | 3.00 | 0.48 | 0 | 0 | 10 | 0 |
| target | 2 | 8 | 6.00 | 8 | 1.89 | 0.00 | 4.94 | 8.60 | 3.29 | 1.12 | 0 | 0 | 17 | 0 |
| target | 3 | 8 | 6.14 | 8 | 2.17 | 0.29 | 4.64 | 8.29 | 3.14 | 0.63 | 0 | 0 | 24 | 0 |
| target | 4 | 8 | 4.57 | 8 | 1.80 | 0.00 | 5.11 | 7.91 | 2.71 | 0.94 | 0 | 0 | 17 | 0 |
| target | 5 | 8 | 6.43 | 8 | 2.23 | 0.00 | 4.60 | 7.93 | 3.43 | 0.57 | 0 | 0 | 23 | 0 |
| sat_tight | 1 | 12 | 11.43 | 12 | 2.00 | 0.43 | 4.19 | 9.51 | 7.00 | 1.61 | 0 | 0 | 10 | 114 |
| sat_tight | 2 | 12 | 11.43 | 12 | 1.61 | 0.29 | 4.44 | 10.09 | 7.57 | 1.96 | 0 | 0 | 18 | 97 |
| sat_tight | 3 | 12 | 11.29 | 12 | 1.60 | 0.71 | 4.67 | 10.26 | 7.71 | 2.24 | 0 | 0 | 27 | 69 |
| sat_tight | 4 | 12 | 11.29 | 12 | 1.62 | 0.43 | 4.90 | 11.16 | 8.43 | 2.73 | 0 | 0 | 14 | 42 |
| sat_tight | 5 | 12 | 11.57 | 12 | 1.62 | 0.14 | 5.30 | 11.14 | 9.57 | 2.70 | 0 | 0 | 18 | 70 |
| target_modopp | 1 | 8 | 2.57 | 6 | 1.80 | 4.29 | 3.72 | 5.80 | 0.43 | 0.44 | 0 | 0 | 5 | 0 |
| target_modopp | 2 | 8 | 3.14 | 4 | 1.89 | 3.71 | 4.40 | 6.48 | 1.00 | 0.44 | 0 | 0 | 2 | 0 |
| target_modopp | 3 | 7 | 2.14 | 6 | 1.85 | 2.71 | 4.17 | 7.00 | 1.00 | 0.52 | 0 | 0 | 3 | 0 |
| target_modopp | 4 | 5 | 2.00 | 2 | 1.81 | 4.57 | 4.44 | 6.36 | 0.71 | 0.43 | 0 | 0 | 6 | 0 |
| target_modopp | 5 | 6 | 2.29 | 4 | 1.80 | 4.00 | 3.35 | 5.93 | 0.43 | 0.36 | 0 | 0 | 2 | 0 |
| sat_mg18 | 1 | 10 | 9.71 | 10 | 2.29 | 0.00 | 4.37 | 9.01 | 5.57 | 1.41 | 0 | 0 | 12 | 132 |
| sat_mg18 | 2 | 10 | 10.00 | 10 | 1.85 | 0.29 | 4.47 | 9.19 | 6.14 | 1.35 | 0 | 0 | 11 | 97 |
| sat_mg18 | 3 | 10 | 9.57 | 10 | 2.25 | 0.14 | 4.41 | 9.01 | 5.43 | 1.17 | 0 | 0 | 9 | 137 |
| sat_mg18 | 4 | 10 | 10.00 | 10 | 1.90 | 0.29 | 5.11 | 9.87 | 7.29 | 1.96 | 0 | 0 | 18 | 158 |
| sat_mg18 | 5 | 10 | 9.71 | 10 | 2.25 | 0.71 | 4.67 | 9.40 | 6.57 | 1.46 | 0 | 0 | 16 | 160 |

How to read the table:
- Columns are means over the 7 cycles of a run, except the max columns.
- Times are seconds after the opposing green end `t_e` (G -> y). Opposing red starts at `t_e + 4`; the HDT green
  starts at `t_e + 6`.
- "backlog end" = vehicles not yet inserted at 900 s. In the `sat*` scenarios these are violators queued back
  to the start of the 351 m LVL_W edge, the intended oversaturation.
- In `target_modopp` "max halting in box" is the largest number halting at any step of an opposing green.
  Most entrants leave early, so the box rarely holds that many at the green end.
- `box_queue.csv` from the observed-schema conversion gives the same mean and max `n_waiting_in_box` as the
  observer in every run (`schema_*` columns of the results file).

Pooled over cycles 1–6 of each run (cycle 0 is the warm-up green that starts at t = 0), 30 cycles per scenario:

| scenario | opposing (veh/h) | violator minGap (m) | mean waiting | p90 waiting | max | cycles at capacity | early leavers / cycle (share of entrants) | box exit headway (s) | first / last exit (s) | in box at HDT green |
|---|---|---|---|---|---|---|---|---|---|---|
| sat | 4700 | 2.5 | 8.00 | 8 | 8 | 100 % | 0 (0 %) | 0.52 | 4.67 / 8.28 | 4.6 |
| target | 4700 | 2.5 | 6.43 | 8 | 8 | 43 % (40 % with violators queued at the stop line) | 0 (0 %) | 0.68 | 4.71 / 8.19 | 3.4 |
| sat_tight | 4700 | 1.0 (minGapLat 0.3) | 12.00 | 12 | 12 | 100 % | 0 (0 %) | 0.51 | 4.72 / 10.36 | 8.5 |
| target_modopp | 1500 | 2.5 | 2.60 | 6 | 7 | 7 % (at 7) | 4.17 (62 %) | 0.88 | 4.01 / 6.59 | 0.8 |
| sat_mg18 | 4700 | 1.8 | 10.00 | 10 | 10 | 100 % | 0 (0 %) | 0.52 | 4.65 / 9.33 | 6.4 |

Early-leaver share = early leavers / (early leavers + waiters at the opposing green end), summed over cycles.

![Box occupancy](figures/phase3_box_occupancy_native.png)

![Waiter positions](figures/phase3_box_lateral_native.png)

## Findings

1. **Vehicles do wait at the internal junction.**
   - In every cycle of every run, the leading waiter halts with its front 0.10 m before the end of
     `:…_16_0`, the waiting point of internal junction `:…_28_0`.
   - All waiters stand on `:…_16_0`, between the stop line and the waiting point.
   - Once that lane is full, further violators stop at the LVL_W stop line on lane 2 (`upstream_halting_lane2`
     > 0 in every saturated cycle). SUMO lets a vehicle enter the junction only while the internal lane has
     room (Simulation/Intersections: no entry when "blocked by vehicles already on the intersection").
   - No option or network change was needed. `--junction-taz` (`sumo --help`: "Initialize a TAZ for every
     junction…") only concerns routing between junctions, so it is not relevant here.
2. **Capacity is geometric, and the sublane model packs two abreast.**
   - Waiters form two columns, at posLat ≈ −1.15 m and ≈ 0 to +0.65 m. At capacity, every waiter has a
     neighbour abreast, with a lateral spread of centres of 1.6–2.2 m inside the 3.2 m lane.
   - Rows = ⌊(18.79 + minGap) / (2.2 + minGap)⌋, where 18.79 m is the leader's front position. This
     predicts 4, 5 and 6 rows at minGap 2.5, 1.8 and 1.0 m, i.e. 8, 10 and 12 waiters. **Measured** 8, 10 and
     12 in all 5 seeds of each.
   - Values outside the tested points are **predicted, untested**: minGap 0.5 m → 7 rows = 14; minGap
     1.9–2.5 m → 4 rows = 8.
   - `minGapLat` 0.3 m did not add a third column. Two motorcycles of 0.9 m need 1.8 m + gap. By the same
     arithmetic, a third column needs `minGapLat` ≤ 0.25 m (**predicted, untested**).
   - The same capacity of 8 is reached with moderate violator demand (`target`) and with moderate opposing
     flow (`target_modopp` seeds 1–2).
3. **Discharge.**
   - The first waiter leaves 4.7 s after the opposing green end (range 2.6–6.5 s). That is about 0.7 s after
     the opposing red onset, because the opposing through keeps arriving during the 4 s yellow.
   - Then about one exit per 0.5 s (sat) to 0.7 s (target). The M7 target box exit headway is 0.5 s.
   - The box is empty 8.2 s after `t_e` with 8 waiters, and 10.4 s after `t_e` with 12 waiters. That is 2–4 s
     into the HDT green.
   - Early leaving through gaps (before the opposing green ends) depends strongly on the opposing flow. The
     M7 target assumes 20 %:
     - dense opposing flow (4700 veh/h): none after the warm-up cycle;
     - moderate opposing flow (1500 veh/h, about the proxy days' LVL_E through): **62 %** of entrants leave
       early (4.2 per cycle), and only 2.6 are still waiting at the green end (target 6).
   - With the proxy-day opposing volume and B0 vTypes, SUMO's gap acceptance therefore lets far too many
     violators go early. Dense flow suppresses early leaving entirely. Neither matches the target without
     calibration.
4. **No deadlock, no non-collision teleport.**
   - The longest box residence is 70.4 s (opposing green 64 s + clearing). No vehicle stays in the box over a
     cycle.
   - All teleports are collision teleports (`n_teleports_noncollision` = 0 in all 25 runs).
   - The collisions (2–27 per run, 334 in all) are, with one exception, between through vehicles of the same
     stream: 269 `junction`, 55 rear-end and 9 `side`, mostly on the through internal lanes. That is the B0 sublane collision issue already reported in Task 4, unrelated
     to the box.
5. **Interaction with the crossing flow.**
   - At the HDT green onset, 3.4 (target) to 4.6 (sat) waiters are still in the box. The waiting point lies
     on the path of HDT_N lane 2.
   - That lane's first stop-line crossing comes 0.4–1.1 s after the onset (B0) and 1.6–2.7 s with 12 waiters.
     The other HDT lanes cross after 0.31 s.
   - A per-cycle least-squares slope of the HDT_N lane-2 first-crossing delay against waiters still in the box
     at the onset gives about 0.2–0.5 s per waiter. The M7c target is 0.3 s per waiter; the M7c metric is
     defined on the whole crossing road, which SUMO does not delay.
   - SSM PET between box clearers and HDT through vehicles: median 1.6–1.8 s.
   - One collision in 25 runs involves a violator: `sat_tight` seed 3 at t = 74.5 s, a side collision on outbound
     `408823207#0_1` between a clearing violator (0.6 m/s) and an HDT_S through motorcycle (15.3 m/s),
     4.5 s into the HDT green.
6. **SSM caveat.**
   - The SSM device logs "collision" pairs between waiting violators and LVL_E through vehicles (geometric
     conflict-area overlap): about 300 per run under dense opposing flow and 57 under moderate flow. SUMO's own collision check (collision-output) reports none
     of them.
   - The waiting point is 1.61 m from the centre line of LVL_E's leftmost through internal lane, whose
     half-width is 1.60 m. A waiter offset laterally therefore touches that lane's conflict area.
   - SSM PET between box waiters and the opposing through (min 0.0–0.65 s) is an artefact of this geometry.
     Do not use it as a realism metric for M7. The M7b proxy uses the tier-1 tables (`box_queue`,
     `traversals`), not SSM.

## Decision and reason

- **Rule (brief Step 2).** Choose (a) native if the max native capacity is at least the target mean
  `n_waiting_in_box`; otherwise choose (b) box edge.
- **Target** (`data/proxy/targets.yaml`, M7):
  - waiting mean 6.0;
  - box entrants ~ negative binomial with mean 7.5 and var/mean 1.5, thinned by `early_leave_share` 0.2.
    Simulated with 200 000 draws (`target_stats`): waiting p90 = 10, p95 = 11; entrants p90 = 12. The
    generated days PROXY_D1–D5 give mean 5.99, p90 10, max 13.
- **Measured:** native capacity 8 (B0) ≥ 6, so the choice is **(a) native**. No box edge is built.
  `build_site_net` now requires `illegal_left.mode` and raises on `box_edge` (not implemented) or on any other
  value.
- **Against the p90 tail:**
  - With B0 values, native capacity (8) is below the target p90 (10). At the target demand the box is full in
    43 % of cycles; the remaining entrants wait at the stop line. The waiting distribution is therefore
    truncated at 8: SUMO p90 is 8, against the target's 10.
  - This is a calibration matter, not a network one. Measured: `custom1` `minGap` 1.8 m gives 10 (the waiting
    p90); 1.0 m gives 12 (the entrant p90).
  - If a measured site ever needs more than about 14 (7 rows at minGap 0.5 m, predicted, untested), there are
    two network-side options, outside the LLM's reach:
    - netconvert connection `contPos`: "an internal junction will be built at this position (in m) from the
      start of the internal lane" (Networks/PlainXML), which moves the waiting point;
    - the box-edge option (b) of PLAN Phase 3, including a TLS `linkIndex2` for the internal link.

## Implications for the `illegal_left_box` rule (Task 7)

Native SUMO already provides:
- entry into the box during the own green;
- queueing up to the geometric capacity (two abreast);
- blocking further entrants at the stop line;
- release after the opposing flow ends;
- clearing headways close to the target.

The rule should therefore not re-implement waiting. What native SUMO does not reproduce (with B0), and what
the rule and its archetype parameters need to control:

1. **Box capacity.** Through vType parameters of the `custom1` archetype, not TraCI.
   - `minGap` sets the rows. Measured: 2.5 / 1.8 / 1.0 m gives 8 / 10 / 12 waiters. Predicted, untested:
     0.5 m gives 14.
   - `minGapLat` may add a third column at ≤ 0.25 m (predicted, untested; validate before allowing values
     below 0.3).
   - Suggested bounds: `minGap` [0.5, 2.5] m; `minGapLat` [0.3, 0.6] m.
2. **Early leaving through gaps** in the opposing flow during its green. The target share is 0.2.
   - Natively the share follows the opposing flow: 0 % at 4700 veh/h, 62 % at 1500 veh/h. At the proxy-day
     volume the rule mostly has to **suppress** early leaving, not create it.
   - The rule should hold, at the waiting point, the waiters not selected to leave early (TraCI hold on the box
     lane until the opposing green ends; log `executed`).
   - Those selected keep SUMO's own gap acceptance. Their gap threshold is the archetype's `jmTimegapMinor`
     (vType, so it acts at every minor link of these vehicles).
   - Rule params: `p_early_leave` [0, 1], the probability that a box entrant may use gaps. Optionally a
     `min_gap_s` [1.0, 4.0] s if the vType threshold proves too coarse.
   - Any leave must keep SUMO's safety checks (no speed-mode override for the leave itself).
3. **Release timing relative to the opposing yellow/red.**
   - Natively the first exit is 4.7 s after the opposing yellow onset. The proxy `clear_lag_s` is 5.65 s,
     measured from max(opposing green end, last opposing crossing).
   - Rule param `release_lag_s` [0, 6] s after the opposing G -> y: hold waiters until then, or let them go
     at yellow (0 = aggressive).
   - Clearing headway is natively about 0.5 s (target 0.5 s), so no headway parameter is needed unless the
     measured data differ.
4. **Clearing versus the crossing green.**
   - 3–5 waiters are still in the box when the HDT green starts. They hold up HDT_N lane 2 by 0.2–0.5 s per
     waiter, and caused one side collision in 25 runs.
   - A rule param `max_clear_into_cross_green_s` [0, 6] s (after it, remaining waiters yield to crossing
     traffic) would control M7c and the collision risk. **Dropped by ruling R25 (Task 9):** the box waiting
     point is not outside the crossing stream (`:…_16_0` crosses the HDT_N through internal lanes; the waiting
     point is 0.03 m from the lane-2 centreline). A `setSpeed(0)` hold there makes the crossing road yield to the
     held vehicle, and telling the crossing vehicles to ignore it (`junctionModel.ignoreIDs`) gives junction
     collisions (55 vs 7 on PROXY_D1 with `--collision.check-junctions`). Only `release_lag_s` remains.
   - Any intervention here must not disable SUMO's junction safety modes (setSpeedMode), or it will add
     collisions. Log `executed` and restore modes (PLAN 4.5).
5. **Patience.** Native box residence is at most ~70 s (one opposing green). With these phases, a
   `max_wait_s` above that never triggers; a range of [30, 70] s is only meaningful together with (2).

**Recommended parameter set for `illegal_left_box`:**
- `p_early_leave` ∈ [0, 1] (held waiters otherwise; natively 0 % at dense and 62 % at proxy-day opposing flow)
- `min_gap_s` ∈ [1.0, 4.0] s (optional; else the archetype's `jmTimegapMinor`)
- `release_lag_s` ∈ [0, 6] s
- ~~`max_clear_into_cross_green_s` ∈ [0, 6] s~~ (dropped, ruling R25)
- capacity via the `custom1` archetype's vType `minGap` ∈ [0.5, 2.5] m (measured 8 / 10 / 12 at 2.5 / 1.8 /
  1.0 m) and `minGapLat` ∈ [0.3, 0.6] m, not via the rule.

All ranges are assumptions sized on the native behaviour above. Each must be checked against
`param_bounds.yaml` sources in Task 7.

## Re-check on the F2 network with check-junctions on (2026-10-26, Linux, Phase 3D)

Network after Task F2-net (lane 0 = continuous right lane with bollards, ruling R37); every run through
`thesis_sumo.sim.runner.run`, so `--collision.check-junctions` is on (R28); 5 seeds × 900 s per scenario, vType B0.
Command: `.venv/bin/python experiments/phase3/box_capacity.py --scenarios target target_modopp --seeds 1 2 3 4 5
--tag f2 --nproc 6` → `experiments/phase3/results_f2.csv`, figures `docs/research/figures/phase3_box_*_f2.png`.

| | target (seeds 1–5) | target_modopp (seeds 1–5) |
|---|---|---|
| max halting in box during opposing green | 13, 8, 8, 7, 10 | 8, 9, 10, 6, 9 |
| mean waiting at opposing green end | 4.3–7.0 | 1.4–2.0 |
| early leavers per cycle | 0–0.29 | 3.1–5.3 |
| first / last exit after opposing green end (mean) | 4.1–5.0 s / 6.9–8.1 s | 2.9–4.5 s / 4.6–6.1 s |
| collisions (all) / with an illegal-left vehicle | 0–1 / 0 | 0 / 0 |
| non-collision teleports, stuck over a cycle | 0, 0 | 0, 0 |
| max box residence | 68–70 s | 64–67 s |

Capacity is identical to the R21 re-check (13, 8, 8, 7, 10): the F2 change does not touch the box. With
check-junctions on, the box produces no collision with illegal-left vehicles and no deadlock. Decision (a) native
still holds; Viktor confirms or reverses it at the Phase 3 stop together with 3C.
