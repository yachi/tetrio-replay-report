/**
 * The `qualify` hook of the seven technique pages that share `technique-qualify.ts` (STSD, STMB Cave,
 * インペリアルクロス, ダブルダガー, BT砲, 千鳥格子, 階段のドネイト), added at yachi's request on 2026-10-23
 * (「睇埋其他中盤」): 社畜トレイン's and 欄干's rules carried over — the key cells whole pieces and never garbage,
 * 階段のドネイト's Z one piece, no Perfect Clear within DPC_LOCKS locks either side of the T.
 *
 *   1. each artefact's per-player tally is pinned, and so is every hit that does NOT qualify on the four pages where
 *      few fail (on 階段のドネイト only the tally: most fail);
 *   2. every committed verdict is re-derived by calling the hook on the hit and its digest;
 *   3. each rule turned off qualifies exactly the hits whose only failures are rules turned off; each rule
 *      fails some hit on at least one page (no single-rule mutant is required to qualify a hit: 階段のドネイト's garbage hits fail other rules too);
 *   4. every key cell is drawn filled inside its variant's window (keyOffsets throws otherwise).
 *
 * The artefacts are rebuilt byte for byte by each technique's own test; this one reads them.
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { digestCorpus, loadTranscription, type TechDigest } from '../sim/technique-facts.ts';
import { TECHNIQUES } from '../sim/techniques.ts';
import { QUALIFY_OPTIONS, keyOffsets, techniqueQualifier, type TechniqueQualifyMutants } from '../sim/technique-qualify.ts';
import { assertCorpusIsEverySessionOnDisk } from '../corpus-membership.ts';

const ROOT = `${import.meta.dir}/../../sessions`;
const SESSIONS = assertCorpusIsEverySessionOnDisk(ROOT,
  ['2026-07-22', '2026-07-24', '2026-07-28', '2026-08-01', '2026-08-09', '2026-08-14',
   '2026-08-19', '2026-08-25', '2026-09-03', '2026-09-10', '2026-09-11', '2026-09-17',
   '2026-09-18', '2026-09-19', '2026-10-03', '2026-10-09', '2026-10-12', '2026-10-20', '2026-10-22']);

const KEYS = ['stsd', 'stmbcave', 'imperialcross', 'doubledagger', 'btcannon', 'cutcopy', 'kaidan'] as const;

const BY_PLAYER: Record<string, any> = {
  stsd: { pinglamb: { not_qualified: {}, qualified: 19 },
          yachi: { not_qualified: { dpc: 1, fragment: 1, ownership_unverified: 1 }, qualified: 46 } },
  stmbcave: { pinglamb: { not_qualified: {}, qualified: 50 }, yachi: { not_qualified: {}, qualified: 83 } },
  imperialcross: { pinglamb: { not_qualified: {}, qualified: 7 }, yachi: { not_qualified: { fragment: 1 }, qualified: 2 } },
  doubledagger: { pinglamb: { not_qualified: {}, qualified: 27 }, yachi: { not_qualified: {}, qualified: 11 } },
  btcannon: { pinglamb: { not_qualified: {}, qualified: 0 }, yachi: { not_qualified: {}, qualified: 0 } },
  cutcopy: { pinglamb: { not_qualified: {}, qualified: 0 }, yachi: { not_qualified: { fragment: 1 }, qualified: 1 } },
  kaidan: { pinglamb: { not_qualified: { fragment: 38, garbage_in_shape: 46, z_not_one_piece: 46 }, qualified: 22 },
            yachi: { not_qualified: { dpc: 1, fragment: 39, garbage_in_shape: 40, ownership_unverified: 2, z_not_one_piece: 64 },
                     qualified: 33 } },
};

/** every hit that does not qualify, with its reasons (階段のドネイト: the tally above only) */
const NOT_QUALIFIED: Record<string, string[]> = {
  stsd: ['2026-07-24 m2r1 yachi lock 32 (stsd): dpc', '2026-08-09 m5r8 yachi lock 82 (stsd): fragment',
         '2026-08-25 m8r6 yachi lock 190 (stsd): ownership_unverified'],
  stmbcave: [],
  imperialcross: ['2026-08-14 m8r1 yachi lock 38 (imperialcross): fragment'],
  doubledagger: [],
  btcannon: [],
  cutcopy: ['2026-09-18 m16r2 yachi lock 215 (cutcopy): fragment'],
};

const qName = (h: any) => `${h.session} m${h.match}r${h.round} ${h.player} lock ${h.lock} (${h.variant})`;
const art = (k: string) => JSON.parse(readFileSync(`${import.meta.dir}/../../analysis/${k}-facts.json`, 'utf8'));
let DIGESTS: Map<string, TechDigest> | null = null;
const digestOf = (h: any) => {
  DIGESTS ??= new Map(digestCorpus(SESSIONS).map(d => [`${d.file}|${d.round}|${d.user}`, d]));
  const d = DIGESTS.get(`${h.file}|${h.round_index0}|${h.player}`);
  if (!d) throw new Error(`no digest for ${qName(h)}`);
  return d;
};

test('qualify: each artefact carries the hook, its tally pinned per player, and the hits that fail it named', () => {
  for (const k of KEYS) {
    const a = art(k);
    expect(a.qualify?.by_player, k).toEqual(BY_PLAYER[k]);
    expect(a.hits.every((h: any) => typeof h.qualifies === 'boolean' && h.qualifies === (h.not_qualified.length === 0)), k).toBe(true);
    expect(a.hits.some((h: any) => h.not_qualified.includes('shape_cell_empty')), k).toBe(false);
    if (k in NOT_QUALIFIED)
      expect(a.hits.filter((h: any) => !h.qualifies).map((h: any) => `${qName(h)}: ${h.not_qualified.join(', ')}`), k)
        .toEqual(NOT_QUALIFIED[k]);
  }
});

test('qualify: every key cell is drawn filled inside its window', () => {
  for (const k of KEYS) {
    const tr = loadTranscription(TECHNIQUES[k]!.transcriptionPath);
    const offs = keyOffsets(tr, QUALIFY_OPTIONS[k]);
    for (const v of tr.variants) expect(offs.get(v.id)!.key.length, `${k} ${v.id}`).toBeGreaterThan(0);
  }
  // a cell the window leaves empty is refused
  const tr = loadTranscription(TECHNIQUES.stsd!.transcriptionPath);
  expect(() => keyOffsets(tr, { keyCells: { stsd: [[2, 2]] } })).toThrow(/not drawn filled/);
  expect(() => keyOffsets(tr, { keyCells: { stsd: [[0, 9]] } })).toThrow(/outside its window/);
});

test('qualify: every committed verdict is the hook\'s, and each rule turned off qualifies exactly the hits failing only it', () => {
  const RULES: [TechniqueQualifyMutants, string[]][] = [
    [{ allowFragments: true }, ['fragment']], [{ allowGarbage: true }, ['garbage_in_shape']],
    [{ allowSplit: true }, ['z_not_one_piece']], [{ noDpc: true }, ['dpc']],
    [{ allowFragments: true, allowGarbage: true, allowSplit: true, noDpc: true }, ['fragment', 'garbage_in_shape', 'z_not_one_piece', 'dpc']],
  ];
  const live = new Set<string>();
  for (const k of KEYS) {
    const P = TECHNIQUES[k]!;
    const a = art(k);
    const opts = QUALIFY_OPTIONS[k];
    const base = techniqueQualifier(P.transcriptionPath, opts);
    for (const h of a.hits) expect(base(h, digestOf(h)), qName(h)).toEqual({ qualifies: h.qualifies, not_qualified: h.not_qualified });
    for (const [m, rules] of RULES) {
      const q = techniqueQualifier(P.transcriptionPath, opts, m);
      const want = a.hits.filter((h: any) => h.not_qualified.every((x: string) => rules.includes(x))).map(qName);
      const got = a.hits.filter((h: any) => q(h, digestOf(h)).qualifies).map(qName);
      expect(got, `${k} ${JSON.stringify(m)}`).toEqual(want);
      if (a.hits.some((h: any) => h.not_qualified.some((x: string) => rules.includes(x)))) live.add(JSON.stringify(m));
    }
  }
  // every rule fails some hit in the corpus (a hit failing only it is not required: 階段's garbage hits also fail others)
  for (const [m] of RULES) expect(live.has(JSON.stringify(m)), JSON.stringify(m)).toBe(true);
}, 1_800_000);
