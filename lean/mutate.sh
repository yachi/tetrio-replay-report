#!/usr/bin/env bash
# Plant each T1/T2/T4 mutant into a COPY of this project and require the build to fail on it.
#
# Per mutant: copy the sources (not .lake/, not the generated T3 data) to a fresh temp dir, apply
# one exact-string patch (refused unless it matches exactly the expected number of times, so a
# patch that silently matched nothing cannot pass for a kill), build only the module it touches,
# and name every declaration an error lands in. A mutant is KILLED only if the build fails AND the
# declaration it targets is among the failures — either its own proof, or its inline axioms guard
# now showing a proof-hole axiom.
#
# A failing build shows a proof depends on the rule. Whether the rule is what makes the statement
# TRUE is shown elsewhere: T1Witness.lean (each T1 mutant is order-dependent on a concrete board,
# kernel decide) and Discriminate.lean (each T2/T4 mutant changes a count on the committed data, or
# is pinned as equivalent there with its reason).
#
# Temp dirs are left in place and printed (set MUTATE_CLEANUP=1 to remove them on exit).
set -euo pipefail
cd "$(dirname "$0")"
export PATH="$HOME/.elan/bin:$PATH"
here=$(pwd)
work=$(mktemp -d "${TMPDIR:-/tmp}/route-orders-mutants.XXXXXX")
if [ -n "${MUTATE_CLEANUP:-}" ]; then trap 'rm -rf "$work"' EXIT; fi
echo "mutate.sh: working in $work"

python3 - "$here" "$work" <<'PY'
import os, re, shutil, subprocess, sys

here, work = sys.argv[1], sys.argv[2]

T1_CLEAR_ROWS = ("  { rows := keep.map Prod.fst ++ List.replicate (b.rows.length - keep.length) emptyRow,\n"
                 "    rowmap := keep.map Prod.snd ++ List.replicate (b.rowmap.length - keep.length) none }")
T1_KEEP = "  let keep := (List.zip b.rows b.rowmap).filter (fun p => !full W p.1)"
HOLD_FIRST = ("  /-- (c) hold empty: hold the current token, place the next one -/\n"
              "  | holdFirst {s t t' r g} : t ≠ .star → t' ≠ .star → D.groupOf t' = some g → D.can s g = true →\n"
              "      Step D (s, t :: t' :: r, none) (s ||| bit g, r, some t)\n")
ACC_C = "(t != .star) && (match place D s t' with"

MUTANTS = [
    # control: the unpatched copy must BUILD, or every "kill" below could be the copy's fault
    ('control (no patch)', 'RouteOrders/Hold.lean', [], 'RouteOrders.Hold RouteOrders.T1', []),
    # (id, file, [(old, new, expected count)], module, target declarations (any one suffices))
    ('T1 clear without compaction', 'RouteOrders/T1.lean',
     [(T1_CLEAR_ROWS,
       "  { rows := b.rows.map (fun r => if full W r then emptyRow else r),\n"
       "    rowmap := keep.map Prod.snd ++ List.replicate (b.rowmap.length - keep.length) none }", 1)],
     'RouteOrders.T1', ['order_independent']),
    ('T1 clear a row that is not full (the one above a full row)', 'RouteOrders/T1.lean',
     [(T1_KEEP,
       "  let keep := ((List.zip b.rows b.rowmap).zip (false :: b.rows.map (full W))).filter"
       " (fun q => !q.2) |>.map Prod.fst", 1)],
     'RouteOrders.T1', ['order_independent']),
    ('T2 drop case (c)', 'RouteOrders/Hold.lean',
     [(HOLD_FIRST, "", 1)],
     'RouteOrders.Hold', ['acc_iff_reaches']),
    ("T2 allow placing '*'", 'RouteOrders/Hold.lean',
     [(HOLD_FIRST, HOLD_FIRST +
       "  | playStar {s r h g} : D.can s g = true → Step D (s, .star :: r, h) (s ||| bit g, r, h)\n", 1)],
     'RouteOrders.Hold', ['acc_iff_reaches']),
    ('T2 hold step without a placement', 'RouteOrders/Hold.lean',
     [(HOLD_FIRST, HOLD_FIRST +
       "  | holdOnly {s t r h} : t ≠ .star → Step D (s, t :: r, h) (s, r, some t)\n", 1)],
     'RouteOrders.Hold', ['acc_iff_reaches']),
    # case (c) removed from the procedure AND the specification AND acc's own equation lemma, so T2's
    # statement stays consistent and what can fail is the T4 argument
    ('T4 under a missing case (c)', 'RouteOrders/Hold.lean',
     [(HOLD_FIRST, "", 1), (ACC_C, "false && (match place D s t' with", 2)],
     'RouteOrders.Hold', ['acc_cons_none', 'empty_eq_next']),
]

DECL = re.compile(r'^(?:private )?(?:theorem|lemma|def|abbrev|inductive|structure)\s+([^\s:(]+)')
GUARD = re.compile(r'^#print axioms\s+(\S+)')
ERR = re.compile(r'^error: ([^:]+\.lean):(\d+):\d+:')


def owner(lines, n):
    """The declaration an error at 1-based line n belongs to. An error inside an axioms-guard block
    (docstring, `#guard_msgs in`, `#print axioms X`, no blank line between) is attributed to the
    guard of X."""
    for k in range(n - 1, min(n + 5, len(lines))):
        if not lines[k].strip():
            break
        m = GUARD.match(lines[k])
        if m:
            return 'axioms(' + m.group(1).split('.')[-1] + ')'
    for k in range(n - 1, -1, -1):
        m = DECL.match(lines[k])
        if m:
            return m.group(1)
    return '?'


killed = 0
for idx, (name, rel, patches, module, targets) in enumerate(MUTANTS):
    d = os.path.join(work, f'm{idx}')
    os.makedirs(os.path.join(d, 'RouteOrders'))
    for f in ('lakefile.toml', 'lean-toolchain'):
        shutil.copy(os.path.join(here, f), d)
    for f in os.listdir(os.path.join(here, 'RouteOrders')):
        if f.endswith('.lean'):
            shutil.copy(os.path.join(here, 'RouteOrders', f), os.path.join(d, 'RouteOrders'))
    path = os.path.join(d, rel)
    src = open(path, encoding='utf-8').read()
    for old, new, count in patches:
        got = src.count(old)
        if got != count:
            sys.exit(f'mutate.sh: {name}: patch matches {got} times, expected {count} — refusing')
        src = src.replace(old, new)
    if patches and src == open(os.path.join(here, rel), encoding='utf-8').read():
        sys.exit(f'mutate.sh: {name}: patch left the file unchanged')
    open(path, 'w', encoding='utf-8').write(src)
    print(f'-- {name}: lake build {module} in {d}', flush=True)
    r = subprocess.run(['lake', 'build', *module.split()], cwd=d, capture_output=True, text=True)
    out = r.stdout + r.stderr
    lines = src.split('\n')
    failing = []
    for line in out.split('\n'):
        m = ERR.match(line)
        if m and m.group(1) == rel:
            o = owner(lines, int(m.group(2)))
            if o not in failing:
                failing.append(o)
    if not patches:
        if r.returncode != 0:
            sys.exit(f'mutate.sh: the unpatched control copy does not build:\n{out}')
        print('   control builds (exit 0)', flush=True)
        continue
    hit = [t for t in targets if t in failing or f'axioms({t})' in failing]
    ok = r.returncode != 0 and bool(hit)
    killed += ok
    print(f'   build exit {r.returncode}; failing: {", ".join(failing) or "-"}', flush=True)
    print(f'   {"KILLED" if ok else "SURVIVED"} (target {" / ".join(targets)}'
          f'{": hit " + ", ".join(hit) if hit else ": not hit"})', flush=True)

planted = sum(1 for m in MUTANTS if m[2])
print(f'mutate.sh: {killed} of {planted} mutants killed')
sys.exit(0 if killed == planted else 1)
PY
