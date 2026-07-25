#!/usr/bin/env bash
# Anti-vacuity gate for a generated Dafny directory.
#
#   pipeline/mutation_test.sh <dafny-dir> [n]
#
# A lemma that verifies but pins nothing is worthless. This flips one literal in
# Facts.dfy at a time and requires `dafny verify` to FAIL each time. A mutant that
# survives means no lemma actually depends on that datum — either the claim is vacuous
# or the const is dead. Both are bugs worth knowing about.
#
# Consts are chosen deterministically (evenly spaced through the file) so runs are
# reproducible, and the file is always restored.
set -euo pipefail

DIR="${1:?usage: pipeline/mutation_test.sh <dafny-dir> [mutations]}"
N="${2:-12}"
cd "$DIR"
[ -f Facts.dfy ] && [ -f Claims.dfy ] || { echo "no Facts.dfy/Claims.dfy in $DIR" >&2; exit 1; }

command -v dafny >/dev/null || { echo "dafny not installed" >&2; exit 1; }

cp Facts.dfy Facts.dfy.orig
restore() { mv -f Facts.dfy.orig Facts.dfy 2>/dev/null || true; }
trap restore EXIT

# Numeric consts are the mutation targets; string consts (winners) are handled too.
mapfile -t NUM < <(grep -n '^const .*: int := [0-9]' Facts.dfy | cut -d: -f1)
mapfile -t STR < <(grep -n '^const .*: string := ' Facts.dfy | cut -d: -f1)
TOTAL=${#NUM[@]}
[ "$TOTAL" -gt 0 ] || { echo "no numeric consts found" >&2; exit 1; }

killed=0
tried=0
STEP=$(( TOTAL / (N > 1 ? N - 1 : 1) ))
[ "$STEP" -lt 1 ] && STEP=1

try_mutation() {   # $1 = line, $2 = sed program -> 0 if verification broke
  cp Facts.dfy.orig Facts.dfy
  sed -i.bak "$1$2" Facts.dfy && rm -f Facts.dfy.bak
  ! dafny verify Facts.dfy Claims.dfy --cores 4 >/dev/null 2>&1
}

run_one() {   # $1 = line number, $2 = sed program, $3 = description
  tried=$((tried + 1))
  if try_mutation "$1" "$2"; then
    echo "  [$tried] killed    $3"
    killed=$((killed + 1))
  else
    echo "  [$tried] SURVIVED  $3"
  fi
}

# A value may only be constrained beyond a threshold — a datum compared against a
# session maximum is not pinned by a +1 nudge, because the nudged value still loses to
# the maximum. That is a weak mutation operator, not a vacuous lemma, so escalate to a
# value far outside any plausible range before calling a mutant a survivor.
run_escalating() {   # $1 = line, $2 = const name, $3 = value
  tried=$((tried + 1))
  local big=$(( $3 * 10 + 100000 ))
  if try_mutation "$1" "s/:= $3\$/:= $(( $3 + 1 ))/"; then
    echo "  [$tried] killed    $2 $3 -> $(( $3 + 1 ))"
    killed=$((killed + 1))
  elif try_mutation "$1" "s/:= $3\$/:= ${big}/"; then
    echo "  [$tried] killed    $2 $3 -> ${big} (needed a large mutation)"
    killed=$((killed + 1))
  else
    echo "  [$tried] SURVIVED  $2 (unconstrained at $3, $(( $3 + 1 )) and ${big})"
  fi
}

echo "mutating $N of $TOTAL numeric consts in $DIR/Facts.dfy"
for ((i = 0; i < N && i * STEP < TOTAL; i++)); do
  LINE="${NUM[$((i * STEP))]}"
  NAME=$(sed -n "${LINE}p" Facts.dfy.orig | sed -E 's/^const ([a-zA-Z0-9_]+).*/\1/')
  VAL=$(sed -n "${LINE}p" Facts.dfy.orig | sed -E 's/.*:= ([0-9]+).*/\1/')
  run_escalating "$LINE" "$NAME" "$VAL"
done

# also flip one round winner and one match winner if present
if [ "${#STR[@]}" -gt 0 ]; then
  for LINE in "${STR[0]}" "${STR[$(( ${#STR[@]} / 2 ))]}"; do
    NAME=$(sed -n "${LINE}p" Facts.dfy.orig | sed -E 's/^const ([a-zA-Z0-9_]+).*/\1/')
    run_one "$LINE" 's/"yachi"/"__flipped__"/; s/"pinglamb"/"__flipped__"/' "$NAME winner flipped"
  done
fi

echo
echo "MUTATION TEST: ${killed}/${tried} killed"
[ "$killed" -eq "$tried" ]
