#!/usr/bin/env bash
# mutation_test.sh — the anti-vacuity gate, as bin/verify-session expects to find it.
#
# All 106 lemmas of this session — 88 generated plus 18 hand — come out of
# pipeline/codegen.py into one dafny/, so there is nothing session-specific to do
# beyond pointing the shared script at it.
#
# Nothing emits this file. Not bin/new-session, not pipeline/skeleton.py; it is copied
# from the previous session by hand, and bin/verify-session REQUIRES it to exist —
# without it, step 6 prints "mutation test skipped (set MUTATION=1 to run it)" even
# when MUTATION=1 is set, which reads as a forgotten environment variable rather than
# a missing file. That is why the count above is worth keeping accurate: it is the only
# thing in this file that says which session it was copied for.
set -eu
cd "$(dirname "$0")"
exec bash ../../../pipeline/mutation_test.sh dafny "${1:-12}"
