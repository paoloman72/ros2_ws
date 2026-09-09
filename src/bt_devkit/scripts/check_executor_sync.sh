#!/usr/bin/env bash
# Verifies that the devkit's bt_executor is still byte-identical to the
# simulator's executor (bt_runtime_tools). Run it from the source tree
# after any change to either file.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
devkit_dir="$(dirname "$here")"
simulator_executor="$(cd "$devkit_dir/.." && pwd)/bt_runtime_tools/src/bt_executor.cpp"
devkit_executor="$devkit_dir/src/bt_executor.cpp"

if [[ ! -f "$simulator_executor" ]]; then
  echo "ERROR: simulator executor not found: $simulator_executor" >&2
  exit 1
fi

if diff -u "$simulator_executor" "$devkit_executor"; then
  echo "OK: bt_executor is identical to the simulator's executor."
else
  echo "MISMATCH: the devkit executor drifted from the simulator's." >&2
  echo "Review the diff above and re-sync (copy the simulator file in)." >&2
  exit 1
fi
