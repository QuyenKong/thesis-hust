# Phase 3A: blocking the continuous right-turn lane (behaviour 6)

**Question (PLAN Phase 3A, R37).** Straight-going violators (`custom1` = motorcycle defaults, `custom2` = passenger
defaults) use the continuous right-turn lane (lane 0) upstream of the bollards to pass the straight queue. They
then have to squeeze back into the through lanes before the bollards start, and they stop in lane 0 while they
wait for a gap. Four questions:

1. Does SUMO 1.27.0 (SL2015, sublane) do this by itself (speed gain) when the straight queue is long? Does it
   also do it when the queue is short? In other words, is a TraCI trigger needed?
2. Do the violators stop in lane 0 before the bollard start, and are the right-turners behind them delayed?
3. Deadlocks, teleports and collisions (with `--collision.check-junctions`). Can `setLaneChangeMode` keep
   violators out of lane 0 until a queue trigger fires, and let them in once it does? The rule is the R25 one:
   collision avoidance is never switched off.
4. Do compliant cars and motorcycles on a straight route ever get stuck in lane 0?

**Short answer.**
- **(1)** No. Native SL2015 almost never takes lane 0 for a straight route: 0 violators in 12 heavy runs with
  queues up to 232 m. It happened only as rare 4–12 s overtakes far upstream at queue 0, and nobody stopped.
  So behaviour 6 has to be **actively triggered by TraCI**. The trigger can be gated on queue length, and
  nothing happens without it.
- **(2)** With the trigger, violators ride lane 0, merge back in the last metres before the bollard start, and
  stop there when no gap is free. Right-turner delay grows with the share of violators released:
  - B0-like reference: 3.4 s mean timeLoss;
  - p = 0.3 release: 4.2 s;
  - p = 1 release: 8–27 s, with up to 990 veh·s of right-turners halted behind blockers per 900 s.
- **(3)**
  - **Junction collisions:** 0 in all 90 runs.
  - **Lane collisions:** 0–1 per run at p = 0.3, 0–4 at p = 1. Almost all are SL2015 side collisions while a
    violator merges back into the stopped lane-1 queue.
  - **Jam teleport:** 1 in 1 of the 6 p = 1 runs (a violator stuck on the straight junction lane).
  - **Lock mode:** not needed. Under the tested lock modes (517–1621), 0 violators entered lane 0.
  - **Release:** `setLaneChangeMode(1621)` + `changeLane(0, hold)`, ended by `changeLane(0, 0)` 15 m before the
    bollard start, works. A TraCI request to lane 1 at the merge point does not (see "merge action").
- **(4)** No. 0 compliant blockers and 0 straight vehicles on the bollard part of lane 0 in all 90 runs.
  Compliant vehicles enter lane 0 only for short native overtakes (3 motorcycles per L in the 3 `open` heavy seeds), and an
  upstream `changeRight` restriction removes even those.

**Every number in "Setup" is an experimental setting chosen for this toy, not a field value.** That includes the
bollard length L, flows, violator share, cycle, trigger threshold and release probability. The bollard length at
LVL x HDT is unknown (`TODO_MEASURE`).

## Setup

Script: `SUMO/experiments/phase3a/right_lane_blocking.py`. It builds a toy network in `experiments/phase3a/net/`
and does not touch the main net, `src/`, `config/`, `scenario/`, `rules/` or `data/`.

- **Network.**
  - One approach, W -> C, 3 lanes x 3.5 m, 50 km/h, into a TLS node C. Exits: `outE` (2 lanes, straight) and
    `outS` (1 lane, right). Exit width equals entry width (R21).
  - The approach is split into `up` (400 m) and `bol` (the bollard stretch, length **L = 30 m or 60 m**;
    checked by assert after netconvert).
  - Connections: lane 0 -> `outS` only. Lanes 1, 2 -> `outE`. No straight connection from lane 0, which is what
    R37's `disallow="all"` gives in the main net.
  - TLS: a 120 s cycle, `gGG` 64 s / `gyy` 4 s / `grr` 52 s. The right link is always `g` (never stopped by the
    signal); nothing conflicts with it in the toy.
- **Bollards = lane-change prohibition on `bol`.**
  - `bol` lane 0 has `changeLeft="emergency"` and lane 1 has `changeRight="emergency"`.
  - Semantics, from sumo.dlr.de/docs/Networks/PlainXML.html (lane attributes): "changeLeft: List of vehicle
    classes that may change left from this lane". Same for `changeRight`. Both are type `xsd:string` in
    `$SUMO_HOME/data/xsd/edges_file.xsd`.
  - The docs call `"ignoring"` "the strongest restriction". **netconvert 1.27.0 silently drops
    `changeLeft="ignoring"` from the output net**, so the lane is left unrestricted (checked by building it).
    `"emergency"` is written, and no emergency vehicles exist. An empty value is a netconvert error. Unknown
    classes (`custom3`) are an error too.
  - Check: **0 lane changes between lanes 0 and 1 on `bol`** across all 90 runs, under the sublane model. Lanes
    1 and 2 still exchanged 5994 times.
  - SL2015's strategic model respects the restriction. A probe put a straight car in `up` lane 0, 20 m before
    `bol` on an empty net. It braked and merged into lane 1 at 398.6 m, before the bollard start, and did not
    drive into `bol` lane 0.
- **Two net variants.**
  - `open`: no restriction on `up`.
  - `lock`: on `up`, lane 1 has `changeRight="custom1 custom2 emergency"`. Compliant classes cannot move from
    lane 1 into lane 0 upstream; violators can.
- **Vehicle types.** `rules/compiled/B0/vtypes.add.xml`, read only: `moto_B0`, `car_B0`, `moto_violator_B0`
  (`custom1`) and `car_violator_B0` (`custom2`). All are SL2015 with SUMO defaults.
- **SUMO options.** `--step-length 0.1 --lateral-resolution 0.4 --collision.check-junctions true`. Default
  `collision.action` (teleport) and `time-to-teleport` (300 s). 900 s per run, seeds 1–3. Backend: libsumo.
- **Demand (Poisson, experimental).**
  - heavy: straight 4000 moto/h + 650 car/h.
  - light: straight 700 + 120.
  - Both: right 300 moto/h + 60 car/h.
  - 20 % of straight vehicles are violators. The draw is made per vehicle, so arrivals are identical across
    scenarios for one (demand, seed).
  - `departLane="best"`: straight vehicles depart in lanes 1–2, right-turners in lane 0.
  - Max straight queue: heavy 145–232 m, light 20–45 m.
- **Scenarios.**

  | scenario | net | violators | TraCI |
  |---|---|---|---|
  | `noviol` | lock | 0 % | none (reference) |
  | `open` | open | 20 % | none (native SL2015) |
  | `lock` | lock | 20 % | none |
  | `trig` | lock | 20 % | lock mode 1541 at departure. While the straight queue (farthest halting vehicle on lanes 1–2) is ≥ **50 m**, each violator on `up` lanes 1–2 within queue + **60 m** of the stop line draws once and is released with **p = 0.3**: `setLaneChangeMode(1621)` + `changeLane(0, 600 s)` (held in lane 0). **15 m** before the bollard start the hold ends with `changeLane(0, 0)`, and SL2015's strategic model merges it back. A released vehicle not yet in lane 0 at that point is dropped ("giveup"). |
  | `trigp1` | lock | 20 % | as `trig`, p = 1 |
  | `trigshort` | lock | 20 % | as `trig` but only `changeLane(0, 3 s)`, no hold; SL2015 decides when to go back |
  | `probe_<mode>` | lock, heavy, L = 60 | 20 % | violators run with lane-change mode 1621 / 1605 / 1541 / 517 for the whole trip, never released |

  The bit meanings below are from sumo.dlr.de/docs/TraCI/Change_Vehicle_State.html. All lock modes keep bits
  8–9 = `10` ("respect speed/brake gaps"); collision avoidance is never switched off.

  | mode | change from 1621 |
  |---|---|
  | 1605 | speed gain off |
  | 1541 | speed gain and keep-right off |
  | 517 | speed gain, keep-right and sublane off |

## Results

Means over 3 seeds; collision and teleport columns are totals over 3 seeds. Measures:
- **blockers:** straight vehicles halted (< 0.1 m/s) on `up` lane 0 within 20 m of the bollard start.
- **RT behind:** veh·s of right-turners halted on `up` lane 0 behind a halted straight vehicle.
- **timeLoss:** from tripinfo, for vehicles departing in 60–720 s.

| demand, L | scenario | max queue m | violators into lane 0 | released | blockers | RT behind veh·s | RT timeLoss mean / p90 s | straight timeLoss s | lane coll. | teleports | pending at end (max) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| heavy, 30 | noviol | 169 | – | – | 0 | 0 | 3.4 / 7.1 | 33.6 | 0 | 0 | 0 |
| heavy, 30 | open | 176 | 0 | – | 0 | 0 | 3.4 / 7.3 | 33.4 | 0 | 0 | 0 |
| heavy, 30 | lock | 163 | 0 | – | 0 | 0 | 3.4 / 7.3 | 32.8 | 0 | 0 | 0 |
| heavy, 30 | trig (p 0.3) | 210 | 35.7 | 50.3 | 15.7 | 3.2 | 4.2 / 10.3 | 41.0 | 1 | 1 | 0 |
| heavy, 30 | trigshort | 197 | 22.7 | 47.0 | 11.3 | 27.7 | 5.0 / 12.7 | 41.6 | 1 | 1 | 0 |
| heavy, 30 | trigp1 | 379 | 159.3 | 219.3 | 56.3 | 703.7 | 26.6 / 77.7 | 78.9 | 6 | 7 | 37 |
| heavy, 60 | noviol | 171 | – | – | 0 | 0 | 3.6 / 7.8 | 33.5 | 0 | 0 | 0 |
| heavy, 60 | open | 163 | 0 | – | 0 | 0 | 3.5 / 7.6 | 32.6 | 0 | 0 | 0 |
| heavy, 60 | lock | 161 | 0 | – | 0 | 0 | 3.5 / 7.8 | 33.0 | 1 | 1 | 0 |
| heavy, 60 | trig (p 0.3) | 211 | 28.7 | 37.3 | 15.3 | 1.9 | 4.2 / 10.3 | 38.6 | 1 | 1 | 0 |
| heavy, 60 | trigshort | 182 | 17.0 | 35.0 | 6.0 | 16.0 | 4.1 / 9.5 | 37.4 | 0 | 0 | 0 |
| heavy, 60 | trigp1 | 289 | 116.3 | 173.7 | 40.7 | 84.5 | 8.2 / 22.3 | 45.7 | 8 | 8 | 0 |
| light, 30/60 | all | 24–31 | 0–0.7 | 0 | 0 | 0 | 2.2–2.3 / 4.4–4.7 | 15.6–16.2 | 0 | 0 | 0 |

Per-seed values are in `experiments/phase3a/results.csv`.

### (1) Native SL2015 does not reproduce behaviour 6

- **Heavy, `open`/`lock`, 12 runs, queues up to 232 m:** 0 violators changed into `up` lane 0.
- **Native entries overall:** 2 violators in light runs (`S_vm_54`, `S_vm_206`, each in both nets) and 3
  compliant motorcycles in `open` heavy runs (the same 3 for L = 30 and L = 60).
  - All were at queue 0–1 m, 100–170 m before the bollard start.
  - All went back to lane 1 within 4–12 s.
  - None stopped.
  - These look like overtakes of a slower leader, not queue jumping.
- **Why:** lane 0 has no straight continuation, and SL2015's strategic look-ahead counts the
  `changeLeft`/`changeRight` restriction, so for a straight route lane 0 is a dead end. Speed gain does not
  outweigh that.
- **Consequence:** the behaviour does not appear without TraCI, at any queue length. That answers the PLAN 3A
  question "nếu không có luật, xe vi phạm có thể vào làn này cả khi không ùn" ("without a rule, could violators
  enter this lane even when there is no congestion?"). In this toy they do not.
- **Queue gating:** with the queue trigger (≥ 50 m), entries happen only while the queue is long. In light
  demand the queue never reached 50 m, so `trig*` runs equal `lock` runs: 0 releases.

### (2) Stopping before the bollards and delay to right-turners

- **Hold design (`trig`, `trigp1`).** Released violators ride lane 0 and merge back where the hold ends. Distance
  from the bollard start at the 0 -> 1 change:
  - `trig`: median 2.4 m, p75 7.2 m (192 merges);
  - `trigp1`: median 6.3 m.

  When lanes 1–2 are queued there, they stop in lane 0. That gives 15–16 blockers per 900 s at p = 0.3 and
  41–56 at p = 1.
- **Delay to right-turners, against `noviol` (3.4–3.6 s mean timeLoss):**
  - p = 0.3: +0.6 to +0.8 s mean, +2.5 to +3.2 s p90;
  - p = 1: +4.6 s (L 60) and +23 s (L 30) mean, p90 up to 78 s.

  At p = 1 the right lane spilled back to the upstream end in one L = 30 seed: 37 vehicles not inserted, queue
  428 m.
- **Gain for the violators.** Released violators lost less time than compliant straight vehicles in the same
  runs. This is the incentive the behaviour assumes:
  - `trig`: 32.3 s vs 40.9 s (L 30) and 30.5 s vs 38.4 s (L 60);
  - at p = 1 the gain is gone (L 30: 103 s vs 76 s), because the violators block each other.
- **No hold (`trigshort`).** After the 3 s request, SL2015 sends the vehicle back to lane 1 wherever it finds a
  gap: median 12.6 m, mean 27.7 m, up to 155 m before the bollard start. That means fewer blockers (6–11), but
  more right-turner time behind them (16–28 veh·s), because the stops are spread along lane 0. It does not
  represent "ride to the bollards, then squeeze in".
- **Bollard length.** L enters only through where the merge zone sits relative to the queue. At p = 1 the 30 m
  stretch hurt right-turners more than 60 m (26.6 s vs 8.2 s), because the merge point lies deeper inside the
  dense part of the straight queue. At p = 0.3 there was no difference (4.2 s for both). With 3 seeds this is a
  hint, not a result. It does show that the result depends on the bollard length, so the length has to be
  measured.

### (3) Safety, deadlock, TraCI bits

- **Junction collisions:** 0 in all 90 runs (check-junctions on).
- **Lane collisions (all teleport-resolved, stage `laneChange`, on `up`):**
  - `noviol` and `open`: 0;
  - `lock` / `probe_1621` (identical runs): 1, a right-turn moto vs right-turn moto side collision in lane 0;
  - `trig` / `trigshort` (p 0.3): 1 per 3 runs per setting;
  - `trigp1`: 6 (L 30) and 8 (L 60) per 3 runs.

  Of the 17 under the trigger:
  - 13 are side collisions on `up_1` between a violator merging back and a vehicle in the lane-1 queue;
  - 2 are car-car `move` (rear-end) collisions in the lane-1 queue (`trigp1`);
  - 2 are right-turn moto vs right-turn moto in lane 0. All happen with the default
  bits 8–9 = `10` ("respect speed/brake gaps"). This is SL2015 sublane merging into a stopped queue under
  strategic urgency. It is not caused by switching off a safety bit, and it scales with how many vehicles are
  released. In the main net these count against the R28 lane-collision threshold, so the release probability
  the LLM picks costs collisions. This needs to be visible in the report on each spec.
- **Deadlock.** One jam teleport in `trigp1_heavy_L30_s2`. A released violator that gave up (it never reached
  lane 0) stopped on the straight junction lane `:C_1_0`:
  - it sat at lateral −1.55 m (right edge), speed 0, with no leader, for 300 s;
  - the merge-zone cancel `changeLane(idx, 0)` had been sent.

  An earlier version left the lane-0 request active after the vehicle left `up` and produced this more often
  (3 jam teleports on `:C_1_0` across the `trig`/`trigp1` runs). The fix (drop the request at the merge zone or
  on leaving `up`) reduced it to 1 in 6 p = 1 runs and 0 at p = 0.3. A single-vehicle probe could not reproduce it, so the cause inside SL2015 is not
  identified. It is a known residual risk for the runtime rule. A watchdog that recentres or drops any request
  of a released violator on the bollard edge is the obvious guard (not tested).
- **Lock bits.** `probe_*` (heavy, L 60, 3 seeds each): 0 violators into lane 0 under 1621, 1605, 1541 and 517
  alike. The minimal lock in this geometry is **none**, because the dead-end lane already keeps them out. The
  lock modes also had a side effect: switching off speed gain/keep-right for violators raised the straight
  timeLoss of everybody (31.5–34.2 s under 1621, 35.2–42.8 s under 1541). So a defensive lock is not free.
- **Release bits.** Restoring 1621 and calling `changeLane(0, duration)` moved 61–81 % of released violators into
  lane 0 (`trig`, per run). The rest could not find a gap within the window and were dropped at the merge zone.
  Violators released from lane 2 need two changes.
- **Merge action** (`--only merge`, `trigp1`, heavy, L 60, 3 seeds):

  | merge action | RT timeLoss mean | pending at end | jam teleports |
  |---|---|---|---|
  | `changeLane(1, 600 s)` (request to lane 1) | 82–344 s | 259–419 | 1 per run, on the junction lane |
  | `changeLane(0, 0)` (end the request) | 5–13 s | 0 | 0 |

  Use "end the request, let SL2015 merge".

### (4) Compliant vehicles

- 0 compliant blockers, 0 straight vehicles of any class on `bol` lane 0, and 0 straight vehicles departing in
  lane 0, in all 90 runs.
- In the `open` net, 3 compliant motorcycles made the short native overtakes described in (1). The `lock` net
  (`up` lane 1 `changeRight="custom1 custom2 emergency"`) removes them; there were 0 under `lock`.
- That restriction would also stop compliant right-turners from moving from lane 1 to lane 0. In the toy they
  all depart in lane 0, so this is untested for the main net, where right-turners may arrive in lane 1 from
  upstream edges.

## Interpretation and recommendation

1. **Network patch (static, LLM never touches it).**
   - Model the bollard stretch on every approach as **its own edge**: split the approach edge at
     `stop line − bollard_length_m`.
   - On that edge set `changeLeft="emergency"` on lane 0 and `changeRight="emergency"` on lane 1. Do not use
     `"ignoring"`, which netconvert drops.
   - Keep R37's `disallow="all"` straight connection from lane 0.
   - This needs hard data per approach: **`bollard_length_m`**, the distance from the stop line to the first
     bollard (`TODO_MEASURE`). With L unknown the patch cannot be built, and the toy shows that L changes how
     much right-turners suffer.
   - Optional, upstream of the bollards: lane 1 `changeRight="custom1 custom2 emergency"`. It keeps the rare
     native compliant overtakes out of lane 0. It also blocks compliant right-turners that are not already in
     lane 0, so it should only be added if the upstream edge is long enough for them to be in lane 0 from
     insertion. Viktor to decide (`TODO_DECIDE`).
2. **TraCI, `queue_space_seeking` option `right_lane`.**
   - **Lock:** no lane-change-mode lock is needed. Native SL2015 does not enter lane 0 for a straight route, and
     a lock (1541) changes lanes 1–2 behaviour. If a guard is still wanted, keep it as a check (log any
     untriggered violator in lane 0) rather than a mode.
   - **Trigger:** queue on the straight lanes ≥ `q` (and/or `t_w`) → per-violator draw with `p_right`.
   - **Action:**
     - `setLaneChangeMode(1621)` + `changeLane(0, hold)` and log whether the vehicle reaches lane 0 (61–81 %
       did here);
     - end the request with `changeLane(0, 0)` `merge_zone_m` before the bollard edge, and let SL2015 merge
       (this produces the stop-and-block);
     - drop the request if the vehicle is not in lane 0 by then, or if it leaves the approach edge;
     - never request lane 1 at the merge point (gridlock).
   - **Optional `v_creep`:** cap the speed with `setSpeed` while in lane 0. Not tested here.
   - **Parameters for the LLM:** `q`, `p_right` and, if wanted, `merge_zone_m` (a few metres to ~20 m). The
     toy shows `p_right` drives both the right-turn delay and the lane-collision count, so the R28 lane
     threshold will bound it in practice.
3. **Metrics.** Behaviour 6 is visible as: straight vehicles halted in lane 0 just upstream of the bollard edge,
   and right-turner timeLoss / halts behind them. The `space_seeking_events.csv` row (`space = right_lane`) should
   be written at release time, with the queue length then, as here.

## Open questions for Viktor

1. **Bollard length per approach** (stop line to first bollard), and whether the bollards are continuous up to
   the stop line on every approach (R37 says "bollards on every approach").
2. Where do violators really cut back: right at the first bollard, or earlier? This sets `merge_zone_m`.
3. Do right-turners reach lane 0 far upstream, so that a `changeRight` restriction for compliant classes
   upstream is safe? Or do they change late?
4. Roughly what share of straight motorcycles / cars use the right lane when the queue is long, and from what
   queue length? This gives an order of magnitude for `p_right` and `q`. The toy shows p = 1 gridlocks.

## Limits

- A toy geometry with no other approaches, no conflicting flow for the right turn and no pedestrians. Demand is
  synthetic, 3 seeds x 900 s per setting.
- Each `light` `trig*` run equals the corresponding `lock` run, because no trigger fired.
- The jam-teleport cause on `:C_1_0` is not identified.

## Reproduce

From `SUMO/`:

```bash
.venv/bin/python experiments/phase3a/right_lane_blocking.py --nproc 10            # 84 runs: probes + main matrix -> results.csv
.venv/bin/python experiments/phase3a/right_lane_blocking.py --only merge --nproc 6  # 6 runs: merge action -> results_merge.csv
```

Run time on the Linux box with 10 workers: about 13 min, then about 4 min.

Outputs:
- `experiments/phase3a/net/`: the toy nets and plain XML;
- `results*.csv`, `lc_events*.csv`, `interventions*.csv`;
- `runs/<run>/`: routes, tripinfo, SUMO log.
