#!/bin/bash
# Quick run script - sets up if needed, then runs

cd "$(dirname "$0")"

# Setup if .venv doesn't exist
if [ ! -d ".venv" ]; then
    ./setup.sh
fi

source .venv/bin/activate
python -m gamemotion_backend.main --preview "$@"
