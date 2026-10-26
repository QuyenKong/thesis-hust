"""Which wrong-lane dodges a junction allows (shared by the runtime rule `wrong_lane_dodge` and the validator, R27).

A dodge moves a vehicle from its lane i (whose markings permit its movement) to an adjacent lane j whose markings
(site `approaches[].lane_movements`, the M8 definition) do not permit it. It is usable only if lane j has a
connection to the vehicle's next edge that allows the vehicle's vClass; otherwise the vehicle would be stuck at the
end of lane j. The inputs are plain data so both sides can fill them: the runtime from TraCI (`lane.getLinks`, the
via lane's `lane.getAllowed`), the validator from the net file (sumolib connections, `Connection.allows`).
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


def usable_dodges(links_by_approach: dict[str, list[list[LaneLink]]], marks_by_approach: dict[str, list[list[str]]],
                  vclass: str) -> list[tuple[str, int, str, int]]:
    """Every (approach, lane, next edge, target lane) dodge a `vclass` vehicle could make: it drives a connection of
    lane i that allows it and that lane i's markings permit, and has a usable wrong adjacent lane."""
    out = []
    for app, links in links_by_approach.items():
        marks = marks_by_approach[app]
        for i, lane in enumerate(links):
            for lk in lane:
                if lk.allows(vclass) and lk.movement in marks[i]:
                    out += [(app, i, lk.to_edge, j) for j in dodge_targets(links, marks, i, lk.to_edge, vclass)[1]]
    return sorted(set(out))
