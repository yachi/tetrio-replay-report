#!/usr/bin/env bash
# mutation_test.sh (07-24) — non-vacuity check. Applies ONE mutation at a time
# to a generated .dfy (data literal / predicate constant / player / comparison),
# reruns `dafny verify` scoped to the affected lemma, asserts it now FAILS, then
# restores. Ends "MUTATION TEST: N/N killed".
set -u
cd "$(dirname "$0")/dafny"
DAFNY=/opt/homebrew/bin/dafny
COMMON="Facts24.dfy"
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
  total=$((total+1))
  cp "$file" "$file.bak"
  local r; r="$(apply "$file" "$frm" "$to")"
  if [ "$r" != "CHANGED" ]; then
    echo "  [$total] NOT-APPLIED ($desc): pattern not found — TEST BROKEN"; mv "$file.bak" "$file"; return
  fi
  if $DAFNY verify $COMMON "$claims" --filter-symbol "$filt" --cores 2 >/dev/null 2>&1; then
    echo "  [$total] SURVIVED ($desc) — lemma $filt is VACUOUS"
  else
    echo "  [$total] killed  ($desc)"; killed=$((killed+1))
  fi
  mv "$file.bak" "$file"
}

echo "Running mutation tests (each must be KILLED = verify fails)..."
# --- data-literal flips in Facts24.dfy ---
mutate "flip min-round dur 21023->21024"   Facts24.dfy Claims24.dfy C006 "m4_r1_pinglamb_lifetime: int := 21023" "m4_r1_pinglamb_lifetime: int := 21024"
mutate "flip max-round dur 240131->240130" Facts24.dfy Claims24.dfy C007 "m2_r2_yachi_lifetime: int := 240131" "m2_r2_yachi_lifetime: int := 240130"
mutate "flip max spike 17->16"             Facts24.dfy Claims24.dfy C017 "m4_r7_pinglamb_maxspike: int := 17" "m4_r7_pinglamb_maxspike: int := 16"
mutate "flip m1 longest dur 116222->116221" Facts24.dfy Claims24.dfy C008 "m0_r4_pinglamb_lifetime: int := 116222" "m0_r4_pinglamb_lifetime: int := 116221"
mutate "flip m7r3 pinglamb queued ge0 6->7" Facts24.dfy Claims24.dfy C018 "m6_r2_pinglamb_ge0: int := 6" "m6_r2_pinglamb_ge0: int := 7"
mutate "flip m3r3 round winner yachi->pinglamb" Facts24.dfy Claims24.dfy C010 'm2_r2_winner: string := "yachi"' 'm2_r2_winner: string := "pinglamb"'
# --- predicate-constant / comparison mutations in Claims24.dfy ---
mutate "flip C003 pieces target 4439->4440" Claims24.dfy Claims24.dfy C003 "== 4439" "== 4440"
mutate "flip C002 round-win target 29->30"  Claims24.dfy Claims24.dfy C002 "== 29" "== 30"
mutate "flip C005 allclear target 10->11"   Claims24.dfy Claims24.dfy C005 "== 10" "== 11"
mutate "flip C004 agg-pps target 132->133"  Claims24.dfy Claims24.dfy C004 "== 132" "== 133"
mutate "flip C019 winner-VS compare > to <" Claims24.dfy Claims24.dfy C019 'm0_r0_pinglamb_vs) > (if' 'm0_r0_pinglamb_vs) < (if'

echo ""
echo "MUTATION TEST: ${killed}/${total} killed"
[ "$killed" -eq "$total" ]
