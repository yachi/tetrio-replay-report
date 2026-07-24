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

# --- Facts.dfy data-literal flips (diverse claim kinds) ---
mutate "flip max lines 204->203"           Facts.dfy Claims_narrative.dfy C007 "m1_r2_yachi_lines: int := 204" "m1_r2_yachi_lines: int := 203"
mutate "flip max tspins 21->20"            Facts.dfy Claims_narrative.dfy C018 "m1_r7_pinglamb_tspins: int := 21" "m1_r7_pinglamb_tspins: int := 20"
mutate "flip max B2B 10->9"                Facts.dfy Claims_coaching.dfy  R013 "m8_r5_pinglamb_topbtb: int := 10" "m8_r5_pinglamb_topbtb: int := 9"
mutate "flip yachi garb-recv 127->128"     Facts.dfy Claims_coaching.dfy  R019 "m1_r2_yachi_garbagereceived: int := 127" "m1_r2_yachi_garbagereceived: int := 128"
mutate "flip max vs 262582->262581"        Facts.dfy Claims_narrative.dfy C010 "m6_r1_pinglamb_vs: int := 262582" "m6_r1_pinglamb_vs: int := 262581"
mutate "flip max apm 114223->114224"       Facts.dfy Claims_narrative.dfy C009 "m6_r1_pinglamb_apm: int := 114223" "m6_r1_pinglamb_apm: int := 114224"
mutate "flip max lifetime 228310->228311"  Facts.dfy Claims_narrative.dfy C006 "m1_r2_yachi_lifetime: int := 228310" "m1_r2_yachi_lifetime: int := 228311"
mutate "flip m10-decider apm 74105->74106" Facts.dfy Claims_coaching.dfy  R021 "m9_r8_yachi_apm: int := 74105" "m9_r8_yachi_apm: int := 74106"
mutate "flip m1r0 round winner p->y"       Facts.dfy Claims_narrative.dfy C022 'm0_r0_winner: string := "pinglamb"' 'm0_r0_winner: string := "yachi"'

# --- Claims_*.dfy predicate mutations ---
mutate "flip R004 target 7546->7547"         Claims_coaching.dfy  Claims_coaching.dfy  R004 "== 7546" "== 7547"
mutate "swap player yachi->pinglamb (C007)"  Claims_narrative.dfy Claims_narrative.dfy C007 "m1_r2_yachi_lines == 204" "m1_r2_pinglamb_lines == 204"
mutate "flip R026 variance direction < to >" Claims_coaching.dfy  Claims_coaching.dfy  R026 " < 79 * (((((((m0_r0_pinglamb_" " > 79 * (((((((m0_r0_pinglamb_"

echo ""
echo "MUTATION TEST: ${killed}/${total} killed"
[ "$killed" -eq "$total" ]
