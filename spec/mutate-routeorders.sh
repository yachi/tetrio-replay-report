#!/bin/bash
# Mutate RouteOrders.dfy and check that the proofs object — the house rule: a lemma no mutant can
# kill is decorative. Verdict discipline copied from spec/mutate-donationcave.sh: a mutant is
# KILLED only by a verification ERROR that is not a timeout; a TIMEOUT is UNRESOLVED, not a kill;
# a sed that matched nothing is a NO-OP, not a survivor. The baseline must verify with a NONZERO
# count. Each run is one `dafny verify` at a time — never run this beside another verifier.
#
# A kill needs Dafny's own verdict: the summary line "Dafny program verifier finished with N verified,
# M errors" with M > 0 and a non-timeout "Error:" line. Output with a parse or resolution error, or
# with no summary line, never reached the verifier and is a HARNESS failure (exit 1), not a kill —
# a sed that breaks the syntax proves nothing about the proofs. Each kill prints the declarations
# that carry an error (the "Error:" line mapped to its enclosing lemma/method) and those that timed
# out, so the log says whether the theorem itself fails or only a witness. Per-mutant logs are kept
# in $DIR/mutant-<n>.log.
#
# Measured 2026-10-18 at 60 s, before RouteOrders.dfy gave ReachToAcc, AccToReach and Go
# {:isolate_assertions} and named each step's facts: three mutants killed only through a witness
# while the theorem timed out — "relation without case (c)" (T2Witness; AccToReach timed out),
# "hold step WITHOUT a placement" (JunkHoldHasNoMove; ReachToAcc timed out), "T4 procedure without
# case (c)" (ReachToAcc, HoldIsDeferral, T2Witness; Go timed out). After it, AccToReach, ReachToAcc
# and Go each carry a real error under those mutants; the table this script prints is the record.
set -u
SP="$(cd "$(dirname "$0")" && pwd)"
SRC="$SP/RouteOrders.dfy"
DIR=${TMPDIR:-/tmp}/routeorders-mut
mkdir -p "$DIR"
LIMIT=${DAFNY_TIME_LIMIT:-300}  # 60 s left the holdNoPlace mutant a TIMEOUT on 2026-10-17, before {:isolate_assertions}; on 2026-10-18 all mutants resolved at 60 s

# The summary line Dafny prints after a run that got as far as verification. A mutant whose output
# lacks it (or carries a parse / resolution error) never reached the verifier, so it says nothing
# about the proofs: that is a HARNESS failure, never a kill.
SUMMARY='Dafny program verifier finished with [0-9][0-9]* verified, [0-9][0-9]* errors\{0,1\}'

# decl_of FILE LINE -> the name of the lemma / method / function enclosing LINE in FILE (attributes
# such as {:isolate_assertions} between the keyword and the name are skipped)
decl_of() {
  awk -v L="$2" 'NR > L { exit }
    match($0, /^[ \t]*(ghost[ \t]+)?(lemma|method|function|predicate)[ \t]+(\{:[^}]*\}[ \t]+)*[A-Za-z0-9_]+/) {
      t = substr($0, RSTART, RLENGTH); sub(/.*[ \t]/, "", t); name = t }
    END { print (name == "" ? "?" : name) }' "$1"
}

# where FILE OUT -> "err: A B; timeout: C" — which declarations carry a real error, which timed out
where() {
  local errs="" tos="" ln n
  while IFS= read -r ln; do
    n=$(decl_of "$1" "$ln"); case " $errs " in *" $n "*) ;; *) errs="$errs $n" ;; esac
  done < <(grep "Error:" <<<"$2" | grep -v "timed out" | sed -n 's/.*\.dfy(\([0-9][0-9]*\),[0-9][0-9]*): Error:.*/\1/p')
  while IFS= read -r n; do
    case " $tos " in *" $n "*) ;; *) tos="$tos $n" ;; esac
  done < <(grep "Error:.*timed out" <<<"$2" | sed -n "s/.*Verification of '[A-Za-z0-9_]*\.\([A-Za-z0-9_]*\)[^']*' timed out.*/\1/p")
  echo "err:${errs:- none}; timeout:${tos:- none}"
}

verdict() {  # file out -> prints: error | timeout | clean | harness
  local out="$2" m
  if grep -q "resolution/type errors\|parse errors" <<<"$out" || ! grep -q "$SUMMARY" <<<"$out"; then
    echo harness; return
  fi
  m=$(grep -o "$SUMMARY" <<<"$out" | tail -1 | sed 's/.*verified, \([0-9]*\) error.*/\1/')
  if [ "$m" -gt 0 ] && grep "Error:" <<<"$out" | grep -qv "timed out"; then echo error
  elif grep -q "Error:.*timed out" <<<"$out"; then echo timeout
  elif [ "$m" -eq 0 ]; then echo clean
  else echo harness; fi
}

# --- baseline: the unmutated file must verify, and must verify SOMETHING -----------------------
base=$(dafny verify --verification-time-limit "$LIMIT" "$SRC" 2>&1)
count=$(grep -o '[0-9]* verified' <<<"$base" | grep -o '[0-9]*' || echo 0)
if [ "$(verdict "$SRC" "$base")" != clean ] || [ "${count:-0}" -eq 0 ]; then
  echo "BASELINE BROKEN: $SRC does not verify cleanly with a nonzero count"; exit 1
fi
echo "baseline: $count verified, 0 errors"

# --- control: a mutant that breaks the syntax or the types must be scored HARNESS, never a kill ---
for ctl in 's@^module RouteOrders {@module RouteOrders { lemma @' 's@^  const NoMut: Mut := @  const NoMut: Mut := NoSuchThing; const Unused: Mut := @'; do
  sed "$ctl" "$SRC" > "$DIR/control.dfy"
  v=$(verdict "$DIR/control.dfy" "$(dafny verify --verification-time-limit "$LIMIT" "$DIR/control.dfy" 2>&1)")
  if [ "$v" != harness ]; then echo "CONTROL FAILED: a parse/resolution-broken file scored '$v', not harness ($ctl)"; exit 1; fi
done
echo "control: parse-broken and resolution-broken copies both scored HARNESS"

fail=0
idx=0
run() {  # name, sed-script (one or more `;`-separated commands)
  idx=$((idx + 1))
  local f="$DIR/RouteOrders.dfy" out
  sed "$2" "$SRC" > "$f"
  if cmp -s "$SRC" "$f"; then echo "  NO-OP   $1  <- the pattern matched nothing"; fail=1; return; fi
  out=$(dafny verify --verification-time-limit "$LIMIT" "$f" 2>&1)
  printf '%s\n' "$out" > "$DIR/mutant-$idx.log"
  case "$(verdict "$f" "$out")" in
    error)   echo "  killed  $1"; echo "            [$(where "$f" "$out")]" ;;
    timeout) echo " TIMEOUT  $1  <- UNRESOLVED, not a kill; retry with a larger DAFNY_TIME_LIMIT"
             echo "            [$(where "$f" "$out")]"; fail=1 ;;
    harness) echo " HARNESS  $1  <- no verification verdict (parse/resolution error or no summary); see $DIR/mutant-$idx.log"; fail=1 ;;
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
