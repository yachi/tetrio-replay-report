#!/bin/bash
# Mutate DonationCave.dfy and check that the proof objects — the house rule: a lemma no mutant
# can kill is decorative. Verdict discipline copied from spec/mutate-bfskey.sh: a mutant is
# KILLED only by a verification ERROR that is not a timeout; a TIMEOUT is UNRESOLVED, not a
# kill; a sed that matched nothing is a NO-OP, not a survivor. The baseline must verify with a
# NONZERO count.
set -u
SP="$(cd "$(dirname "$0")" && pwd)"
SRC="$SP/DonationCave.dfy"
DIR=${TMPDIR:-/tmp}/donationcave-mut
mkdir -p "$DIR"
LIMIT=${DAFNY_TIME_LIMIT:-60}

verdict() {  # file -> prints: error | timeout | clean
  local out; out=$(dafny verify --verification-time-limit "$LIMIT" "$1" 2>&1)
  if   grep "Error:" <<<"$out" | grep -qv "timed out"; then echo error
  elif grep -q "Error:.*timed out" <<<"$out";          then echo timeout
  elif grep -q ", 0 errors" <<<"$out";                 then echo clean
  else echo error; fi
}

# --- baseline: the unmutated file must verify, and must verify SOMETHING -----------------------
base=$(dafny verify --verification-time-limit "$LIMIT" "$SRC" 2>&1)
count=$(grep -o '[0-9]* verified' <<<"$base" | grep -o '[0-9]*' || echo 0)
if ! grep -q ", 0 errors" <<<"$base" || [ "${count:-0}" -eq 0 ]; then
  echo "BASELINE BROKEN: $SRC does not verify cleanly with a nonzero count"; exit 1
fi
echo "baseline: $count verified, 0 errors"

fail=0
run() {  # name, sed-expr
  sed "$2" "$SRC" > "$DIR/DonationCave.dfy"
  if cmp -s "$SRC" "$DIR/DonationCave.dfy"; then echo "  NO-OP   $1  <- the pattern matched nothing"; fail=1; return; fi
  case "$(verdict "$DIR/DonationCave.dfy")" in
    error)   echo "  killed  $1" ;;
    timeout) echo " TIMEOUT  $1  <- UNRESOLVED, not a kill; retry with DAFNY_TIME_LIMIT=300"; fail=1 ;;
    *)       echo "SURVIVED  $1"; fail=1 ;;
  esac
}

# --- the load-bearing hypothesis: the cleared rows are FULL ------------------------------------
run "full-rows hypothesis weakened to range-only (every lemma)" \
  's@requires ClearedRowsFull@requires ClearedInRange@'
run "nonemptiness dropped from ClearedRowsFull" \
  's@|cleared| > 0 \&\& forall r :: r in cleared ==> 0 <= r < h \&\& RowFull(g, h, w, r)@forall r :: r in cleared ==> 0 <= r < h \&\& RowFull(g, h, w, r)@'

# --- claim 1: the naive clause -----------------------------------------------------------------
run "naive conclusion negated" \
  's@ensures forall r :: r in cleared ==> g\[r\]\[c\]@ensures forall r :: r in cleared ==> !g[r][c]@'
run "FilledIn identity retargeted at FilledOut" \
  's@ensures FilledIn(g, h, w, cleared, c) == cleared@ensures FilledOut(g, h, w, cleared, c) == cleared@'
run "guard-unreachable claims the inR guard FIRES everywhere" \
  's@ensures forall c :: 0 <= c < w ==> |FilledIn(g, h, w, cleared, c)| > 0@ensures forall c :: 0 <= c < w ==> |FilledIn(g, h, w, cleared, c)| == 0@'
run "equivalence claims the RE-OPENING clause is the redundant one" \
  's@<==> DonationColPassNoNaive@<==> DonationColPassNoReopen@'

# --- claim 2: the roof -------------------------------------------------------------------------
run "coverage demanded strictly above BOTH cleared rows" \
  's@exists r :: 0 <= r < under \&\& g\[r\]\[k\]@exists r :: 0 <= r < under - 2 \&\& g[r][k]@'
run "cave equivalence demands an UNROOFED cave" \
  's@<==> CaveRun(g, h, w, under, t, c, e) \&\& Roofed@<==> CaveRun(g, h, w, under, t, c, e) \&\& !Roofed@'

# --- non-vacuity: the witnesses must really witness --------------------------------------------
run "donation witness loses a wall cell" \
  's@\[true, false, true \],   // row 3@[true, false, false],  // row 3@'
run "cave witness nub row broken" \
  's@\[true,  true,  true,  true \],   // row 1 — cleared: the nub row the Double completed@[true,  false, true,  true ],   // row 1@'

exit $fail
