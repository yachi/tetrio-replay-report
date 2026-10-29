"""Refetch every pinned harddrop wikitext revision a route or technique transcription rests on, and re-check it.

    python3 -m pipeline.openers.check_wikitext_sources               # live: fetch, hash, re-parse
    python3 -m pipeline.openers.check_wikitext_sources --save <dir>  # ...and keep the bytes in <dir>
    python3 -m pipeline.openers.check_wikitext_sources --selftest    # no network: the mutants

A route transcription read from a harddrop page's wikitext (SDPC Spin, `sdpcspin-routes.json`) records
the page's revision (`oldid`), MediaWiki's own sha1 of that revision (`revision_sha1`) and our sha256 of
its bytes (`snapshot_sha256`). The page itself is not committed, so without this gate nothing re-reads
it: `--html-dir` exists on every extractor, and only a person with the bytes could run it.

Which routes files are checked is DISCOVERED, never listed: every `pipeline/openers/*-routes.json` whose
`source` or `cross_source` carries both `oldid` and `revision_sha1`. A record with an `oldid` and no
`revision_sha1` (ガムシロ積み's harddrop HTML cross-source) is not a wikitext revision and is not touched.

Technique transcriptions are discovered the same way, by structure: every `pipeline/openers/*-technique.json`
holding, ANYWHERE in it, an object carrying both `oldid` and `revision_sha1` (which ones is whatever discovery
returns — the run prints the list; never re-type it here); the record's role is its dotted path. A discovered
technique whose extractor declares no `wikitext_checks` / `synthetic_wikitext` is a SURVIVOR of `--selftest`,
because the live run would fail its extractor step on it. A `*-setups.json` (harddrop's DPC setup pages,
`extract_<key>_setups`) is discovered and checked as a technique file; every board in it is a parse of its
pinned revisions, so its `--wikitext-dir` re-parses them all and it has no gap lines. Two things differ from a routes file, and both are stated in the output:

  * the extractor (`pipeline.openers.extract_<key>_shapes`) is run with `--wikitext-dir`, not
    `--html-dir`: a technique's page is shiwehi.com HTML (and 欄干 pins a Tetrisチャンネル page beside it),
    which no api.php call returns. `--wikitext-dir` runs the spec's `wikitext_checks` alone — the pinned
    revisions' hashes and the re-parse of every recorded drawing — and FAILS when the spec declares none.
  * every other snapshot the file records (a `snapshot_file` with no `revision_sha1`) is printed as a
    `gap` line, NOT re-read here: that half of `--html-dir` still needs a person with the refetched page.

Per routes file, every check prints one line and every failure is collected (no short-circuit):

  * fetch: the pinned revision from the MediaWiki API (`revids=<oldid>`), with Python's urllib and a
    descriptive User-Agent (not curl). A non-200, a network error, or JSON without that revision is a
    FAIL naming what came back — never a skip.
  * revision: the API's revid is the pinned oldid.
  * sha1: the API's sha1 == sha1 of the bytes == the recorded `revision_sha1` (two authorities and ours).
  * sha256 / bytes: sha256 of the bytes == `snapshot_sha256`, and their length == `snapshot_bytes`.
  * latest: the page's newest revision (`pageids=<pageid>`). Newer than the pin is a FAIL carrying both
    revids and the re-transcription command: a page edited upstream is a page we have not read.
  * extractor: every snapshot of the file saved under its `snapshot_file` in ONE directory, then the
    routes file's own extractor (`pipeline.openers.extract_<key>_routes`, verified to write exactly that
    routes file) run with `--html-dir <dir>`, which re-parses every board and the cross-source table.
"""
from __future__ import annotations

import argparse
import copy
import email.message
import hashlib
import importlib
import json
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
API = 'https://harddrop.com/w/api.php'
USER_AGENT = 'tetrio-replay-report/1.0 (https://github.com/yachi/tetrio-replay-report)'
TIMEOUT_S = 30

#: fetch(url) -> (HTTP status, body bytes). The real one is urllib; the selftest injects a fake.
Fetcher = Callable[[str], 'tuple[int, bytes]']
#: run_extractor(module, html_dir) -> (exit code, combined output)
Extractor = Callable[[str, Path], 'tuple[int, str]']


class CheckFailed(Exception):
    pass


def urllib_fetch(url: str) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read() or b''
    except (urllib.error.URLError, OSError) as e:
        raise CheckFailed(f'network error fetching {url}: {e}') from e


def subprocess_extractor(module: str, html_dir: Path, flag: str = '--html-dir') -> tuple[int, str]:
    p = subprocess.run([sys.executable, '-m', module, flag, str(html_dir)], cwd=REPO,
                       capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def wikitext_extractor(module: str, html_dir: Path) -> tuple[int, str]:
    return subprocess_extractor(module, html_dir, '--wikitext-dir')


# ── discovery ──────────────────────────────────────────────────────────────────────────────────
def wikitext_records(data: dict) -> list[tuple[str, dict]]:
    """The (role, record) pairs of a routes file that pin a harddrop wikitext revision."""
    return [(role, data[role]) for role in ('source', 'cross_source')
            if isinstance(data.get(role), dict) and 'oldid' in data[role] and 'revision_sha1' in data[role]]


def discover(openers: Path = HERE) -> list[Path]:
    return [p for p in sorted(openers.glob('*-routes.json'))
            if wikitext_records(json.loads(p.read_text()))]


def _walk(o, path: str, hit, out: list) -> None:
    if isinstance(o, dict):
        if hit(o):
            out.append((path, o))
            return
        for k, v in o.items():
            _walk(v, f'{path}.{k}' if path else k, hit, out)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            _walk(v, f'{path}[{i}]', hit, out)


def technique_wikitext_records(data: dict) -> list[tuple[str, dict]]:
    """(dotted path, record) for every object anywhere in a technique transcription pinning a revision."""
    out: list = []
    _walk(data, '', lambda o: 'oldid' in o and 'revision_sha1' in o, out)
    return out


def technique_other_snapshots(data: dict) -> list[tuple[str, dict]]:
    """(dotted path, record) for every snapshot the transcription records that is NOT a pinned revision."""
    out: list = []
    _walk(data, '', lambda o: 'snapshot_file' in o and 'revision_sha1' not in o, out)
    return out


def discover_techniques(openers: Path = HERE) -> list[Path]:
    # a setups transcription (secondpc-setups.json) is read the same way: structure, --wikitext-dir, its SPEC's hooks
    # (dpc-setups.json is read off a video and pins no revision, so it is not discovered)
    return [p for p in sorted([*openers.glob('*-technique.json'), *openers.glob('*-setups.json')])
            if technique_wikitext_records(json.loads(p.read_text()))]


def extractor_module(routes: Path) -> str:
    """`pipeline.openers.extract_<key>_routes` (`_shapes` for a `-technique.json`, `_setups` for a
    `-setups.json`), and only if that
    module writes exactly `routes`."""
    if routes.name.endswith('-technique.json'):
        name = f'pipeline.openers.extract_{routes.name[:-len("-technique.json")]}_shapes'
    elif routes.name.endswith('-setups.json'):
        name = f'pipeline.openers.extract_{routes.name[:-len("-setups.json")]}_setups'
    else:
        name = f'pipeline.openers.extract_{routes.name[:-len("-routes.json")]}_routes'
    try:
        mod = importlib.import_module(name)
    except ImportError as e:
        raise CheckFailed(f'{routes.name}: no extractor module {name} ({e})') from e
    out = getattr(mod, 'OUT', None)
    if out is None or Path(out).resolve() != routes.resolve():
        raise CheckFailed(f'{routes.name}: {name}.OUT is {out}, not this routes file')
    return name


# ── the API ────────────────────────────────────────────────────────────────────────────────────
def api_url(**params) -> str:
    q = {'action': 'query', 'prop': 'revisions', 'format': 'json', 'formatversion': '2', **params}
    return API + '?' + urllib.parse.urlencode(q, safe='|')


def api_page(fetch: Fetcher, url: str) -> dict:
    """query.pages[0] with at least one revision, or CheckFailed naming what came back."""
    status, body = fetch(url)
    if status != 200:
        raise CheckFailed(f'HTTP {status} from {url}')
    try:
        d = json.loads(body)
        page = d['query']['pages'][0]
        page['revisions'][0]
    except (ValueError, KeyError, IndexError, TypeError):
        raise CheckFailed(f'no revision in the API response from {url}: {body[:300]!r}')
    return page


def check_record(role: str, rec: dict, fetch: Fetcher, html_dir: Path, say) -> bool:
    """Fetch one pinned revision into `html_dir`; print a line per check; True when all pass."""
    ok = True
    tag = f'{role} {rec["snapshot_file"]} (oldid {rec["oldid"]})'

    def line(good: bool, what: str) -> None:
        nonlocal ok
        ok &= good
        say(f'{"ok  " if good else "FAIL"} {tag}: {what}')

    if not rec['snapshot_file'].endswith('.wikitext'):
        line(False, 'pins a revision but its snapshot is not a .wikitext page — this gate reads wikitext only')
        return False
    try:
        page = api_page(fetch, api_url(revids=rec['oldid'], rvprop='ids|sha1|size|timestamp|content',
                                       rvslots='main'))
        rev = page['revisions'][0]
        content = rev['slots']['main']['content']
    except CheckFailed as e:
        line(False, f'fetch: {e}')
        return False
    except (KeyError, TypeError):
        line(False, 'fetch: the revision carries no main-slot content')
        return False
    raw = content.encode('utf8')
    line(True, f'fetch: HTTP 200, {len(raw)} bytes')
    line(rev.get('revid') == rec['oldid'], f'revision: the API served revid {rev.get("revid")}')
    got1 = hashlib.sha1(raw).hexdigest()
    line(rev.get('sha1') == got1 == rec['revision_sha1'],
         f'sha1: API {rev.get("sha1")} / bytes {got1} / recorded {rec["revision_sha1"]}')
    got256 = hashlib.sha256(raw).hexdigest()
    line(got256 == rec['snapshot_sha256'], f'sha256: bytes {got256} / recorded {rec["snapshot_sha256"]}')
    # required, like every hash: a record without it fails here rather than skipping the check
    line(len(raw) == rec.get('snapshot_bytes'), f'bytes: {len(raw)} / recorded {rec.get("snapshot_bytes")}')
    (html_dir / rec['snapshot_file']).write_bytes(raw)

    try:
        latest = api_page(fetch, api_url(pageids=page['pageid'], rvprop='ids|timestamp'))['revisions'][0]
    except (CheckFailed, KeyError) as e:
        line(False, f'latest: {e}')
        return False
    if not isinstance(latest.get('revid'), int):
        line(False, f'latest: the API returned no revid for {page.get("title")!r}')
        return False
    newer = latest['revid'] > rec['oldid']
    line(not newer,
         f'latest: {page.get("title")!r} is at revid {latest.get("revid")} ({latest.get("timestamp")})'
         + (f', NEWER than the pinned {rec["oldid"]} — re-transcribe: save the new revision and run '
            f'the extractor with --html-dir <dir> (then --write), and re-pin oldid and both hashes'
            if newer else ', the pinned revision'))
    return ok


def check_routes(routes: Path, data: dict, fetch: Fetcher, extract: Extractor, html_dir: Path,
                 say=print) -> bool:
    ok = True
    recs = wikitext_records(data)
    for role in ('source', 'cross_source'):
        r = data.get(role)
        if isinstance(r, dict) and 'snapshot_file' in r and (role, r) not in recs:
            # a snapshot this gate cannot fetch: --html-dir would fail on its absence, not on a defect
            say(f'FAIL {routes.name}: {role} {r["snapshot_file"]} is not a pinned wikitext revision, '
                f'so --html-dir cannot be run from refetched pages alone')
            ok = False
    for role, rec in recs:
        ok &= check_record(role, rec, fetch, html_dir, say)
    try:
        module = extractor_module(routes)
    except CheckFailed as e:
        say(f'FAIL extractor: {e}')
        return False
    code, out = extract(module, html_dir)
    good = code == 0
    say(f'{"ok  " if good else "FAIL"} extractor: python3 -m {module} --html-dir <dir> exited {code}')
    if not good:
        for x in out.splitlines():
            if x.startswith('FAIL'):
                say(f'     {x}')
    return ok and good


def check_technique(path: Path, data: dict, fetch: Fetcher, extract: Extractor, html_dir: Path,
                    say=print) -> bool:
    """A technique transcription: every pinned revision fetched and checked, then the extractor's
    `--wikitext-dir` (the wikitext half alone). The snapshots no api.php call returns are printed as gaps."""
    ok = True
    for role, r in technique_other_snapshots(data):
        say(f'gap  {role} {r["snapshot_file"]}: not a MediaWiki revision, not re-read here '
            f'(--html-dir with a refetched page re-checks it)')
    for role, rec in technique_wikitext_records(data):
        ok &= check_record(role, rec, fetch, html_dir, say)
    try:
        module = extractor_module(path)
    except CheckFailed as e:
        say(f'FAIL extractor: {e}')
        return False
    code, out = extract(module, html_dir)
    good = code == 0
    say(f'{"ok  " if good else "FAIL"} extractor: python3 -m {module} --wikitext-dir <dir> exited {code}')
    if not good:
        for x in out.splitlines():
            if x.startswith('FAIL'):
                say(f'     {x}')
    return ok and good


def run(fetch: Fetcher = urllib_fetch, extract: Extractor = subprocess_extractor,
        save: Path | None = None, extract_wikitext: Extractor = wikitext_extractor) -> int:
    files = discover()
    if not files:
        print('FAIL no routes file pins a harddrop wikitext revision — the discovery rule matched nothing')
        return 1
    techniques = discover_techniques()
    if not techniques:
        print('FAIL no technique file pins a harddrop wikitext revision — the discovery rule matched nothing')
        return 1
    ok = True
    for routes in files:
        print(f'{routes.relative_to(REPO)}')
        data = json.loads(routes.read_text())
        if save:
            d = save / routes.name[:-len('-routes.json')]
            d.mkdir(parents=True, exist_ok=True)
            ok &= check_routes(routes, data, fetch, extract, d)
        else:
            with tempfile.TemporaryDirectory() as td:
                ok &= check_routes(routes, data, fetch, extract, Path(td))
    for tech in techniques:
        print(f'{tech.relative_to(REPO)}')
        data = json.loads(tech.read_text())
        if save:
            d = save / tech.name[:-len('.json')]
            d.mkdir(parents=True, exist_ok=True)
            ok &= check_technique(tech, data, fetch, extract_wikitext, d)
        else:
            with tempfile.TemporaryDirectory() as td:
                ok &= check_technique(tech, data, fetch, extract_wikitext, Path(td))
    print('wikitext sources OK' if ok else 'wikitext sources: FAILED')
    return 0 if ok else 1


# ── selftest ───────────────────────────────────────────────────────────────────────────────────
class FakeWiki:
    """The two API calls this gate makes, served from memory, dispatched on parsed query params."""

    def __init__(self, pages: dict[int, dict]):
        # oldid -> {'pageid', 'title', 'content', 'sha1' (served), 'latest', 'status', 'drop'}
        self.pages = pages

    def __call__(self, url: str) -> tuple[int, bytes]:
        q = {k: v[0] for k, v in urllib.parse.parse_qs(urllib.parse.urlparse(url).query).items()}
        if 'revids' in q:
            p = self.pages.get(int(q['revids']))
            if p is None:
                return 200, json.dumps({'query': {'badrevids': {q['revids']: {'missing': True}}}}).encode()
            if p.get('status', 200) == 403:
                return 403, b'<html>403 Forbidden</html>'
            if p.get('drop'):
                return 200, json.dumps({'batchcomplete': True, 'query': {'pages': [
                    {'pageid': p['pageid'], 'title': p['title']}]}}).encode()
            rev = {'revid': int(q['revids']), 'timestamp': '2025-01-01T00:00:00Z', 'sha1': p['sha1'],
                   'size': len(p['content'].encode()), 'slots': {'main': {'content': p['content']}}}
            return 200, json.dumps({'query': {'pages': [
                {'pageid': p['pageid'], 'title': p['title'], 'revisions': [rev]}]}}).encode()
        if 'pageids' in q:
            p = next(v for v in self.pages.values() if v['pageid'] == int(q['pageids']))
            latest = {'timestamp': '2026-01-01T00:00:00Z'}
            if p['latest'] is not None:
                latest['revid'] = p['latest']
            return 200, json.dumps({'query': {'pages': [{'pageid': p['pageid'], 'title': p['title'],
                'revisions': [latest]}]}}).encode()
        return 400, b'unexpected query'


def synthetic_pages(data: dict) -> dict[str, str]:
    """snapshot_file -> a faithful synthetic page for each wikitext record, the way the extractor's own
    selftest rebuilds one (the real bytes are not committed and the selftest has no network)."""
    from pipeline.openers import route_transcription as RT
    out = {}
    for role, rec in wikitext_records(data):
        if role == 'source':
            out[rec['snapshot_file']] = RT.synthetic_snapshot(data)
        else:
            out[rec['snapshot_file']] = RT.synthetic_wikitext([[]] * rec['table'] + [rec['fields']])
    return out


def selftest() -> int:
    from pipeline.openers import route_transcription as RT
    files = discover()
    survived = 0
    killed = 0

    def report(label: str, caught: bool, want_caught: bool, why: str = '') -> None:
        nonlocal survived, killed
        if caught == want_caught:
            killed += want_caught
            print(f'  {"killed" if want_caught else "passed"}: {label}{why}')
        else:
            survived += 1
            print(f'  {"SURVIVED" if want_caught else "FAILED control"}: {label}{why}', file=sys.stderr)

    # discovery: ガムシロ積み's cross-source pins an oldid but no revision_sha1 — not a wikitext record
    gam = json.loads((HERE / 'gamushiro-routes.json').read_text())
    report('a record with oldid and no revision_sha1 is not discovered (control)',
           bool(wikitext_records(gam)), False)
    report('the discovery rule finds at least one routes file (control)', not files, False)
    planted = copy.deepcopy(gam)
    planted['cross_source']['revision_sha1'] = '0' * 40
    report('the same record with a revision_sha1 IS discovered', bool(wikitext_records(planted)), True)
    # technique discovery: by structure, anywhere in the file, never by a hand list
    techniques = discover_techniques()
    report('the discovery rule finds at least one technique file (control)', not techniques, False)
    stsd = json.loads((HERE / 'stsd-technique.json').read_text())
    report('a technique file pinning no revision is not discovered (control)',
           bool(technique_wikitext_records(stsd)), False)
    planted = copy.deepcopy(stsd)
    planted.setdefault('cross_source', {})['deep'] = {'list': [{'harddrop': {
        'oldid': 1, 'revision_sha1': '0' * 40, 'snapshot_file': 'X.wikitext'}}]}
    found = technique_wikitext_records(planted)
    report('a pin nested two levels inside a list IS discovered, at its dotted path',
           [r for r, _ in found] == ['cross_source.deep.list[0].harddrop'], True)
    planted['cross_source']['deep']['list'][0]['harddrop'].pop('revision_sha1')
    report('the same nested record without revision_sha1 is not discovered (control)',
           bool(technique_wikitext_records(planted)), False)
    report('...and is printed as a gap, not dropped',
           any(r == 'cross_source.deep.list[0].harddrop' for r, _ in technique_other_snapshots(planted)), True)
    report('a technique record is not discovered by the routes rule (control: routes behaviour unchanged)',
           any(t in discover() for t in techniques), False)
    try:
        report('extract_<key>_shapes resolves to its own technique file (control)',
               not all(extractor_module(t).endswith('_setups' if t.name.endswith('-setups.json') else '_shapes')
                       for t in techniques), False)
    except CheckFailed as e:
        report(f'extract_<key>_shapes resolves to its own technique file (control): {e}', True, False)
    # --wikitext-dir on a spec declaring no wikitext_checks fails by name (the REAL extractor, stmbcave)
    with tempfile.TemporaryDirectory() as td:
        code, out = wikitext_extractor('pipeline.openers.extract_stmbcave_shapes', Path(td))
    report('--wikitext-dir on a spec with no wikitext_checks fails, naming it',
           code != 0 and 'declares no wikitext_checks' in out, True)
    try:
        extractor_module(HERE / 'gamushiro-routes.json')
        report('extractor_<key>_routes resolves to its own routes file (control)', False, False)
    except CheckFailed:
        report('extractor_<key>_routes resolves to its own routes file (control)', True, False)
    with tempfile.TemporaryDirectory() as td:
        stray = Path(td) / 'gamushiro-routes.json'       # same name, not the file the module writes
        stray.write_text('{}')
        try:
            extractor_module(stray)
            report('a module whose OUT is another file', False, True)
        except CheckFailed:
            report('a module whose OUT is another file', True, True)
    # the real fetcher turns an HTTPError into its status rather than raising or skipping
    real_urlopen = urllib.request.urlopen

    def urlopen_403(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, 403, 'Forbidden', email.message.Message(), None)
    urllib.request.urlopen = urlopen_403
    try:
        status, _ = urllib_fetch(api_url(revids=1))
    finally:
        urllib.request.urlopen = real_urlopen
    report('urllib_fetch reports an HTTPError 403 as status 403', status == 403, True)

    for routes in files:
        base = json.loads(routes.read_text())
        pages = synthetic_pages(base)
        # recorded hashes recomputed from the synthetic bytes, in memory only
        data = copy.deepcopy(base)
        wiki_pages = {}
        for pid, (role, rec) in enumerate(wikitext_records(data), start=1):
            raw = pages[rec['snapshot_file']].encode()
            rec['revision_sha1'] = hashlib.sha1(raw).hexdigest()
            rec['snapshot_sha256'] = hashlib.sha256(raw).hexdigest()
            rec['snapshot_bytes'] = len(raw)
            wiki_pages[rec['oldid']] = {'pageid': pid, 'title': f'{role} page', 'latest': rec['oldid'],
                                        'content': pages[rec['snapshot_file']],
                                        'sha1': rec['revision_sha1']}

        sha256_excused = []

        def offline_extractor(module: str, html_dir: Path) -> tuple[int, str]:
            # the REAL subprocess: it checks the committed hashes, which synthetic bytes cannot meet, so
            # its sha256 lines (and only those) are excused here — counted and printed, never silent
            _, out = subprocess_extractor(module, html_dir)
            fails = [x for x in out.splitlines() if x.startswith('FAIL')]
            hashes = [x for x in fails if 'sha256' in x and 'is not the recorded one' in x]
            sha256_excused.append(len(hashes))
            rest = [x for x in fails if x not in hashes]
            return (1 if rest else 0), '\n'.join(rest)

        def attempt(label: str, wiki: Fetcher, d: dict, want_caught: bool, must: str = '') -> None:
            lines: list[str] = []
            with tempfile.TemporaryDirectory() as td:
                ok = check_routes(routes, d, wiki, offline_extractor, Path(td), say=lines.append)
            caught = not ok and (not must or any(must in x for x in lines))
            report(f'{routes.name}: {label}', caught, want_caught,
                   '' if caught == want_caught else f' — {[x for x in lines if x.startswith(("FAIL", "    "))][:3]}')

        attempt('faithful pages at the pinned revision (control)', FakeWiki(copy.deepcopy(wiki_pages)),
                data, False)
        print(f'    extractor control: {sha256_excused[-1]} sha256 line(s) excused offline, 0 other failures')

        oid = wikitext_records(data)[0][1]['oldid']

        d = copy.deepcopy(data)
        wikitext_records(d)[0][1]['revision_sha1'] = 'f' * 40
        attempt('wrong recorded revision_sha1', FakeWiki(copy.deepcopy(wiki_pages)), d, True, 'sha1:')

        w = copy.deepcopy(wiki_pages)
        w[oid]['content'] = w[oid]['content'].replace(' ', '  ', 1)   # bytes edited, API sha1 still the old
        attempt('content edited (sha1 of the bytes disagrees)', FakeWiki(w), data, True, 'sha1:')

        w = copy.deepcopy(wiki_pages)
        w[oid]['sha1'] = '0' * 40
        attempt('API sha1 disagreeing with the bytes', FakeWiki(w), data, True, 'sha1:')

        d = copy.deepcopy(data)
        wikitext_records(d)[0][1]['snapshot_sha256'] = '0' * 64
        attempt('wrong recorded snapshot_sha256', FakeWiki(copy.deepcopy(wiki_pages)), d, True, 'sha256:')

        w = copy.deepcopy(wiki_pages)
        w[oid]['latest'] = oid + 1
        attempt('a newer latest revision', FakeWiki(w), data, True, 'NEWER')

        w = copy.deepcopy(wiki_pages)
        w[oid]['latest'] = None
        attempt('the latest revision with no revid', FakeWiki(w), data, True, 'no revid')

        d = copy.deepcopy(data)
        del wikitext_records(d)[0][1]['snapshot_bytes']
        attempt('a record with no snapshot_bytes', FakeWiki(copy.deepcopy(wiki_pages)), d, True, 'bytes:')

        w = copy.deepcopy(wiki_pages)
        w[oid]['status'] = 403
        attempt('HTTP 403', FakeWiki(w), data, True, 'HTTP 403')

        w = copy.deepcopy(wiki_pages)
        w[oid]['drop'] = True
        attempt('the revision missing from the JSON', FakeWiki(w), data, True, 'no revision')

        w = copy.deepcopy(wiki_pages)
        del w[oid]
        attempt('a bad revid (badrevids)', FakeWiki(w), data, True, 'no revision')

        def failing_fetch(url: str) -> tuple[int, bytes]:
            raise CheckFailed(f'network error fetching {url}: planted')
        attempt('a network error', failing_fetch, data, True, 'network error')

        # a board edited in the content, re-pinned so every hash agrees: only --html-dir can see it
        rows = {n['id']: n['rows'] for n in base['nodes'] if 'rows' in n}
        rows.update({b['id']: b['rows'] for b in base['basic_form']})
        first = rows[base['page_order'][0]]
        r, c = next((i, j) for i, row in enumerate(first) for j, ch in enumerate(row) if ch != RT.EMPTY)
        edited = [row[:c] + RT.EMPTY + row[c + 1:] if i == r else row for i, row in enumerate(first)]
        src = next(rec for role, rec in wikitext_records(data) if role == 'source')
        page: str = pages[src['snapshot_file']]
        old_frag = RT.synthetic_wikitext([[first]])
        new_frag = RT.synthetic_wikitext([[edited]])
        # synthetic_wikitext writes one table per call; replace the first board's rows in place
        old_rows = old_frag[old_frag.index('{{pfstart}}'):old_frag.index('{{pfend}}')]
        new_rows = new_frag[new_frag.index('{{pfstart}}'):new_frag.index('{{pfend}}')]
        assert old_rows in page and old_rows != new_rows
        page2 = page.replace(old_rows, new_rows, 1)
        d = copy.deepcopy(data)
        w = copy.deepcopy(wiki_pages)
        s = next(rec for role, rec in wikitext_records(d) if role == 'source')
        s['revision_sha1'] = hashlib.sha1(page2.encode()).hexdigest()
        s['snapshot_sha256'] = hashlib.sha256(page2.encode()).hexdigest()
        s['snapshot_bytes'] = len(page2.encode())
        w[src['oldid']].update(content=page2, sha1=s['revision_sha1'])
        attempt('a board edited in the content (every hash re-pinned)', FakeWiki(w), d, True, 'differs')

    for tech in techniques:
        mod = importlib.import_module(extractor_module(tech))
        synth = getattr(mod.SPEC, 'synthetic_wikitext', None)
        if synth is None or getattr(mod.SPEC, 'wikitext_checks', None) is None:
            # the live run FAILS this file at its extractor step (--wikitext-dir names the missing hook), so a
            # discovered technique without both hooks is a SURVIVOR here: the per-push gate goes red on it now,
            # not the weekly job later
            report(f'{tech.name}: SPEC declares wikitext_checks and synthetic_wikitext (the live run fails its '
                   f'extractor step without them)', False, True)
            continue
        base = json.loads(tech.read_text())
        pages = synth(base)
        data = copy.deepcopy(base)
        wiki_pages = {}
        recs = technique_wikitext_records(data)
        if sorted(pages) != sorted(r['snapshot_file'] for _, r in recs):
            report(f'{tech.name}: synthetic_wikitext covers exactly the pinned revisions', True, False,
                   f' — {sorted(pages)}')
            continue
        for pid, (role, rec) in enumerate(recs, start=1):
            raw = pages[rec['snapshot_file']].encode()
            rec['revision_sha1'] = hashlib.sha1(raw).hexdigest()
            rec['snapshot_sha256'] = hashlib.sha256(raw).hexdigest()
            rec['snapshot_bytes'] = len(raw)
            wiki_pages[rec['oldid']] = {'pageid': pid, 'title': f'{role} page', 'latest': rec['oldid'],
                                        'content': pages[rec['snapshot_file']], 'sha1': rec['revision_sha1']}
        hash_excused = []

        def offline_wikitext(module: str, html_dir: Path) -> tuple[int, str]:
            # the REAL --wikitext-dir: it checks the committed hashes, which synthetic bytes cannot meet, so
            # its `<tag>: hash:` lines (and only those) are excused — counted and printed, never silent
            _, out = wikitext_extractor(module, html_dir)
            fails = [x for x in out.splitlines() if x.startswith('FAIL')]
            hashes = [x for x in fails if ': hash: ' in x]
            hash_excused.append(len(hashes))
            rest = [x for x in fails if x not in hashes]
            return (1 if rest else 0), '\n'.join(rest)

        def tattempt(label: str, wiki: Fetcher, d: dict, want_caught: bool, must: str = '') -> None:
            lines: list[str] = []
            with tempfile.TemporaryDirectory() as td:
                ok = check_technique(tech, d, wiki, offline_wikitext, Path(td), say=lines.append)
            caught = not ok and (not must or any(must in x for x in lines))
            report(f'{tech.name}: {label}', caught, want_caught,
                   '' if caught == want_caught else f' — {[x for x in lines if x.startswith(("FAIL", "    "))][:3]}')

        tattempt('faithful pages at the pinned revisions (control)', FakeWiki(copy.deepcopy(wiki_pages)),
                 data, False)
        print(f'    extractor control: {hash_excused[-1]} hash line(s) excused offline, 0 other failures')
        for role, rec in recs:
            oid = rec['oldid']
            d = copy.deepcopy(data)
            dict(technique_wikitext_records(d))[role]['revision_sha1'] = 'f' * 40
            tattempt(f'{role}: wrong recorded revision_sha1', FakeWiki(copy.deepcopy(wiki_pages)), d, True,
                     'sha1:')
            w = copy.deepcopy(wiki_pages)
            w[oid]['latest'] = oid + 1
            tattempt(f'{role}: a newer latest revision', FakeWiki(w), data, True, 'NEWER')
            w = copy.deepcopy(wiki_pages)
            w[oid]['status'] = 403
            tattempt(f'{role}: HTTP 403', FakeWiki(w), data, True, 'HTTP 403')
            # a recorded board edited in the content, re-pinned so every hash agrees: only the
            # extractor's re-parse can see it. A pfrow table loses one filled cell; a page drawing its board as
            # a fumen (欄干's) has one character of the fumen changed instead; a page with neither is a survivor
            page = pages[rec['snapshot_file']]
            m = next((x for x in re.finditer(r'\{\{pfrow\|([^}]*)\}\}', page)
                      if any(c.strip() for c in x.group(1).split('|'))), None)
            fm = re.search(r'<fumen>(?:code=)?([^<]+)</fumen>', page)
            if m is not None:
                cells = m.group(1).split('|')
                j = next(i for i, c in enumerate(cells) if c.strip())
                cells[j] = ' '
                page2 = page[:m.start(1)] + '|'.join(cells) + page[m.end(1):]
            elif fm is not None:
                k = fm.end(1) - 2
                page2 = page[:k] + ('B' if page[k] != 'B' else 'C') + page[k + 1:]
            else:
                report(f'{tech.name}: {role}: the synthetic page holds a recorded board (pfrow or fumen) to edit',
                       False, True)
                continue
            d = copy.deepcopy(data)
            w = copy.deepcopy(wiki_pages)
            r2 = dict(technique_wikitext_records(d))[role]
            r2['revision_sha1'] = hashlib.sha1(page2.encode()).hexdigest()
            r2['snapshot_sha256'] = hashlib.sha256(page2.encode()).hexdigest()
            r2['snapshot_bytes'] = len(page2.encode())
            w[oid].update(content=page2, sha1=r2['revision_sha1'])
            tattempt(f'{role}: a recorded board edited in the content (every hash re-pinned)', FakeWiki(w), d,
                     True, 'FAIL extractor')

    print(f'selftest: {killed} killed, {survived} survived')
    return 1 if survived else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or '').split('\n')[0])
    ap.add_argument('--selftest', action='store_true', help='plant the mutants against a fake API (no network)')
    ap.add_argument('--save', type=Path, help='keep the fetched bytes under <dir>/<key>/ instead of a temp dir')
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    return run(save=args.save)


if __name__ == '__main__':
    raise SystemExit(main())
