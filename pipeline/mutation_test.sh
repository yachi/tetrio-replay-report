#!/usr/bin/env bash
# Anti-vacuity gate for a generated Dafny directory.
#
#   pipeline/mutation_test.sh <dafny-dir> [n]
#
# A lemma that verifies but pins nothing is worthless. This flips one literal in
# Facts.dfy at a time and requires `dafny verify` to FAIL each time. A mutant that
# survives means no lemma constrains that datum in any direction the ladder below
# reaches — either the claim is vacuous or the const is dead. Both are bugs worth
# knowing about, and so is a ladder that does not reach far enough: the qualifier is
# load-bearing, and the comment on `ladder_rungs` says what it cost to learn.
#
# Consts are chosen deterministically (evenly spaced through the file) so runs are
# reproducible, and the file is always restored. A SURVIVOR IS THEREFORE NEVER A FLAKE:
# which datum lands in the sample is a function of how many consts the file holds and
# in what order, so the same session survives the same mutant every time, and a finding
# that arrives the week a session lands has been latent for as long as that file's
# shape. Re-running it is not a response.
set -euo pipefail

# A value may only be constrained beyond a threshold — a datum compared against a
# session maximum is not pinned by a +1 nudge, because the nudged value still loses to
# the maximum. That is a weak mutation operator, not a vacuous lemma, so escalate
# before calling a mutant a survivor.
#
# ESCALATE BOTH WAYS. Many claims here are ONE-SIDED: G056 is
# `sum(yachi.finesse_perfect) * sum(pinglamb.pieces) > sum(pinglamb.finesse_perfect) *
# sum(yachi.pieces)`, a single `>` over two pooled products, so every INCREASE to a
# datum on the winning side leaves it true. An upward-only ladder reports such a datum
# as unconstrained when it is merely constrained downward — a false alarm, not a
# finding. 2026-09-21's scheduled run is where that cost a red build:
# 2026-09-19's `m13_r2_yachi_finesse_perfect` is read by G056 and by nothing else, so
# raising it can falsify nothing and only a large enough DECREASE can. The size of that
# decrease, and the margin it comes from, are in CLAUDE.md and deliberately not repeated
# here: one home per figure, and a comment cannot go red.
#
# THE LADDER IS `check_smt.perturbations`', plus the `v*10 + 100000` rung this harness
# already had. One operator, two gates. The SMT gate learned both-ways escalation on
# its own one-sided case (`m4_r3_pinglamb_inputs`) and the lesson was written down for
# SMT alone, so the second copy of the operator drifted from the first for as long as
# nobody ran both against the same datum — which is this repo's standing 冇第二份 shape
# with a rule in place of a figure. Keeping the old rung too makes this ladder a
# superset of both, so no mutant that died before can survive now.
ladder_rungs() {   # $1 = value -> the rungs to try, in order, one per line
  local v=$1 rung seen=""
  for rung in $(( v + 1 )) $(( v - 1 )) $(( v + 1000 )) $(( v - 1000 )) \
              $(( v + 1000000 )) $(( v * 10 + 100000 )) 0; do
    # A rung equal to the original mutates nothing and a repeated rung re-asks a
    # question already answered; either one "surviving" is evidence of nothing at all,
    # so neither is reported as a probe. Both collide in practice — `v - 1000` is 0 at
    # v = 1000, and `v + 1000000` meets `v * 10 + 100000` at v = 100000.
    if [ "$rung" = "$v" ]; then continue; fi
    case ",$seen," in *",$rung,"*) continue ;; esac
    seen="${seen:+$seen,}$rung"
    echo "$rung"
  done
}

# `--ladder <value>` prints the ladder and exits, needing no dafny-dir and no dafny.
# `pipeline/check_mutation_ladder.py` is its only caller: it compares what this prints
# against what `check_smt.perturbations` would try, so the two gates cannot drift again
# without a red build. Printing rather than being PARSED is the point — a gate that a
# reformat of this file breaks is a gate whose normal state is red.
if [ "${1:-}" = "--ladder" ]; then
  ladder_rungs "${2:?usage: pipeline/mutation_test.sh --ladder <value>}"
  exit 0
fi

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

# Rungs escalate and the ladder short-circuits on the first kill, so the message names
# the SMALLEST perturbation that falsified something, and the extra dafny runs are paid
# only on the data that needed them. Adding a rung can only turn SURVIVED into killed,
# never the reverse.
run_escalating() {   # $1 = line, $2 = const name, $3 = value
  tried=$((tried + 1))
  local v=$3 rung probed=""
  local -a rungs
  # Read the ladder into an array FIRST. A `while read` over a process substitution
  # would hand its stdin to `dafny` inside the loop, which is how a harness silently
  # stops trying most of its rungs.
  mapfile -t rungs < <(ladder_rungs "$v")
  for rung in "${rungs[@]}"; do
    probed="${probed:+$probed,}$rung"
    if try_mutation "$1" "s/:= ${v}\$/:= ${rung}/"; then
      echo "  [$tried] killed    $2 $v -> $rung"
      killed=$((killed + 1))
      return
    fi
  done
  echo "  [$tried] SURVIVED  $2 (unconstrained at $v; tried ${probed//,/, })"
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
