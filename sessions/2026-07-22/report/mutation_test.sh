#!/usr/bin/env bash
# mutation_test.sh — non-vacuity check for the Dafny proof layer.
# Applies ONE mutation at a time to a generated .dfy file (flip a data literal,
# a comparison constant, a player, or an inequality direction), reruns
# `dafny verify` scoped to the affected lemma, and asserts it now FAILS. A
# surviving mutation (verify still passes) means that lemma is vacuous.
# Restores the file after each mutation. Ends: "MUTATION TEST: N/N killed".
set -u
cd "$(dirname "$0")/dafny"
DAFNY=/opt/homebrew/bin/dafny
COMMON="Facts.dfy"

killed=0
total=0

# first-occurrence, literal (non-regex) replace; prints CHANGED / UNCHANGED
apply() { python3 - "$1" "$2" "$3" <<'PY'
import sys
path, frm, to = sys.argv[1], sys.argv[2], sys.argv[3]
s = open(path, encoding="utf-8").read()
i = s.find(frm)
if i < 0:
    print("UNCHANGED"); sys.exit(0)
s2 = s[:i] + to + s[i+len(frm):]
open(path, "w", encoding="utf-8").write(s2)
print("CHANGED")
PY
}

mutate() {
  local desc="$1" file="$2" claims="$3" filt="$4" frm="$5" to="$6"
  total=$((total+1))
  cp "$file" "$file.bak"
  local r; r="$(apply "$file" "$frm" "$to")"
  if [ "$r" != "CHANGED" ]; then
    echo "  [$total] NOT-APPLIED ($desc): pattern not found — TEST BROKEN"
    mv "$file.bak" "$file"; return
  fi
  if $DAFNY verify $COMMON "$claims" --filter-symbol "$filt" --cores 2 >/dev/null 2>&1; then
    echo "  [$total] SURVIVED ($desc) — lemma $filt is VACUOUS"
  else
    echo "  [$total] killed  ($desc)"
    killed=$((killed+1))
  fi
  mv "$file.bak" "$file"
}

echo "Running mutation tests (each must be KILLED = verify fails)..."

# R004's bound used to be hardcoded HERE as well as in the ledger and in the session's
# own codegen_dafny.py — three copies of one number, and only one of them was checked
# against the data. The emitter is gone; this reads the bound out of the ledger's spec,
# so the mutation still targets a PREDICATE constant (a different kind of mutation from
# the data-literal flips below) without minting a third copy of the value.
R004=$(python3 -c "import json;print([c for c in json.load(open('../claims-coaching.json')) if c['id']=='R004'][0]['spec']['xs'][0]['b']['v'])")

# --- Facts.dfy data-literal flips (diverse claim kinds) ---
mutate "flip max lines 204->203"           Facts.dfy Claims.dfy C007 "m1_r2_yachi_lines: int := 204" "m1_r2_yachi_lines: int := 203"
mutate "flip max tspins 21->20"            Facts.dfy Claims.dfy C018 "m1_r7_pinglamb_tspins: int := 21" "m1_r7_pinglamb_tspins: int := 20"
mutate "flip max B2B 10->9"                Facts.dfy Claims.dfy R013 "m8_r5_pinglamb_topbtb: int := 10" "m8_r5_pinglamb_topbtb: int := 9"
mutate "flip yachi garb-recv 127->128"     Facts.dfy Claims.dfy R019 "m1_r2_yachi_garbagereceived: int := 127" "m1_r2_yachi_garbagereceived: int := 128"
mutate "flip max vs 262582->262581"        Facts.dfy Claims.dfy C010 "m6_r1_pinglamb_vs: int := 262582" "m6_r1_pinglamb_vs: int := 262581"
mutate "flip max apm 114223->114224"       Facts.dfy Claims.dfy C009 "m6_r1_pinglamb_apm: int := 114223" "m6_r1_pinglamb_apm: int := 114224"
mutate "flip max lifetime 228310->228311"  Facts.dfy Claims.dfy C006 "m1_r2_yachi_lifetime: int := 228310" "m1_r2_yachi_lifetime: int := 228311"
mutate "flip m10-decider apm 73680->73681" Facts.dfy Claims.dfy R021 "m9_r8_yachi_apm: int := 73680" "m9_r8_yachi_apm: int := 73681"
mutate "flip m1r0 round winner p->y"       Facts.dfy Claims.dfy C022 'm0_r0_winner: string := "pinglamb"' 'm0_r0_winner: string := "yachi"'
# The corpus's one boolean datum, emitted as 0/1 — R021 is the only claim that reads it.
mutate "flip m10-decider alive 1->0"       Facts.dfy Claims.dfy R021 "m9_r8_yachi_alive: int := 1" "m9_r8_yachi_alive: int := 0"
# nrounds and nmatches are structural consts the ported claims newly read.
mutate "flip m10 nrounds 9->8"             Facts.dfy Claims.dfy C004 "m9_nrounds: int := 9" "m9_nrounds: int := 8"
mutate "flip nmatches 10->9"               Facts.dfy Claims.dfy R003 "const nmatches: int := 10" "const nmatches: int := 9"

# --- Claims.dfy predicate mutations ---
mutate "flip R004 pieces target"             Claims.dfy Claims.dfy R004 "== $R004" "== $((R004+1))"
mutate "swap player yachi->pinglamb (C007)"  Claims.dfy Claims.dfy C007 "m1_r2_yachi_lines == 204" "m1_r2_pinglamb_lines == 204"
mutate "flip R026 variance direction < to >" Claims.dfy Claims.dfy R026 ") < ((79 * (((((((m0_r0_pinglamb_" ") > ((79 * (((((((m0_r0_pinglamb_"
# C021's window bounds cannot be tested by mutating the BOUND: relaxing 5 to 6 leaves
# the conjunct true, and a conjunction with one weakened-but-true conjunct still
# verifies, so such a mutant survives for a reason that says nothing about the lemma.
# (Tightening it to 4 would be killed, but only by making the clause false, which shows
# it is present rather than load-bearing.) The bounds are load-bearing against the DATA:
# m1r3 is pinglamb's, and flipping it to yachi joins the two neighbouring runs into one
# of seven. The witnesses below still hold under that flip, so only the window bounds
# can catch it — which is exactly what they are there for.
mutate "C021 make a 7-run (m1r3 p->y)"       Facts.dfy Claims.dfy C021 'm0_r2_winner: string := "pinglamb"' 'm0_r2_winner: string := "yachi"'
# ... and the run itself: break the named five-round witness.
mutate "break C021 witness m1r4 y->p"        Facts.dfy Claims.dfy C021 'm0_r3_winner: string := "yachi"' 'm0_r3_winner: string := "pinglamb"' 

echo ""
echo "MUTATION TEST: ${killed}/${total} killed"
[ "$killed" -eq "$total" ]
