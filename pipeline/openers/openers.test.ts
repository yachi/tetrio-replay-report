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
import { loadCatalogue, prepare, occGrid, mirrorRows, exactMatches, nearest, distance,
         cellsOf, isCSpin, ROWS } from './match.ts';
import { analyse } from './run-openers.ts';

const cat = loadCatalogue();
const prepared = prepare(cat.pages);
const cspin = prepared.filter(p => isCSpin(p.name));

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

/* ── the corpus result, pinned ────────────────────────────────────────────────────────────────
 * Slow (it simulates every round), so it runs only when the sessions are present. */
test('no round comes within four cells of a catalogued C-Spin', () => {
  const dirs = ['sessions/2026-07-22', 'sessions/2026-07-24', 'sessions/2026-07-28', 'sessions/2026-08-01']
    .map(d => `${import.meta.dir}/../../${d}`);
  const res = analyse(dirs);
  const clean = res.filter(r => r.clean);
  expect(clean.length).toBe(300);
  expect(clean.filter(r => r.bestCSpin!.d <= 4)).toHaveLength(0);
  // ... and the instrument is not simply blind: it finds five exact matches, all the same opener
  const exact = clean.filter(r => r.exact!.asDrawn.length || r.exact!.asMirror.length);
  expect(exact).toHaveLength(5);
  for (const r of exact)
    expect([...r.exact!.asDrawn, ...r.exact!.asMirror].some(n => /Perfect Clear Opener/.test(n))).toBe(true);
  // the Triple-bearing rounds are the bulk of the corpus, so the zero is not a small-n dodge
  expect(clean.filter(r => r.sbTriple).length).toBe(219);
}, 300_000);
