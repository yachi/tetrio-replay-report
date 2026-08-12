/**
 * Controls for the opener matcher, and the corpus result as a regression.
 *
 * A lookup that finds nothing is indistinguishable from a lookup that is broken, so the negative
 * result ("no round is within four cells of a catalogued C-Spin") is only worth stating if the
 * instrument demonstrably finds things when they are there. Four controls, in order of what they
 * rule out:
 *
 *   1. round-trip     — every C-Spin page, fed back in as a board, is named as itself
 *   2. mirror         — and is found again with its columns reversed and L<->J, S<->Z swapped
 *   3. negative       — a board no opener draws is named as nothing
 *   4. no shift       — the distance to a real board is not a constant offset in disguise
 *
 * Run: REPLAY_DIR=sessions/2026-07-22 bun test pipeline/openers/openers.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { loadCatalogue, prepare, occGrid, mirrorRows, exactMatches, nearest, distance,
         cellsOf, isCSpin, isTKI, isDTCannon, isDTFamily, NAME_SETS, ROWS } from './match.ts';
import { analyse } from './run-openers.ts';
import { build, serialise } from '../sim/emit-opener-facts.ts';

const cat = loadCatalogue();
const prepared = prepare(cat.pages);
const cspin = prepared.filter(p => isCSpin(p.name));

const SESSIONS = ['2026-07-22', '2026-07-24', '2026-07-28', '2026-08-01', '2026-08-09'];
const sessionDir = (d: string) => `${import.meta.dir}/../../sessions/${d}`;

test('the vendored catalogue is the pinned upstream commit, decoded whole', () => {
  expect(cat.provenance.commit).toBe('b4a66878a47466b557165dec9171701bfeafab93');
  expect(cat.provenance.data_json_sha256)
    .toBe('d1fbade1f6df174766b5a354c6ab6d5be992e9c30cbaad3bc6ee1ba4a359a8bf');
  expect(cat.provenance.fumens_failed).toBe(0);      // a partial decode would silently shrink the catalogue
  expect(cat.pages.length).toBe(783);
  expect(new Set(cat.pages.map(p => p.name)).size).toBe(360);
  for (const p of cat.pages) for (const r of p.rows) expect(r.length).toBe(10);
});

test('control 1 — every C-Spin page is named as itself when fed back in', () => {
  expect(cspin.length).toBeGreaterThan(0);
  for (const p of cspin) {
    const hit = exactMatches(p.grid, prepared);
    expect(hit.asDrawn).toContain(p.name);
    expect(nearest(p.grid, cspin).d).toBe(0);
  }
});

test('control 2 — and is found again mirrored', () => {
  for (const p of cspin) {
    const mirrored = occGrid(mirrorRows(p.page.rows));
    const hit = exactMatches(mirrored, prepared);
    expect([...hit.asDrawn, ...hit.asMirror]).toContain(p.name);
  }
});

test('control 3 — a board no opener draws is named as nothing', () => {
  const junk = occGrid(['##########', '#........#', '##########']);
  const hit = exactMatches(junk, prepared);
  expect(hit.asDrawn).toHaveLength(0);
  expect(hit.asMirror).toHaveLength(0);
});

test('control 4 — the distance is not a constant offset: shifting a page one row costs cells', () => {
  // If the grids were misaligned, every real board would sit at the same non-zero distance and the
  // histogram would say "variants" when it meant "off by one row". A page shifted up by one row
  // must therefore be strictly further away than the page itself.
  const p = cspin[0]!;
  const shifted = [...p.page.rows.slice(1), '..........'];
  expect(distance(p.grid, occGrid(shifted))).toBeGreaterThan(0);
  expect(distance(p.grid, p.grid)).toBe(0);
});

test('mirroring twice is the identity, and swaps the handed pieces once', () => {
  const rows = ['L.........', 'LJS.Z.....'];
  expect(mirrorRows(mirrorRows(rows))).toEqual(rows);
  // reversed to '......ZSJL', then each handed piece swapped: Z->S, S->Z, J->L, L->J
  expect(mirrorRows(['LJSZ......'])).toEqual(['......SZLJ']);
});

test('a grid is always ROWS tall and cell counts survive the trim', () => {
  const g = occGrid(['..........', '#.........']);
  expect(g).toHaveLength(ROWS);
  expect(cellsOf(['#.........', '##........'])).toBe(3);
});

/* ── the name sets, and what they actually select ──────────────────────────────────────────────
 * The negatives this file pins are statements about SETS OF PAGES. A regex that quietly selects
 * the wrong pages turns "no round played a C-Spin" into a sentence about nothing, so what each
 * predicate picks is asserted by name rather than by count alone. */
test('isCSpin selects three doubtful names, and that is the coverage caveat in code', () => {
  const names = [...new Set(cat.pages.filter(p => isCSpin(p.name)).map(p => p.name))];
  expect(names).toHaveLength(3);
  // Not one of them is the C-Spin as harddrop draws it. If a future catalogue adds the real
  // thing this test fails, which is the point: the caveat in openers/README.md and in the
  // report section would then be wrong and must be rewritten.
  expect(names.some(n => /^Fake C-Spin/.test(n))).toBe(true);
  expect(names.some(n => /^Secspin/.test(n))).toBe(true);
  expect(names.some(n => /SDPC-Spin/.test(n))).toBe(true);
});

test('the DT sets separate the cannon proper from the substring hits', () => {
  const dtc = [...new Set(cat.pages.filter(p => isDTCannon(p.name)).map(p => p.name))];
  expect(dtc.some(n => /^DT Cannon \{/.test(n))).toBe(true);       // 開幕DT砲 itself
  // The word-boundary guard is load-bearing: a bare /DT ?Cannon/ swallows these four by
  // substring and silently widens the "canonical" set to openers it does not contain.
  for (const bogus of ['SDT Cannon', 'SDDT Cannon', 'SZDT Cannon', 'NEWDT Cannon'])
    expect(dtc.some(n => n.startsWith(bogus))).toBe(false);
  // ... while the widest reading does carry them, which is what makes it the widest reading
  const fam = [...new Set(cat.pages.filter(p => isDTFamily(p.name)).map(p => p.name))];
  for (const wide of ['SDDT Cannon', 'SZDT Cannon Opener', 'NEWDT Cannon'])
    expect(fam.some(n => n.startsWith(wide))).toBe(true);
  expect(fam.length).toBeGreaterThan(dtc.length);
  expect(NAME_SETS.map(s => s.key)).toEqual(['cspin', 'cspin_or_tki', 'dt_cannon', 'dt_family']);
});

test('TKI is in the catalogue under its own name, so widening C-Spin to it is a real widening', () => {
  // The whole reason `cspin_or_tki` exists: C-Spin is commonly identified with TKI, and TKI-3 is
  // catalogued with 12 pages that `isCSpin` does not select. If this were empty, reporting the
  // wide reading would be reporting the narrow one twice.
  const tki = [...new Set(cat.pages.filter(p => isTKI(p.name)).map(p => p.name))];
  expect(tki.some(n => /^TKI-3/.test(n))).toBe(true);
  expect(prepared.filter(p => isTKI(p.name) && !isCSpin(p.name)).length).toBeGreaterThan(0);
});

/* ── the corpus result, pinned ────────────────────────────────────────────────────────────────
 * Slow (it simulates every round), so it runs only when the sessions are present. */
test('no round comes within four cells of a catalogued C-Spin', () => {
  const res = analyse(SESSIONS.map(sessionDir));
  const clean = res.filter(r => r.clean);
  // Population re-blessed 2026-08-11: the longer verified prefix admits more clean-first-bag rounds
  // (358 -> 466 for the `hoisted`-DAS fix, -> 470 when `attackModel:'exact'` became the drift default,
  // -> 471 with confirm-timed garbage, -> 477 with triangle's exact DAS/ARR port). The finding is the
  // line below — `d <= 4` is still empty — not the population size.
  expect(clean.length).toBe(477);
  expect(clean.filter(r => r.bestCSpin!.d <= 4)).toHaveLength(0);
  // ... and the instrument is not simply blind: it finds five exact matches, all the same opener
  const exact = clean.filter(r => r.exact!.asDrawn.length || r.exact!.asMirror.length);
  expect(exact).toHaveLength(5);
  for (const r of exact)
    expect([...r.exact!.asDrawn, ...r.exact!.asMirror].some(n => /Perfect Clear Opener/.test(n))).toBe(true);
  // the Triple-bearing rounds are the bulk of the corpus, so the zero is not a small-n dodge
  // (264 -> 346 with the `hoisted`-DAS fix's longer prefix, -> 349 with confirm-timed garbage, -> 355
  // with the DAS/ARR port; still the bulk of 477 clean rounds)
  expect(clean.filter(r => r.sbTriple).length).toBe(355);
}, 300_000);

/* ── the artifact the report reads ─────────────────────────────────────────────────────────────
 * Every other artifact in this repo has to reproduce itself — the extractor must reproduce
 * facts.json, codegen the .dfy, build_claims the ledger. A simulator artifact nothing can
 * re-derive is a file nobody can check, so opener-facts.json is held to the same rule. */
test('rebuilding every session reproduces its committed opener-facts.json byte for byte', () => {
  for (const s of SESSIONS) {
    const path = `${sessionDir(s)}/sim/opener-facts.json`;
    process.env.REPLAY_DIR = sessionDir(s);
    expect(serialise(build(sessionDir(s)))).toBe(readFileSync(path, 'utf8'));
  }
}, 300_000);

test('the ordering metric separates the two openers, in every session, both players', () => {
  for (const s of SESSIONS) {
    const data = JSON.parse(readFileSync(`${sessionDir(s)}/sim/opener-facts.json`, 'utf8'));
    for (const p of data.ordering.players) {
      // Exposure first: a zero over rounds that never held both spins would say nothing at all.
      expect(p.rounds_with_both).toBeGreaterThan(0);
      // DT Cannon is a Double then a Triple; the C-Spin is a Triple then a Double. Every round
      // holding both runs the C-Spin order and none runs the DT order — the finding this
      // section exists to carry, pinned so a change to the simulator has to face it.
      expect(p.dt_order).toBe(0);
      expect(p.cspin_order).toBe(p.rounds_with_both);
    }
    // ... and it is not the verified-prefix window doing it: dropping the window adds exposure
    // and leaves the split alone. The strong claim — every round runs the C-Spin order —
    // stays exact (`cspin_order === rounds_with_both`, asserted below and unchanged). What the
    // `hoisted`-DAS fix changed (2026-08-11) is only the full-round DT count: extending the sim
    // past the verified prefix into UNVALIDATED boards surfaces a stray Double-then-Triple
    // subsequence in two rounds (07-28 and 08-09 pinglamb, 1 each). That exposure lives entirely
    // outside the window where the sim is oracle-checked, so it is bounded, not pinned to zero —
    // the windowed metric above stays strictly 0. A DT order that ever RIVALLED the C-Spin order
    // (dt_order approaching cspin_order) would still fail here.
    for (const p of data.ordering_full_round.players) {
      expect(p.cspin_order).toBe(p.rounds_with_both);
      expect(p.dt_order).toBeLessThanOrEqual(1);
      expect(p.dt_order).toBeLessThan(p.cspin_order / 10);
    }
  }
});

test('the slot-geometry test is a Triple-shape detector, which is why it is never a C-Spin count', () => {
  for (const s of SESSIONS) {
    const data = JSON.parse(readFileSync(`${sessionDir(s)}/sim/opener-facts.json`, 'utf8'));
    const by = Object.fromEntries(data.slot_geometry.rows.map((r: any) => [r.lines, r]));
    // The control, asserted rather than described: Triples overwhelmingly match the wiki window
    // and Doubles overwhelmingly do not. If these ever converge, the window has stopped
    // discriminating and the section's control paragraph is no longer true.
    expect(by[3].share_x1000).toBeGreaterThan(800);
    expect(by[2].share_x1000).toBeLessThan(250);
  }
});
