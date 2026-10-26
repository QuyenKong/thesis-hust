"""Load the YAML config files.

The site file is the only place field data lives. `load_site()` with no argument always reads the
measured file `config/site.yaml`; a literature proxy is used only when its path is passed explicitly,
and every Site carries `.source` ("MEASURED" or "LITERATURE_PROXY") so runs can record it.
A required value that is still `null` raises `MissingFieldDataError`; there is no fallback default.
"""

from __future__ import annotations

from fnmatch import fnmatchcase
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO_ROOT / "config"
SITE_SOURCES = ("MEASURED", "LITERATURE_PROXY")
# `<key>_evidence` vocabulary (ruling R13) of values standing in for field data (proxy site file, proxy targets)
EVIDENCE = ("literature", "literature_transferred", "assumed")
# a modelling choice (TODO_DECIDE in site.yaml) settled by an experiment of this repo; allowed only on these keys
EXPERIMENT_EVIDENCE = "experiment"
EXPERIMENT_EVIDENCE_KEYS = ("illegal_left.mode",)  # PLAN Phase 3 decision (experiments/phase3)
# a fact Viktor confirmed in the field (PLAN 0 "Hạ tầng đã xác nhận") but has not measured; only on these keys
# (fnmatch patterns, `*` = a list index)
FIELD_OBSERVATION_EVIDENCE = "field_observation"
FIELD_OBSERVATION_EVIDENCE_KEYS = ("approaches.*.continuous_right_lane", "approaches.*.right_lane_separator")


def allowed_evidence(dotted_key: str) -> tuple[str, ...]:
    """Evidence labels a proxy site value at `dotted_key` may carry."""
    return (EVIDENCE + ((EXPERIMENT_EVIDENCE,) if dotted_key in EXPERIMENT_EVIDENCE_KEYS else ())
            + ((FIELD_OBSERVATION_EVIDENCE,) if any(fnmatchcase(dotted_key, k)
                                                    for k in FIELD_OBSERVATION_EVIDENCE_KEYS) else ()))


class MissingFieldDataError(ValueError):
    """A required site value is still `null` (TODO_MEASURE)."""

    def __init__(self, key: str, path: Path):
        self.key = key
        self.path = path
        super().__init__(
            f"{key} is null in {path} (TODO_MEASURE). Measure it, or pass a proxy site file "
            f"explicitly (e.g. --site config/site.proxy.yaml); no default is substituted."
        )


class Site(dict):
    """Site config as a dict, plus `.source`, `.path` and `require()`."""

    def __init__(self, data: dict, path: Path):
        super().__init__(data)
        self.path = path
        self.source: str = data["site_source"]

    def require(self, dotted_key: str) -> Any:
        """Value at `dotted_key` (integer parts index lists); raise if it is `null`."""
        node: Any = self
        for part in dotted_key.split("."):
            try:
                node = node[int(part)] if isinstance(node, list) else node[part]
            except (KeyError, IndexError, ValueError, TypeError):
                raise KeyError(f"{dotted_key!r} not found in {self.path}") from None
        if node is None:
            raise MissingFieldDataError(dotted_key, self.path)
        return node


def _read_yaml(path: Path) -> dict:
    with Path(path).open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a YAML mapping at top level")
    return data


def load_site(path: Path | None = None) -> Site:
    """Load the site file (default: the measured `config/site.yaml`)."""
    path = Path(path) if path is not None else CONFIG_DIR / "site.yaml"
    data = _read_yaml(path)
    source = data.get("site_source")
    if source not in SITE_SOURCES:
        raise ValueError(f"{path}: top-level site_source must be one of {SITE_SOURCES}, got {source!r}")
    return Site(data, path)


def load_experiment(path: Path | None = None) -> dict:
    return _read_yaml(Path(path) if path is not None else CONFIG_DIR / "experiment.yaml")


def load_llm(path: Path | None = None) -> dict:
    return _read_yaml(Path(path) if path is not None else CONFIG_DIR / "llm.yaml")
