# Task context

Mode: $mode
$mode_rules

## Intersection

$site

The site values above and the observation targets below are proxy values from the literature or assumptions
(evidence label per value), not field measurements of this intersection. Do not fit noise: the observed days
themselves differ (see R in the feedback).

## Behaviours in scope (10)

Group F1, signal non-compliance
1. Patience / red-light running: vType `impatience`, `jmDriveAfterRedTime`, `jmDriveRedSpeed`, `lcImpatience`.
2. Swarm pressure, red running in groups: rule `swarm_red_running`.
3. Early start before green: rule `early_start`.

Group F2, seeking space when queued (a long queue makes drivers look for other space to reach the queue head)
4. Lateral gap, encroachment, filtering: `minGapLat`, `latAlignment`, `lcSublane`, `lcPushy`,
   `lcMaxSpeedLatStanding`.
5. Wrong lane to dodge the signal: rule `queue_space_seeking`, option `p_wrong_lane`.
6. Straight vehicles blocking the continuous right-turn lane while the straight queue is long: rule
   `queue_space_seeking`, option `p_right_lane` (violator classes custom1 / custom2 only).
7. Riding on the sidewalk to pass the queue: rule `queue_space_seeking`, option `p_sidewalk` (custom1 only).

Group F3, interaction inside the junction
8. Risky gap acceptance, cutting in: `lcAssertive`, `lcPushyGap`, `jmTimegapMinor`, `tau`.
9. Illegal left turn that waits inside the junction box until the opposing straight green ends: the custom1
   archetypes of the `moto_violator` distribution (their `jm*` attributes) and rule `illegal_left_box`.
10. Slow motorcycles riding in the lane centre: `speedFactor`, `speedDev` (own archetype) and rule
    `slow_lane_center`.

Right turns from the continuous right-turn lane during red are legal here and are not violations. Wrong-way
driving is not modelled.

Vehicle classes: `passenger` (cars, distribution `car`), `motorcycle` (distribution `moto`), `custom1` (violating
motorcycles: distribution `moto_violator` = the illegal-left riders, or `moto` = straight riders that may seek
space), `custom2` (violating cars: distribution `car_violator` (unused by the demand) or `car`). The demand
references the distributions `car`, `moto`, `moto_violator`; each needs at least one archetype.

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
