"""Every named import in the repo's TypeScript must resolve to a real export.

Why this exists as a gate rather than a habit. `forecast.test.ts` imported
`isForecastOrUnverified` for weeks. Nothing exported it — not that file, not any file. The suite
ran green the whole time, because three separate things have to go wrong at once and all three
were true here when this file was written:

  * Bun does not validate named exports. A missing one is `undefined` at runtime, and a name that
    is imported but never *called* is never evaluated, so nothing throws. STILL TRUE.
  * There is no `tsc` step. No tsconfig, no typescript dependency, nothing that reads the types.
    STILL TRUE — checked 2026-08-16, there is no `package.json` either.
  * `bun test` is not in CI. Only `cross-extractor` runs Bun, and only to re-run the extractors.
    **NO LONGER TRUE**, and the same commit that added this gate is what changed it: the
    `typescript` job's "Run the simulator test suite" step runs
    `REPLAY_DIR=sessions/2026-07-22 bun test`. (Cited as `verify.yml:569` until 2026-08-17, by
    which time the step had moved to line 601 — a line number is a citation that rots on every
    edit above it, so this one names the job and the step instead.) Running
    the suite does not subsume this gate, because the original defect was an import that was never
    *called* — no amount of test execution evaluates it. It does narrow the window: a renamed
    export that some test does call now fails in CI.

So the import was invisible to every gate in the repo. The interesting part is not the dead name;
it is that the same hole hides a *renamed* export, which is a real breakage that shows up as a
runtime `undefined` at whatever moment the caller first runs — possibly inside a report build.

This is deliberately not a typechecker. It answers one question, needs no dependencies, and can be
demonstrated to fail (`--selftest`), which is the standard the rest of the gates here are held to.
A real `tsc` pass would subsume it and is worth doing; it needs a tsconfig and a pinned typescript,
which is a bigger decision than this file.

    python3 -m pipeline.check_ts_imports [root]
    python3 -m pipeline.check_ts_imports --selftest
"""
from __future__ import annotations

import pathlib
import re
import sys
import tempfile

# Any `import ... from '...'`, whatever sits between. Matching the whole statement rather than
# only the brace form is the point: a form this gate cannot read must be REPORTED, not skipped.
# A checker that silently ignores what it does not recognise reports "all clear" for the files it
# never looked at.
IMPORT = re.compile(r'^import\s+(?P<what>.*?)\s+from\s+[\'"](?P<spec>[^\'"]+)[\'"]', re.M | re.S)
NAMED_ONLY = re.compile(r'^(?:type\s+)?\{(?P<names>[^}]*)\}$', re.S)
DECL = re.compile(
    r'^export\s+(?:declare\s+)?(?:async\s+)?'
    r'(?:function|const|let|var|class|type|interface|enum)\s+([A-Za-z_$][\w$]*)', re.M)
DECL_LIST = re.compile(r'^export\s+(?:type\s+)?\{(?P<names>[^}]*)\}', re.M)
STAR = re.compile(r'^export\s+\*\s', re.M)
DECL_MULTI = re.compile(r'^export\s+(?:const|let|var)\s+[A-Za-z_$]', re.M)
IDENT = re.compile(r'\s*([A-Za-z_$][\w$]*)\s*=')


def _more_declarators(src: str, start: int) -> list[str]:
    """The names after the first in one `export const a = …, b = …, c = …;` statement.

    Walks from `start` (the statement's first character) to its end at bracket depth 0, skipping
    strings and comments, and reads the identifier after every depth-0 comma. A vendored module
    (the Triangle engine's kick tables) exports three tables this way; without this they read as
    not exported. A regex literal holding a bracket would throw the depth off, so a statement this
    walk cannot close is an error rather than a guess.
    """
    names, depth, i, n = [], 0, start, len(src)
    while i < n:
        c = src[i]
        if c in '\'"`':
            j = i + 1
            while j < n and src[j] != c:
                j += 2 if src[j] == '\\' else 1
            i = j + 1
            continue
        if src.startswith('//', i):
            i = src.find('\n', i)
            i = n if i < 0 else i
            continue
        if src.startswith('/*', i):
            i = src.find('*/', i) + 2
            if i < 2:
                break
            continue
        if c in '([{':
            depth += 1
        elif c in ')]}':
            depth -= 1
            if depth < 0:
                raise ValueError(f'unbalanced brackets in an export statement at offset {start}')
        elif depth == 0 and c == ';':
            return names
        elif depth == 0 and c == ',':
            m = IDENT.match(src, i + 1)
            if m:
                names.append(m.group(1))
        elif depth == 0 and c == '\n' and src.startswith('export', i + 1):
            return names                              # no semicolon: the next export starts it
        i += 1
    if depth != 0:
        raise ValueError(f'an export statement at offset {start} never closes')
    return names
SKIP_DIRS = {'vendor', 'node_modules', '.git'}


def exported_names(path: pathlib.Path) -> tuple[set[str], bool]:
    """Names `path` exports, and whether it re-exports someone else's with `export *`."""
    src = path.read_text()
    names = set(DECL.findall(src))
    for m in DECL_MULTI.finditer(src):
        names.update(_more_declarators(src, m.start()))
    for block in DECL_LIST.findall(src):
        for part in block.split(','):
            part = part.strip().removeprefix('type ').strip()
            if part:
                names.add(part.split(' as ')[-1].strip())
    return names, bool(STAR.search(src))


def resolve(importer: pathlib.Path, spec: str) -> pathlib.Path | None:
    """A relative specifier to a file on disk, trying the extensions Bun would."""
    base = (importer.parent / spec).resolve()
    for cand in (base, base.with_suffix('.ts'), base / 'index.ts'):
        if cand.is_file():
            return cand
    return None


def scan(root: pathlib.Path) -> list[str]:
    problems: list[str] = []
    for f in sorted(root.rglob('*.ts')):
        if SKIP_DIRS & set(f.parts):
            continue
        for m in IMPORT.finditer(f.read_text()):
            spec, what = m.group('spec'), m.group('what').strip()
            here = f.relative_to(root)
            if not spec.startswith('.'):
                continue                       # a package, not this repo's business
            named = NAMED_ONLY.match(what)
            if not named:
                problems.append(f'{here}: import form this gate cannot read: import {what} from {spec!r}')
                continue
            target = resolve(f, spec)
            if target is None:
                problems.append(f'{here}: imports {spec!r}, which is not a file')
                continue
            names, star = exported_names(target)
            if star:
                continue                       # re-exports someone else's names; out of scope
            for part in named.group('names').split(','):
                part = part.strip().removeprefix('type ').strip()
                if not part:
                    continue
                want = part.split(' as ')[0].strip()
                if want not in names:
                    problems.append(f'{here}: {want!r} is not exported by {spec}')
    return problems


def selftest() -> int:
    """Plant a dangling import and require the gate to reject it — and only it."""
    with tempfile.TemporaryDirectory() as tmp:
        d = pathlib.Path(tmp)
        # `export type { … }` is an export list too (a shim re-exporting types uses it)
        (d / 'lib.ts').write_text('export const real = 1;\nexport { real as aliased };\n'
                                  'type Shape = number;\nexport type { Shape };\n')
        # `export const a = …, b = …` exports b too (the vendored kick tables do this)
        (d / 'multi.ts').write_text("export const one = { a: [1, 2], s: 'x, y = 3' }, two = 2,\n"
                                    "  three = (4, 5);\nexport const four = 4;\n")
        (d / 'ok.ts').write_text("import { real, aliased, type Shape } from './lib.ts';\n"
                                 "import { one, two, three, four } from './multi.ts';\n")
        if scan(d):
            print('SELFTEST FAIL: a sound import was reported', file=sys.stderr)
            return 1
        (d / 'bad.ts').write_text("import { real, missing } from './lib.ts';\n"
                                  "import { two } from './multi.ts';\n")
        # a name inside the first table's value or string is not an export
        (d / 'bad2.ts').write_text("import { y } from './multi.ts';\n")
        (d / 'odd.ts').write_text("import Default from './lib.ts';\n")
        found = scan(d)
        if len(found) != 3 or not any("'missing'" in p for p in found) \
                or not any("'y'" in p for p in found) \
                or not any('cannot read' in p for p in found):
            print(f'SELFTEST FAIL: expected a dangling name and an unreadable form, got {found}',
                  file=sys.stderr)
            return 1
    print('selftest ok — the gate rejects a dangling name and an import form it cannot read')
    return 0


def main(argv: list[str]) -> int:
    if '--selftest' in argv:
        return selftest()
    root = pathlib.Path(argv[1]).resolve() if len(argv) > 1 else pathlib.Path(__file__).resolve().parents[1]
    problems = scan(root)
    for p in problems:
        print('FAIL  ' + p, file=sys.stderr)
    if problems:
        print(f'{len(problems)} unresolved import(s)', file=sys.stderr)
        return 1
    n = sum(1 for f in root.rglob('*.ts') if not SKIP_DIRS & set(f.parts))
    print(f'ok — every named import in {n} TypeScript files resolves to an export')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
