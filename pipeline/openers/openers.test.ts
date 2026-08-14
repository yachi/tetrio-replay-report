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
import { build, serialise, donationCols, caveAt, cavity, dualVerdict,
         DONATION_CAVITY, DONATION_WALLED_ROWS, CAVE_MIN_WIDTH } from '../sim/emit-opener-facts.ts';

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

/* ── DONATION and STMB CAVE ────────────────────────────────────────────────────────────────────
 * The two per-T-spin board-state metrics. Both are QUARANTINED (one simulator, no second
 * implementation) and both report numbers that are small or zero, which is the hardest kind of
 * number to publish: a detector that has never been shown to FIRE cannot make a null mean
 * anything. So this block is in three parts, in increasing strength:
 *
 *   1. the corpus result, as LITERALS — same rule as PERFECT_CLEARS above. A test that
 *      re-derives a value the way the code does can only catch a typo.
 *   2. INSTRUMENT CONTROLS — harddrop's own drawings for both techniques, fed straight through
 *      the two predicates. Every positive must fire, both negatives must not.
 *   3. DISCRIMINATING POWER — that the naive reading of each technique is NOT what is counted,
 *      asserted by behaviour on purpose-built boards rather than by editing the source.
 */

/** Corpus result per session, written out. `clears` is the licensing denominator
 *  (`donation.check.tspin_clears`), not a count of anything donated. */
const DONATION: Record<string, { donations: number; natural: number; b2b: number; clears: number }> = {
  '2026-07-22': { donations: 21, natural: 13, b2b: 2, clears: 795 },
  '2026-07-24': { donations: 15, natural: 10, b2b: 1, clears: 544 },
  '2026-07-28': { donations: 13, natural: 13, b2b: 0, clears: 626 },
  '2026-08-01': { donations: 20, natural: 13, b2b: 2, clears: 612 },
  '2026-08-09': { donations: 13, natural:  8, b2b: 0, clears: 565 },
};

/** `width_ge_3` is the RAW shape count and is NOT a cave count — `min_depth_ge_2` is the column
 *  to read, and `triple_control` is the same shape under the spin the technique is not about. */
const CAVE: Record<string, { width_ge_3: number; min_depth_ge_2: number; triple_control: number }> = {
  '2026-07-22': { width_ge_3: 4, min_depth_ge_2: 0, triple_control:  8 },
  '2026-07-24': { width_ge_3: 6, min_depth_ge_2: 1, triple_control: 10 },
  '2026-07-28': { width_ge_3: 5, min_depth_ge_2: 0, triple_control:  8 },
  '2026-08-01': { width_ge_3: 8, min_depth_ge_2: 0, triple_control:  4 },
  '2026-08-09': { width_ge_3: 7, min_depth_ge_2: 0, triple_control:  8 },
};

/** THE DENOMINATOR ANCHOR, per session, as literals: the replay's own whole-round T-spin-clear
 *  total (the twice-extracted counters summed) and what the verified prefix scores out of it.
 *
 *  Written out rather than recomputed for the reason the whole block above is: a test that
 *  re-derives a value the way the code does can only catch a typo. This one has a second reason —
 *  the anchor's failure mode is silent in the direction that looks GOOD. Were the emitter to start
 *  reading a counter that is absent, `?? 0` on both sides would make the comparison trivially agree
 *  and `agrees` would stay true over a corpus of zeros, which is exactly the shape of the bug that
 *  published "no perfect clears" for five sessions holding 65. So `replay` is pinned, and the sum
 *  is asserted against the corpus figure. */
const TSPIN_ANCHOR: Record<string, { rounds: number; replay: number; scored: number }> = {
  '2026-07-22': { rounds: 158, replay: 879, scored: 795 },
  '2026-07-24': { rounds: 100, replay: 578, scored: 544 },
  '2026-07-28': { rounds: 128, replay: 667, scored: 626 },
  '2026-08-01': { rounds: 106, replay: 658, scored: 612 },
  '2026-08-09': { rounds: 100, replay: 597, scored: 565 },
};

/** THE SECOND ENGINE, per session, as literals: [both_yes, oracle_positives] for each metric, and
 *  how far the comparison reached. The cave agrees on every positive in range and the donation on a
 *  quarter of them — two results the OVERALL agreement rate (98%+ for both) hides completely,
 *  because 1292 of the donation's 1301 agreements are two engines saying "no". */
const DUAL: Record<string, { comparable: number; scored: number; sameBoard: number;
                             cave: [number, number]; don: [number, number] }> = {
  '2026-07-22': { comparable: 360, scored: 795, sameBoard: 222, cave: [3, 3], don: [2, 7] },
  '2026-07-24': { comparable: 244, scored: 544, sameBoard: 142, cave: [2, 2], don: [2, 9] },
  '2026-07-28': { comparable: 273, scored: 626, sameBoard: 157, cave: [2, 2], don: [0, 6] },
  '2026-08-01': { comparable: 229, scored: 612, sameBoard: 133, cave: [2, 2], don: [2, 9] },
  '2026-08-09': { comparable: 240, scored: 565, sameBoard: 141, cave: [4, 4], don: [3, 5] },
};

const facts = (s: string) =>
  JSON.parse(readFileSync(`${sessionDir(s)}/sim/opener-facts.json`, 'utf8'));
const sum = (xs: number[]) => xs.reduce((a, b) => a + b, 0);

test('the second engine agrees on every cave and on a quarter of the donations', () => {
  let cavePos = 0, caveHit = 0, donPos = 0, donHit = 0, bothNo = 0;
  let comparable = 0, scored = 0;
  for (const s of SESSIONS) {
    const f = facts(s);
    const d = f.donation.dual_engine;
    const want = DUAL[s]!;
    // the same block is embedded under both metrics and must be the same object
    expect(JSON.stringify(f.stmb_cave.dual_engine)).toBe(JSON.stringify(d));
    expect([s, d.locks_comparable]).toEqual([s, want.comparable]);
    expect([s, d.locks_scored]).toEqual([s, want.scored]);
    // a check reaching everything would mean the hand-port's prefix had stopped being the limit,
    // which is a change of premise rather than an improvement — it must fail here first
    expect(d.locks_comparable).toBeLessThan(d.locks_scored);

    for (const [k, w] of [['cave', want.cave], ['donation', want.don]] as const) {
      const m = d[k];
      expect([s, k, m.agreement_on_positives]).toEqual([s, k, w]);
      expect([s, k, m.both_yes + m.oracle_only]).toEqual([s, k, m.oracle_positives]);
      // the four cells partition the comparable locks
      expect(m.both_yes + m.oracle_only + m.other_only + m.both_no).toBe(d.locks_comparable);
      expect(m.agreement_overall).toEqual([m.both_yes + m.both_no, d.locks_comparable]);
    }
    cavePos += d.cave.oracle_positives; caveHit += d.cave.both_yes;
    donPos += d.donation.oracle_positives; donHit += d.donation.both_yes;
    bothNo += d.donation.both_no;
    comparable += d.locks_comparable; scored += d.locks_scored;
  }
  // THE TWO CORPUS FIGURES, and the gap between them is the finding.
  expect([caveHit, cavePos]).toEqual([13, 13]);      // every cave in range, both engines
  expect([donHit, donPos]).toEqual([9, 36]);         // three donations in four disagree
  expect([comparable, scored]).toEqual([1346, 3142]);

  // …and the reason neither number may be quoted as an overall rate: the donation's 96.7% is
  // almost entirely two engines agreeing that nothing happened. Asserted rather than commented,
  // so a future change that makes the overall rate meaningful has to restate this.
  const overallAgree = donHit + bothNo;
  expect(bothNo / overallAgree).toBeGreaterThan(0.99);
  expect(donHit / donPos).toBeLessThan(0.3);

  // The cave result is REAL but PARTIAL, and the second half is what keeps it in quarantine: the
  // corpus holds 30 wide gaps and only 13 are reachable by a second engine.
  const allCaves = sum(SESSIONS.map(s => sum(facts(s).stmb_cave.players.map((p: any) => p.width_ge_3))));
  expect(allCaves).toBe(30);
  expect(cavePos).toBeLessThan(allCaves);
});

test('the board split is what makes the donation 9/36 readable, and it is not the cave\'s story', () => {
  // WHY THIS IS A SEPARATE TEST. `agreement_on_positives` says the two engines disagree about three
  // donations in four; it does not say WHY. Splitting the positives by whether the other engine had
  // the same board answers it — and answers it differently for the two metrics, which is why the
  // section may not word them alike.
  let same = 0, comparable = 0;
  const agg = { don: [0, 0, 0, 0], cave: [0, 0, 0, 0] };  // [posSame, posDiff, agreeSame, agreeDiff]
  for (const s of SESSIONS) {
    const d = facts(s).donation.dual_engine;
    expect([s, d.locks_same_board]).toEqual([s, DUAL[s]!.sameBoard]);   // pinned, never re-derived
    same += d.locks_same_board; comparable += d.locks_comparable;
    for (const k of ['don', 'cave'] as const) {
      const b = d.board_split[k];
      const m = d[k === 'don' ? 'donation' : 'cave'];
      // the split must partition the SAME positives the confusion matrix counted, or the two blocks
      // are describing different populations while sitting in one object
      expect([s, k, b.positives_same_board + b.positives_diff_board]).toEqual([s, k, m.oracle_positives]);
      expect([s, k, b.agree_same_board + b.agree_diff_board]).toEqual([s, k, m.both_yes]);
      agg[k][0] += b.positives_same_board; agg[k][1] += b.positives_diff_board;
      agg[k][2] += b.agree_same_board;     agg[k][3] += b.agree_diff_board;
    }
  }
  // At 41% of the comparison points the two engines are judging DIFFERENT boards. Every figure in
  // dual_engine has to be read inside that.
  expect([same, comparable]).toEqual([795, 1346]);

  // THE DONATION: where the boards agree the verdicts agree perfectly, and where they differ they
  // mostly do not. So the disagreement is the BOARD (oracle-source.ts's garbage-hole columns), not
  // the predicate — the opposite of what "the two engines disagree about donations" sounds like.
  expect(agg.don).toEqual([6, 30, 6, 3]);
  expect(agg.don[2]).toBe(agg.don[0]);                    // 6 of 6 on identical boards
  expect(agg.don[3] * 3).toBeLessThan(agg.don[1]);        // 3 of 30 on boards that differ

  // THE CAVE: a different statement, and it must not be worded like the donation's. Its verdict
  // survives boards that differ (10 of 10), which is ROBUSTNESS — consistent with the drift sitting
  // in low garbage rows while the cave is local to the spin. It is not evidence of correctness.
  expect(agg.cave).toEqual([3, 10, 3, 10]);
  expect(agg.cave[3]).toBe(agg.cave[1]);
});

test('dualVerdict refuses a lock its own engine contradicts, and refuses one it cannot check', () => {
  // THE TEETH FOR THE STRONG LICENCE. Reverting to the index lookup or off-by-one-ing the frame is
  // already caught by the byte-identity gate (locks_comparable collapses 1346 -> 0). What that gate
  // CANNOT catch is weakening the licence itself: dropping back to `rows.length === lk.cleared`, or
  // comparing only the LENGTH of clearedRows, leaves all five artefacts byte-identical on this
  // corpus. Both are killed here, on synthetic boards, because no real lock exercises them.
  const H = 40, W = 10;
  const board = () => Array.from({ length: H }, (_, r) =>
    Array.from({ length: W }, (_, c) => (r === 38 && c < 9 ? 'X' : null)));
  const lk = { piece: 'T', spin: 'full', cleared: 1, frame: 100,
               cells: [{ row: 38, col: 9 }, { row: 37, col: 9 }, { row: 37, col: 8 }] };
  const at = (records: { frame: number; clearedRows: number[] }[]) =>
    dualVerdict({ locks: [{ ...lk, frame: 1 }, lk], boards: [board(), board()], records }, 1);

  // the board makes row 38 full; the engine's own record says it cleared row 37. Same LENGTH,
  // different CONTENT — a length-only compare waves this through.
  expect(at([{ frame: 100, clearedRows: [37] }])).toBeNull();
  // no record at the lock's frame: UNKNOWN, compared against nothing.
  expect(at([])).toBeNull();
  // …and the licence is not simply refusing everything: the honest version of the same lock passes.
  expect(at([{ frame: 100, clearedRows: [38] }])).not.toBeNull();

  // NOT ASSERTED, DELIBERATELY: that a missing record is excluded rather than read as `[]`. A lock
  // with cleared > 0 always makes at least one row full, so an empty `theirs` can never match and
  // the two spellings return null for every possible input. It is an equivalent mutant, not a gap —
  // writing a test that appeared to cover it would be writing for the checker.
});

test('the denominator is anchored to the replay\'s own twice-extracted T-spin counters', () => {
  let rounds = 0, agreeing = 0, simTotal = 0, replayTotal = 0, scored = 0;
  for (const s of SESSIONS) {
    const f = facts(s);
    const a = f.donation.counter_anchor;
    const want = TSPIN_ANCHOR[s]!;

    // every player-round checked, none unknown, and every one of them agreeing
    expect([s, a.player_rounds]).toEqual([s, want.rounds]);
    expect([s, a.checked]).toEqual([s, want.rounds]);
    expect([s, a.unknown_rounds]).toEqual([s, 0]);
    expect([s, a.rounds_agreeing]).toEqual([s, want.rounds]);
    expect([s, a.agrees]).toEqual([s, true]);
    // a T-spin clear of a kind no counter names would be dropped from the SIM side only, which
    // makes agreement easier — so it is asserted at zero rather than trusted
    expect([s, a.unclassified_sim_clears]).toEqual([s, 0]);

    // the two totals, pinned. Not `sim === replay` alone: two zeros satisfy that.
    expect([s, a.tspin_clears_replay]).toEqual([s, want.replay]);
    expect([s, a.tspin_clears_sim]).toEqual([s, want.replay]);
    expect([s, a.tspin_clears_scored]).toEqual([s, want.scored]);
    expect(a.tspin_clears_replay).toBeGreaterThan(0);

    // the anchor covers the licensing denominator, and the prefix is a SUBSET of the whole round
    expect([s, a.tspin_clears_scored]).toEqual([s, f.donation.check.tspin_clears]);
    expect(a.tspin_clears_scored).toBeLessThanOrEqual(a.tspin_clears_replay);

    // the per-kind tallies partition the total, and each kind agrees in every round
    expect(sum(Object.values(a.by_kind).map((k: any) => k.replay))).toBe(a.tspin_clears_replay);
    expect(sum(Object.values(a.by_kind).map((k: any) => k.sim))).toBe(a.tspin_clears_sim);
    for (const [kind, k] of Object.entries<any>(a.by_kind))
      expect([s, kind, k.rounds_agreeing]).toEqual([s, kind, want.rounds]);

    // the per-player columns the section prints must add up to the same two numbers
    expect([s, sum(f.donation.players.map((p: any) => p.tspin_clears_replay))])
      .toEqual([s, want.replay]);
    expect(sum(f.stmb_cave.players.map((p: any) => p.tspin_doubles_replay)))
      .toBe(a.by_kind.tspindoubles.replay + a.by_kind.minitspindoubles.replay);
    expect(f.stmb_cave.triple_control.tspin_triples_replay)
      .toBe(a.by_kind.tspintriples.replay + a.by_kind.minitspintriples.replay);
    // the cave metric is a subset of the doubles it is scored over
    expect(sum(f.stmb_cave.players.map((p: any) => p.tspin_doubles_scored)))
      .toBeLessThanOrEqual(sum(f.stmb_cave.players.map((p: any) => p.tspin_doubles_replay)));

    rounds += a.player_rounds; agreeing += a.rounds_agreeing;
    simTotal += a.tspin_clears_sim; replayTotal += a.tspin_clears_replay; scored += a.tspin_clears_scored;
  }
  // The corpus figure this whole change rests on, stated once: the simulator reproduces the
  // replay's own T-spin counters on every player-round of every session, and the verified prefix
  // the two tables score covers 3142 of those 3379 clears.
  expect([rounds, agreeing]).toEqual([592, 592]);
  expect([simTotal, replayTotal, scored]).toEqual([3379, 3379, 3142]);
});

test('the donation counts are pinned per session, and the licensing check is clean', () => {
  for (const s of SESSIONS) {
    const d = facts(s).donation;
    const want = DONATION[s]!;
    expect([s, sum(d.players.map((p: any) => p.donations))]).toEqual([s, want.donations]);
    expect([s, sum(d.players.map((p: any) => p.natural))]).toEqual([s, want.natural]);
    expect([s, sum(d.players.map((p: any) => p.b2b_breaking))]).toEqual([s, want.b2b]);
    expect([s, d.check.tspin_clears]).toEqual([s, want.clears]);
    // the per-player scored counts must add up to the check's denominator — one number, two paths
    expect(sum(d.players.map((p: any) => p.tspin_clears_scored))).toBe(d.check.tspin_clears);

    // THE LICENSING FIGURE. `withT` (the per-lock board snapshot plus the lock's cells) and the
    // engine's own clearedRows were built from different states; every scored clear is one they
    // agreed about. A disagreement is dropped rather than scored, so a corpus that started
    // disagreeing would quietly shrink the denominator instead of failing — hence the assertion.
    expect([s, d.check.reconstruction_disagreed]).toEqual([s, 0]);
    expect(d.check.reconstruction_agreed).toBe(d.check.tspin_clears);
    expect(d.check.agrees).toBe(true);

    // Every well in this corpus is garbage-derived, which is the caveat the section may not drop:
    // the oracle keeps the engine's seeded-RNG hole columns, so WHICH column was donated into is
    // not established. A self-built well appearing here would change that sentence.
    expect([s, sum(d.players.map((p: any) => p.self_built_well))]).toEqual([s, 0]);
    expect(sum(d.players.map((p: any) => p.garbage_derived_well))).toBe(want.donations);
    // the three plug classes partition the donations
    expect(sum(d.players.map((p: any) => p.natural + p.b2b_breaking + p.plug_unknown)))
      .toBe(want.donations);
  }
});

test('the STMB cave counts are pinned, and the corpus holds exactly one genuine cave', () => {
  let deeper = 0;
  for (const s of SESSIONS) {
    const c = facts(s).stmb_cave;
    const want = CAVE[s]!;
    expect([s, sum(c.players.map((p: any) => p.width_ge_3))]).toEqual([s, want.width_ge_3]);
    expect([s, sum(c.players.map((p: any) => p.min_depth_ge_2))]).toEqual([s, want.min_depth_ge_2]);
    expect([s, c.triple_control.width_ge_3]).toEqual([s, want.triple_control]);
    expect(c.min_width).toBe(CAVE_MIN_WIDTH);
    // the two histograms and the per-player columns are the same events counted twice
    expect(sum(Object.values<number>(c.width_histogram))).toBe(want.width_ge_3);
    expect(sum(Object.values<number>(c.min_depth_histogram))).toBe(want.width_ge_3);
    expect(sum(Object.entries<number>(c.min_depth_histogram)
      .filter(([k]) => Number(k) >= 2).map(([, v]) => v))).toBe(want.min_depth_ge_2);
    deeper += want.min_depth_ge_2;
  }
  // THE FINDING. One genuine cave in 592 player-rounds across five sessions — every other >=3-wide
  // hit is a single row deep, i.e. a dimple. Pinned as a corpus total so a change has to break this
  // test rather than silently re-rate the metric from "essentially never" to "occasionally".
  expect(deeper).toBe(1);
});

/* ── instrument controls, from harddrop's own diagrams ─────────────────────────────────────────
 * Rows are 10 wide, '.' empty and any other character filled; T cells are written (col,row) as
 * the articles number them. The board handed to the predicates is the occupancy WITH the T in it,
 * and the cleared rows are the ones that are full because of it — exactly the two values the
 * session walk in emit-opener-facts.ts computes before calling them. */
function drawn(rows: string[], t: [number, number][] | null) {
  for (const r of rows) expect(r.length).toBe(10);
  const g = rows.map(r => [...r].map(ch => ch !== '.'));
  const cells = (t ?? []).map(([col, row]) => ({ row, col }));
  for (const q of cells) g[q.row]![q.col] = true;
  const cleared: number[] = [];
  for (let r = 0; r < g.length; r++) if (g[r]!.every(Boolean)) cleared.push(r);
  return { g, cells, cleared, h: g.length };
}

/** The controls come out of `wiki-tspin-techniques.json` rather than being typed here, and that is
 *  the point: the same boards written down twice are two things that can drift, and this repo
 *  gates that everywhere else. The JSON is generated from the raw wiki HTML by
 *  `extract_wiki_techniques.py` (whose own selftest kills 19 mutants), and it carries each board's
 *  EXPECTED outcome — `clears`, `well_col`, `cavity`, `cave_width` — so these tests assert that the
 *  predicate reproduces the transcription's own declared values rather than merely returning
 *  something. A control list that is silently emptied upstream fails here on the count assertions. */
interface Ctl {
  name: string; kind: string; rows: string[]; occupancy: string[]; cells: number;
  t_cells: [number, number][] | null; clears: number;
  well_col?: number; cavity?: number; cave_first_col?: number; cave_width?: number;
}
const WIKI_TECH = JSON.parse(
  readFileSync(`${import.meta.dir}/wiki-tspin-techniques.json`, 'utf8')) as {
    schema: string;
    provenance: { page: string; oldid: number; sha256: string }[];
    donation: { cavity_cells: number; walled_deepest_rows: number; controls: Ctl[];
                near_miss: { works: string; fails: string; differing_cells: [number, number][] } };
    stmb_cave: { min_width: number; controls: Ctl[] };
  };

const controls = (tech: 'donation' | 'stmb_cave', kind: 'positive' | 'negative') =>
  WIKI_TECH[tech].controls.filter(c => c.kind === kind);
const control = (tech: 'donation' | 'stmb_cave', name: string) =>
  WIKI_TECH[tech].controls.find(c => c.name === name)!;

const DONATION_POSITIVES = controls('donation', 'positive');
const DONATION_NEGATIVES = controls('donation', 'negative');

test('the committed controls still cover both techniques', () => {
  // Guards the guards: every assertion below iterates these lists, so a transcription that lost its
  // positives would turn each control test into a vacuous pass over an empty array.
  expect(DONATION_POSITIVES.length).toBeGreaterThanOrEqual(3);
  expect(DONATION_NEGATIVES.length).toBeGreaterThanOrEqual(1);
  expect(controls('stmb_cave', 'positive').length).toBeGreaterThanOrEqual(3);
  expect(controls('stmb_cave', 'negative').length).toBeGreaterThanOrEqual(1);
});

test('the transcription is pinned to a revision, self-consistent, and carries the thresholds', () => {
  expect(WIKI_TECH.schema).toBe('wiki-tspin-techniques/1');
  for (const p of WIKI_TECH.provenance) {
    expect(p.oldid).toBeGreaterThan(0);        // a revision, not "the page as it stood one afternoon"
    expect(p.sha256).toMatch(/^[0-9a-f]{64}$/);
  }
  // The transcription carries each board twice — as the pieces are DRAWN and as an occupancy mask —
  // and the tests below read the drawn view. Two views that disagreed would mean the tests were
  // scoring a board the article does not draw, so they are checked against each other here.
  for (const tech of ['donation', 'stmb_cave'] as const)
    for (const c of WIKI_TECH[tech].controls) {
      for (const r of c.rows) expect(r.length).toBe(10);
      expect([c.name, c.rows.map(r => [...r].map(x => (x === '.' ? '.' : '#')).join(''))])
        .toEqual([c.name, c.occupancy]);
      expect([c.name, c.cells])
        .toEqual([c.name, sum(c.occupancy.map(r => [...r].filter(x => x === '#').length))]);
    }
  // AND THE THRESHOLDS ARE HARDDROP'S, now with two independent transcriptions of them to compare.
  // `DONATION_CAVITY` and friends are the numbers the article's drawings support; a constant nobody
  // can trace back to the source is a threshold chosen to fit the result, and this is what stops one
  // being tuned quietly. (Read with the cavity-5 positive below: the code's 4 is a FLOOR, not a copy
  // of one drawing.)
  expect(WIKI_TECH.donation.cavity_cells).toBe(DONATION_CAVITY);
  expect(WIKI_TECH.donation.walled_deepest_rows).toBe(DONATION_WALLED_ROWS);
  expect(WIKI_TECH.stmb_cave.min_width).toBe(CAVE_MIN_WIDTH);
});

test('control — the donation predicate fires on every setup harddrop draws as a donation', () => {
  // A count of 21 in a session of 795 T-spin clears is only a measurement if the instrument is
  // shown to find the thing when it is unambiguously there. These are the article's own boards,
  // and each is asserted against the outcome the transcription recorded for it — including the
  // T-Spin Single donation, which clears ONE row over a five-cell cavity. Pinning "a Double with
  // cavity 4" here would have quietly excluded it.
  for (const ctl of DONATION_POSITIVES) {
    const b = drawn(ctl.rows, ctl.t_cells);
    expect([ctl.name, b.cleared.length]).toEqual([ctl.name, ctl.clears]);
    const wells = donationCols(b.g, b.cleared, b.cells, b.h);
    expect([ctl.name, wells.length]).toEqual([ctl.name, 1]);
    expect([ctl.name, wells[0]!.col]).toEqual([ctl.name, ctl.well_col]);
    expect([ctl.name, wells[0]!.cavity]).toEqual([ctl.name, ctl.cavity]);
    expect([ctl.name, wells[0]!.cavity >= DONATION_CAVITY]).toEqual([ctl.name, true]);
  }
});

test('control — and does not fire on harddrop\'s own "an S donation does not work" case', () => {
  // The article draws this one to show the setup FAILING: the T-spin clears nothing, so nothing is
  // donated. A predicate that scored it would be scoring the shape rather than the technique.
  //
  // It is the strongest negative on the page because it is a MINIMAL PAIR — `near_miss` records
  // that it differs from the working T-Spin Single donation at exactly one cell — so it cannot be
  // passed by a detector that merely dislikes the general look of the board.
  for (const ctl of DONATION_NEGATIVES) {
    const b = drawn(ctl.rows, ctl.t_cells);
    expect([ctl.name, b.cleared.length]).toEqual([ctl.name, ctl.clears]);
    expect([ctl.name, donationCols(b.g, b.cleared, b.cells, b.h)]).toEqual([ctl.name, []]);
  }
});

test('control — harddrop\'s own minimal pair: ONE cell decides the donation', () => {
  // THE STRONGEST CONTROL HERE, and it is the article's rather than this test's. harddrop draws
  // "A case where an S donation does not work" directly beneath the setup that does work, and the
  // two boards differ in a single cell. A detector that fired on both would be reading the
  // silhouette; one that fired on neither would be dead. The predicate has to SPLIT them, and
  // splitting a one-cell difference is not something a coincidence does.
  //
  // The comment above the negatives test asserts this pair exists — so it is checked, not described:
  // the differing cells are recomputed from the two boards and compared with what the transcription
  // recorded, which also catches `near_miss` naming a pair that has since been re-transcribed apart.
  const nm = WIKI_TECH.donation.near_miss;
  const ok = drawn(control('donation', nm.works).rows, control('donation', nm.works).t_cells);
  const no = drawn(control('donation', nm.fails).rows, control('donation', nm.fails).t_cells);
  const diff: [number, number][] = [];
  for (let r = 0; r < ok.g.length; r++)
    for (let c = 0; c < 10; c++) if (ok.g[r]![c] !== no.g[r]![c]) diff.push([c, r]);
  expect(diff).toEqual(nm.differing_cells);
  expect(diff).toHaveLength(1);
  expect(donationCols(ok.g, ok.cleared, ok.cells, ok.h)).toHaveLength(1);
  expect(donationCols(no.g, no.cleared, no.cells, no.h)).toHaveLength(0);
});

/** Basic Structures from harddrop's STMB Cave page, read out of the committed transcription. The
 *  cave is OFFSET from the T — it shares two of the T's three columns and reaches one column past
 *  them — which is why the predicate tests overlap and never containment. */
const CAVE_POSITIVES = controls('stmb_cave', 'positive');
const CAVE_NEGATIVES = controls('stmb_cave', 'negative');

test('control — the cave predicate fires on every Basic Structure harddrop draws', () => {
  for (const ctl of CAVE_POSITIVES) {
    const b = drawn(ctl.rows, ctl.t_cells);
    expect([ctl.name, b.cleared.length]).toEqual([ctl.name, ctl.clears]);   // a Double, per the page
    const cave = caveAt(b.g, b.cleared, b.cells, b.h);
    expect([ctl.name, cave?.width ?? null]).toEqual([ctl.name, ctl.cave_width]);
    expect([ctl.name, (cave?.width ?? 0) >= CAVE_MIN_WIDTH]).toEqual([ctl.name, true]);
    // and it is the T's OWN cave: the run under the cleared rows overlaps the T's column span,
    // starting at the column the transcription recorded
    const tc = new Set(b.cells.map(q => q.col));
    const run = runAt(b.g, Math.max(...b.cleared) + 1, tc);
    expect([ctl.name, run?.from ?? null]).toEqual([ctl.name, ctl.cave_first_col]);
    // DEPTH, and it is worth asserting right beside the corpus result above. harddrop's own drawn
    // caves are 2-3 rows deep; 29 of the corpus's 30 >=3-wide hits are ONE row deep. So the metric's
    // width column is not merely a weak signal — the shapes it counts are not the shape the article
    // draws, and `min_depth_ge_2` is the only column that says so.
    expect([ctl.name, (cave?.minDepth ?? 0) >= 2]).toEqual([ctl.name, true]);
  }
});

test('control — harddrop\'s own unfinished setups have no cave yet', () => {
  // The page draws each structure mid-build; before the overhang goes on there is nothing to spin
  // into, so these must not score. Complements the flat-floor negative below, which is the harder
  // case: a real T-spin Double that simply has no cave under it.
  for (const ctl of CAVE_NEGATIVES) {
    const b = drawn(ctl.rows, ctl.t_cells ?? []);
    expect([ctl.name, b.cleared.length]).toEqual([ctl.name, ctl.clears]);
    expect([ctl.name, caveAt(b.g, b.cleared, b.cells, b.h)]).toEqual([ctl.name, null]);
  }
});

test('control — a T-spin Double over a flat floor has no cave', () => {
  // The null case the metric needs in order for its small counts to mean anything. Built so the
  // Double really clears exactly TWO rows: the row beneath is one cell short of full, because a
  // board of full rows would clear three and be rejected for the wrong reason.
  const b = drawn(['####...###', '#####.####', '#########.', '#########.'],
                  [[4, 0], [5, 0], [6, 0], [5, 1]]);
  expect(b.cleared).toEqual([0, 1]);
  expect(caveAt(b.g, b.cleared, b.cells, b.h)).toBeNull();
});

/** The maximal empty run at `row` overlapping `cols` — what `caveAt` measures, recomputed here
 *  because the test needs something the return value does not carry: WHICH columns it spans. */
function runAt(g: boolean[][], row: number, cols: Set<number>) {
  let c = 0;
  while (c < 10) {
    if (g[row]![c]) { c++; continue; }
    let e = c;
    while (e < 10 && !g[row]![e]) e++;
    if ([...cols].some(k => k >= c && k < e)) return { from: c, to: e };
    c = e;
  }
  return null;
}

/* ── discriminating power ──────────────────────────────────────────────────────────────────────
 * Same argument the `<= N 格` control makes for the named-opener table: a column that fires on
 * almost everything is not evidence, whatever it is labelled. Both of these metrics have a naive
 * reading that would fire constantly, so each one's distance from its naive reading is asserted. */

test('the donation rate is nowhere near the naive reading, in every session', () => {
  // The naive reading — "the well column was filled through the rows the spin cleared" — is FORCED
  // BY ARITHMETIC (a full row requires every column filled) and so fires on 100% of all T-spin
  // clears; proved as `NaiveClauseForced` in spec/DonationCave.dfy. As a predicate at the shipped
  // thresholds with the re-opening clause deleted it fires on 29-34%.
  // What is counted is the RE-OPENING clause on top of it. If the published rate ever
  // approached the naive one, the clause would have stopped doing the work and the metric would be
  // a line-clear counter. Measured: 2.0-3.3% across the five sessions.
  for (const s of SESSIONS) {
    const d = facts(s).donation;
    const don = sum(d.players.map((p: any) => p.donations));
    expect([s, don * 20 < d.check.tspin_clears]).toEqual([s, true]);   // under 5%
  }
});

test('the cave metric\'s own controls have teeth: >=3 wide is not a cave count', () => {
  // Two directions, and the section may not print the width count without both.
  //   BY LINES — the same >=3-wide gap appears under T-spin TRIPLES, where it is ordinary TST
  //   residue nobody calls a cave. In most sessions there are MORE of them under Triples than
  //   under Doubles, off a much smaller base.
  const tripleWins = SESSIONS.filter(s =>
    CAVE[s]!.triple_control >= CAVE[s]!.width_ge_3);
  expect(tripleWins.length).toBeGreaterThanOrEqual(1);
  for (const s of SESSIONS) {
    const c = facts(s).stmb_cave;
    expect(c.triple_control.tspin_triples_scored).toBeGreaterThan(0);   // exposure, not a vacuous 0
  }
  //   BY DEPTH — nearly every hit is one row deep. 29 dimples to 1 cave over the corpus, so the
  //   raw width count overstates the technique by an order of magnitude.
  let oneDeep = 0, deeper = 0;
  for (const s of SESSIONS)
    for (const [k, v] of Object.entries<number>(facts(s).stmb_cave.min_depth_histogram))
      Number(k) === 1 ? (oneDeep += v) : Number(k) >= 2 ? (deeper += v) : 0;
  expect(oneDeep).toBeGreaterThan(deeper * 5);
});

test('mutation — containment instead of overlap would kill every drawn cave', () => {
  // The predicate's load-bearing choice, asserted as behaviour rather than by editing the source:
  // in all four of harddrop's drawn structures the cave reaches a column the T does not occupy, so
  // a containment test (run ⊆ the T's span) rejects all four. That mutant is dead.
  for (const ctl of CAVE_POSITIVES) {
    const b = drawn(ctl.rows, ctl.t_cells);
    const tc = new Set(b.cells.map(q => q.col));
    const run = runAt(b.g, Math.max(...b.cleared) + 1, tc)!;
    const contained = [...Array(run.to - run.from)].every((_, i) => tc.has(run.from + i));
    expect([ctl.name, contained]).toEqual([ctl.name, false]);
    expect([ctl.name, caveAt(b.g, b.cleared, b.cells, b.h)?.width ?? null])
      .toEqual([ctl.name, ctl.cave_width]);  // ... while the real predicate still fires
  }
});

test('mutation — dropping the re-opening clause would fire on a board that must be rejected', () => {
  // Every setup harddrop draws, with ONE extra cell: the well column also filled ABOVE the rows the
  // spin clears. The shape is otherwise untouched — same plug, same walled cavity beneath, same
  // cleared rows — but the clear no longer re-opens the column to the surface, so the plug is a wall
  // and not a loan. This is the one clause carrying the whole metric (the naive clause without it is
  // forced by arithmetic and fires on 100%; the naive predicate at the shipped thresholds fires on
  // 29-34%), and it is asserted by BEHAVIOUR rather than by editing the source.
  //
  // Derived from the committed transcription rather than typed out, for the same reason the controls
  // are: a board written down twice is a board that can drift, and a mutation board that had drifted
  // from its positive would be testing a difference of two cells while claiming one.
  for (const ctl of DONATION_POSITIVES) {
    const b = drawn(ctl.rows, ctl.t_cells);
    const well = ctl.well_col!;
    const before = donationCols(b.g, b.cleared, b.cells, b.h);
    expect([ctl.name, before.map(w => w.col)]).toEqual([ctl.name, [well]]);

    // the topmost row that the spin does NOT clear and where the well is still open
    const row = b.g.findIndex((r, i) => !b.cleared.includes(i) && !r[well]);
    expect([ctl.name, row]).not.toEqual([ctl.name, -1]);
    b.g[row]![well] = true;

    // the mutation must change exactly the one thing it claims to: the row it touched is still not
    // full, so the same rows clear and the cavity beneath the plug is untouched
    expect([ctl.name, b.g[row]!.every(Boolean)]).toEqual([ctl.name, false]);
    const cleared: number[] = [];
    for (let r = 0; r < b.g.length; r++) if (b.g[r]!.every(Boolean)) cleared.push(r);
    expect([ctl.name, cleared]).toEqual([ctl.name, b.cleared]);
    expect([ctl.name, cavity(b.g, well, b.h).cavity]).toEqual([ctl.name, ctl.cavity]);
    // the naive clause still holds — the well is filled through every row the spin cleared ...
    expect([ctl.name, b.cleared.every(r => b.g[r]![well]!)]).toEqual([ctl.name, true]);
    // ... yet the real predicate now finds no well at all
    expect([ctl.name, donationCols(b.g, b.cleared, b.cells, b.h)]).toEqual([ctl.name, []]);
  }
});

/* ── OPENER vs MID-GAME ────────────────────────────────────────────────────────────────────────
 * The window's own control. Every count in the ordering metric is taken over spins at
 * lock <= `window_pieces`, so "354 of 354 rounds ran Triple-first" had two readings the artifact
 * gave no way to separate: a fact about OPENINGS, or a fact about how these two players throw
 * T-spins at any point in a round. They imply completely different things about the C-Spin, and
 * only the first is what the section says.
 *
 * The same split is applied to the two techniques, where it answers a citation with a measurement:
 * harddrop files Donation and STMB Cave under `Mid-game T-Spin setups`, and until now the artifact
 * repeated that filing rather than testing it.
 *
 * Literals, same rule as PERFECT_CLEARS and DONATION above — a test that re-derives a value the way
 * the code does can only catch a typo. */

/** The ordering metric re-scored on spins AFTER the opener window, summed over both players.
 *  `rounds_with_both` is the exposure and it is TINY (9 across the corpus against 354 inside the
 *  window), which is why every figure here is a count and none of them may become a rate. */
const MID_GAME_ORDER: Record<string, { rounds_with_both: number; cspin: number; dt: number }> = {
  '2026-07-22': { rounds_with_both: 3, cspin: 3, dt: 1 },
  '2026-07-24': { rounds_with_both: 0, cspin: 0, dt: 0 },
  '2026-07-28': { rounds_with_both: 2, cspin: 1, dt: 2 },
  '2026-08-01': { rounds_with_both: 0, cspin: 0, dt: 0 },
  '2026-08-09': { rounds_with_both: 4, cspin: 3, dt: 2 },
};

/** Both techniques split by the same window, summed over both players. Read the cave's `in_opener`
 *  column first: it is 0 in every session, which is harddrop's filing of the technique MEASURED. */
const WINDOW_SPLIT: Record<string, { donation: [number, number]; cave: [number, number] }> = {
  //              [in_opener, mid_game]
  '2026-07-22': { donation: [3, 18], cave: [0, 4] },
  '2026-07-24': { donation: [4, 11], cave: [0, 6] },
  '2026-07-28': { donation: [9,  4], cave: [0, 5] },
  '2026-08-01': { donation: [4, 16], cave: [0, 8] },
  '2026-08-09': { donation: [3, 10], cave: [0, 7] },
};

const orderPlayers = (s: string) => facts(s).ordering.players as any[];

test('the mid-game ordering counts are pinned per session', () => {
  for (const s of SESSIONS) {
    const mg = orderPlayers(s).map(p => p.mid_game);
    const want = MID_GAME_ORDER[s]!;
    expect([s, sum(mg.map(m => m.rounds_with_both))]).toEqual([s, want.rounds_with_both]);
    expect([s, sum(mg.map(m => m.cspin_order))]).toEqual([s, want.cspin]);
    expect([s, sum(mg.map(m => m.dt_order))]).toEqual([s, want.dt]);
    // a round can hold both orders (a stray extra spin), so the two columns need not partition the
    // exposure — but neither can exceed it, and a count above it would mean rounds counted twice
    for (const m of mg) {
      expect([s, m.cspin_order]).toEqual([s, Math.min(m.cspin_order, m.rounds_with_both)]);
      expect([s, m.dt_order]).toEqual([s, Math.min(m.dt_order, m.rounds_with_both)]);
    }
  }
});

test('the opener window does real work: unanimous inside it, both ways outside it', () => {
  // THE REASON THE SPLIT EXISTS. Inside the window the corpus is not merely lopsided, it is
  // unanimous — every round holding both spins ran the Triple first, all five sessions, both
  // players. Outside it the same instrument on the same rounds finds Double-first orders. So
  // "Triple-before-Double" is a property of these OPENINGS and not of how these players throw
  // T-spins, which is the sentence the section is entitled to only because of this test.
  let insideBoth = 0, outsideBoth = 0, outsideDt = 0;
  for (const s of SESSIONS) {
    for (const p of orderPlayers(s)) {
      expect([s, p.user, p.cspin_order]).toEqual([s, p.user, p.rounds_with_both]);
      expect([s, p.user, p.dt_order]).toEqual([s, p.user, 0]);
      insideBoth += p.rounds_with_both;
      outsideBoth += p.mid_game.rounds_with_both;
      outsideDt += p.mid_game.dt_order;
    }
  }
  // and the other half of the contrast, without which the unanimity above is just a small sample:
  // the DT order does happen in this corpus, it just never happens in the opener.
  expect(outsideDt).toBeGreaterThan(0);
  expect(outsideDt).toBe(sum(SESSIONS.map(s => MID_GAME_ORDER[s]!.dt)));
  expect([insideBoth, outsideBoth]).toEqual([354, 9]);
});

test('the mid-game denominator is far too small to be published as a rate', () => {
  // Nine rounds against 354. The 全消 section refuses a percentage over 3-12 rounds for the same
  // reason, and this asserts the shape of the data that makes the refusal correct: if a future
  // change ever printed "75% of mid-game rounds ran the C-Spin order", it would be a percentage of
  // four. Pinned per session so the check cannot be satisfied by one session growing.
  for (const s of SESSIONS) {
    const [inside, outside] = [orderPlayers(s), orderPlayers(s).map(p => p.mid_game)]
      .map(ps => sum(ps.map((p: any) => p.rounds_with_both)));
    expect([s, outside! * 10 < inside!]).toEqual([s, true]);
  }
});

test('the window splits every donation and every cave, losing none', () => {
  // A split that drops rows is worse than no split: the two halves would still look like a finding.
  // So each metric's own total is the sum of its two columns, per player, in every session.
  for (const s of SESSIONS) {
    const d = facts(s), want = WINDOW_SPLIT[s]!;
    for (const p of d.donation.players)
      expect([s, p.user, p.in_opener + p.mid_game]).toEqual([s, p.user, p.donations]);
    for (const p of d.stmb_cave.players)
      expect([s, p.user, p.in_opener + p.mid_game]).toEqual([s, p.user, p.width_ge_3]);

    expect([s, [sum(d.donation.players.map((p: any) => p.in_opener)),
                sum(d.donation.players.map((p: any) => p.mid_game))]]).toEqual([s, want.donation]);
    expect([s, [sum(d.stmb_cave.players.map((p: any) => p.in_opener)),
                sum(d.stmb_cave.players.map((p: any) => p.mid_game))]]).toEqual([s, want.cave]);
    // and the totals the rest of this file already pins are the same numbers, one path further out
    expect([s, sum(d.donation.players.map((p: any) => p.in_opener + p.mid_game))])
      .toEqual([s, DONATION[s]!.donations]);
    expect([s, sum(d.stmb_cave.players.map((p: any) => p.in_opener + p.mid_game))])
      .toEqual([s, CAVE[s]!.width_ge_3]);
  }
});

test('the STMB cave is a mid-game shape, and that is measured rather than cited', () => {
  // harddrop files STMB Cave under `Mid-game T-Spin setups`. This is that filing as a number: not
  // one >=3-wide hit in the whole corpus falls inside the opener window, in any session, for either
  // player — 0 in, 30 out. If it ever becomes non-zero this test must break, because the sentence
  // the section prints would then be a citation again and not a measurement.
  let out = 0;
  for (const s of SESSIONS) {
    for (const p of facts(s).stmb_cave.players) expect([s, p.user, p.in_opener]).toEqual([s, p.user, 0]);
    out += sum(facts(s).stmb_cave.players.map((p: any) => p.mid_game));
  }
  expect(out).toBe(30);
  expect(out).toBe(sum(SESSIONS.map(s => CAVE[s]!.width_ge_3)));   // nothing was lost on the way
});

test('both splits are scored against the ordering metric\'s own window', () => {
  // A technique split against a different window than the ordering counts would be silently
  // incomparable with them — the two tables sit side by side in the section and would be read as
  // one. One number, three places it has to agree.
  for (const s of SESSIONS) {
    const d = facts(s);
    expect([s, d.donation.opener_window_pieces]).toEqual([s, d.window_pieces]);
    expect([s, d.stmb_cave.opener_window_pieces]).toEqual([s, d.window_pieces]);
    expect([s, d.window_pieces]).toEqual([s, 21]);
  }
});
