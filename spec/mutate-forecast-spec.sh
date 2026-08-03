#!/bin/bash
# Mutate the DEFINITION and check that some witness objects.
#
# The mutant is verified together with ForecastExamples.dfy, which `include`s it: the examples are
# the only things in the spec that assert a concrete verdict, so a mutant that changes what the
# definition MEANS but breaks no general lemma still has to survive seven worked boards.
SRC=spec/Forecast.dfy
EX=spec/ForecastExamples.dfy
DIR=/private/tmp/claude-501/-Users-yachi-Downloads-Telegram-Desktop-replay-2026-07-22/f6bd97c8-9ae3-41dd-970b-6b9378bf8461/scratchpad/mut
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
