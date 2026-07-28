#!/usr/bin/env bash
# gen_consistency.sh — prove the committed dafny/*.dfy are exactly what codegen emits
# from facts.json plus this session's two ledgers.
#
# Unlike 07-22 and 07-24, this session has no bespoke codegen_dafny.py: its hand claims
# carry specs, so `pipeline.codegen` renders them alongside the generated ones into a
# single Facts.dfy / Claims.dfy. The ledger order here must match the one
# `pipeline.codegen.session_ledgers` produces, or the byte comparison fails for a
# reason that has nothing to do with the data.
set -eu
cd "$(dirname "$0")"
REPO="$(cd ../../.. && pwd)"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT

cd "$REPO"
W="sessions/2026-07-28/report"
python3 -m pipeline.codegen "$W/facts.json" \
  --claims "$W/claims-generated.json" "$W/claims-narrative.json" \
  --outdir "$tmp/regenerated" >/dev/null

if diff -r "$W/dafny" "$tmp/regenerated"; then
  echo "CONSISTENCY: committed dafny/*.dfy are byte-identical to codegen output from facts.json + claims-*.json"
  exit 0
else
  echo "CONSISTENCY: MISMATCH"; exit 1
fi
