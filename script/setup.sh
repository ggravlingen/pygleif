#!/bin/sh
# Setup pre-commit

# Stop on errors
set -e

cd "$(dirname "$0")/../"

script/bootstrap.sh

pre-commit install
