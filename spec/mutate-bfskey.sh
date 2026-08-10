#!/bin/bash
# Mutate BfsKey.dfy and check that the proof objects. A lemma no mutant can kill is decorative
# (house rule), so every clause that carries the finding gets a mutant:
#
#   - the superset direction, the metric monotonicity, and the 3x bound (the three theorems)
#   - the pair-closure clause that IS the fix (weakened back to the shipped state-closure)
#   - the parent ordering and the pinned start arrival (the soundness skeleton)
#   - the witness's valuation, its run, and the Arrival enumeration (non-vacuity)
#
# Verdict discipline copied from spec/mutate-forecast-spec.sh: a mutant is KILLED only by a
# verification ERROR that is not a timeout; a TIMEOUT is UNRESOLVED, not a kill; a sed that
# matched nothing is a NO-OP, not a survivor. The baseline must verify with a NONZERO count —
# `dafny verify` on a file with zero lemmas prints "0 verified, 0 errors" and exits 0.
set -u
cd "$(dirname "$0")/.." || exit 1   # repo root; this file lives in spec/
SRC=spec/BfsKey.dfy
DIR=${TMPDIR:-/tmp}/bfskey-mut
mkdir -p "$DIR"
LIMIT=${DAFNY_TIME_LIMIT:-60}

verdict() {  # file -> prints: error | timeout | clean
  local out; out=$(dafny verify --verification-time-limit "$LIMIT" "$1" 2>&1)
  if   grep "Error:" <<<"$out" | grep -qv "timed out"; then echo error
  elif grep -q "Error:.*timed out" <<<"$out";          then echo timeout
  elif grep -q ", 0 errors" <<<"$out";                 then echo clean
  else echo error; fi
}

# --- baseline: the unmutated file must verify, and must verify SOMETHING -------------------------
base=$(dafny verify --verification-time-limit "$LIMIT" "$SRC" 2>&1)
count=$(grep -o '[0-9]* verified' <<<"$base" | grep -o '[0-9]*' || echo 0)
if ! grep -q ", 0 errors" <<<"$base" || [ "${count:-0}" -eq 0 ]; then
  echo "BASELINE BROKEN: $SRC does not verify cleanly with a nonzero count"; exit 1
fi
echo "baseline: $count verified, 0 errors"

fail=0
run() {  # name, sed-expr
  sed "$2" "$SRC" > "$DIR/BfsKey.dfy"
  if cmp -s "$SRC" "$DIR/BfsKey.dfy"; then echo "  NO-OP   $1  <- the pattern matched nothing"; fail=1; return; fi
  case "$(verdict "$DIR/BfsKey.dfy")" in
    error)   echo "  killed  $1" ;;
    timeout) echo " TIMEOUT  $1  <- UNRESOLVED, not a kill; retry with DAFNY_TIME_LIMIT=300"; fail=1 ;;
    *)       echo "SURVIVED  $1"; fail=1 ;;
  esac
}

# --- the three theorems ---------------------------------------------------------------------------
run "theorem 1: subset flipped to superset" \
  's@ensures NodesOf(posRun) <= NodesOf(arrRun)@ensures NodesOf(posRun) >= NodesOf(arrRun)@'
run "theorem 2: monotone claimed strict" \
  's@ensures MaxOver(NodesOf(posRun), P) <= MaxOver(NodesOf(arrRun), P)@ensures MaxOver(NodesOf(posRun), P) < MaxOver(NodesOf(arrRun), P)@'
run "theorem 4: bound claims 2 arrivals per state" \
  's@ensures |run| <= 3 \* |SS|@ensures |run| <= 2 * |SS|@'
run "theorem 4: cap keeps the position-keyed 1680" \
  's@ensures |run| <= 5040@ensures |run| <= 1680@'
run "product card says 2 per state" \
  's@ensures |NodesOver(SS)| == 3 \* |SS|@ensures |NodesOver(SS)| == 2 * |SS|@'

# --- the fix itself: weaken pair closure back to the SHIPPED state closure -----------------------
run "arrival closure weakened to the shipped state closure" \
  's@==> n in NodesOf(run))@==> exists j :: 0 <= j < |run| \&\& run[j].s == n.s)@'
run "arrival-keyed dedup dropped" \
  's@\&\& (forall i, j :: 0 <= i < j < |run| ==> run\[i\] != run\[j\])@\&\& true@'

# --- the soundness skeleton -----------------------------------------------------------------------
run "parent may point forward (order dropped)" \
  's@exists j :: 0 <= j < i \&\& run\[i\] in G(run\[j\].s)@exists j :: 0 <= j < |run| \&\& run[i] in G(run[j].s)@'
run "path start arrival unpinned" \
  's@\&\& p\[0\] == SNode(start, ByMove)@\&\& p[0].s == start@'

# --- non-vacuity: the witness must really witness --------------------------------------------------
run "witness valuation forgets the kick" \
  's@:= n => if n == SNode(1, ByRotate(true)) then 1 else 0@:= n => if n == SNode(1, ByMove) then 1 else 0@'
run "witness pos run granted the rotation arrival" \
  's@var posRun := \[SNode(0, ByMove), SNode(1, ByMove)\];@var posRun := [SNode(0, ByMove), SNode(1, ByRotate(true))];@'
run "Arrival enumeration drops the kicked rotation" \
  's@{ByMove, ByRotate(false), ByRotate(true)}@{ByMove, ByRotate(false)}@'

exit $fail
