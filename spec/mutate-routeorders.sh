#!/bin/bash
# Mutate RouteOrders.dfy and check that the proofs object — the house rule: a lemma no mutant can
# kill is decorative. Verdict discipline copied from spec/mutate-donationcave.sh: a mutant is
# KILLED only by a verification ERROR that is not a timeout; a TIMEOUT is UNRESOLVED, not a kill;
# a sed that matched nothing is a NO-OP, not a survivor. The baseline must verify with a NONZERO
# count. Each run is one `dafny verify` at a time — never run this beside another verifier.
set -u
SP="$(cd "$(dirname "$0")" && pwd)"
SRC="$SP/RouteOrders.dfy"
DIR=${TMPDIR:-/tmp}/routeorders-mut
mkdir -p "$DIR"
LIMIT=${DAFNY_TIME_LIMIT:-300}  # 60 s leaves the holdNoPlace mutant a TIMEOUT (measured 2026-10-17)

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
run() {  # name, sed-script (one or more `;`-separated commands)
  sed "$2" "$SRC" > "$DIR/RouteOrders.dfy"
  if cmp -s "$SRC" "$DIR/RouteOrders.dfy"; then echo "  NO-OP   $1  <- the pattern matched nothing"; fail=1; return; fi
  case "$(verdict "$DIR/RouteOrders.dfy")" in
    error)   echo "  killed  $1" ;;
    timeout) echo " TIMEOUT  $1  <- UNRESOLVED, not a kill; retry with DAFNY_TIME_LIMIT=300"; fail=1 ;;
    *)       echo "SURVIVED  $1"; fail=1 ;;
  esac
}

# --- T1: the lock process ----------------------------------------------------------------------
run "T1 clear WITHOUT compaction (full rows emptied in place, nothing shifts, rowmap frozen)" \
  's@KeepRows(e) + FreshRows(MaxLabel(e) + 1, |e| - |KeepRows(e)|, w)@ClearInPlace(e, w)@'
run "T1 clear a row that is NOT full (one cell short counts as full)" \
  's@(if FullRow(e\[0\].cells) then \[\] else \[e\[0\]\])@(if NearFullRow(e[0].cells) then [] else [e[0]])@'
run "T1 fresh rowmap id off by one (max(1000, ...rowmap) + 2)" \
  's@FreshRows(MaxLabel(e) + 1,@FreshRows(MaxLabel(e) + 2,@'
run "T1 cell-disjointness hypothesis dropped" \
  's@    \&\& (forall a, b, c :: 0 <= a < |G| \&\& 0 <= b < |G| \&\& a != b \&\& c in G\[a\].cells ==> c !in G\[b\].cells)@@'
run "T1 avoid-the-initial-board hypothesis dropped" \
  's@ \&\& 0 <= c.d < |B0| \&\& B0\[c.d\]\[c.x\] == 0)@ \&\& 0 <= c.d < |B0|)@'
run "T1 witness: the expected board after both orders altered" \
  's@var want := \[ERow(1, \[3, 0\])@var want := [ERow(1, [0, 3])@'

# --- T2: the hold relation vs the decision procedure -------------------------------------------
run "T2 relation without case (c) — an empty hold cannot take the current piece" \
  's@case HoldFirst(g) => c.h.Empty? \&\& c.i + 1 < |st|@case HoldFirst(g) => false \&\& c.i + 1 < |st|@'
run "T2 relation lets the next bag's '*' be placed" \
  "s@case PlaceCur(g) => c.i < |st| \&\& st\[c.i\] != '\*' \&\& GroupOf(d, st\[c.i\]) == g@case PlaceCur(g) => c.i < |st| \&\& (st[c.i] == '*' || GroupOf(d, st[c.i]) == g)@"
run "T2 relation gains a hold step WITHOUT a placement (the held piece is dropped)" \
  's@datatype Move = PlaceCur(g: int) | Swap(g: int) | HoldFirst(g: int)@datatype Move = PlaceCur(g: int) | Swap(g: int) | HoldFirst(g: int) | HoldOnly(g: int)@;s@^    case HoldFirst(g) => c.h.Empty? \&\& c.i + 1@    case HoldOnly(g) => c.i < |st| \&\& g == 0\n    case HoldFirst(g) => c.h.Empty? \&\& c.i + 1@;s@^    case HoldFirst(g) => Key(c.s + Pow2(g), c.i + 2, Held(st\[c.i\]))@    case HoldOnly(g) => Key(c.s, c.i + 1, Held(st[c.i]))\n    case HoldFirst(g) => Key(c.s + Pow2(g), c.i + 2, Held(st[c.i]))@;s@^      case HoldFirst(g) => assert Fits@      case HoldOnly(g) => {}\n      case HoldFirst(g) => assert Fits@'
run "T2 procedure: a seen key answers true instead of false" \
  's@if key in seen { return false, seen; }@if key in seen { return true, seen; }@'
run "T2 procedure: the swap loop skipped" \
  's@    if h.Held? \&\& !m.noSwap {@    if false \&\& h.Held? \&\& !m.noSwap {@'

# --- T4: empty hold == next held ---------------------------------------------------------------
run "T4 procedure without case (c)" \
  "s@|| (h.Empty? \&\& !m.noHoldFirst \&\& st\[i\] != '\*'@|| (false \&\& h.Empty? \&\& !m.noHoldFirst \&\& st[i] != '*'@"
run "T4 the '*'-only-at-the-end premise dropped" \
  's@^    requires StarOnlyLast(st)$@@'
run "T4 counter-witness run WITH case (c) (T4 holds there, so the witness must fail)" \
  's@    var m := Mut(false, true, false, false, false);@    var m := Mut(false, false, false, false, false);@'

exit $fail
