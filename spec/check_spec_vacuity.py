#!/usr/bin/env python3
"""
Vacuity gate for the HAND-WRITTEN spec.

`pipeline/check_lemma_vacuity.py` is the SMT gate over the GENERATED session claims. `spec/Forecast.dfy`
is hand written and outside it; until 2026-08-08 its only anti-vacuity coverage was a prose comment
listing three witnesses by hand.

The test: for each lemma that has hypotheses and does not `returns`, emit

    lemma Probe(<same params>) <same requires> ensures false { }

If Dafny PROVES that, the hypotheses are contradictory and the original lemma is vacuously true —
green verifier, no content.

ONE-DIRECTIONAL, and saying so is the point. A probe that verifies is proof of vacuity. A probe that
FAILS is not proof of the opposite: it may only mean Dafny could not derive `false` unaided. So the
output separates VACUOUS (proved) from `not shown` (no claim either way). Reporting the second as
"healthy" would be exactly the overclaim this gate exists to catch.

Two controls run every time, because a uniform verdict is the signature of a broken harness rather
than a finding — this repo has already shipped a vacuity gate that reported EVERY lemma vacuous
because of an awk bug, and `dafny verify` on a file with no lemmas prints "0 verified, 0 errors" and
exits 0. The poison control must be caught and the healthy control must not be; either failure exits 2.

    python3 spec/check_spec_vacuity.py [spec/Forecast.dfy]
"""
import os
import re
import subprocess
import sys

SRC = sys.argv[1] if len(sys.argv) > 1 else 'spec/Forecast.dfy'
ABS = os.path.abspath(SRC)
src = open(SRC).read()

LEMMA = re.compile(r'^  lemma\s+(\w+)\s*\(([^)]*)\)([^\{]*?)\n  \{', re.M | re.S)

CONTROLS = [
    # (name, params, requires, must_be_flagged)
    ('poison', 's: Step, a: int, b: int', ['a < b', 'b < a'], True),
    ('healthy', 's: Step, a: int', ['Survives(s, a)'], False),
]


def probe(name: str, params: str, reqs: list[str]) -> bool:
    """True when Dafny proves `false` from these hypotheses, i.e. they are contradictory."""
    body = '\n'.join(f'    requires {r}' for r in reqs)
    path = f'{os.environ.get("TMPDIR", "/tmp")}/vac_{name}.dfy'
    with open(path, 'w') as fh:
        fh.write(f'include "{ABS}"\nmodule Vac_{name} {{\n  import opened Forecast\n'
                 f'  lemma Probe({params})\n{body}\n    ensures false\n  {{ }}\n}}\n')
    out = subprocess.run(['dafny', 'verify', path], capture_output=True, text=True, timeout=300)
    return ', 0 errors' in out.stdout


bad_control = False
for name, params, reqs, must_flag in CONTROLS:
    got = probe(f'control_{name}', params, reqs)
    ok = (got == must_flag)
    print(f'control/{name:<8} flagged={got}  expected={must_flag}  {"ok" if ok else "HARNESS BROKEN"}')
    bad_control |= not ok
if bad_control:
    print('\nthe controls did not behave — every verdict below is meaningless', file=sys.stderr)
    sys.exit(2)

cases = []
for m in LEMMA.finditer(src):
    name, params, clauses = m.group(1), m.group(2), m.group(3)
    if 'returns' in clauses:
        continue                                  # a witness lemma must assign its outputs
    reqs = [r.strip() for r in re.findall(r'^\s*requires\s+(.+?)$', clauses, re.M)
            if not r.strip().startswith('//')]
    if reqs:
        cases.append((name, params.strip(), reqs))

print(f'\n{len(cases)} lemmas with hypotheses\n')
vacuous = []
for name, params, reqs in cases:
    hit = probe(name, params, reqs)
    if hit:
        vacuous.append(name)
    print(f'{"VACUOUS  " if hit else "not shown"}  {name}')

print(f'\nVACUOUS (hypotheses provably contradictory): {len(vacuous)}')
for n in vacuous:
    print(f'    {n}')
print(f'not shown (no claim either way): {len(cases) - len(vacuous)}')
sys.exit(1 if vacuous else 0)
