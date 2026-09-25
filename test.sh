#!/usr/bin/env bash
# One-command smoke test runner (headless).
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
    python3 -m venv .venv
    .venv/bin/python -m pip install --disable-pip-version-check -q -r requirements.txt
fi

exec .venv/bin/python -m unittest discover -s tests -v
