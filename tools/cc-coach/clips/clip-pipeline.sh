#!/usr/bin/env bash
# One player's clip set, end to end: candidates -> re-judged examples -> clip inputs -> 8 seeded
# cold-clear rollouts with frame self-checks -> lower-median clips-chosen.json.
#
# Usage, from the work directory the top-level pipeline (../README.md) left behind — the one holding
# positions.jsonl, mid.jsonl, grade-mid.jsonl, rollouts-40k.priced.jsonl and positions.jsonl.rounds.json:
#
#   REPLAY_DIR=/path/to/session/replays bash ~/tetrio-replay-report/tools/cc-coach/clips/clip-pipeline.sh <player>
#
# Writes ./<player>/ (override with OUT=). CC= points at the built cc-coach harness.
set -euo pipefail
P=$1
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
O=${OUT:-$P}
CC=${CC:-cc/target/release/cc-coach}
: "${REPLAY_DIR:?set REPLAY_DIR to the session .ttrm directory}"
mkdir -p "$O"
python3 "$HERE/pick-candidates.py" "$P" "$O"
COACH_SEED=0 CC_NODES=160000 COACH_DUEL=320000 "$CC" < "$O/verify.jsonl" > "$O/verify-out.jsonl"
python3 "$HERE/choose-examples.py" "$O"
python3 "$HERE/build-clips-p.py" "$P" "$O"
for s in 0 1 2 3 4 5 6 7; do
  COACH_SEED=$s CC_NODES=40000 COACH_MODE=rollout "$CC" < "$O/clips-in.jsonl" > "$O/clips-cc-s$s.jsonl"
  cp "$O/clips-cc-s$s.jsonl" "$O/clips-cc.jsonl"
  OUT=$O REPLAY_DIR=$REPLAY_DIR bun "$HERE/build-frames-p.ts" > "$O/frames-check-s$s.txt" 2>&1
  grep -q false "$O/frames-check-s$s.txt" && { echo "SELF-CHECK FAILED seed $s"; exit 1; }
  cp "$O/clips.json" "$O/clips-s$s.json"
done
python3 "$HERE/finalize-clips.py" "$O"
echo PIPELINE OK
