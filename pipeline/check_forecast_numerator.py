"""Every count of forecast records must come from `isVerifiedForecast`, not a hand-rolled predicate.

Why this exists as a gate rather than a habit. For weeks four published reports carried a
split-half reliability figure (0.139 / 0.099 and worse) computed by `validity-checks.ts` with
`recs.filter(x => x.kind !== 'reactive').length` — the numerator `isVerifiedForecast` was written
to abolish, the one that predates clauses 2 and 4 and counts every opener. `forecast.ts` even
asserts the opposite in a comment: "every consumer already routes its numerator through this one
predicate." That was false, and nothing caught it, because:

  * The stale numerator never went *stale*. `pairs.ts` grew a source fingerprint after the
    2026-08-05 cache incident, but `validity-checks.ts` never called `isVerifiedForecast` at all,
    so it was computing something else from the start — a fingerprint cannot catch that.
  * `check_forecast_section.py` re-renders and compares, but both sides are downstream of the
    numerator, so it is blind to it by construction.

The defect is that `ForecastRecord.kind` is public, so a *count* of forecasts is something anyone
can re-derive. The real fix is a branded `VerifiedCount` type that makes the re-derivation a
compile error — but this tree has no typechecker (no tsconfig, no tsc step), so a brand is
enforced by nothing here. Until that lands, this scanner is the enforcement.

The rule: outside `forecast.ts` (the definition) and the tests, no `.filter(...)` whose predicate
mentions `.kind` may be immediately `.length`-ed. Bucketing BY kind stays legal — the four-bucket
tally in `emit-forecast-facts.ts` is correct and required; producing a *count* is not.

Like the other gates here it answers one question, needs no dependencies, and can be demonstrated
to fail (`--selftest`).

    python3 -m pipeline.check_forecast_numerator [root]
    python3 -m pipeline.check_forecast_numerator --selftest
"""
from __future__ import annotations

import pathlib
import re
import sys
import tempfile

# A `.filter(<predicate mentioning .kind>).length`, on one line. The `(?!\)\.length)` guards keep
# the match from straddling an unrelated `.length` further along the line, which is what made a
# blunter "any .kind comparison" version fire on the legitimate bucket tally and comments.
COUNT = re.compile(r"\.filter\((?:(?!\)\.length)[^\n])*?\.kind(?:(?!\)\.length)[^\n])*?\)\.length")

SKIP_DIRS = {'node_modules', '.git', 'vendor'}
# forecast.ts DEFINES isVerifiedForecast and the kinds; tests build fixtures freely; the mutation
# harness stores source strings verbatim (it re-derives the stale numerator on purpose, and its
# find-strings are round-tripped against forecast.ts, so a drift there fails that harness instead).
ALLOW_NAMES = {'forecast.ts', 'mutate-forecast.ts'}


def scan(root: pathlib.Path) -> list[str]:
    problems: list[str] = []
    for f in sorted(root.rglob('*.ts')):
        if SKIP_DIRS & set(f.parts):
            continue
        if f.name in ALLOW_NAMES or f.name.endswith('.test.ts'):
            continue
        for i, line in enumerate(f.read_text().splitlines(), 1):
            if COUNT.search(line):
                problems.append(f'{f.relative_to(root)}:{i}  {line.strip()}')
    return problems


def selftest() -> int:
    """Plant a count-by-kind and require rejection — and require the legitimate tally to pass."""
    with tempfile.TemporaryDirectory() as tmp:
        d = pathlib.Path(tmp)
        # legitimate: bucketing BY kind, not counting; must NOT fire
        (d / 'ok.ts').write_text(
            'for (const r of recs) if (r.kind === "forecast_garbage") p.fg++;\n'
            'const buckets = recs.filter(x => x.kind === "reactive");\n')  # no .length -> not a count
        if scan(d):
            print(f'SELFTEST FAIL: a legitimate kind use was reported: {scan(d)}', file=sys.stderr)
            return 1
        # the defect: a hand-rolled numerator
        (d / 'bad.ts').write_text(
            '  fc: recs.filter(x => x.kind !== "reactive").length,\n')
        found = scan(d)
        if len(found) != 1 or 'bad.ts' not in found[0]:
            print(f'SELFTEST FAIL: expected exactly the planted numerator, got {found}',
                  file=sys.stderr)
            return 1
    print('selftest ok — the gate rejects a count-by-kind and passes a bucket tally')
    return 0


def main(argv: list[str]) -> int:
    if '--selftest' in argv:
        return selftest()
    root = pathlib.Path(argv[1]).resolve() if len(argv) > 1 else pathlib.Path(__file__).resolve().parents[1]
    problems = scan(root)
    for p in problems:
        print('FAIL  ' + p, file=sys.stderr)
    if problems:
        print(f'{len(problems)} forecast count(s) not routed through isVerifiedForecast', file=sys.stderr)
        return 1
    n = sum(1 for f in root.rglob('*.ts')
            if not SKIP_DIRS & set(f.parts) and f.name not in ALLOW_NAMES and not f.name.endswith('.test.ts'))
    print(f'ok — no hand-rolled forecast numerator in {n} TypeScript files')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
