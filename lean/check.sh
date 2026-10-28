#!/usr/bin/env bash
# The Lean gate for the route-order proofs: T1, T2, T4 (kernel-checked) and T3 (native_decide).
#
#   1. gen_data.py transcribes analysis/sdpcspin-orders.json into RouteOrders/Generated/ (gitignored)
#   2. lake build — T1/T2/T4 proofs, T3's 4 theorems per node (count and bitset, both modes), the
#      mutant discrimination theorems, the T1/T2/T4 mutant witnesses (T1Witness, HoldWitness), and
#      the INLINE axioms gate (#guard_msgs on #print axioms)
#   3. generator sanity check, NOT a gate: one T3 theorem family and one axioms guard per artefact
#      node. Both sides are read from the same JSON (gen_data.py writes the theorems from it, and the
#      node count is read back from it here), so this only catches gen_data.py dropping a node or a
#      guard; a wrong count is step 2's to catch (each T3 theorem equates Lean's own recount with it)
#   4. no proof hole anywhere in the sources (the build dir .lake/ is excluded: it is not source)
#   5. lake exe measure — the per-node mutant table (informational)
#
# The toolchain is pinned by lean-toolchain (leanprover/lean4:v4.35.0); no dependency, no network.
set -euo pipefail
cd "$(dirname "$0")"
export PATH="$HOME/.elan/bin:$PATH"

echo "== 1. generate T3 data"
python3 gen_data.py

echo "== 2. lake build (T3 checks run as native code; the counts module takes about a minute)"
lake build

echo "== 3. generator sanity check (theorems and guards per node; not a gate)"
nodes=$(python3 -c "import json; print(len(json.load(open('../analysis/sdpcspin-orders.json'))['nodes']))")
gen=RouteOrders/Generated/SdpcspinCounts.lean
for fam in empty next bits_empty bits_next; do
  n=$(grep -cE "^theorem n[0-9]+_${fam} :" "$gen" || true)
  g=$(grep -cE "^#print axioms RouteOrders\.Generated\.n[0-9]+_${fam}$" "$gen" || true)
  if [ "$n" != "$nodes" ] || [ "$g" != "$nodes" ]; then
    echo "check.sh: $fam: $n theorems and $g axioms guards for $nodes nodes" >&2; exit 1
  fi
  echo "  $fam: $n theorems, $g axioms guards, $nodes nodes"
done

echo "== 4. no proof hole in the sources"
for hole in 's''orry' 'ad''mit'; do   # spelled apart so this script does not match itself
  if grep -rnw "$hole" . --exclude-dir=.lake; then
    echo "check.sh: '$hole' found in the Lean sources" >&2; exit 1
  fi
done
echo "  none"

echo "== 5. per-node counts under each mutant (Discriminate.lean asserts on these)"
lake exe measure

echo "check.sh: OK"
