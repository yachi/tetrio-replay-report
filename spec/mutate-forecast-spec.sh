#!/bin/bash
# Mutate the DEFINITION and check that some witness objects.
#
# The mutant is verified together with ForecastExamples.dfy, which `include`s it: the examples are
# the only things in the spec that assert a concrete verdict, so a mutant that changes what the
# definition MEANS but breaks no general lemma still has to survive seven worked boards.
SRC=spec/Forecast.dfy
EX=spec/ForecastExamples.dfy
DIR=${TMPDIR:-/tmp}/forecast-spec-mut   # was a dead path inside one session's scratchpad
mkdir -p "$DIR"
cp "$EX" "$DIR/ForecastExamples.dfy"
# `dafny verify` checks only the file it is given — an `include` is trusted, not re-verified. So both
# files are run, and the mutant dies if EITHER objects.
# A mutant is KILLED only by a verification ERROR. Dafny exits non-zero on a TIMEOUT too, so judging
# on the exit code alone scores "this made the verifier slow" as "this was caught" — and timeouts are
# routine in this file, which itself records that a three-step ground window does not finish in 30 s.
# So the output is read, not just the status, and a timeout is reported as its own outcome.
# A TIMEOUT is an UNRESOLVED mutant, not a killed one.
#
# ERRORS DOMINATE TIMEOUTS, and getting that precedence backwards was the same bug one layer up.
# 2026-08-08 this read `timed out` FIRST, so a file that reported nine failing obligations AND one
# slow one was scored `timeout` and the nine kills were thrown away. That is what made "gap test
# inverted (>= not <)" look unresolved: measured per-obligation on 2026-08-09 against the spec as it
# stood BEFORE this commit, that mutant failed SeparationOneIsNeverAForecast, ForecastIsSatisfiable,
# CSpinWitnessIsRejected, NoHoleWitnessIsRejected, NotASpinIsRejected,
# GarbageWitnessLeavesTheGapAlone, AnySizeOfClearIsAForecast, RowsAccumulateAcrossClears and
# ClearsOutsideThePairCloseNothing, and only GapClauseIsLoadBearingAtZero ran long — nine kills
# behind one slow obligation. A proved error is a kill; some OTHER obligation
# being slow does not unprove it. `timeout` is now reported only when nothing errored, which is the
# case where it really does mean "unread".
#
# The slow obligation was then fixed at the source rather than by raising the limit: pinning both
# tracked positions in GapClauseIsLoadBearingAtZero takes it from >26 s to 1.3 s under that mutant.
# Raising the limit was the alternative and was rejected — nothing runs this suite in CI (there is
# no spec job in .github/workflows/verify.yml at all), so "run CI at 300 s" would have been a
# setting on a job that does not exist, and a 300 s budget hides the next slow obligation instead
# of surfacing it.
LIMIT=${DAFNY_TIME_LIMIT:-60}

# NOTE the shape of the error test. A timeout is ALSO reported on an `Error:` line —
#   Error: Verification of 'Forecast.X' timed out after 20 seconds.
# — so "does the output contain Error:" cannot be the first question, and simply swapping the two
# branches would score every timeout as a kill. Real errors are the `Error:` lines that are NOT
# timeouts; that is the set that has to be non-empty before a mutant is called killed.
verdict() {  # file -> prints: error | timeout | clean
  local out; out=$(dafny verify --verification-time-limit "$LIMIT" "$1" 2>&1)
  if   grep "Error:" <<<"$out" | grep -qv "timed out"; then echo error
  elif grep -q "Error:.*timed out" <<<"$out";          then echo timeout
  elif grep -q ", 0 errors" <<<"$out";                 then echo clean
  else echo error; fi
}

run() {  # name, sed-expr
  sed "$2" "$SRC" > "$DIR/Forecast.dfy"
  # a sed that matched nothing verifies exactly like the original and reads as a survivor
  if cmp -s "$SRC" "$DIR/Forecast.dfy"; then echo "  NO-OP   $1  <- the pattern matched nothing"; return; fi
  local a b
  a=$(verdict "$DIR/Forecast.dfy"); b=$(verdict "$DIR/ForecastExamples.dfy")
  case "$a $b" in
    *error*)              echo "  killed  $1" ;;
    *timeout*)            echo " TIMEOUT  $1  <- UNRESOLVED, not a kill; retry with DAFNY_TIME_LIMIT=300" ;;
    *)                    echo "SURVIVED  $1" ;;
  esac
}
run "drop the pre-existing-hole clause"   's|    && HolePreExisted(e)                  // 2\..*|    \&\& true|'
run "drop the non-spin-clear clause"      's|    && ClosedByPlain(h, e) >= minLines.*|    \&\& true|'
run "drop the gap-closed clause"          's|    && GapClosed(h, e)                    // 3\..*|    \&\& true|'
run "drop the tucked clause"              's|    && Tucked(e)                          // 1\..*|    \&\& true|'
run "count spins instead of plain clears" 's|{ RemovedBetween(h, e.j, e.k - 1, At(e.roofAt), At(e.floorAt), false) }|{ RemovedBetween(h, e.j, e.k - 1, At(e.roofAt), At(e.floorAt), true) }|'
run "gap test inverted (>= not <)"        's|    && FloorFinal(h, e).row - RoofFinal(h, e).row < e.floorAt - e.roofAt|    \&\& FloorFinal(h, e).row - RoofFinal(h, e).row >= e.floorAt - e.roofAt|'
run "Advance ignores garbage"             's|    r + CountBelow(s.clearedRows, r) - s.garbageRows|    r + CountBelow(s.clearedRows, r)|'
run "CountBetween uses <= not <"          's|else (if a < cleared\[0\] && cleared\[0\] < b then 1 else 0)|else (if a <= cleared[0] \&\& cleared[0] <= b then 1 else 0)|'
run "CountBelow counts above instead"     's|else (if cleared\[0\] > r then 1 else 0)|else (if cleared[0] < r then 1 else 0)|'
run "IsForecastTriple is really any-clear" 's|  { IsForecast(h, e, 3) }|  { IsForecast(h, e, 1) }|'
run "the T-spin flag is ignored"          's|&& s.wasSpin == spins|&& true|'
run "CountBetween counts everything below a" 's|else (if a < cleared\[0\] && cleared\[0\] < b then 1 else 0)|else (if a < cleared[0] then 1 else 0)|'

# --- clause 4 counts ROWS, not clears -----------------------------------------------------------
# The reading these three catch: "a line clear happened between them" instead of "n rows were taken
# from between them". Every witness in the file cleared exactly ONE row until 2026-08-06, so all
# three of these used to be indistinguishable from the original.
run "clause 4 counts clears, not rows"    's|        then CountBetween(s.clearedRows, a.row, b.row) else 0|        then (if CountBetween(s.clearedRows, a.row, b.row) > 0 then 1 else 0) else 0|'
run "clause 4 caps a clear at two rows"   's|        then CountBetween(s.clearedRows, a.row, b.row) else 0|        then (var c := CountBetween(s.clearedRows, a.row, b.row); if c > 2 then 2 else c) else 0|'
# This one SURVIVED the pre-2026-08-06 spec (c8e380a) and is killed only by the parametric lemma:
# the worked examples top out at a Triple, so nothing there could tell "any n" from "n <= 3".
run "clause 4 caps a clear at three rows" 's|        then CountBetween(s.clearedRows, a.row, b.row) else 0|        then (var c := CountBetween(s.clearedRows, a.row, b.row); if c > 3 then 3 else c) else 0|'
run "rows below the pair count too"       's|  { RemovedBetween(h, e.j, e.k - 1, At(e.roofAt), At(e.floorAt), false) }|  { RemovedBetween(h, e.j, e.k - 1, At(e.roofAt), At(e.floorAt + 100), false) }|'

# --- the two guards added 2026-08-09 ------------------------------------------------------------
# A guard no mutant can kill is decorative, so each of them gets one.

# Clause 1's flag against the history. Killed by AForecastIsASpinInTheHistory, which is exactly the
# statement that was unprovable while `spinAtK` floated free of `h`.
run "WellFormed stops tying the spin flag to the history" \
  's|    && e.spinAtK == h\[e.k - 1\].wasSpin.*|    \&\& true|'

# The window's right endpoint. Measured against the committed spec (2026-08-09): this mutant errors
# on two UNIVERSALS -- SeparationOneIsNeverAForecast and GarbageAloneCannotMakeAForecast, both of
# whose hypotheses are stated in terms of the window bound -- and times out four witnesses, so the
# old timeout-first verdict scored it UNRESOLVED. No witness distinguished the two windows: every
# one of them padded with an inert final step, which Track passes through unchanged. The ones that
# resolved all passed, and the four that timed out settled nothing either way.
# TheSpinsOwnClearDoesNotCloseTheGap now kills it on the definition's own numbers in 1.3 s.
run "the window runs past the spin's own lock" \
  's|Track(h, e.j, e.k - 1, At(e.roofAt))|Track(h, e.j, e.k, At(e.roofAt))|
   s|Track(h, e.j, e.k - 1, At(e.floorAt))|Track(h, e.j, e.k, At(e.floorAt))|
   s|RemovedBetween(h, e.j, e.k - 1, At(e.roofAt), At(e.floorAt), true)|RemovedBetween(h, e.j, e.k, At(e.roofAt), At(e.floorAt), true)|
   s|RemovedBetween(h, e.j, e.k - 1, At(e.roofAt), At(e.floorAt), false)|RemovedBetween(h, e.j, e.k, At(e.roofAt), At(e.floorAt), false)|'
