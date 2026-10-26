# Phase 3B: sidewalk lane for `custom1` (toy feasibility experiment)

**Question (PLAN Phase 3B).** Does a `custom1` vehicle (moto_violator) enter a sidewalk lane, ride to its end and
merge back at the right place? Is there jamming or teleporting at the merge point?

**Short answer.**
- **SUMO can represent it, but not by itself.**
  - SL2015 almost never chooses the sidewalk on its own: 0–1 of 134 `custom1` per run, even when the queue
    reached past the sidewalk start.
  - A route-based sidewalk (separate edge) is a routing choice, not a lane-change choice.
  - So **a TraCI trigger is required** in every topology (PLAN 4.5 `queue_space_seeking`, option `sidewalk`).
- **The merge is the critical design point.**
  - With SUMO's default right-of-way, the sidewalk is a *minor* stream, so riders yield to the saturated road
    stream at the merge and never get a gap.
  - The sidewalk then jams: riders took 500–640 s against 85 s on the road, most were still on the sidewalk at
    900 s, and the jam spilled back into the right-turn lane.
  - This happens with any merge that yields (topologies b and c below).
- **Workable topology: (c)+priority.** The sidewalk is a separate one-lane edge that runs to the stop line and
  has its own TLS links at the junction. Its straight link is `G`, not `g`, so road vehicles yield to it.
  - 0 jam teleports and no gridlock; 97 % of riders finished.
  - 0 compliant vehicles on the sidewalk.
  - It keeps the road lane indices and, after pinning, the TLS link indices of the road unchanged.
  - The riders' travel-time gain in this toy is small or negative. It depends on the sidewalk speed setting and
    the queue delay (see the numbers below).
- **Topology (a), the sidewalk as an extra lane 0 of the same edge, is not recommended.**
  - It shifts every lane index.
  - A lane-change trigger blocked the right-turn lane: compliant right-turn time loss rose from 3 s to 133–137 s.
  - The end opening also became an entry.

**Not field data.** Every number here is an experiment setting on a toy net: lane width, sidewalk width
2.0 / 3.0 m, sidewalk speed 5 / 8.33 m/s, lengths, signal plan and demand. None of it is from `config/site.yaml`.
`sidewalk_width_m` and `f2_measured_approaches` stay `TODO_MEASURE`.

**No safety metric for the sidewalk (PLAN 7).** SUMO models no pedestrians here (out of scope), so the sidewalk
lane has no conflict partner. No PET/TTC is reported for it. The collision counts below cover vehicle–vehicle
contacts only.

## Setup

Script: `SUMO/experiments/phase3b/sidewalk.py`. Generated toy files are in `experiments/phase3b/toy/<variant>/`:
plain XML, `toy.net.xml`, the runtime TLS program `toy.tll.add.xml`, the pinned program `toy.pin.tll.xml` and the
route files. Results:
- `results_runs.csv`: one row per run;
- `results_vehicles.csv`: one row per `custom1`, with entry and exit lane, sidewalk halting time and trip time;
- `results_summary.csv`: mean over 3 seeds.

Raw outputs are in `out/` (git-ignored). Nothing in `src/`, `config/`, `scenario/`, `rules/` or `data/` was
changed; `rules/compiled/B0/vtypes.add.xml` is only read.

### Toy approach

The approach heads east into the signalised node J:
- **Road lanes.** 3 lanes of 3.5 m at 13.89 m/s.
  - Road lane 0 is the continuous right turn. Its link is `g` in every phase (R37: not signal controlled).
  - Road lanes 1–2 go straight. Fixed signal: 64 s G / 4 s y / 52 s r, cycle 120 s.
- **Bollards** on the last 20 m between the right-turn lane and the straight lanes.
- **Sidewalk.** `allow="custom1"` only; speed 5 m/s, or 8.33 m/s in the `f` variants. Width 2.0 m or 3.0 m.
  It starts 170 m before the stop line.
- **Insertion edge.** `up`, from 420 m to 170 m before the stop line.

**Lane-change restriction syntax.** It was checked in `$SUMO_HOME/data/xsd/edges_file.xsd` and
`connections_file.xsd` (lane and connection attributes `changeLeft` / `changeRight`) and in
sumo.dlr.de/docs/Networks/PlainXML.html: "List of vehicle classes that may change left/right from this lane"; "The
strongest restriction is the value `ignoring`".
- **Finding:** netconvert 1.27.0 drops `changeLeft="ignoring"` silently; the attribute is missing from the
  `.net.xml`, which then means "all may change".
- The script uses `"emergency"` instead. That class is absent from the demand, and the restriction does reach the
  net (checked in `toy.net.xml`).

### Topologies

| id | Sidewalk | Where riders rejoin |
|---|---|---|
| `ctrl` | none (reference) | — |
| `a` | extra **lane 0 of the same edges**; road lanes shift to 1..3. S1 (170–150 m) is an opening, S2 (150–20 m) is closed (sidewalk `changeLeft="emergency"`, road lane 1 `changeRight="emergency"`), S3 (last 12.5 m after the junction cut) is an opening to the right-turn lane | own links at J: right `g` always, straight `g` in the green; or a lane change into the right-turn lane in S3 |
| `b` | **separate edge `sw`** from diverge node D (170 m) to merge node M (20 m before the stop line). Edge priority 1 against `mid` priority 2 | at M into `ap_end` lane 0 (right) or lane 1 (straight) |
| `c` | **separate edge `sw`** from D **to the stop line J** | own TLS links at J: right `g` always; straight `g` in the green, or `G` with flag `p`. Pinned to link indices 3, 4 |

Flags on the variant id (`<topology><flags>_w<width>`):
- **No flag.**
  - `a`: SL2015 decides alone.
  - `b`/`c`: every `custom1` is routed over `sw` (mechanics test).
- **`t`: TraCI trigger** when the queue back is ≥ 60 m (setting).
  - `a`: `changeLane(v, 0, 5 s)` on S1.
  - `b`/`c`: `setRoute` over `sw` when the vehicle is ≤ 300 m from J.
- **`p`: sidewalk has priority at the merge.**
  - `b`: edge priority 3 > 2.
  - `c`: the straight link is `G`. The program is given to netconvert, so the junction response matrix makes the
    road links yield.
- **`f`: sidewalk speed 8.33 m/s.**

### Demand and run settings

**Demand** (veh/h, Poisson; `heavy` / `light` = 25 % of heavy):

| Movement | car | moto | custom1 |
|---|---|---|---|
| Straight | 800 | 4500 | 400 |
| Right | 150 | 600 | 150 |

- The heavy queue back has p90 185 m in `ctrl`, so it passes the sidewalk start at 170 m.
- The light queue back has p90 26 m.

**Run settings:**
- B0 vTypes (SL2015, motorcycle defaults for `custom1`).
- `--lateral-resolution 0.4`, `--step-length 0.1`, `--collision.check-junctions` (R28).
- Default `collision.action` and `time-to-teleport`.
- Seeds 1, 2, 3; 900 s each.

The script ran 21 variants × 2 demands × 3 seeds = 126 runs, with libsumo.

## Results (mean over 3 seeds)

### Heavy demand

TT = mean trip time over 420 m + exit (s); TL = time loss.

| variant | sidewalk users / custom1 seen | TT custom1 straight (users) | TT custom1 right (users) | TL compliant straight | TL compliant right | sidewalk halt / user (s) | queue p90 (m) | not inserted | teleports (jam/yield) | junction collisions |
|---|---|---|---|---|---|---|---|---|---|---|
| ctrl | – / 134 | 84.8 | 47.0 | 42.2 | 3.2 | – | 185 | 0.3 | 1.3 (0/0) | 0 |
| a_w2 | 1.0 / 134 | 88.1 | 46.5 (43.7) | 43.9 | 3.0 | 0.0 | 198 | 0 | 3.0 (0/0) | 0 |
| a_w3 | 0.7 / 134 | 89.0 | 46.8 (42.6) | 45.8 | 3.0 | 0.0 | 198 | 0.7 | 2.7 (0/0) | 0 |
| at_w2 | 19.0 / 124 | 128.4 (150.7) | 151.2 (146.5) | 85.1 | **137.0** | 2.9 | 341 | **125** | 4.3 (0/0) | 0 |
| at_w3 | 15.0 / 125 | 126.1 (168.1) | 160.1 (138.6) | 74.6 | **132.7** | 2.6 | 392 | **168** | 6.7 (0/0) | 1.0 |
| b_w2 | 37.7 / 97 | **517 (530)** | **480** | 42.5 | 95.2 | **572** | 396 | 86 | 1.7 (0/0) | 0.7 |
| b_w3 | 70.3 / 117 | **497** | **477** | 39.3 | 35.8 | **516** | 369 | 35 | 0.3 (0/0) | 0.3 |
| bt_w3 | 66.0 / 132 | 177 (535) | 160 (421) | 44.7 | 10.3 | 379 | 243 | 12 | 3.7 (0/0) | 1.3 |
| bp_w2 | 130.3 / 134 | 84.3 | 73.5 | **219.8** | 10.9 | 9.2 | 396 | **429** | 2.0 (0/0) | 0 |
| bp_w3 | 130.3 / 134 | 82.5 | 70.0 | **195.6** | 7.9 | 7.7 | 393 | **352** | 1.3 (0/0) | 0.3 |
| c_w2 | 35.0 / 99 | **518 (573)** | 187 (85) | 40.8 | 77.7 | **678** | 396 | 82 | 3.3 (1/1) | 0 |
| c_w3 | 70.7 / 118 | **637** | **505** | 38.0 | 33.0 | **559** | 380 | 31 | 2.3 (0/2) | 0 |
| ct_w3 | 62.7 / 133 | 173 (569) | 97 (345) | 39.7 | 7.1 | 364 | 205 | 5 | 4.7 (0/2.7) | 0 |
| cp_w2 | 130.3 / 134 | 97.1 | 85.9 | 83.8 | 17.0 | 17.9 | 361 | 30 | 2.7 (0/0) | 0 |
| cp_w3 | 130.3 / 134 | 88.8 | 78.6 | 67.8 | 12.2 | 14.4 | 284 | 5.7 | 2.7 (0/0) | 0.3 |
| **cpt_w2** | 83.3 / 134 | 100.5 (99.8) | 69.1 (79.3) | 61.0 | 12.2 | 12.0 | 267 | 2.0 | 1.3 (0/0) | 0 |
| **cpt_w3** | 88.7 / 134 | 102.7 (104.2) | 70.8 (78.3) | 58.6 | 10.3 | 14.6 | 261 | 1.0 | 2.3 (0/0) | 0 |
| cpf_w2 | 130.3 / 134 | 79.5 | 72.6 | 83.2 | 15.1 | 14.3 | 344 | 27 | 1.7 (0/0) | 0 |
| cpf_w3 | 130.3 / 134 | 75.1 | 65.0 | 66.7 | 12.2 | 12.8 | 269 | 1.7 | 1.7 (0/0) | 0.3 |

How to read the table:
- **Teleports.** Almost all are `collision.action` teleports after a side or rear collision between motorcycles on
  the road lanes. Those occur in `ctrl` too (sublane B0 artefact). Jam teleports: 1 in total (`c_w2`). Yield
  teleports: at most 2.7 per run, only in `c`/`ct`, with the yielding sidewalk link.
- **Sidewalk lane.** Collisions on it: **0** in all 126 runs. Steps with a compliant vehicle on it: **0** in all
  runs, so `allow="custom1"` holds.
- **Junction collisions.** There were 14 in total across all runs, none in `ctrl`, and every one involved a
  `custom1`. They happened at:
  - diverge D: 6;
  - merge M: 3 (`bt_w3`);
  - J: 5. These were on `:J_3_0` (road through against a rider entering `out_s_0`, `cp` light, 2), `:J_2_0`
    (`cpf`) and the sidewalk right link `:J_0_0` (`at_w3`).

  They are rare, but they show that the merge conflict exists.

### Light demand (no queue beyond the red phase)

- `a`, `at`, `bt`, `ct`, `cpt`: **0** sidewalk users. SL2015 does not choose it, and the trigger does not fire.
- Forced routing makes riders slower than the road (ctrl `custom1` straight 61.5 s):
  - `cp_w2`/`cp_w3`: 79.5 / 78.4 s;
  - `cpf_w3`: 68.7 s;
  - `c_w2`: 250 s (yield jam even at light demand);
  - `b_w3`: 114 s.

## Interpretation

### 1. Does `custom1` enter the sidewalk by itself?

No: the trigger is necessary.
- **Topology a, SL2015 alone.**
  - 0–1 of 134 `custom1` per run used the sidewalk. Of the 43–45 who reached the 170 m point with a queue
    ≥ 170 m, 0–1 used it.
  - All 5 native entries were right-turners slipping into the sidewalk in the **end** opening (S3), not at the
    start.
  - The speedGain incentive of a 5 m/s lane is too weak, and straight `custom1` would have to cross the
    right-turn lane inside a 20 m opening.
- **Topologies b and c.** The sidewalk is a route, so use is decided by routing or TraCI only. This is cleaner: the
  decision is explicit and can be logged, which PLAN 4.5 requires.
- **With the trigger.** `cpt` had no light-demand use and 83–89 users per run under heavy demand.

### 2. Do they ride to the end and rejoin at the right place?

- **c / cp / cpt.** Riders rejoin at J through their own link: straight → `:J_1_0` → `out_s_0`, right →
  `:J_0_0` → `out_r_0`. In `cp_w3`, 273 + 106 of 391 heavy-demand users did so. The rest were still on the
  sidewalk at 900 s, in transit.
- **b / bp.** Riders rejoin at M into `ap_end` lane 1 (straight) or lane 0 (right): 274 + 106 in `bp_w3`.
- **a + trigger.** It is not controlled.
  - Only 57 of 244 triggered vehicles (w2) and 44 of 225 (w3) got in.
  - About half entered through the end opening S3.
  - Right-turners dominate (straight vehicles must cross the right-turn lane within 20 m).
  - The opening at the sidewalk end must be one-way (sidewalk → road only), otherwise it becomes an entry.

### 3. Jamming at the merge

This is decided by right-of-way, not by width.
- **Yielding merge (`b`, `c`, `bt`, `ct`).** The sidewalk becomes a minor stream into a saturated road stream.
  - The head rider (straight) waits through the whole green for a gap and then sits through the red.
  - Riders behind it, including right-turners whose link is always `g`, are trapped single-file. In the `c_w2`
    trace every rider stayed at posLat 0.
  - Results: 500–640 s trip times, 360–680 s halting on the sidewalk, most riders not finished at 900 s, and
    spill-back to `up` lane 0 (compliant right time loss 33–95 s against 3 s).
  - This is the opposite of the field behaviour, where riders on the sidewalk gain.
- **Priority at an upstream merge (`bp`).** Riders flow (82–84 s), but road traffic yields to riders who
  *cross* the right-turn lane into lane 1 at M.
  - Compliant straight time loss: 196–220 s against 42 s.
  - 350–430 vehicles not inserted.
  - This is not usable.
- **Priority at the stop line (`cp`, `cpt`).**
  - It works mechanically: no jam teleports, sidewalk halting 10–18 s per user, ≥ 97 % finished.
  - Cost to the road: compliant straight time loss 59–84 s against 42 s; right-turn lane time loss 10–17 s
    against 3 s. Riders now enter `out_s_0` ahead of the road stream.
  - The 2 → 3 m width helps a little (cp: 97 → 89 s; road time loss 84 → 68 s).

### 4. Travel-time gain

It is small and set by the settings, not by the topology.
- At 5 m/s the 170 m sidewalk takes about 34 s; the road at free flow takes about 12 s. The mean road queue delay
  in this toy is only about 42 s.
- So with priority, riders reach 89–104 s against 85 s for `custom1` in `ctrl`: no gain.
- With 8.33 m/s (`cpf`) they reach 75–79 s, a gain of 6–10 s (7–12 %).
- The gain in the main net therefore depends on two unknowns:
  - the sidewalk riding speed: a vType or lane-speed parameter, which can be a calibration parameter;
  - the real queue delay.

## What a main-net patch needs (PLAN 1.4 `sidewalk.edg.xml` / `sidewalk.con.xml`)

### Topology (a), extra lane 0 on the existing approach edge

This is what the `apply_patches.py` docstring warns about:
- **Lane IDs.** Every lane index of the approach shifts by +1: `edge_0` becomes the sidewalk. This breaks:
  - `lane_widths_m` / `lane_movements` in `site.yaml` (lists by lane index);
  - the stop-line `instantInductionLoop` ids/lanes;
  - lateral-position references (`posLat` is relative to the lane, and the right edge of the road moves);
  - R37 (lane 0 = continuous right turn);
  - every lane-index-based metric (M-series per lane).
- **TLS link indices.** The sidewalk links are numbered first, so `ctrl` 0,1,2 became 2,3,4 in the toy. Every
  `signal.tll.xml` state string would change.
- **Lane-change openings.** These need segment splits of the approach edge, which creates new edge ids.

### Topology (c), separate `sw` edge to the stop line (recommended)

It avoids the lane shift: road lane IDs and indices, `lane_widths_m`, `lane_movements`, stop-line detectors and
lateral positions stay unchanged. What remains:
- **TLS link indices.** netconvert again numbers the new links first. They can be **pinned**: a
  `<connection from to fromLane toLane tl linkIndex>` in a `-i` tllogic file keeps the road links at their old
  indices and appends the sidewalk links. This was verified in the toy (`toy.pin.tll.xml`: road 0..2, sidewalk
  3, 4). `signal.tll.xml` would only gain 2 characters per state string per approach. Their state comes from the
  rule: right `g` always, straight `G` in the approach's through green.
- **Internal lane ids at J are renumbered.** In the toy the road ones moved from `:J_0_0`/`:J_1_x` to
  `:J_2_0`/`:J_3_x`. Code that names internal lanes must resolve them from connections, not from fixed ids; the
  `junction_geometry` box lanes should be checked.
- **Diverge node D.** The approach edge must be split there. That is a new node and an upstream edge id; the
  stop-line edge keeps its id if the split is named that way, which needs a check.
- **New conflicts at J.**
  - The sidewalk right link merges with the continuous right turn into the exit lane.
  - The sidewalk straight link merges into exit lane 0 and crosses nothing else in the toy. In the real
    4-arm junction it also meets crossing traffic and the right-turners of the left arm. Its foes must be
    checked in the main net.
- **Runtime.** A TraCI trigger (`queue_space_seeking`, `sidewalk`) does `setRoute` while the vehicle is upstream
  of D. The trigger must fire early enough for the rider to reach the rightmost lane before D. Lane 0 of `up`
  before D was a conflict point: 6 of the 14 junction collisions were at D's internal lanes (variants b, bt, ct,
  cp), and in `ct`/`cpt` some riders were triggered but did not reach `sw`.

## Recommendation

1. **Use topology (c) with priority (`cpt` = c + p + TraCI trigger)** if behaviour 7 is kept.
   - Do not use (a): lane-index shift, blocking of the right-turn lane by lane-change triggers, and an
     uncontrolled entry at the end opening.
   - Do not use (b): an upstream merge that yields jams; one with priority blocks the road.
2. **Model sidewalk use only through the TraCI trigger,** with its decision logged. Without it, SL2015 does not
   use the sidewalk.
3. **Treat sidewalk speed as a parameter** (lane speed or a `custom1` speedFactor on that edge) and report the
   travel-time gain as sensitive to it.
4. **Expect a small throughput cost** to the road through stream from priority riders at the stop line. Report it
   as a model consequence, not as a calibrated effect.
5. **Report no PET/TTC for the sidewalk** (PLAN 7). Vehicle–vehicle junction collisions at D and J are counted
   like every other collision (R28).

## Open questions for Viktor

1. **Approaches** (`f2_measured_approaches`): on which approaches do riders use the sidewalk?
2. **Start (diverge) point** per approach: distance from the stop line where riders get on the sidewalk, and
   whether it is a curb ramp, a driveway or any point.
3. **End (rejoin) point.**
   - Do straight riders come off at the corner and cut into the front of the straight queue at the stop line, as
     in topology c?
   - Or do they rejoin earlier, before the bollards?
   - Do right-turn riders go straight into the exit road?
   - How long are the bollards (TODO_MEASURE, see R37)?
4. **Usable sidewalk width** (`sidewalk_width_m`), minus trees, poles, parked motorcycles and vendors. Is it one
   rider wide or two?
5. **Typical riding speed on the sidewalk**, if it can be read from video. It decides the gain.
6. **When does it happen?** Only when the queue reaches past the start point, or also at short queues (sets the
   trigger threshold `q`)?
7. **Is the right-of-way at the rejoin point correct?** Do riders force in ahead of the road stream at the stop
   line (priority, as modelled in `cp`), or wait for gaps?

## Reproduce

```bash
cd SUMO
.venv/bin/python experiments/phase3b/sidewalk.py --nproc 11            # all 21 variants x heavy/light x seeds 1-3, 900 s (~13 min on 11 cores)
.venv/bin/python experiments/phase3b/sidewalk.py --variants ctrl cpt_w2 --demands heavy --seeds 1  # one quick check
```

Windows: `.venv/Scripts/python`. Results are deterministic: two full campaigns gave identical numbers for the
shared variants.
