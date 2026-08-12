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
         cellsOf, isCSpin, isTKI, isDTCannon, isDTFamily, NAME_SETS, ROWS,
         loadWikiOpeners, openerPages, hasFullRow } from './match.ts';
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
  // Population re-blessed 2026-08-12 for the ORACLE board source (runCaseOracle): the far longer verified
  // prefix (24.8% -> 92.3%) admits more clean-first-bag rounds, 505 -> 522. The finding is the line below —
  // `d <= 4` is still empty — not the population.
  expect(clean.length).toBe(522);
  expect(clean.filter(r => r.bestCSpin!.d <= 4)).toHaveLength(0);
  // ... and the instrument is not simply blind: it finds exact matches, all the same opener. (5 -> 4 on
  // the oracle: one round the sim's short prefix had mislabelled clean now resolves differently.)
  const exact = clean.filter(r => r.exact!.asDrawn.length || r.exact!.asMirror.length);
  expect(exact).toHaveLength(4);
  for (const r of exact)
    expect([...r.exact!.asDrawn, ...r.exact!.asMirror].some(n => /Perfect Clear Opener/.test(n))).toBe(true);
  // the Triple-bearing rounds are the bulk of the corpus, so the zero is not a small-n dodge
  // (oracle: 374 -> 380; still the bulk of clean)
  expect(clean.filter(r => r.sbTriple).length).toBe(380);
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
      // DT Cannon is a Double then a Triple; the C-Spin is a Triple then a Double. The finding this
      // section carries is the STRONG claim: every round holding both spins runs the C-Spin order
      // (`cspin_order === rounds_with_both`), pinned so a change to the simulator has to face it.
      expect(p.cspin_order).toBe(p.rounds_with_both);
      // The weaker "0 DT order in the window" was an artefact of a SHORTER verified prefix. The
      // network garbage-cancel port (2026-08-12, igeHandler/ackiid) corrected the boards and
      // extended the prefix, so the same bounded stray Double-then-Triple SUBSEQUENCE that the
      // full-round metric already tolerates now falls inside the window in two rounds (07-22 and
      // 08-09 pinglamb, 1 each). These are C-Spin rounds carrying an extra early TSD, not DT
      // Cannons — `cspin_order === rounds_with_both` still includes them. Bounded exactly as the
      // full-round metric below: a DT order that ever RIVALLED the C-Spin order still fails.
      expect(p.dt_order).toBeLessThanOrEqual(1);
      expect(p.dt_order).toBeLessThan(p.cspin_order / 10);
    }
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

// ── the named openers ──────────────────────────────────────────────────────────────────────────
// Controls for the second source and for the table it feeds. Same shape of argument as above: the
// named-opener table's headline is that two players have DIFFERENT opening repertoires, and a
// difference is only worth stating once the instrument is shown to (a) agree with the catalogue
// wherever both draw an opener, (b) find nothing on boards that are not that opener, and (c) rest
// on a column that discriminates — which `≤N 格` provably does not.

const wiki = loadWikiOpeners();

test('the wiki transcription is internally consistent and pinned to a revision', () => {
  expect(wiki.schema).toBe('wiki-openers/1');
  expect(wiki.openers.length).toBe(7);              // 6 named openers, Mountainous split 1/2/3
  for (const p of wiki.provenance) expect(p.oldid).toBeGreaterThan(0);
  for (const op of wiki.openers) {
    expect(op.fields.length).toBeGreaterThan(0);
    for (const f of op.fields) {
      for (const r of f.rows) expect(r.length).toBe(10);
      expect(cellsOf(f.rows)).toBe(f.cells);
      expect(f.cells).toBe(f.locks * 4);
      // a full row would have CLEARED, so a field carrying one is not a board state and could
      // never equal a real opening — the defect that makes 484 catalogue pages unusable
      expect(hasFullRow(f.rows)).toBe(false);
    }
  }
});

test('control — the two sources agree wherever both draw the same opener', () => {
  // The dual-source argument applied to the opener fields. opener_db and harddrop are maintained
  // by different people from different diagrams, so agreement is evidence; this is the same check
  // extract_wiki_openers.cross_check runs, re-implemented here against the TS matcher so a bug in
  // one language's occupancy handling cannot pass both.
  let checked = 0;
  for (const op of wiki.openers) {
    if (!op.catalogue) continue;
    const clean = prepared.filter(p =>
      p.name.toLowerCase().includes(op.catalogue!.toLowerCase()) && !hasFullRow(p.page.rows));
    if (!clean.length) continue;                    // TKI-3: 12 pages, none of them clean
    for (const f of op.fields) {
      expect(nearest(occGrid(f.rows), clean).d).toBe(0);
      checked++;
    }
  }
  expect(checked).toBeGreaterThan(0);               // a vacuous pass here would prove nothing
});

test('control — TKI-3 is in the catalogue and is still unmeasurable from it', () => {
  // The justification for carrying a second source at all, asserted so it cannot quietly stop
  // being true: the catalogue KNOWS this opener and draws it only on a filled base.
  const named = prepared.filter(p => p.name.toLowerCase().includes('tki-3'));
  expect(named.length).toBe(12);
  expect(named.filter(p => !hasFullRow(p.page.rows)).length).toBe(0);
});

test('control — a board no named opener draws is matched by none of them', () => {
  const junk = occGrid(['#.#.#.#.#.', '.#.#.#.#.#', '#.#.#.#.#.', '.#.#.#.#.#']);
  for (const op of wiki.openers)
    expect(nearest(junk, openerPages(op, prepared).pages).d).not.toBe(0);
});

test('the ≤N band discriminates nothing, and the exact column does', () => {
  // THE control the section's fourth table may not be published without. If this ever fails, the
  // table has become readable as a hit rate and the paragraph saying otherwise is wrong.
  for (const s of SESSIONS) {
    const data = JSON.parse(readFileSync(`${sessionDir(s)}/sim/opener-facts.json`, 'utf8'));
    const rows = data.named_openers.openers.flatMap((o: any) =>
      o.players.map((p: any) => ({ key: o.key, ...p })));
    // the near band is reached about as often by the openers a player is NOT playing
    const within = rows.reduce((a: number, r: any) => a + r.within_threshold, 0);
    const baseWithin = rows.reduce((a: number, r: any) => a + r.baseline.within_threshold, 0);
    expect(baseWithin).toBeGreaterThan(within * 0.8);
    // while an exact match separates: Honey Cup outscores everything else in the catalogue on the
    // same boards, in every session and for both players. Stated as a COMPARISON and not as
    // `baseline.exact === 0`, which is what this assertion said first and is false — on 07-24 and
    // 08-01 two of yachi's boards do exactly match some other catalogued opener. The claim the
    // section makes is that exact discriminates, not that nothing else ever matches.
    for (const r of rows.filter((r: any) => r.key === 'honey_cup')) {
      expect(r.exact).toBeGreaterThan(0);
      expect(r.exact).toBeGreaterThan(r.baseline.exact);
    }
  }
});

test('the repertoire split reproduces in every session', () => {
  // The finding itself, pinned. pinglamb opens Honey Cup far more than yachi; yachi opens
  // Mountainous Stacking far more than pinglamb and is the only one who plays TKI-3 at all.
  // Five independent sessions, so this is a regression rather than an observation.
  for (const s of SESSIONS) {
    const data = JSON.parse(readFileSync(`${sessionDir(s)}/sim/opener-facts.json`, 'utf8'));
    const of = (key: string, user: string) => data.named_openers.openers
      .find((o: any) => o.key === key).players.find((p: any) => p.user === user);
    expect(of('honey_cup', 'pinglamb').exact).toBeGreaterThan(of('honey_cup', 'yachi').exact);
    expect(of('mountainous_1', 'yachi').exact)
      .toBeGreaterThan(of('mountainous_1', 'pinglamb').exact);
    expect(of('tki_3', 'yachi').exact).toBeGreaterThan(0);
    expect(of('tki_3', 'pinglamb').exact).toBe(0);
  }
});

test('the ordering metric names a class, and the class is harddrop\'s own', () => {
  for (const s of SESSIONS) {
    const data = JSON.parse(readFileSync(`${sessionDir(s)}/sim/opener-facts.json`, 'utf8'));
    const cls = data.ordering_class;
    expect(cls.openers).toBe(38);
    // the control is only a control if it covers the openers it is quoted against
    for (const n of ['C-Spin', 'Honey Cup', 'Stray Cannon', 'Mountainous Stacking'])
      expect(cls.members).toContain(n);
  }
});

test('a round claimed by two openers is only ever the documented alias', () => {
  // The columns must be independent apart from openers drawn into the SAME first-bag shape.
  // Mountainous Stacking 1 and 2 are that case; anything else appearing here would mean the
  // 6-lock and 7-lock samples had started double-counting rounds.
  for (const s of SESSIONS) {
    const data = JSON.parse(readFileSync(`${sessionDir(s)}/sim/opener-facts.json`, 'utf8'));
    const aliases = new Map<string, string[]>(
      data.named_openers.openers.map((o: any) => [o.key, o.occupancy_aliases]));
    for (const [key, row] of Object.entries<any>(data.named_openers.round_overlap)) {
      const wikiNames = data.named_openers.openers
        .filter((o: any) => Object.keys(row).includes(o.key)).map((o: any) => o.wiki);
      for (const n of wikiNames) expect(aliases.get(key)).toContain(n);
    }
  }
});

/**
 * Perfect Clears per session, from the `.ttrm` by way of facts.json. Written out because the
 * previous version of this test recomputed the total from facts.json inside the test and compared
 * it with the artifact — and BOTH walked the same wrong path (`players[u].allclear`, one level
 * above the counter, which lives under `clears`). Every session agreed on 0 and every session
 * actually held perfect clears; all five reports published "not one all night".
 *
 * A test that re-derives a value the same way the code does can only catch a typo. These are the
 * numbers themselves, so a reader can check one against `jq` and a future path change has to move
 * them rather than agree with itself.
 */
const PERFECT_CLEARS: Record<string, Record<string, number>> = {
  '2026-07-22': { yachi: 12, pinglamb: 7 },
  '2026-07-24': { yachi: 6, pinglamb: 4 },
  '2026-07-28': { yachi: 6, pinglamb: 8 },
  '2026-08-01': { yachi: 4, pinglamb: 8 },
  '2026-08-09': { yachi: 3, pinglamb: 7 },
};

test('the Perfect Clear count comes from the verified extractors, and is not zero', () => {
  for (const s of SESSIONS) {
    const data = JSON.parse(readFileSync(`${sessionDir(s)}/sim/opener-facts.json`, 'utf8'));
    expect(data.session_perfect_clears.source).toContain('facts.json');
    const per = data.session_perfect_clears.per_player;
    const expected = PERFECT_CLEARS[s];
    if (expected) expect(per).toEqual(expected);
    // The load-bearing assertion, independent of the table above: these sessions all HAVE perfect
    // clears, so a reader that returns zero for every player is a broken reader, not a quiet night.
    expect(Object.values<number>(per).reduce((a, b) => a + b, 0)).toBeGreaterThan(0);
    // and a session with no perfect clear cannot contain a completed PCO
    const pco = data.named_openers.openers.find((o: any) => o.key === 'pco');
    for (const p of pco.players)
      if (!per[p.user]) expect(p.matched_and_delivered ?? 0).toBe(0);
  }
});

test('Perfect Clear timing is published only where the simulator matched the replay', () => {
  // The count is the control on the timing: the simulator's per-round Perfect Clear count is
  // compared with `results.stats.clears.allclear` for every player-round, and the piece numbers
  // are emitted as null unless every round agreed. Over the five committed sessions the check is
  // clean, which is the finding — the same flag an earlier revision of this file called wrong.
  for (const s of SESSIONS) {
    const data = JSON.parse(readFileSync(`${sessionDir(s)}/sim/opener-facts.json`, 'utf8'));
    const t = data.perfect_clear_timing;
    expect(t.check.checked).toBe(t.check.player_rounds);      // no round left unchecked
    expect(t.check.rounds_agreeing).toBe(t.check.checked);
    expect(t.check.perfect_clears_sim).toBe(t.check.perfect_clears_replay);
    expect(t.check.agrees).toBe(true);

    // The two sources must land on the same per-player total, one counted off lock indices and
    // one off facts.json.
    const per = data.session_perfect_clears.per_player;
    for (const p of t.players) {
      expect(p.perfect_clears).toBe(per[p.user]);
      const placed = Object.values<number>(p.by_piece).reduce((a, b) => a + b, 0);
      expect(placed).toBe(p.perfect_clears);
      // Every Perfect Clear inside harddrop's ten-piece PCO deadline is counted as such, and a
      // PCO can only be DELIVERED in a round that had one.
      expect(p.within_pco_window)
        .toBe(Object.entries<number>(p.by_piece)
          .filter(([k]) => Number(k) <= t.pco_window_locks).reduce((a, [, v]) => a + v, 0));
    }
    const pco = data.named_openers.openers.find((o: any) => o.key === 'pco');
    const delivered = pco.players.reduce((a: number, p: any) => a + (p.matched_and_delivered ?? 0), 0);
    expect(delivered).toBeLessThanOrEqual(
      t.players.reduce((a: number, p: any) => a + p.within_pco_window, 0));
  }
});

/** Perfect Clears that met harddrop's ten-piece PCO deadline, per session. Pinned PER SESSION
 *  rather than pooled: a sixth session must not be able to change a pooled headline by arriving,
 *  and a per-session table makes a drift name the session it came from. */
const IN_PCO_WINDOW: Record<string, number> = {
  '2026-07-22': 1, '2026-07-24': 1, '2026-07-28': 0, '2026-08-01': 1, '2026-08-09': 0,
};

test('these sessions run mid-game Perfect Clears, not the Perfect Clear Opener', () => {
  // The finding the timing metric exists for, and the reason the PCO row reads the way it does:
  // almost every Perfect Clear here lands on piece 20 — two bags of stacking — not inside the
  // opener. Pinned so a change of board source has to restate it rather than absorb it.
  let total = 0, inWindow = 0, atTwenty = 0;
  for (const s of SESSIONS) {
    const t = JSON.parse(readFileSync(`${sessionDir(s)}/sim/opener-facts.json`, 'utf8'))
      .perfect_clear_timing;
    let sessionWindow = 0;
    for (const p of t.players) {
      total += p.perfect_clears;
      inWindow += p.within_pco_window;
      sessionWindow += p.within_pco_window;
      atTwenty += p.by_piece['20'] ?? 0;
    }
    if (IN_PCO_WINDOW[s] !== undefined) expect([s, sessionWindow]).toEqual([s, IN_PCO_WINDOW[s]!]);
  }
  // The pooled shape, stated against the same corpus the table above covers.
  const pinned = SESSIONS.filter(s => PERFECT_CLEARS[s]);
  if (pinned.length === SESSIONS.length) {
    expect(total).toBe(Object.values(PERFECT_CLEARS)
      .reduce((a, r) => a + Object.values(r).reduce((x, y) => x + y, 0), 0));
    expect(inWindow).toBe(Object.values(IN_PCO_WINDOW).reduce((a, b) => a + b, 0));
    expect(atTwenty).toBeGreaterThan(total / 2);   // the cluster IS the finding
  }
});
