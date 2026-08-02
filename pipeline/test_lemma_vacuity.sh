#!/usr/bin/env bash
# Tests for pipeline/check_lemma_vacuity.py — a gate whose own failure mode is
# silence, so it needs planting as well as passing.
#
#   pipeline/test_lemma_vacuity.sh
#
# Each case builds a tiny claims.smt2 by hand, runs the gate on it and asserts both
# the exit code and what it said. The four cases that are not about finding a
# tautology are the ones that matter most: this gate's first version reported EVERY
# lemma vacuous because a name was mis-extracted, and the verifier it was driving
# printed "0 verified, 0 errors" and exited 0 on a file containing no lemmas. A
# harness that cannot fail loudly turns a broken parse into a clean report.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

pass=0
fail=0

# A minimal artefact in codegen_smt's shape: a legend, coded constants marked by the
# trailing `; label` the emitter writes, and plain measurements.
prelude() {
  cat <<'SMT'
; string codes:
; 1 = yachi
; 2 = pinglamb
; 3 = topout

(set-logic QF_NIA)
(define-fun m0_r0_yachi_apm () Int 100)
(define-fun m0_r0_pinglamb_apm () Int 90)
(define-fun m0_nrounds () Int 2)
(define-fun m0_winner () Int 1)  ; yachi
(define-fun m0_r0_yachi_gameoverreason () Int 3)  ; topout
SMT
}

block() {   # $1 = id, $2 = gloss, $3 = the term the claim asserts
  printf '\n; %s [demo] %s\n(push 1)\n(echo "%s")\n(assert (not %s))\n(check-sat)\n(pop 1)\n' \
    "$1" "$2" "$1" "$3"
}

# The two load-bearing claims every fixture carries, so a case is never testing an
# empty file by accident.
live_claims() {
  block G001 "yachi threw 100 APM in round 1"            '(= m0_r0_yachi_apm 100)'
  block G002 "yachi out-paced pinglamb in round 1"       '(> m0_r0_yachi_apm m0_r0_pinglamb_apm)'
  block G003 "round 1 ended in a topout"                 '(= m0_r0_yachi_gameoverreason 3)'
}

check() {   # $1 = name, $2 = expected rc (0 or 1), $3... = substrings that must appear
  local name="$1" want="$2"; shift 2
  local dir="$WORK/$name" out rc=0
  out="$(python3 -m pipeline.check_lemma_vacuity "$dir" 2>&1)" || rc=$?
  local bad=""
  [ "$rc" = "$want" ] || bad="exit $rc, expected $want"
  for want_text in "$@"; do
    case "$out" in *"$want_text"*) ;; *) bad="${bad:+$bad; }missing: $want_text" ;; esac
  done
  if [ -z "$bad" ]; then
    echo "  ok  $name"
    pass=$((pass + 1))
  else
    echo "FAIL  $name — $bad" >&2
    echo "$out" | sed 's/^/        | /' >&2
    fail=$((fail + 1))
  fi
}

new() { mkdir -p "$WORK/$1"; prelude > "$WORK/$1/claims.smt2"; }

# --- 1. a clean artefact passes, and says the controls discriminated ---------
# "0 vacuous" alone would also be printed by a harness that checks nothing, so the
# control line is part of what a green run has to show.
new clean; live_claims >> "$WORK/clean/claims.smt2"
check clean 0 "controls — 2 planted tautologies flagged, 1 real claim not" \
              "3 of 3 claims falsified by a concrete in-domain perturbation" \
              "0 not pinned at all"

# --- 2. the reported bug: a bound written with literals ---------------------
# 154 * 317 = 48818 <= 49000 holds whatever the session did. Per-CONSTANT mutation
# cannot see this: the claim reads no constant, so no constant survives because of it.
new literal; live_claims >> "$WORK/literal/claims.smt2"
block G004 "yachi's attack cleared the session bar" '(<= (* 154 317) (* 1000 49))' \
  >> "$WORK/literal/claims.smt2"
check literal 1 "G004 is vacuous: no assignment of the constants it reads falsifies it" \
                "yachi's attack cleared the session bar" "1 not pinned at all"

# --- 3. a tautology that DOES read its constants ----------------------------
# The shape a text search for the const name would clear, and the reason this gate
# asks the solver instead of counting references.
new reads; live_claims >> "$WORK/reads/claims.smt2"
block G005 "the two players' APM sum to something non-negative" \
  '(>= (+ m0_r0_yachi_apm m0_r0_pinglamb_apm) 0)' >> "$WORK/reads/claims.smt2"
check reads 1 "G005 is vacuous over the data" \
              "m0_r0_pinglamb_apm->-910, a value no extractor can produce"

# --- 4. a claim that is FALSE on the committed data aborts the run ----------
# Not "one vacuous claim" — no verdict at all. A vacuity result computed against a
# baseline that does not hold is not a weaker result, it is a meaningless one.
new false; live_claims >> "$WORK/false/claims.smt2"
block G006 "yachi threw 999 APM in round 1" '(= m0_r0_yachi_apm 999)' \
  >> "$WORK/false/claims.smt2"
check false 1 "G006: sat on the unmutated data" "the baseline does not hold"

# --- 5. an artefact with no claims at all -----------------------------------
# The exact shape of this gate's first bug: nothing was emitted, and the tool it
# drove answered "0 verified, 0 errors" and exited 0.
new empty
check empty 1 "defines no claims"

# --- 6. a block the parser cannot identify ----------------------------------
# Without the echo there is no id to pair a `sat` with, and check_smt's line-based
# parser would attach the answer to whatever id it saw last. The parse dies instead.
new noecho; live_claims >> "$WORK/noecho/claims.smt2"
printf '\n(push 1)\n(assert (not (= m0_nrounds 2)))\n(check-sat)\n(pop 1)\n' \
  >> "$WORK/noecho/claims.smt2"
check noecho 1 "has no (echo)"

# --- 7. a term the solver refuses is an error, never a verdict --------------
# `==` is how Python and Dafny spell equality and it is not SMT-LIB; the solver
# answers `unknown constant ==`. A token-based reader once counted the words inside
# such an error as claim ids and reported kills on a file that had been refused.
new badop; live_claims >> "$WORK/badop/claims.smt2"
block G007 "a term no solver accepts" '(== m0_nrounds 2)' >> "$WORK/badop/claims.smt2"
check badop 1 "errored, so nothing was checked"

# --- 8. a block the artefact never asks the solver about --------------------
# Missing `(check-sat)`, so the committed file itself never has this claim checked.
# The gate rebuilds every block and emits its own, which is why it still judges the
# claim: the verdict is about the claim's TERM, not about how the artefact happens
# to drive a solver. Locked in deliberately — the alternative is a gate that goes
# quiet on exactly the block that was already being skipped.
new unasked; live_claims >> "$WORK/unasked/claims.smt2"
printf '\n; G008 [demo] a block with no check-sat of its own\n(push 1)\n(echo "G008")\n(assert (not (= m0_nrounds 2)))\n(pop 1)\n' \
  >> "$WORK/unasked/claims.smt2"
check unasked 0 "4 of 4 claims falsified by a concrete in-domain perturbation"

# --- 9. two blocks claiming the same id -------------------------------------
# Answers are paired to ids by position in the solver's output, so a repeated id
# means one claim's verdict silently becomes the other's. Nothing downstream could
# tell; this refuses to produce a verdict at all.
new dupe; live_claims >> "$WORK/dupe/claims.smt2"
block G001 "a second claim wearing G001's id" '(= m0_nrounds 2)' >> "$WORK/dupe/claims.smt2"
check dupe 1 "answered for G001 twice"

# --- 10. a tautology that only the LEGEND makes one -------------------------
# "the winner is one of the names we have a code for" is falsifiable over the
# integers and unfalsifiable over the data, so it is caught only if coded constants
# are restricted to the legend rather than merely to non-negative — the same
# read-coded-ness-from-the-name rule check_smt's categorical operator follows.
new coded; live_claims >> "$WORK/coded/claims.smt2"
block G009 "the match had a winner with a name" \
  '(or (= m0_winner 1) (= m0_winner 2) (= m0_winner 3))' >> "$WORK/coded/claims.smt2"
check coded 1 "G009 is vacuous over the data" "no perturbation reaches it at all"

echo
echo "LEMMA VACUITY TEST: ${pass}/$((pass + fail)) passed"
[ "$fail" -eq 0 ]
