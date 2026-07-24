#!/usr/bin/env bash
# mutation_test.sh — non-vacuity check. Applies ONE mutation at a time to a
# generated .dfy (data literal / predicate constant / player / comparison),
# reruns `dafny verify` scoped to the affected lemma, asserts it now FAILS, then
# restores. Ends "MUTATION TEST: N/N killed".
set -u
cd "$(dirname "$0")/dafny"
DAFNY=/opt/homebrew/bin/dafny
COMMON="Facts.dfy"
killed=0; total=0

apply() { python3 - "$1" "$2" "$3" <<'PY'
import sys
path, frm, to = sys.argv[1:4]
s = open(path, encoding="utf-8").read()
i = s.find(frm)
if i < 0:
    print("UNCHANGED"); sys.exit(0)
open(path, "w", encoding="utf-8").write(s[:i] + to + s[i+len(frm):])
print("CHANGED")
PY
}

mutate() {
  local desc="$1" file="$2" claims="$3" filt="$4" frm="$5" to="$6"
  total=$((total+1)); cp "$file" "$file.bak"
  local r; r="$(apply "$file" "$frm" "$to")"
  if [ "$r" != "CHANGED" ]; then echo "  [$total] NOT-APPLIED ($desc): pattern not found"; mv "$file.bak" "$file"; return; fi
  if $DAFNY verify $COMMON "$claims" --filter-symbol "$filt" --cores 2 >/dev/null 2>&1; then
    echo "  [$total] SURVIVED ($desc) — lemma $filt is VACUOUS"
  else echo "  [$total] killed  ($desc)"; killed=$((killed+1)); fi
  mv "$file.bak" "$file"
}

echo "Running mutation tests (each must be KILLED = verify fails)..."
# --- data-literal flips in Facts.dfy (diverse claim kinds) ---
mutate "flip max single-round APM 95498->95499"   Facts.dfy Claims_narrative.dfy C007 "m4_r1_pinglamb_apm: int := 95498" "m4_r1_pinglamb_apm: int := 95499"
mutate "flip max single-round VS 178457->178456"   Facts.dfy Claims_narrative.dfy C008 "m4_r1_pinglamb_vs: int := 178457" "m4_r1_pinglamb_vs: int := 178456"
mutate "flip longest-round lifetime 240131->240130" Facts.dfy Claims_narrative.dfy C011 "m2_r2_yachi_lifetime: int := 240131" "m2_r2_yachi_lifetime: int := 240130"
mutate "flip max tspins 18->17"                    Facts.dfy Claims_narrative.dfy C018 "m1_r2_pinglamb_tspins: int := 18" "m1_r2_pinglamb_tspins: int := 17"
mutate "flip max B2B 8->7"                          Facts.dfy Claims_narrative.dfy C019 "m5_r4_pinglamb_topbtb: int := 8" "m5_r4_pinglamb_topbtb: int := 7"
mutate "flip match-APM leader 64901->64902"         Facts.dfy Claims_narrative.dfy C020 "m3_lb_pinglamb_apm: int := 64901" "m3_lb_pinglamb_apm: int := 64902"
mutate "flip max spike 17->16"                      Facts.dfy Claims_narrative.dfy C010 "m4_r7_pinglamb_maxspike: int := 17" "m4_r7_pinglamb_maxspike: int := 16"
mutate "flip m3r3 yachi queued ge0 6->7"            Facts.dfy Claims_narrative.dfy C012 "m2_r2_yachi_ge0: int := 6" "m2_r2_yachi_ge0: int := 7"
mutate "flip m1 match winner pinglamb->yachi"       Facts.dfy Claims_narrative.dfy C003 'm0_winner: string := "pinglamb"' 'm0_winner: string := "yachi"'
mutate "flip m7 final round winner yachi->pinglamb" Facts.dfy Claims_narrative.dfy C017 'm6_r8_winner: string := "yachi"' 'm6_r8_winner: string := "pinglamb"'
# --- predicate-constant / comparison mutations in Claims_*.dfy ---
mutate "flip C022 pps-lead count 7->8"              Claims_narrative.dfy Claims_narrative.dfy C022 "== 7)" "== 8)"
mutate "flip R005 pieces target 4748->4749"         Claims_coaching.dfy  Claims_coaching.dfy  R005 "== 4748" "== 4749"
mutate "flip R024 holds target 1792->1793"          Claims_coaching.dfy  Claims_coaching.dfy  R024 "== 1792" "== 1793"
mutate "flip R019 APM-variance direction < to >"    Claims_coaching.dfy  Claims_coaching.dfy  R019 " < (50 * ((((((m0_r0_pinglamb_apm" " > (50 * ((((((m0_r0_pinglamb_apm"

echo ""
echo "MUTATION TEST: ${killed}/${total} killed"
[ "$killed" -eq "$total" ]
