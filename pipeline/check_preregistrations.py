"""A pre-registration is a script plus a pinned hash plus a gate, or it is a wish.

Why this exists as a gate rather than a paragraph in ROADMAP.md. `## Open — 2026-08-07` item 1
pre-registered `downstack rate under pressure` and said: bank sessions, then test once. Nothing was
breached — the registration predates every session it governs — but in the eleven days that followed,
two sessions landed (08-09, 08-14) and the instrument moved underneath the registration twice
(hoisted-DAS lengthened the verified prefix ~31%, `c9f3065`; the board source became `runCaseOracle`,
`a38ccc1`). Both changes were improvements made blind to this hypothesis. Neither was noticed *by the
registration*, because a registration written in prose has nothing that can notice.

That is the third time in one week this repo has measured the same shape: an obligation with no gate
does not survive contact with its own velocity. `check_cross_artefact` was the second (two artefacts
of one session drifting apart because `verify-session` only ever saw one directory at a time), and
the ROADMAP audit of 2026-08-16 was the first (six items filed open that were already done).

So the ledger (`pipeline/preregistrations.json`) carries the three things prose cannot enforce:

  * WHICH SESSIONS ARE WHICH. `exploratory` sessions were used to find the effect and can never
    confirm it; `banked` sessions are held for the confirmatory test; `tested` sessions have been
    spent. Sessions are DISCOVERED by glob, the `check_cross_artefact` pattern, so a seventh session
    fails this gate the moment it is added rather than the moment someone remembers the ledger.
    An unclassified session is a failure, not a default — a default is how a new session quietly
    joins the exploratory pile and dilutes the very thing being held out.
  * WHAT THE INSTRUMENT IS, by commit hash. Not "as `board-metrics.ts` computes it today" — that
    sentence is what went ambiguous. The pin plus the estimand's import closure is a set of bytes.
  * WHAT MOVED, dated. Every advance of the pin needs a deviation entry, and the last entry's
    `pin_to` must BE the current pin, so the pin cannot be advanced silently.

The estimand's files are not enumerated in the ledger; they are the **import closure** of
`estimand_entry`, walked at check time. Enumeration would go stale exactly when it mattered — the
first time someone adds an import. Walking from HEAD is sufficient to catch a *removed* dependency
too: dropping an import means editing a file that is itself in the closure.

The drift check diffs the pin against the WORKING TREE, not against HEAD. In CI the two are the same
thing; locally it fires before the commit rather than after, which is when it is still cheap.

    python3 -m pipeline.check_preregistrations [root]
    python3 -m pipeline.check_preregistrations --selftest
"""
from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

LEDGER = 'pipeline/preregistrations.json'
STATUSES = {'exploratory', 'banked', 'tested'}
# a relative specifier in an import/export ... from '...' — .ts and .mjs alike
SPEC = re.compile(r"""(?:from|import)\s*\(?\s*['"](\.[^'"]+)['"]""")


def closure(root: pathlib.Path, entry: str) -> list[str]:
    """Every repo file the estimand transitively imports, `entry` included."""
    seen: set[str] = set()
    stack = [entry]
    while stack:
        rel = stack.pop()
        if rel in seen:
            continue
        p = root / rel
        if not p.is_file():
            continue
        seen.add(rel)
        for spec in SPEC.findall(p.read_text()):
            t = (p.parent / spec).resolve()
            for cand in (t, t.with_suffix('.ts')):
                if cand.is_file():
                    stack.append(str(cand.relative_to(root.resolve())))
                    break
    return sorted(seen)


def git(root: pathlib.Path, *args: str) -> tuple[int, str]:
    r = subprocess.run(['git', *args], cwd=root, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def check(root: pathlib.Path) -> list[str]:
    problems: list[str] = []
    ledger_path = root / LEDGER
    if not ledger_path.is_file():
        return [f'{LEDGER} is missing — a pre-registration with no ledger is a wish']
    reg = json.loads(ledger_path.read_text())

    # sessions are DISCOVERED, never listed: a directory holding replays is a session
    on_disk = {d.name for d in sorted((root / 'sessions').glob('*'))
               if d.is_dir() and any(d.glob('*.ttrm'))}

    for name, r in sorted(reg.items()):
        classified = set(r['sessions'])
        for s in sorted(on_disk - classified):
            problems.append(f'{name}: session {s} is not classified in {LEDGER}. Every session is '
                            f'exploratory, banked or tested before it is anything else.')
        for s in sorted(classified - on_disk):
            problems.append(f'{name}: {LEDGER} classifies {s}, which holds no replays on disk')
        for s, st in sorted(r['sessions'].items()):
            if st not in STATUSES:
                problems.append(f'{name}: session {s} has status {st!r}, not one of {sorted(STATUSES)}')

        # the pin may only ever be what the last dated deviation says it is
        devs = r.get('deviations', [])
        last = devs[-1]['pin_to'] if devs else None
        if last != r['pinned_commit']:
            problems.append(
                f'{name}: pinned_commit is {r["pinned_commit"][:12]} but the last deviation pins to '
                f'{(last or "nothing")[:12]}. Advancing a pin needs a dated deviation entry.')

        # has the instrument moved since the pin?
        files = closure(root, r['estimand_entry'])
        rc, out = git(root, 'diff', '--name-only', r['pinned_commit'], '--', *files)
        if rc != 0:
            problems.append(f'{name}: cannot diff against pinned commit {r["pinned_commit"][:12]}: {out}')
        elif out:
            moved = out.splitlines()
            problems.append(
                f'{name}: the estimand has moved since the pin ({len(moved)} of {len(files)} files: '
                f'{", ".join(moved[:4])}{" ..." if len(moved) > 4 else ""}). Record a dated deviation '
                f'entry saying what changed and why, then advance pinned_commit to its pin_to.')
    return problems


def selftest() -> int:
    """Both mutants, against a COPY of the tree — never in place."""
    root = pathlib.Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as tmp:
        d = pathlib.Path(tmp) / 'tree'
        rc, out = git(root, 'clone', '--quiet', '--no-hardlinks', str(root), str(d))
        if rc != 0:
            print(f'SELFTEST FAIL: could not clone the tree: {out}', file=sys.stderr)
            return 1
        shutil.copy(root / LEDGER, d / LEDGER)          # the ledger may not be committed yet
        shutil.copy(pathlib.Path(__file__), d / 'pipeline' / pathlib.Path(__file__).name)

        if check(d):
            print(f'SELFTEST FAIL: the pristine tree was reported: {check(d)}', file=sys.stderr)
            return 1

        # mutant 1 — a seventh session lands and nobody classifies it
        seventh = d / 'sessions' / '2026-08-21'
        seventh.mkdir()
        (seventh / 'replay-2026-08-21-1.ttrm').write_text('{}')
        found = check(d)
        if not any('2026-08-21 is not classified' in p for p in found):
            print(f'SELFTEST FAIL: an unclassified session was not reported, got {found}',
                  file=sys.stderr)
            return 1
        shutil.rmtree(seventh)

        # mutant 2 — the estimand drifts past its pin with no deviation entry
        est = d / json.loads((d / LEDGER).read_text())['downstack-under-pressure']['estimand_entry']
        est.write_text(est.read_text() + '\n// drift\n')
        found = check(d)
        if not any('has moved since the pin' in p for p in found):
            print(f'SELFTEST FAIL: estimand drift was not reported, got {found}', file=sys.stderr)
            return 1

        # ... and a deviation entry ALONE does not clear it. The pin must advance too, or the
        # disclosure could be written once and hold the gate open for good.
        led = json.loads((d / LEDGER).read_text())
        led['downstack-under-pressure']['deviations'].append(
            {'date': '2026-08-21', 'what': 'x', 'why': 'y',
             'pin_from': '5ee57969ecc5f6b31f5a85cf562349c2335c549e',
             'pin_to': '5ee57969ecc5f6b31f5a85cf562349c2335c549e'})
        (d / LEDGER).write_text(json.dumps(led))
        if not any('has moved since the pin' in p for p in check(d)):
            print('SELFTEST FAIL: a deviation entry alone cleared the drift', file=sys.stderr)
            return 1
    print('selftest ok — an unclassified session and an unpinned estimand drift are both rejected, '
          'and a deviation entry alone does not clear the drift')
    return 0


def main(argv: list[str]) -> int:
    if '--selftest' in argv:
        return selftest()
    root = pathlib.Path(argv[1]).resolve() if len(argv) > 1 else pathlib.Path(__file__).resolve().parents[1]
    problems = check(root)
    for p in problems:
        print('FAIL  ' + p, file=sys.stderr)
    if problems:
        print(f'{len(problems)} pre-registration problem(s)', file=sys.stderr)
        return 1
    reg = json.loads((root / LEDGER).read_text())
    for name, r in sorted(reg.items()):
        n = len(closure(root, r['estimand_entry']))
        banked = sum(1 for s in r['sessions'].values() if s == 'banked')
        print(f'ok — {name}: {n} estimand files unchanged since {r["pinned_commit"][:12]}, '
              f'{len(r["sessions"])} sessions classified ({banked} banked), '
              f'{len(r.get("deviations", []))} deviation(s) recorded')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
