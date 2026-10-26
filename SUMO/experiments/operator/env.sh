# Sourced by the operator scripts: cd to SUMO/ and pick the venv python on Linux (.venv/bin) or Windows Git Bash
# (.venv/Scripts), so the scripts run unchanged on both.
cd "$(dirname "${BASH_SOURCE[0]}")/../.." || exit 1
PY=.venv/bin/python; [ -x "$PY" ] || PY=.venv/Scripts/python
