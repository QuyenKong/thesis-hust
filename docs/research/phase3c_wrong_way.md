# Phase 3C: wrong-way riding past a red queue (feasible or defer)

**Question (PLAN Phase 3C, behaviour 8).** Can SUMO 1.27.0 reproduce this movement: ride on the opposite lane
alongside a standing red queue where there is no median, then cut back in before the hard median that starts a
short distance before the stop line? The movement must work with `laneChangeModel="SL2015"` and the sublane model
used everywhere else. If it does not, does a virtual contraflow lane for `custom1` work instead?

**Verdict: native opposite-direction driving is not feasible on the site net. Only the virtual-lane fallback
works.** A TraCI `changeSublane` move onto a native opposite lane does work mechanically. It is an experimental
option, not a recommendation (see Options). Viktor decides whether to do this now or defer it.

The key reasons:
- The SUMO docs restrict native overtaking through the opposite lane: from a multi-lane edge, only emergency
  vehicles do it. In the toy runs, 0 episodes occurred on 2-lane edges in every configuration. LVL has 3 lanes per
  approach (OSM, `config/site.proxy.yaml`), and `custom1` cannot be an emergency vehicle.
- With default parameters the movement practically never happens: 1 short episode in 18 runs.
- LC2013 can do it on a single-lane edge. LC2013 is refused under sublane: SUMO raises *"Lane change model
  'LC2013' is not compatible with sublane simulation"*.
- SL2015 does it only with sublane on and `lcOpposite` far above its default. Even then the riders gain nothing on
  average and some get stuck on the opposite lane.

Everything here is a toy scenario. Geometry, signal, demand and median length are experimental settings, not
field values. Nothing in `src/`, `config/`, `scenario/`, `rules/` or `data/` was changed.

## What the docs say (checked 2026-10-26)

- **Simulation/OppositeDirectionDriving** (https://sumo.dlr.de/docs/Simulation/OppositeDirectionDriving.html, raw
  md on GitHub `docs/web/docs/Simulation/OppositeDirectionDriving.md`):
  - the net must contain `<neigh>` elements, which come from `netconvert --opposites.guess`, from netedit, or
    from an explicit `<neigh lane=.../>` in `.edg.xml`;
  - "only emergency vehicles will overtake through the opposite direction if they are on a multi-lane edge";
  - "only straight prioritized links may be used for opposite-direction overtaking";
  - the model checks for "free space at the end of the column being overtaken", with a 150 m look-ahead;
  - the safety buffers are calibrated with `lcOpposite`;
  - "not compatible with the sublane model before version 1.9.0";
  - the visibility of oncoming traffic is not modelled;
  - both edges must have the same length (`--opposites.guess.fix-lengths`).
  - The page says nothing about standing queues or TraCI.
- **Networks/PlainXML**, "Neighboring opposite-direction Lanes": `<edge ...><neigh lane="b_0"/></edge>` declares
  the innermost lanes adjacent. The 1.27.0 `edges_file.xsd` has `neighType` with a required `lane` attribute.
- **Definition_of_Vehicles…** (vType LC table):
  - `lcOpposite`: "The eagerness for overtaking through the opposite-direction lane", default 1.0, listed for
    **LC2013 only**. The experiment shows SL2015 also reacts to it under sublane (see below).
  - `lcOvertakeRight` and `lcOvertakeDeltaSpeedFactor` are LC2013/SL2015 attributes with no opposite-direction
    meaning.
- **TraCI/Change_Vehicle_State**:
  - No text mentions "opposite".
  - `changeLane`: "Forces a lane change to the lane with the given index".
  - `changeSublane`: "Forces a lateral change by the given amount … conform to safety-constraints as configured by
    laneChangeMode".
  - Both behaviours were therefore tested by experiment.
- `sumo/netconvert --help` (1.27.0): `--opposites.guess`, `--opposites.guess.fix-lengths`,
  `--lateral-resolution`, `--collision.check-junctions`.

## Setup

Script: `SUMO/experiments/phase3c/wrong_way.py`. It writes the toy plain XML, builds the nets with netconvert and
runs every case with libsumo.

- **Net (toy).** Two-way road `A -> B -> J`:
  - `up`, 400 m. This stretch has no median: `up` and `up_r` are `<neigh>`.
  - `med`, M = 30 m (setting). This is the hard median, with no `<neigh>`.
  - Signalised cross junction J with a N–S street.
  - Lane width 3.2 m.
  - Three net variants:
    - `n1`: 1 lane per direction;
    - `n2`: 2 lanes per direction, innermost lanes neighbours;
    - `v1`: 1 lane, plus a virtual left lane `up_1` with `allow="custom1"`. It has no `<neigh>` and merges into
      `med_0` at node B (explicit connection).
- **Signal.** 120 s cycle. W–E/E–W: green 42 s + yellow 3 s. N–S: green 72 s + yellow 3 s. This gives a 78 s red
  queue in the direction of interest.
- **Demand per lane of W–E.** Poisson arrivals: 200 car/h, 400 moto/h, 150 `custom1`/h. The `custom1` vehicles
  are motorcycles with the B0 `moto_violator` attributes.
- **Opposing traffic, moderate.**
  - E–W through: 150 car/h + 300 moto/h per lane.
  - N->W right turns: 200 moto/h. S->W left turns: 100 moto/h. These turns keep the opposite lane busy during the
    W–E red.
  - N–S through: 300 moto/h each way.
- **Cases.** Each case runs 3 seeds (1, 2, 3) x 600 s, step 0.1 s, `--collision.check-junctions` (R28), with the
  default collision action (teleport, as in the project). Sublane runs use `--lateral-resolution 0.4`.
  - Only `custom1` gets the modified LC attributes. Cars and motos keep the defaults.
  - "eager" = `lcOpposite=100 lcSpeedGain=100`.
- **Observer (no intervention).**
  - Opposite episode: a W–E vehicle whose current edge is `up_r`/`med_r`.
  - Virtual episode: a `custom1` on `up_1`.
  - Logged per episode: the halting vehicles ahead at the start (speed < 5 km/h), and where and when the vehicle
    came back.
  - Rank gain = departure rank − stop-line crossing rank within W–E (> 0 means it overtook).
  - Also logged: collisions by type and victim, teleports, and the SUMO warnings "Unexpected end of opposite lane"
    and "emergency braking".
- **TraCI part.** A standing `custom1` in the leftmost lane of the red queue gets one of two commands:
  `vehicle.changeLane(id, numLanes, 20)`, which is one index past the leftmost forward lane, or
  `vehicle.changeSublane(id, 3.2)`. The log records whether it reaches `up_r`, where it comes back, and its
  collisions within 60 s.
- **Toy caveat.** In a 3.2 m lane a centred car (1.8 m) leaves 0.7 m on each side. That is less than a moto
  (0.9 m) plus `minGapLat`. So no vehicle filters past the queue inside its own lane, and sublane vs no-sublane
  results without opposite driving are identical. The queue is a solid single file. This is the most favourable
  case for wrong-way riding.

## Results (sums or ranges over seeds 1–3, 600 s each; 71 `custom1` departures on n1/v1, 130 on n2)

| case | opposite / virtual episodes | with >= 3 halted ahead | custom1 users | rank gain of users (per seed) | returned before median / at median node / still on at end / teleported | collisions (all lane; junction 0) | custom1 travel time (s, per seed) |
|---|---|---|---|---|---|---|---|
| LC2013 n1 no-sublane, defaults | 1 (a moto, 0.4 s, moving) | 0 | 0/71 | 0 | 1/0/0/0 | 0 | 102–109 (= baseline) |
| LC2013 n1 sublane | — SUMO error: LC2013 not compatible with sublane | | | | | | |
| SL2015 n1 no-sublane / sublane, defaults | 0 / 0 | 0 | 0/71 | — | — | 0 | 102–109 |
| LC2013 n1 no-sublane, `lcOpposite=100` | 54 | 47 | 32/71 | +4.1, +3.2, +6.7 | 44/0/2/8 | 8, all frontal, victims = N/S turners entering the opposite lane | 89–103 |
| LC2013 n1 no-sublane, eager | 109 | 77 | 41/71 | +4.2, +3.6, +8.3 | 98/1/2/8 | 9 frontal (7 turners, 2 E–W cars) | — |
| SL2015 n1 sublane, `lcOpposite=100` | 18 | 18 | 16/71 | −6.0, −1.2, +0.2 | 13/1/4/0 | 1 rear-end | 111–148 (worse) |
| SL2015 n1 sublane, eager | 19 | 19 | 17/71 | −3.2, +6.0, +3.8 | 14/2/3/0 | 1 side | — |
| SL2015 n1 sublane, `lcSpeedGain=100` only | 0 | — | 0/71 | — | — | 0 | — |
| SL2015 n1 no-sublane, eager | 0 | — | 0/71 | — | — | 0 | — |
| LC2013 n2 / SL2015 n2 (defaults and eager) | 0 in all 4 cases | — | 0/130 | — | — | 0 | — |
| **virtual lane v1, SL2015 sublane** | 71 | median 17 halted ahead | **71/71** | **+12.8, +10.6, +20.1** | merge at B 61 / on lane at end 10 | **0** (0 teleports) | **65–74** |
| virtual lane v1, SL2015 no-sublane | 71 | median 17 | 71/71 | +12.9, +10.5, +18.9 | 62 / 9 | 0 (0 teleports) | 65–73 |

More detail:
- **Native SL2015, sublane, `lcOpposite=100`.** Episodes are long: median 54 s, max 215 s. The rider usually
  stands on the opposite lane next to the queue (13/18 reach speed < 0.1 m/s). The return point is a median of
  42.5 m before the median start.
  - One rider ran into the median node with SUMO's warning "Unexpected end of opposite lane for vehicle … at lane
    ':B_1_0'".
  - The other W–E traffic also slows: car travel time 127–137 s vs 103–127 s without wrong-way riding.
- **Native LC2013, `lcOpposite=100`.** Episodes are short (median 7 s). Riders return early: median 172 m before the
  median start, so they do not ride alongside the whole queue up to the median.
  - In every collision, the overtaker hit an oncoming vehicle that had just turned into the opposite lane from
    the junction.
- **Virtual lane.** Every `custom1` uses the lane from the moment it departs (`departLane="best"`), not only when
  a queue exists. The merge back happens at node B, in front of the queue waiting there.
  - Cost to the others: W–E car travel time 123–142 s vs 103–127 s, moto 112–143 s vs 103 s.
  - Sublane on or off makes almost no difference.
- **TraCI command** (`traci_cmd.csv`):
  - `changeLane(numLanes)`: no effect and no error, in 12/12 runs (n1 LC2013 / SL2015 / SL2015-sublane, n2
    SL2015-sublane).
  - `changeSublane(+3.2)` without sublane: no effect (0/6).
  - `changeSublane(+3.2)` with sublane: the vehicle reaches the opposite lane within 2.1 s in **6/6** runs, on n1
    and on the 2-lane n2. So TraCI bypasses the multi-lane restriction. What happens next is SUMO's choice:
    - n1: back 20–28 m before the median after 11–53 s (2 runs); one frontal collision with a turner (1 run);
    - n2: back exactly at the median start (0 m) after 37–41 s (2 runs); still on the opposite lane after 60 s
      (1 run).
- **Reproducibility.** A second full run produced byte-identical `results.csv` and `episodes.csv`.

## Interpretation and options for the thesis

1. **Native opposite overtaking (`<neigh>` + LC model): not usable.**
   - On LVL's multi-lane approaches SUMO only lets emergency vehicles do it. The docs say so and the experiment
     confirms it (0 on n2).
   - Even on a single lane, the default eagerness gives about zero use.
   - SL2015 reacts to `lcOpposite` only under sublane. When it does, it produces long standing episodes, no gain
     and stuck vehicles, not "ride past and cut in".
   - LC2013 behaves more plausibly on a single lane, but it is refused under sublane. Using it would mean dropping
     the sublane model that F2/F3 depend on.
2. **Virtual contraflow lane for `custom1` (works).**
   - It is mechanically clean: 0 collisions, 0 teleports, a clear positive gain, and the merge-back point is fixed
     by the network.
   - **SUMO computes NO conflicts between the virtual lane and the real opposing traffic.** The oncoming flow
     neither sees nor brakes for the riders. Its capacity is unaffected, so the model overstates opposing
     throughput while riders are present.
   - **No safety metric (PET, TTC, collisions) is possible on the virtual lane** (PLAN Phase 7 already excludes
     it).
   - It is a network patch (a plain-XML lane plus connections, built by script), not an LLM edit.
   - In the toy, 100 % of `custom1` used it all the time. A real use needs the PLAN `queue_space_seeking`
     gating (lane locked by `setLaneChangeMode` or `setDisallowed`, opened when the queue ≥ q). That gating is
     not tested here.
   - It interacts with the sublane model only as an extra lane on the edge. Sublane vs no-sublane results are
     the same.
3. **TraCI `changeSublane` onto a native `<neigh>` lane (experimental).**
   - It does put a `custom1` on the real opposite lane, including from a multi-lane edge.
   - SUMO then does compute interaction with oncoming traffic: emergency braking and frontal collisions. In
     principle this allows safety metrics.
   - The return is left to the model. Riders come back late (at the median start), get stuck, or collide.
   - It needs `<neigh>` on the site net. Note: LVL's leftmost lane is the BRT lane, so its neighbour opposite
     lane is also a BRT lane.
   - It would need its own return rule and its own tests. This is the most effort and the least predictable
     option.

## Open questions for Viktor

1. Do now (virtual lane, with the stated limits) or defer behaviour 8? If now: virtual lane (option 2), or try
   TraCI `changeSublane` (option 3)?
2. Real cross-section: is there actually a stretch of LVL (or HDT) without a median where riders cross into the
   oncoming lanes, and which lane do they use (BRT lane?)? Also `hard_median_length_m` stays `null # TODO_MEASURE`.
3. If virtual lane: should the merge back be at the median start (as tested), or should riders be forced to
   change back into the queue before it?

## Reproduce (from `SUMO/`)

```bash
.venv/bin/python experiments/phase3c/wrong_way.py --nproc 8              # all cases, seeds 1-3, 600 s (~20 s)
.venv/bin/python experiments/phase3c/wrong_way.py --cases SL2015_v1_sub  # one case; overwrites the CSVs (TraCI part always runs)
```

Outputs:
- `experiments/phase3c/results.csv`: one row per run;
- `experiments/phase3c/episodes.csv`: one row per opposite or virtual episode;
- `experiments/phase3c/traci_cmd.csv`;
- toy plain XML and nets: `experiments/phase3c/toy/{n1,n2,v1}/`;
- raw SUMO output: `experiments/phase3c/out/` (git-ignored, `out/`).

On Windows use `.venv/Scripts/python`.
