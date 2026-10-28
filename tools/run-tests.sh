#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
engine="${GODOT_BIN:-godot}"
"$engine" --headless --editor --import --quit
"$engine" --headless --path . res://tests/test_runner.tscn
