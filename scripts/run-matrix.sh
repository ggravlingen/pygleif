#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

runs=(
  "py311-v1 tests/v1 tests/compat"
  "py311-v2 tests/v2 tests/compat"
)

for run in "${runs[@]}"; do
  group="${run%% *}"
  paths="${run#* }"
  echo "==> syncing group: $group"
  uv sync --group "$group"
  echo "==> running tests: $paths"
  uv run pytest $paths
  echo
  echo "==> completed: $group"
  echo
done
