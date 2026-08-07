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
run() {  # name, sed-expr
  sed "$2" "$SRC" > "$DIR/Forecast.dfy"
  # a sed that matched nothing verifies exactly like the original and reads as a survivor
  if cmp -s "$SRC" "$DIR/Forecast.dfy"; then echo "  NO-OP   $1  <- the pattern matched nothing"; return; fi
  if dafny verify "$DIR/Forecast.dfy" >/dev/null 2>&1 \
  && dafny verify "$DIR/ForecastExamples.dfy" >/dev/null 2>&1
  then echo "SURVIVED  $1"; else echo "  killed  $1"; fi
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
