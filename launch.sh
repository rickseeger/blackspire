#!/usr/bin/env bash
# One-command launcher for the Black Spire slice.
# Creates a local virtualenv (if needed), installs the one dependency, and
# runs the game.  Any extra args (e.g. --frames 30, --scene road, --list)
# are forwarded to the app.
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
    python3 -m venv .venv
fi

.venv/bin/python -m pip install --disable-pip-version-check -q -r requirements.txt
exec .venv/bin/python -m black_spire "$@"
