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

# R005's and R024's bounds used to be hardcoded here as well as in the ledger and in
# this session's own codegen_dafny.py. That emitter is gone; these read the bound out of
# the ledger's spec, so the mutation still targets a PREDICATE constant without minting
# a third copy of the number.
R005=$(python3 -c "import json;print([c for c in json.load(open('../claims-coaching.json')) if c['id']=='R005'][0]['spec']['xs'][0]['b']['v'])")
R024=$(python3 -c "import json;print([c for c in json.load(open('../claims-coaching.json')) if c['id']=='R024'][0]['spec']['xs'][0]['b']['v'])")

# --- data-literal flips in Facts.dfy (diverse claim kinds) ---
mutate "flip max single-round APM 95498->95499"   Facts.dfy Claims.dfy C007 "m4_r1_pinglamb_apm: int := 95498" "m4_r1_pinglamb_apm: int := 95499"
mutate "flip max single-round VS 178457->178456"   Facts.dfy Claims.dfy C008 "m4_r1_pinglamb_vs: int := 178457" "m4_r1_pinglamb_vs: int := 178456"
mutate "flip longest-round lifetime 240131->240130" Facts.dfy Claims.dfy C011 "m2_r2_yachi_lifetime: int := 240131" "m2_r2_yachi_lifetime: int := 240130"
mutate "flip max tspins 18->17"                    Facts.dfy Claims.dfy C018 "m1_r2_pinglamb_tspins: int := 18" "m1_r2_pinglamb_tspins: int := 17"
mutate "flip max B2B 8->7"                          Facts.dfy Claims.dfy C019 "m5_r4_pinglamb_topbtb: int := 8" "m5_r4_pinglamb_topbtb: int := 7"
mutate "flip match-APM leader 64901->64902"         Facts.dfy Claims.dfy C020 "m3_lb_pinglamb_apm: int := 64901" "m3_lb_pinglamb_apm: int := 64902"
mutate "flip max spike 17->16"                      Facts.dfy Claims.dfy C010 "m4_r7_pinglamb_maxspike: int := 17" "m4_r7_pinglamb_maxspike: int := 16"
mutate "flip m3r3 yachi queued ge0 6->7"            Facts.dfy Claims.dfy C012 "m2_r2_yachi_ge0: int := 6" "m2_r2_yachi_ge0: int := 7"
mutate "flip m1 match winner pinglamb->yachi"       Facts.dfy Claims.dfy C003 'm0_winner: string := "pinglamb"' 'm0_winner: string := "yachi"'
mutate "flip m7 final round winner yachi->pinglamb" Facts.dfy Claims.dfy C017 'm6_r8_winner: string := "yachi"' 'm6_r8_winner: string := "pinglamb"'
# nrounds is a structural const the ported claims newly read (C014/C015/C016).
mutate "flip m7 nrounds 9->8"                       Facts.dfy Claims.dfy C015 "m6_nrounds: int := 9" "m6_nrounds: int := 8"
# R011 counts ADJACENT round pairs; flipping one round changes two pairs at once.
mutate "flip m2r1 winner for the pair count"        Facts.dfy Claims.dfy R011 'm1_r1_winner: string := "yachi"' 'm1_r1_winner: string := "pinglamb"'

# --- predicate-constant / comparison mutations in Claims.dfy ---
mutate "flip C022 pps-lead comparison"              Claims.dfy Claims.dfy C022 "m0_lb_yachi_pps > m0_lb_pinglamb_pps" "m0_lb_yachi_pps < m0_lb_pinglamb_pps"
mutate "flip R005 pieces target"                    Claims.dfy Claims.dfy R005 "== $R005" "== $((R005+1))"
mutate "flip R024 holds target"                     Claims.dfy Claims.dfy R024 "== $R024" "== $((R024+1))"
mutate "flip R019 APM-variance direction < to >"    Claims.dfy Claims.dfy R019 ") < ((50 * ((((((m0_r0_pinglamb_apm" ") > ((50 * ((((((m0_r0_pinglamb_apm"

echo ""
echo "MUTATION TEST: ${killed}/${total} killed"
[ "$killed" -eq "$total" ]
