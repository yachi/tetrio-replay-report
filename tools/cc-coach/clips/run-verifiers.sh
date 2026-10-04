#!/usr/bin/env bash
# Re-run one player's four independent frame checkers and SAVE what they print.
#
#   tools/cc-coach/clips/run-verifiers.sh <player> <data-dir>
#
# <data-dir> holds that player's clips-chosen.json, clips-in.jsonl, clips-cc-s<seed>.jsonl and
# clipdump/ (clip-pipeline.sh writes them to ./<player>/), with positions.jsonl one level up. Each
# checker reads the files beside itself, so it is copied in and run there; its output lands in
# <player>/verify-out/batch-N.txt, and adjudicate.py turns those outputs into adjudication.json.
#
# CC_GARBAGE_MODE=early: verify-batch-1.py carries two readings of Cold Clear's garbage timing. Its
# default lets the player's step-N rows reach Cold Clear only AFTER Cold Clear's step-N piece; 'early'
# queues them before it, which is the rule the pages state ("on the same piece ... if its piece there
# clears lines, the rows wait") and the rule the clips were built with. The default reading reports
# every such step as a mismatch; that run is not saved, because it tests a rule the clips never used.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
P="$1"; DATA="$(cd "$2" && pwd)"
mkdir -p "$HERE/$P/verify-out"
for n in 0 1 2 3; do
  cp "$HERE/$P/verify-batch-$n.py" "$DATA/"
  [ -f "$HERE/$P/verify-batch-$n-extra.py" ] && cp "$HERE/$P/verify-batch-$n-extra.py" "$DATA/"
  (cd "$DATA" && CC_GARBAGE_MODE=early python3 "verify-batch-$n.py") > "$HERE/$P/verify-out/batch-$n.txt" 2>&1
done
python3 "$HERE/adjudicate.py" "$DATA/clips-chosen.json" "$HERE/$P/verify-out" > "$HERE/$P/adjudication.json"
