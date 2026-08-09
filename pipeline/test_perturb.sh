#!/usr/bin/env bash
# Tests for pipeline/perturb.py — and, more to the point, for the assertions that make
# in-place mutation safe to substitute for copy.deepcopy.
#
#   pipeline/test_perturb.sh [report-dir]      # default sessions/2026-08-01/report
#
# The report dir is an argument so the CI matrix runs case 5 against ITS OWN session rather
# than five times against one — the same wall clock, five different fact bases. An artefact
# with no generated ledger (sessions/2026-07-24/proof) has nothing for check_rate_coverage
# to perturb, so cases 5 and 6 skip there rather than failing.
#
# deepcopy could not corrupt the original; make/unmake can. That is the whole risk of the
# change, and it is a SILENT risk: a sweep that restores 4 439 of 4 440 sites still prints
# a coverage figure, still exits 0, and is simply wrong. So the callers fingerprint the
# tree either side of their sweep — and a guard nobody has watched fail is decorative.
#
# Cases 1-4 are the module's own properties. Case 5 is the one that matters: it PLANTS a
# broken restore in perturb.py and requires check_rate_coverage to die on it. If that case
# ever passes silently, the fingerprint assertion has stopped working and the deepcopy
# removal is no longer justified.
set -euo pipefail

REPORT_ARG="${1:-}"
cd "$(dirname "${BASH_SOURCE[0]}")/.."
SESSION="${REPORT_ARG:-sessions/2026-08-01/report}"
pass=0
fail=0
skip=0

ok()   { echo "  ok  $1"; pass=$((pass + 1)); }
bad()  { echo "  FAIL $1"; fail=$((fail + 1)); }
check() { if [ "$2" = "$3" ]; then ok "$1"; else bad "$1 (got '$2', want '$3')"; fi; }

# --- 1. a write is visible inside the block and gone after it -----------------
OUT=$(python3 - <<'PY'
from pipeline.perturb import perturbed
d = {"a": 1, "b": {"c": 2}}
with perturbed([(d, "a", 99), (d["b"], "c", 77)]):
    inside = (d["a"], d["b"]["c"])
print(inside == (99, 77) and d == {"a": 1, "b": {"c": 2}})
PY
)
check "applies inside the block and restores after it" "$OUT" "True"

# --- 2. list indices restore too ----------------------------------------------
OUT=$(python3 - <<'PY'
from pipeline.perturb import perturbed
xs = [1, 2, 3]
with perturbed([(xs, 1, 42)]):
    inside = list(xs)
print(inside == [1, 42, 3] and xs == [1, 2, 3])
PY
)
check "restores a list element" "$OUT" "True"

# --- 3. an exception inside the block still restores ---------------------------
# equiv.py deliberately evaluates predicates that raise (a mutation can break an index)
# and scores them as None, so this is the normal path there, not an edge case.
OUT=$(python3 - <<'PY'
from pipeline.perturb import perturbed
d = {"a": 1}
try:
    with perturbed([(d, "a", 5)]):
        raise ValueError("predicate blew up")
except ValueError:
    pass
print(d == {"a": 1})
PY
)
check "restores when the block raises" "$OUT" "True"

# --- 4. two writes to the SAME slot unwind to the original, not to the middle --
OUT=$(python3 - <<'PY'
from pipeline.perturb import perturbed
d = {"a": 1}
with perturbed([(d, "a", 2), (d, "a", 3)]):
    inside = d["a"]
print(inside == 3 and d["a"] == 1)
PY
)
check "unwinds repeated writes to the original value" "$OUT" "True"

# --- 5. PLANTED: break the restore, and the caller must die --------------------
# The gate under test is check_rate_coverage, which perturbs 100-164 constants per
# session. With the undo loop disabled every one of them stays raised, so later rounds
# are judged against a corrupted baseline — in the direction that makes the gate PASS,
# hiding a hole rather than inventing one. Only the fingerprint assertion can see it.
if [ ! -f "$SESSION/claims-generated.json" ]; then
  echo "  --  $SESSION has no generated ledger, nothing for the gate to perturb"
  skip=2
else
cp pipeline/perturb.py pipeline/perturb.py.testbak
restore_module() { mv -f pipeline/perturb.py.testbak pipeline/perturb.py 2>/dev/null || true; }
trap restore_module EXIT

python3 - <<'PY'
import re
src = open("pipeline/perturb.py").read()
broken = src.replace(
    "        for container, key, old in reversed(undo):\n            container[key] = old",
    "        for container, key, old in reversed(undo):\n            pass  # PLANTED: restore disabled")
assert broken != src, "the planting patch did not apply — test_perturb.sh needs updating"
open("pipeline/perturb.py", "w").write(broken)
PY

set +e
PLANTED_OUT="$(python3 -m pipeline.check_rate_coverage "$SESSION" 2>&1)"
PLANTED_RC=$?
set -e
restore_module
trap - EXIT

if [ "$PLANTED_RC" -eq 0 ]; then
  bad "a disabled restore was NOT caught — the fingerprint assertion is decorative"
elif echo "$PLANTED_OUT" | grep -q "did not restore facts"; then
  ok "a disabled restore is caught by the fingerprint assertion"
else
  bad "a disabled restore failed for the wrong reason: $(echo "$PLANTED_OUT" | tail -1)"
fi

# --- 6. and the real module still passes that same gate ------------------------
if python3 -m pipeline.check_rate_coverage "$SESSION" >/dev/null 2>&1; then
  ok "the unplanted module passes the gate (the plant was restored)"
else
  bad "the gate does not pass after restoring perturb.py"
fi
fi

echo
echo "PERTURB TESTS [$SESSION]: ${pass} passed, ${fail} failed, ${skip} skipped"
[ "$fail" -eq 0 ]
