#!/usr/bin/env bash
# gen_consistency.sh — prove the committed dafny/*.dfy (and claims-proof-map.json)
# are EXACTLY what codegen_dafny.py emits from facts.json + the claims files.
# Regenerates into a temp dir and plain-diffs against the committed copies.
set -eu
cd "$(dirname "$0")"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

cp -r dafny "$tmp/dafny_committed"

python3 codegen_dafny.py >/dev/null

# claims-proof-map.json is intentionally NOT checked here: it is produced by
# build_proof_map.py from real verifier results, not by codegen. Only the .dfy
# data/proof source must be exactly what facts.json + the claims files dictate.
if diff -r "$tmp/dafny_committed" dafny; then
  echo "CONSISTENCY: committed dafny/*.dfy are byte-identical to codegen output from facts.json + claims"
  exit 0
else
  echo "CONSISTENCY: MISMATCH — committed dafny/*.dfy differ from codegen output"
  exit 1
fi
