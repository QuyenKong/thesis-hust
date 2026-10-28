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

## Behaviours in scope (10)

Group F1, signal non-compliance
1. Patience / red-light running: vType `impatience`, `jmDriveAfterRedTime`, `jmDriveRedSpeed`, `lcImpatience`.
2. Swarm pressure, red running in groups: rule `swarm_red_running`.
3. Early start before green: rule `early_start`.

Group F2, seeking space when queued (a long queue makes drivers look for other space to reach the queue head)
4. Lateral gap, encroachment, filtering: `minGapLat`, `latAlignment`, `lcSublane`, `lcPushy`,
   `lcMaxSpeedLatStanding`.
5. Wrong lane to dodge the signal: rule `queue_space_seeking`, option `p_wrong_lane`.
6. Straight vehicles waiting at red in the continuous right-turn lane (lane 0), blocking the right turns: going
   straight from lane 0 is legal on green (no separator), so these vehicles come from the ordinary lane choice of the
   vTypes and the queue; option `p_right_lane` does not exist on this site (its probability is redistributed to the
   other options of `queue_space_seeking`).
7. Riding on the sidewalk to pass the queue: rule `queue_space_seeking`, option `p_sidewalk` (custom1 only;
   only on the approaches with a rideable sidewalk, LVL_W and LVL_E).

Group F3, interaction inside the junction
8. Risky gap acceptance, cutting in: `lcAssertive`, `lcPushyGap`, `jmTimegapMinor`, `tau`.
9. Illegal left turn from HDT_N and HDT_S (left turn banned there) that enters on the HDT_green stage and waits
   inside the junction box until the opposing straight green ends: the custom1 archetypes of the `moto_violator`
   distribution (their `jm*` attributes) and rule `illegal_left_box`.
10. Slow motorcycles riding in the lane centre: `speedFactor`, `speedDev` (own archetype) and rule
    `slow_lane_center`.

Not violations: right turns from the continuous right-turn lane (every approach) at any time, and left turns
and U-turns from LVL_W and LVL_E on their own LVL_left arrow. Wrong-way driving is not modelled.

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

Return one JSON object with `driver_archetypes`, `traci_rules` and optionally `description`, following this
JSON schema:

```json
$schema
```
