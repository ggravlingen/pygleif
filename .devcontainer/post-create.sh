#!/bin/sh
# Setup pre-commit

# Stop on errors
set -e

cd "$(dirname "$0")/../"

make sync

uv run pre-commit install
