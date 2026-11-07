"""Which wrong-lane dodges a junction allows (shared by the `wrong_lane` option of the runtime rule
`queue_space_seeking` and the validator, R27).

A dodge moves a vehicle from its lane i (whose markings permit its movement) to a lane j whose markings (site
`approaches[].lane_movements`, the M8 definition) do not permit it. Two kinds:

- through dodge: j is adjacent to i and has a connection to the vehicle's next edge that allows the vehicle's vClass,
  so the vehicle leaves the approach from lane j (none on the proxy net, R27);
- cut-back dodge (owner decision 2026-11-04, site `violator_turn_lanes`): j is listed for the movement in
  `violator_turn_lanes` (left from lane 0, U-turn from lanes 0 and 1, Viktor 2026-10-29), j has no connection to the
  next edge, the movement is not banned on the approach, and the marked lane i has a connection to the next edge that
  allows the vClass. The vehicle rides lane j and cuts back to lane i before the stop line (the rule's job); without
  a connection it would otherwise stop at the end of lane j.

The inputs are plain data so both sides can fill them: the runtime from TraCI (`lane.getLinks`, the via lane's
`lane.getAllowed`), the validator from the net file (sumolib connections, `Connection.allows`).
"""

from __future__ import annotations

from dataclasses import dataclass

MOVEMENT_OF_DIR = {"r": "r", "s": "s", "l": "l", "t": "u", "L": "l", "R": "r"}  # SUMO link dir -> lane_movements code


@dataclass(frozen=True)
class LaneLink:
    to_edge: str
    direction: str
    allowed: frozenset[str] | None  # vClasses the connection allows; None = no restriction known

    def allows(self, vclass: str) -> bool:
        return self.allowed is None or vclass in self.allowed

    @property
    def movement(self) -> str:
        return MOVEMENT_OF_DIR[self.direction]


def dodge_targets(links: list[list[LaneLink]], marks: list[list[str]], idx: int, next_edge: str,
                  vclass: str) -> tuple[list[int], list[int]]:
    """(wrong adjacent lanes, those of them usable) for a `vclass` vehicle in lane `idx` heading to `next_edge`.
    `links[k]` = the connections of lane k of the approach, `marks[k]` = its permitted movements."""
    mv = next((lk.movement for lane in links for lk in lane if lk.to_edge == next_edge), None)
    if mv is None:
        return [], []
    wrong = [j for j in (idx - 1, idx + 1) if 0 <= j < len(links) and mv not in marks[j]]
    usable = [j for j in wrong if any(lk.to_edge == next_edge and lk.allows(vclass) for lk in links[j])]
    return wrong, usable


def cut_back_targets(links: list[list[LaneLink]], marks: list[list[str]], idx: int, next_edge: str, vclass: str,
                     turn_lanes: dict[str, list[int]] | None, banned: frozenset[str] = frozenset()) -> list[int]:
    """Cut-back wrong lanes (module docstring) for a `vclass` vehicle heading to `next_edge` whose marked lane is
    `idx`. `turn_lanes` = site `violator_turn_lanes` (movement -> lane indices), `banned` = movements banned on the
    approach ('l' with left_turn_banned, 'u' with u_turn_banned)."""
    if not turn_lanes:
        return []
    mv = next((lk.movement for lane in links for lk in lane if lk.to_edge == next_edge), None)
    if mv is None or mv in banned or mv not in marks[idx] \
            or not any(lk.to_edge == next_edge and lk.allows(vclass) for lk in links[idx]):
        return []
    return [j for j in turn_lanes.get(mv, ()) if 0 <= j < len(links) and j != idx and mv not in marks[j]
            and not any(lk.to_edge == next_edge for lk in links[j])]


def usable_dodges(links_by_approach: dict[str, list[list[LaneLink]]], marks_by_approach: dict[str, list[list[str]]],
                  vclass: str, turn_lanes: dict[str, list[int]] | None = None,
                  banned_by_approach: dict[str, frozenset[str]] | None = None) -> list[tuple[str, int, str, int]]:
    """Every (approach, lane, next edge, target lane) dodge a `vclass` vehicle could make: it drives a connection of
    lane i that allows it and that lane i's markings permit, and has a usable wrong adjacent lane or (with
    `turn_lanes`) a cut-back wrong lane."""
    out = []
    for app, links in links_by_approach.items():
        marks = marks_by_approach[app]
        banned = (banned_by_approach or {}).get(app, frozenset())
        for i, lane in enumerate(links):
            for lk in lane:
                if lk.allows(vclass) and lk.movement in marks[i]:
                    out += [(app, i, lk.to_edge, j) for j in dodge_targets(links, marks, i, lk.to_edge, vclass)[1]]
                    out += [(app, i, lk.to_edge, j)
                            for j in cut_back_targets(links, marks, i, lk.to_edge, vclass, turn_lanes, banned)]
    return sorted(set(out))


def banned_movements(approach: dict) -> frozenset[str]:
    """Movements banned on a site approach (its `left_turn_banned` / `u_turn_banned`)."""
    return frozenset(m for m, key in (("l", "left_turn_banned"), ("u", "u_turn_banned")) if approach.get(key))
