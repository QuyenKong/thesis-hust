# Task context

Mode: $mode
$mode_rules

## Intersection

$site

The site values above and the observation targets below are proxy values from the literature or assumptions
(evidence label per value), not field measurements of this intersection. Do not fit noise: the observed days
themselves differ (see R in the feedback).

Signal stages (one cycle): LVL_straight (straight from LVL_W and LVL_E), LVL_left (protected left-turn and U-turn
arrow for LVL_W and LVL_E together, LVL straight red), HDT_green (HDT_N and HDT_S together); each stage is followed
by its yellow and all-red interval. HDT_N and HDT_S face each other: each is the other's opposing approach.

## Behaviours in scope (11)

Group F1, signal non-compliance
1. Patience / red-light running: vType `impatience`, `jmDriveAfterRedTime`, `jmDriveRedSpeed`, `lcImpatience`.
2. Swarm pressure, red running in groups: rule `swarm_red_running`.
3. Early start before green: rule `early_start`.

Group F2, seeking space when queued (a long queue makes drivers look for other space to reach the queue head)
4. Lateral gap, encroachment, filtering: `minGapLat`, `latAlignment`, `lcSublane`, `lcPushy`,
   `lcMaxSpeedLatStanding`.
5. Wrong lane to dodge the queue: rule `queue_space_seeking`, option `p_wrong_lane`. On this site a queued
   left-turner (LVL_W, LVL_E) rides lane 0 and a queued U-turner (every approach) rides lane 0 or 1, past the queue of
   lane 2 (the lane marked for its movement), and cuts back into lane 2 over the continuous right-turn stretch before
   the stop line. Until it gets into lane 2 it stands at the head of lane 0 or 1, where it holds up right-turners or
   straight vehicles behind it (behaviour 6, and behaviour 11 for a standing U-turner).
6. Vehicles going straight, left or U-turn that stand waiting at red in lane 0 over the continuous right-turn stretch
   (the last metres before the stop line, given per approach below), blocking the right turns. Driving through lane 0 is
   legal, going straight from it on green is legal, and upstream of the stretch lane 0 is an ordinary lane. These
   vehicles come from SUMO's own lane choice and the queue, and from the wrong-lane riders of behaviour 5; left
   turns and U-turns enter the junction from lane 2 only.
   Option `p_right_lane` does not exist on this site (its probability is redistributed to the other options of
   `queue_space_seeking`).
7. Riding on the sidewalk to pass the queue: rule `queue_space_seeking`, option `p_sidewalk` (custom1 only;
   only on the approaches with a rideable sidewalk, LVL_W and LVL_E).

Group F3, interaction inside the junction
8. Risky gap acceptance, cutting in: `lcAssertive`, `lcPushyGap`, `jmTimegapMinor`, `tau`.
9. Illegal left turn from HDT_N and HDT_S (left turn banned there) that enters on the HDT_green stage and waits
   inside the junction box until the opposing straight green ends: the custom1 archetypes of the `moto_violator`
   distribution (their `jm*` attributes) and rule `illegal_left_box`.
10. Slow motorcycles riding in the lane centre: `speedFactor`, `speedDev` (own archetype) and rule
    `slow_lane_center`.

Group F2, continued (observed at the site, not from the literature)
11. Passing a standing U-turner: a vehicle held behind a U-turner that stands in the same stop-line lane while the
    held vehicle's own movement has green squeezes past it or moves to the next lane: rule `uturn_bypass` (`p` =
    probability that a held vehicle does so, `t_wait` = how long it stands behind the U-turner first). Observed:
    most motorcycles pass a standing U-turner, cars rarely do.

Not violations: right turns from the continuous right-turn lane (every approach) at any time, and left turns
and U-turns from LVL_W and LVL_E on their own LVL_left arrow from the lanes marked for them. A U-turn on a red arrow
is red-light running. Wrong-way driving is not modelled.

Vehicle classes: `passenger` (cars, distribution `car`), `motorcycle` (distribution `moto`), `custom1` (violating
motorcycles: distribution `moto_violator` = the illegal-left riders from HDT_N and HDT_S, or `moto` = straight
riders that may seek space), `custom2` (violating cars: distribution `car_violator` (unused by the demand) or
`car`). The demand references the distributions `car`, `moto`, `moto_violator`; each needs at least one archetype.

## Parameter dictionary

### vType attributes (set in an archetype's `params`)

$vtype_params

### TraCI rules (`rule_type`, `params`; all listed params are required unless marked optional)

$rule_params

## Observation targets (calibration days, pooled)

$targets

## Output

Return one JSON object with `driver_archetypes`, `traci_rules` and optionally `description`, nothing else. Shape
(the ids, values and the two entries are only an illustration; use the attributes, rules and ranges of the parameter
dictionary):

```json
{"description": "one sentence on the idea of the spec",
 "driver_archetypes": [
  {"id": "moto_a", "base_vclass": "motorcycle", "distribution": "moto", "share": 0.7,
   "params": {"tau": 1.0, "minGapLat": 0.6}, "rationale": "metric it targets and why"}],
 "traci_rules": [
  {"rule_type": "early_start", "applies_to": ["moto_a"], "params": {"t_before_green": 2, "p": 0.1, "v_max": 2},
   "rationale": "metric it targets and why"}]}
```

Every archetype has `id`, `base_vclass`, `distribution`, `share`, `params`, `rationale`; every rule has `rule_type`,
`applies_to` (archetype ids), `params` (all its required parameters), `rationale`.
