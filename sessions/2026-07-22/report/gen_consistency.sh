#!/usr/bin/env bash
# gen_consistency.sh — prove the committed dafny/*.dfy are exactly what codegen emits
# from facts.json plus this session's two HAND ledgers.
#
# This session used to carry its own ~780-line codegen_dafny.py, which hardcoded every
# claim's bound a second time, independently of the ledger. That emitter is gone: the
# hand claims carry specs now (hand_claims_narrative.py / hand_claims_coaching.py), so
# `pipeline.codegen` renders them exactly as it renders every other session's.
#
# Only the HAND ledgers are emitted here, and that is deliberate. The generated ledger's
# lemmas are not committed — CI renders them into a temp dir and checks
# claims-generated-proof-map.json against that — so committing them here would put the
# same lemma in two places. The ledger order must match the one gen_consistency and
# build_proof_map both use, or the byte comparison fails for a reason that has nothing
# to do with the data.
#
# claims-proof-map.json is intentionally NOT checked here: build_proof_map.py writes it
# from real verifier results, not from codegen. Only the .dfy data/proof source must be
# exactly what facts.json + the ledgers dictate.
set -eu
cd "$(dirname "$0")"
REPO="$(cd ../../.. && pwd)"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT

cd "$REPO"
W="sessions/2026-07-22/report"
python3 -m pipeline.codegen "$W/facts.json" \
  --claims "$W/claims-coaching.json" "$W/claims-narrative.json" \
  --outdir "$tmp/regenerated" >/dev/null

if diff -r "$W/dafny" "$tmp/regenerated"; then
  echo "CONSISTENCY: committed dafny/*.dfy are byte-identical to codegen output from facts.json + claims-*.json"
  exit 0
else
  echo "CONSISTENCY: MISMATCH — committed dafny/*.dfy differ from codegen output"
  exit 1
fi
