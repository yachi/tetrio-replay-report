#!/usr/bin/env bash
# Plant each T1/T2/T4 mutant into a COPY of this project and require a WITNESS to be refuted by it.
#
# Per mutant: copy the sources (not .lake/, not the generated T3 data) to a fresh temp dir, apply
# exact-string patches (each refused unless it matches exactly the expected number of times, so a
# patch that silently matched nothing cannot pass for a kill), build the witness module and the proof
# module as SEPARATE lake invocations (lake does not build a module whose import failed, so the
# witnesses import only the model files, `T1Defs` / `HoldDefs`, which is where the mutants go), and
# attribute every error to the declaration it lands in.
#
# The verdict is semantic, not "the build failed":
#   KILLED      no error is an elaboration/name error, AND an error lands directly in (not in the
#               axioms guard of) a declaration on the mutant's expected list and is a REFUTATION
#               ("Tactic `decide` proved that the proposition ... is false"): a witness theorem whose
#               real half the mutant makes false (T1Witness.w1_real / w2_real, the
#               HoldWitness.*_witness theorems);
#   UNRESOLVED  the build failed, but an error is an elaboration/name error ("Invalid alternative
#               name", "has not been provided", "Unknown constant", "Unknown identifier", "Too many
#               variable names"), i.e. the mutant did not reach a proof obligation at all, or no
#               error landed on the expected list;
#   SURVIVED    everything built.
# The script exits nonzero unless every planted mutant is KILLED.
#
# Why the T2/T4 mutants are planted into the PROCEDURE `acc` and not into `Step`: adding or removing
# a constructor of an inductive breaks every `cases` on it by NAME (that is all the previous version
# of this script measured: each T2/T4 "kill" was an elaboration error in `acc_of_step`). Changing a
# disjunct of `acc` keeps every proof elaborating and makes a statement false instead. Each planted
# `acc` mutant is the procedure-side image of a specification mutant: on the witness's single toy
# input it gives the mutated relation's verdict (shown for that input only, not in general), so the witness's real half
# (`acc ... = true/false`, by `decide`) is what fails. `Hold.lean`'s errors are printed but do not
# decide the verdict, and they are not refutations of T2: under the T2 mutants the first failures
# there are `acc`'s equation lemmas (`acc_some` / `acc_none_one` / `acc_none_two`, whose stated shape
# no longer matches), and only the T4 mutant fails inside the T4 argument (`acc_cons_none`).
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
ACC_C = "(t != .star) && (match place D s t' with"
ACC_AFTER_PLAY = "    || (match h with\n        | some th => (match place D s th with\n"

T1_BUILDS = [['RouteOrders.T1Witness'], ['RouteOrders.T1']]
HOLD_BUILDS = [['RouteOrders.HoldWitness'], ['RouteOrders.Hold']]

MUTANTS = [
    # (id, [(file, old, new, expected count)], builds, expected declarations (any one suffices))
    # control: the unpatched copy must build every module below, witnesses included, or a "kill"
    # could be the copy's fault
    ('control (no patch)', [], T1_BUILDS + HOLD_BUILDS, []),
    ('T1 clear without compaction',
     [('RouteOrders/T1Defs.lean', T1_CLEAR_ROWS,
       "  { rows := b.rows.map (fun r => if full W r then emptyRow else r),\n"
       "    rowmap := keep.map Prod.snd ++ List.replicate (b.rowmap.length - keep.length) none }", 1)],
     T1_BUILDS, ['w1_real']),
    ('T1 clear a row that is not full (the one above a full row)',
     [('RouteOrders/T1Defs.lean', T1_KEEP,
       "  let keep := ((List.zip b.rows b.rowmap).zip (false :: b.rows.map (full W))).filter"
       " (fun q => !q.2) |>.map Prod.fst", 1)],
     T1_BUILDS, ['w2_real']),
    # T2: the procedure no longer has case (c), while `Step` keeps it
    ('T2 drop case (c) (acc without holdFirst)',
     [('RouteOrders/HoldDefs.lean', ACC_C, "false && (match place D s t' with", 1)],
     HOLD_BUILDS, ['noHoldFirst_witness']),
    # T2: the procedure also places '*', as any group < 7 the DAG allows (HoldMutants' starWild)
    ("T2 allow placing '*' (acc with playStar)",
     [('RouteOrders/HoldDefs.lean', ACC_AFTER_PLAY,
       "    || (t == .star && (List.range 7).any (fun g => D.can s g && acc D (s ||| bit g) r h))\n"
       + ACC_AFTER_PLAY, 1)],
     HOLD_BUILDS, ['playStar_witness']),
    # T2: the procedure also has a hold move that places nothing (HoldMutants' holdOnly)
    ('T2 hold step without a placement (acc with holdOnly)',
     [('RouteOrders/HoldDefs.lean', ACC_AFTER_PLAY,
       "    || (t != .star && acc D s r (some t))\n" + ACC_AFTER_PLAY, 1)],
     HOLD_BUILDS, ['holdOnly_witness']),
    # T4: case (c) removed from the procedure AND from acc's own equation lemma (`acc_none_two`), so
    # that lemma still holds and what fails is the T4 argument and the T4 witness
    ('T4 under a missing case (c)',
     [('RouteOrders/HoldDefs.lean', ACC_C, "false && (match place D s t' with", 1),
      ('RouteOrders/Hold.lean', ACC_C, "false && (match place D s t' with", 1)],
     HOLD_BUILDS, ['noCaseC_T4_witness']),
]

ELAB = ('invalid alternative name', 'has not been provided', 'unknown constant', 'unknown identifier',
        'too many variable names')

REFUTED = 'Tactic `decide` proved that the proposition'

DECL = re.compile(r'^(?:private )?(?:theorem|lemma|def|abbrev|inductive|structure)\s+([^\s:(]+)')
GUARD = re.compile(r'^#print axioms\s+(\S+)')
ERR = re.compile(r'^error: ([^:]+\.lean):(\d+):\d+: ?(.*)$')


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


counts = {'KILLED': 0, 'UNRESOLVED': 0, 'SURVIVED': 0}
for idx, (name, patches, builds, targets) in enumerate(MUTANTS):
    d = os.path.join(work, f'm{idx}')
    os.makedirs(os.path.join(d, 'RouteOrders'))
    for f in ('lakefile.toml', 'lean-toolchain'):
        shutil.copy(os.path.join(here, f), d)
    for f in os.listdir(os.path.join(here, 'RouteOrders')):
        if f.endswith('.lean'):
            shutil.copy(os.path.join(here, 'RouteOrders', f), os.path.join(d, 'RouteOrders'))
    for rel, old, new, count in patches:
        path = os.path.join(d, rel)
        src = open(path, encoding='utf-8').read()
        got = src.count(old)
        if got != count:
            sys.exit(f'mutate.sh: {name}: patch on {rel} matches {got} times, expected {count} — refusing')
        new_src = src.replace(old, new)
        if new_src == src:
            sys.exit(f'mutate.sh: {name}: patch left {rel} unchanged')
        open(path, 'w', encoding='utf-8').write(new_src)
    errors = []   # (file, owner, first line of the message), every .lean file, not only the patched one
    codes = []
    for mods in builds:
        print(f'-- {name}: lake build {" ".join(mods)} in {d}', flush=True)
        r = subprocess.run(['lake', 'build', *mods], cwd=d, capture_output=True, text=True)
        codes.append(r.returncode)
        for line in (r.stdout + r.stderr).split('\n'):
            m = ERR.match(line)
            if not m:
                continue
            rel = m.group(1)
            lines = open(os.path.join(d, rel), encoding='utf-8').read().split('\n')
            e = (rel, owner(lines, int(m.group(2))), m.group(3).strip())
            if e not in errors:
                errors.append(e)
    if not patches:
        if any(codes):
            sys.exit(f'mutate.sh: the unpatched control copy does not build: {errors}')
        print('   control builds every module (exit 0)', flush=True)
        continue
    for rel, o, msg in errors:
        print(f'   error in {rel} [{o}]: {msg[:110]}', flush=True)
    elab = [e for e in errors if any(p in e[2].lower() for p in ELAB)]
    # a kill is a REFUTATION: decide evaluated the witness's real half and found it false (a decide
    # that could not evaluate, or any other error on the target, does not count)
    hit = sorted({o for _, o, msg in errors if o in targets and REFUTED in msg})
    if not any(codes):
        verdict, why = 'SURVIVED', 'every module built'
    elif elab:
        verdict, why = 'UNRESOLVED', f'elaboration/name error in {elab[0][0]} [{elab[0][1]}]'
    elif hit:
        verdict, why = 'KILLED', f'refuted {", ".join(hit)}'
    else:
        verdict, why = 'UNRESOLVED', f'expected {" / ".join(targets)} not hit'
    counts[verdict] += 1
    print(f'   {verdict} (build exits {codes}; {why})', flush=True)

planted = sum(1 for m in MUTANTS if m[1])
print(f'mutate.sh: {planted} planted: {counts["KILLED"]} killed, {counts["UNRESOLVED"]} unresolved, '
      f'{counts["SURVIVED"]} survived')
sys.exit(0 if counts['KILLED'] == planted else 1)
PY
