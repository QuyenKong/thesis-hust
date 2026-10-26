# Proxy observed-data targets: sources

Research for `data/proxy/targets.yaml`, which drives the generator `thesis_sumo.proxy.generate`
(days `data/observed/PROXY_D1 … PROXY_D5`). Done 2026-10-25 (Task 6).

**These are not field measurements.** They are numbers from published studies of other places, or stated
assumptions. They stand in for Viktor's video until it exists. `config/site.yaml` keeps
`null # TODO_MEASURE`. Every result built on these days is `site_source: LITERATURE_PROXY`.

Evidence labels (ruling R13):
- `literature`: a published source states the value for this site and quantity.
- `literature_transferred`: the value is taken from a source but transferred across site, denominator or
  country. A `transfer_note` in targets.yaml says how.
- `assumed`: no source was found, or an assumption sets the number.

No target is plain `literature`: every sourced number was measured somewhere else, so all of them are
`literature_transferred`.

Source ids `[S..]` are in `docs/research/proxy_sources.md` (Task 1). Ids `[T..]` are at the end of this file.

No source gives any of these quantities for **Le Van Luong x Hoang Dao Thuy**. The closest data come from:
- Lang Ha x Lang [S5], on the same Lang Ha / Le Van Luong corridor, also 3 lanes on the major road;
- Ho Chi Minh City saturation-flow surveys [T1];
- Hanoi motorcycle speed and headway studies [T2].

## 1. Targets

| Metric | Target | Value | Evidence | Source |
|---|---|---|---|---|
| G0 | approach volume (veh/h) | LVL_W 2620, LVL_E 2130, HDT_N 1800, HDT_S 1630 (total 8180) | assumed | total from [S5] Lang Ha x Lang (16352 veh in 2 h of video); split assumed |
| G0 | between-day CV of volume | 0.087 (normal), one factor for all approaches | literature_transferred (North America) | [T6] Abdy & Hellinga 2007 (COV 5.4–13.1 %, mean 8.7 %; Sullivan 2006 mean 8.9 %) |
| G0 | motorcycle share | 0.865 | literature_transferred (other junction) | [S5] 14148 / 16352 |
| G0 | movement split | s 0.70, r 0.15, l 0.10, u 0.05 (banned-left approach: s 0.80, r 0.15, u 0.05) | assumed | no turning count found |
| G0 | 15-min profile | flat | assumed | [S5]: "traffic volume do not change much" in the peak |
| M1 | motorcycle saturation headway (whole 10.5 m approach) | 0.254 s, lognormal cv 0.56 | literature_transferred (HCMC, width-scaled; cv from mid-block headways) | [T1] mixed MC/car flow, 11.5 m approach: 15525 veh/h of green, scaled by width; cv from [T2] (1.16 ± 0.65 s) |
| M1 | car / motorcycle headway | 1.4 | literature_transferred (HCMC) | [T1] f_PC: each 1 % of cars lowers saturation flow by 0.4 % |
| M1 | start-up ramp | headway × (1 + 1.0·exp(−(n−2)/3)) | assumed | [T1]: the flow peaks 6–12 s into green |
| M2 | early-start share (crossing before green) | LVL motorcycle 9.45 %, car 0.27 %; HDT motorcycle 15.82 %, car 0.68 % | literature_transferred (other junction; LVL uses the major-through subset, HDT all flows; share of the approach total) | [S5] Table 3 site 1 major through (LVL); Table 2 site 1 all flows (HDT) |
| M2 | early-start lead | crossing U(4, 10) s before green | assumed | [S5] defines early departure as starting ≥ 5 s before green |
| M2 | first-crossing delay after green | 1.2 s, lognormal cv 0.4 | assumed | [T1]: queues with motorcycles in front discharge at > 14000 veh/h within 2 s; [S13] gives 3.3 s for queues with a car in front |
| M3 | red-running share | LVL motorcycle 6.49 %, car 0.27 %; HDT motorcycle 11.06 %, car 0.50 % | literature_transferred (as M2) | [S5] Table 3 / Table 2 (mapping to approaches assumed) |
| M3 | per-cycle variance / mean | 1.3 (negative binomial) | assumed | [S5] "distributed nearly even among cycles" against conformity effects [T4] |
| M3 | timing | cars: within 2 s after yellow; motorcycles: half within 2 s, half in mid-red in clusters (mean size 2) | assumed (cars only qualitative in [S5]) | [S5]; [T4] (+33 % hazard when others run); [T5] (61 % of red runners are opportunistic) |
| M4 | motorcycles waiting past the stop line | 63 % of halting motorcycles | literature_transferred (Malaysia) | [T3] > 63 % of 4133 motorcycles; also [T5] |
| M4 | overshoot depth | U(0, 4) m | assumed | crosswalk strip in front of the stop line |
| M4 | lateral position | lane band from movement and lane markings, uniform in the band (motorcycles), lane centre ± 0.3 m (cars) | assumed | no Hanoi lateral distribution found; motorcycle half-width 0.32 m from [T2] |
| M5 | queue footprint | motorcycle 2.6 m², car 17.4 m² | assumed (motorcycle from literature dimensions) | [T2] paired-motorcycle lateral spacing 1.10 m, length 1.87 m (+ 0.5 m gap, assumed) |
| M6 | approach speed | motorcycle 27.3 ± 5.2 km/h, car 25 ± 5 km/h | literature_transferred (motorcycle: mid-block speeds), assumed (car) | [T2] Hanoi spot speeds |
| M6 | in-junction speed | motorcycle 21.3 ± 5.1 km/h, car 20 ± 4 km/h | literature_transferred (motorcycle: undivided mixed road), assumed (car) | [T2] |
| M6 | path lengths | s 40.6, r 13.1, l 40.9, u 15.9, illegal_l 36.5 m | assumed | internal-lane lengths of the proxy net (OSM geometry) |
| M7a | halting illegal lefts in the box at the opposing green end | mean 6 per cycle (entrants 7.5, var/mean 1.5) | assumed | [S5] qualitative only: "a large amount of motorcycle … wait for passing when time phase changes" |
| M7a | early leavers (through gaps) | 20 % of entrants | assumed | [S5] "whenever they find an acceptable time gap" |
| M7b | clear lag (PET proxy, definition below) | 5.65 s, lognormal cv 0.5 | assumed (built on a literature PET) | [T7] mean PET of left-turn crossing conflicts 2.15 s, + 2.0 s and + 1.5 s travel offsets (assumed) |
| M7a | box exit headway | 0.5 s, cv 0.56 | assumed | lower bound 0.37 s from [T1] (3.5 m stream) |
| M7c | crossing-road start delay per box waiter | 0.3 s / vehicle | assumed | no measurement found |
| M8 | wrong-lane share of turning vehicles | motorcycle 0.25, car 0.05 | assumed | no measured share; weak lane discipline suggested by motorcyclist turn-signal use of only 40 % in Da Nang [T8] |
| M8 | lane markings (`lane_movements`, site.proxy.yaml) | lane 0: r, s; lane 1: s; lane 2: s, l, u (LVL_W: s, u) | assumed | OSM approach ways have no `turn:lanes`; follows the netconvert connection layout |

Between-day variation of the behaviour targets is ±8–12 % (CV), **assumed** (spec 4.2), except for the
volume CV, which is from [T6]. Each day draws one lognormal factor per target from its own seed (101–105).
The CLI then divides each target's factors by their mean over D1–D5 (`campaign_day_factors`), so the 5-day
mean equals the targets.yaml value by construction. The rescaling is common to all days, so it keeps the CV
of the factors. The factors are written to each day's `manifest.json` (`day_factors`, `day_factors_normalised`).
As a result, the days are independent in their events but not in their day-level means.

## 2. Definitions the generator assumes (Task 10 must use the same)

The tables follow `schema_observed` and `sim.outputs`. On top of those, the generator builds some quantities
that are defined only in this file, and they must be computed the same way on both sides:

- **M1**: headway of queue position n is the time since the previous stop-line crossing of the same approach,
  over all lanes. The queue at a green onset is the set of vehicles in that cycle's `lateral_snapshots`. The
  first `len(queue)` crossings at or after the onset are the discharge.
- **M2 / M3**: a crossing in `r` that lies at most **N = 10 s** before the next green onset of its approach is an
  early start. Any other crossing in `r` is red running. Red crossings after the last observed onset cannot be
  classified (the next onset is outside the window).
- **Continuous right-turn lane** (Task F2-net, PLAN 0: every approach has one, so a right turn on red is not a
  violation): the right turns (movement `r`) of approaches with `continuous_right_lane: true` are not signal
  controlled. They are neither early starts nor red runners and are left out of the M2/M3 shares (numerator and
  denominator), the M2 first-crossing delay (and M7c), the M1 queue and discharge, and the M4 rows
  (`metrics.common.uncontrolled_tracks`). The generator lets them cross at their unimpeded arrival time, never
  queues them, and draws red runners / early starters only from the other vehicles, with per-cycle counts =
  target share x the approach's rate without them. **The target values are unchanged.** [S5] gives the shares
  per approach (LVL: major-through subset, HDT: all flows), so for LVL the denominator already had no right
  turners, but for HDT the [S5] denominator contained right turners that our definition now drops. Applied to
  the smaller denominator, the HDT shares imply fewer red runners / early starters per cycle than before. Whether
  [S5]'s right turners were signal controlled is not stated, so this is flagged, not rescaled: with field data
  the shares are measured on our definition directly.
- **M7b**: the clear lag is computed per `box_queue` row. It is the first box exit (`traversals.t_exit` of
  `illegal_l`) at or after `t`, among the vehicles that entered in that cycle, minus `max(t, last stop-line
  crossing of the opposing approach's straight movement before that exit)`. Tier-1 tables have no positions
  inside the junction, so this is a table-level stand-in for PET. A true PET needs trajectories (video tier 2)
  or SUMO SSM output.
- **M7c**: the delay from the crossing road's green onset to its first stop-line crossing, regressed on
  `n_waiting_in_box` of the last `box_queue` row before that onset.
- **M8**: the lane of a vehicle is found from `lat_m_at_stopline` and the cumulative lane widths. The share
  counts only **turning** vehicles (r, l, u). `illegal_l` is permitted in no lane, so it is left out.
- **box_queue**: a vehicle is halting in the box once it has been there for `HALT_LEAD_S` = 3 s.
- **lateral_snapshots**: at a green onset, the rows are the queue (behind the line and overshooting) plus the
  halting illegal lefts still in the box (past the stop line, at −40…−60 % of the illegal-left path,
  assumed). This matches `sim.outputs`. On the generated days, box waiters at an onset of their own approach
  do not occur, because the box clears before the next LVL_W green. The M1 queue therefore excludes snapshot
  vehicles that crossed before the onset.

## 3. What the generated days look like (D1–D5, derived, not inputs)

The raw 5-day means are compared with the **nominal** targets.yaml values at 15 % (`tests/test_proxy.py`).
- After Task F2-net (continuous right turns excluded, which also changed the generator's random stream), three
  checks are strict `xfail` because of noise: car red running pooled −45 % (~20 events in 5 days, Poisson SE
  ~21 %; it was +18.3 % before), car early start pooled −19 % and LVL_W motorcycle red running +17.6 %.
  `SUMO/experiments/proxy_bias/bias_check.py 200` (200 independent 5-day campaigns, result in
  `result_200.txt`): relative error mean / SD / min / max — motorcycle red running LVL_W +0.1 % / 4.5 % / −15.1 % /
  +12.8 %, LVL_E −0.1 % / 4.6 %, HDT_N +2.9 % / 4.6 %, HDT_S +3.3 % / 4.7 %; car red running −4.3 % / 28 %; car
  early start −2.7 % / 25 %. So the car shares and LVL motorcycle shares are unbiased, the HDT motorcycle red-running
  share runs ~3 % high (SE 0.3 %; inside the 15 % tolerance), and the committed D1–D5 LVL_W value (+17.6 %) is a
  rare draw beyond all 200 campaigns (Viktor decides whether to keep it; seeds are not re-rolled silently).
- Motorcycle M2/M3 shares: early start −1 … +2 %; red running LVL_E +7 %, HDT_N −11 %, HDT_S +13 %.
- The other targets pass at 15 % (`tests/test_proxy.py`); before Task F2-net their largest gaps were car
  wrong-lane share +8 % and M7c slope −6 %, everything else within ±4 % (not re-listed after F2-net).

Derived quantities (no target, reported for transparency):

| Quantity | D1–D5 |
|---|---|
| Vehicles per day (stop-line crossings, 3600 s) | 7602–9099 |
| Illegal lefts | 224 per hour |
| Queue length at green onset (behind the stop line) | mean 11–13 m, max 24 m; never censored at 80 m |
| Halting vehicles behind the line at green onset | 4–5 cars and 6–9 motorcycles; another ~63 % of the motorcycles wait past the line |
| Motorcycle density in `queue_snapshots` (n_moto / area_m2) | ≈ 0.06–0.07 per m² (the queue area is mostly cars, because motorcycles fill the front) |
| Lateral position of halting motorcycles | mean 5.3 m, quartiles 2.3 / 5.4 / 8.3 m of 10.5 m |
| Approach time (range entry → stop line) | motorcycle mean 27 s (median 19 s), car mean 33 s (median 24 s) |
| Junction time (stop line → outbound lane) | s 7.4 s, l 7.5 s, r 2.4 s, u 2.9 s, illegal_l 48 s (includes the box wait) |
| Box | `n_waiting` mean 6.0, var 7.8, max 13; `t_clear_end − t` mean 9.5 s |

These are proxy outcomes, not checks of realism. The queue is short and dense because the motorcycle
discharge at [T1] saturation flows is very fast. SUMO's default queues are expected to be longer.

## 4. Limitations

- No number here was measured at Le Van Luong x Hoang Dao Thuy. Sources are other Hanoi junctions [S5], HCMC
  [T1], Malaysia [T3], Taiwan [T7] and North America [T6].
- The day factors are normalised over D1–D5, which couples the calibration and validation days through
  their mean. Their spread is unchanged.
- One generator produces all five days. D4–D5 validation on proxy data is therefore weaker than validation
  on real days (spec item 10). The noise floor `d_day_day` comes from the assumed between-day CVs, so R is
  illustrative only (spec item 7).
- Many behaviour targets are `assumed`, and the report keeps them apart from the `literature` ones (spec item 8).
- The volumes are ~2× the SYNTHETIC days. If B0 cannot serve them (for example, permissive lefts in lane 2
  blocking straight traffic), the G0 gate fails. That would be a finding, not a reason to change the targets.

## 5. Sources

- [T1] Vu Anh Tuan, Nguyen Dinh Vinh Man (2015). "Mixed Traffic Saturation Flows of Signalized Intersections in
  Motorcycle Dominant Cities". *Proc. EASTS* 10. https://easts.info/on-line/proceedings/vol10/pdf/1246.pdf.
  Used: §4.4 (Nguyen Thai Hoc, 11.5 m, motorcycle-car flow, peak 26730 and sustained 15525 veh/h of green),
  §4.6 (An Duong Vuong, 14000 within 2 s), Table 6 (3.5 m: 9650 veh/h of green), eq. 4 (f_PC).
- [T2] Chu Cong Minh, Shoji Matsumoto, Kazushi Sano (2005). "The Speed, Flow and Headway Analyses of Motorcycle
  Traffic". *J. EASTS* 6, 1496–1508. https://www.jstage.jst.go.jp/article/easts/6/0/6_0_1496/_pdf.
  Used: Table 1 (1.87 × 0.64 m), §4.2 (27.3 ± 5.2 km/h), conclusions (21.3 ± 5.1 km/h mixed traffic,
  headway 1.16 ± 0.65 s), §4.3 (paired lateral distance 1.10 m in mixed traffic).
- [T3] Syed Tajul Arif, Harun (2023). "Motorcyclists' Stopping Position at 4-Legged Signalised Intersections".
  *Construction* 3(2), 163–171, Universiti Malaysia Pahang. https://journal.ump.edu.my/construction/article/view/9595.
  Read from the abstract only, because the journal server refused the connection. The full author names
  are not verified.
- [T4] "Red-light running behavior of delivery-service e-cyclists based on survival analysis" (Shanghai):
  violation hazard +33 % when others violate. SWOV library record
  https://swov.nl/en/publicatie/red-light-running-behavior-delivery-service-e-cyclists-based-survival-analysis.
  Known from the abstract via search only; the authors are not verified. It concerns e-cyclists, not
  motorcycles.
- [T5] Phuengprachuab P., Jantosut P., Satiennam W., Satiennam T. (2022). "The Opportunistic Red-Light Running
  Behavior of Motorcyclists". *KKU Research Journal (Graduate Studies)* 23(2).
  https://ph02.tci-thaijo.org/index.php/gskku/article/view/246474.
- [T6] Zeeshan Abdy, Bruce Hellinga (2007). "Day-to-Day Variability of Signalized Intersection Performance
  during the Peak Hour". *Proc. ITE Canadian District Annual Conference*, Toronto.
  https://www.civil.uwaterloo.ca/bhellinga/publications/Publications/ITE-2007%20Variability%20of%20Peak%20Hour%20Volumes.pdf
- [T7] Hsu T.-P., Chao S.-Y., Hsiao W.-L. (2024). "Effect Analysis of the V2X Motorcycle Safety Warning System
  on Collision Prevention at Intersections – Results of Field Trial". *J. EASTS* 15, 2595–2605.
  https://doi.org/10.11175/easts.15.2595. Used: mean PET of left-turn crossing conflicts 2.15 s before the
  system was installed.
- [T8] "Turn signal use among car drivers and motorcyclists at intersections: a case study of Da Nang, Vietnam"
  (RMIT repository): motorcyclists 40.13 % and car drivers 68.27 % at 24 sites.
  https://research-repository.rmit.edu.au/articles/journal_contribution/Turn_signal_use_among_car_drivers_and_motorcyclists_at_intersections_a_case_study_of_Da_Nang_Vietnam/27520884.
  Known from the search abstract only.
- [S5] Mai, Chu, Vu (2019), EASTS proceedings 12 (see proxy_sources.md). Re-read in full for this task. Used:
  Table 2, Table 3, and the early-departure definition (≥ 5 s before green). Car red runs happen "right after
  the end of yellow time", motorcycles also in mid-red. Violations are "distributed nearly even among
  cycles". Motorcycles wait in the middle of the junction.
- [S13] Torquato et al. (2020), citing Nakatsuji et al. (2001) and Minh & Sano (2003) (see proxy_sources.md).

Searched without a usable result: turning-movement counts or volumes at LVL x HDT (news gives congestion
only); motorcycle queue density per m² in Hanoi; wrong-lane shares; a numeric count of box waiters; PET for
Vietnamese junctions; per-day variation of violation rates.
