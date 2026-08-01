#!/usr/bin/env bash
# mutation_test.sh — the anti-vacuity gate, as bin/verify-session expects to find it.
#
# All 84 lemmas of this session come out of pipeline/codegen.py into one dafny/, so
# there is nothing session-specific to do beyond pointing the shared script at it.
set -eu
cd "$(dirname "$0")"
exec bash ../../../pipeline/mutation_test.sh dafny "${1:-12}"
