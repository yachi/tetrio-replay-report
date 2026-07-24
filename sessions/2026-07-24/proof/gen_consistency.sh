#!/usr/bin/env bash
# gen_consistency.sh (07-24) — prove committed dafny/*.dfy are exactly what
# codegen_dafny.py emits from facts-24.json + claims-24.json.
set -eu
cd "$(dirname "$0")"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
cp -r dafny "$tmp/committed"
python3 codegen_dafny.py >/dev/null
if diff -r "$tmp/committed" dafny; then
  echo "CONSISTENCY: committed dafny/*.dfy are byte-identical to codegen output from facts-24.json + claims-24.json"
  exit 0
else
  echo "CONSISTENCY: MISMATCH"
  exit 1
fi
