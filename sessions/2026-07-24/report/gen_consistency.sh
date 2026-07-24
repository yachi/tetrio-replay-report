#!/usr/bin/env bash
# gen_consistency.sh — prove committed dafny/*.dfy are exactly what codegen emits
# from facts.json + the two claims ledgers.
set -eu
cd "$(dirname "$0")"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
cp -r dafny "$tmp/committed"
python3 codegen_dafny.py >/dev/null
if diff -r "$tmp/committed" dafny; then
  echo "CONSISTENCY: committed dafny/*.dfy are byte-identical to codegen output from facts.json + claims-*.json"
  exit 0
else
  echo "CONSISTENCY: MISMATCH"; exit 1
fi
