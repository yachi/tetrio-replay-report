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
 *   5. the whole-shape rule (`technique-wholeshape.ts`, yachi 2026-10-25) is part of every verdict and is turned off
 *      like the others.
 *
 * The artefacts are rebuilt byte for byte by each technique's own test; this one reads them.
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { digestCorpus, loadTranscription, type TechDigest } from '../sim/technique-facts.ts';
import { TECHNIQUES } from '../sim/techniques.ts';
import { QUALIFY_OPTIONS, keyOffsets, techniqueQualifier, type TechniqueQualifyMutants } from '../sim/technique-qualify.ts';
import { withWholeShape } from '../sim/technique-wholeshape.ts';
import { assertCorpusIsEverySessionOnDisk } from '../corpus-membership.ts';

const ROOT = `${import.meta.dir}/../../sessions`;
const SESSIONS = assertCorpusIsEverySessionOnDisk(ROOT,
  ['2026-07-22', '2026-07-24', '2026-07-28', '2026-08-01', '2026-08-09', '2026-08-14',
   '2026-08-19', '2026-08-25', '2026-09-03', '2026-09-10', '2026-09-11', '2026-09-17',
   '2026-09-18', '2026-09-19', '2026-10-03', '2026-10-09', '2026-10-12', '2026-10-20', '2026-10-22']);

const KEYS = ['stsd', 'stmbcave', 'imperialcross', 'doubledagger', 'btcannon', 'cutcopy', 'kaidan', 'dtcannon'] as const;

const BY_PLAYER: Record<string, any> = {
  stsd: { pinglamb: { qualified: 19, not_qualified: {} }, yachi: { qualified: 46, not_qualified: { dpc: 1, fragment: 1, ownership_unverified: 1 } } },
  stmbcave: { pinglamb: { qualified: 31, not_qualified: { not_whole_shape: 19 } }, yachi: { qualified: 50, not_qualified: { not_whole_shape: 33 } } },
  imperialcross: { pinglamb: { qualified: 7, not_qualified: {} }, yachi: { qualified: 2, not_qualified: { fragment: 1 } } },
  doubledagger: { pinglamb: { qualified: 4, not_qualified: { not_whole_shape: 23 } }, yachi: { qualified: 6, not_qualified: { not_whole_shape: 5 } } },
  btcannon: { pinglamb: { qualified: 0, not_qualified: {} }, yachi: { qualified: 0, not_qualified: {} } },
  cutcopy: { pinglamb: { qualified: 0, not_qualified: {} }, yachi: { qualified: 1, not_qualified: { fragment: 1 } } },
  kaidan: { pinglamb: { qualified: 22, not_qualified: { fragment: 38, garbage_in_shape: 46, z_not_one_piece: 46 } }, yachi: { qualified: 33, not_qualified: { dpc: 1, fragment: 39, garbage_in_shape: 40, ownership_unverified: 2, z_not_one_piece: 64 } } },
  dtcannon: { pinglamb: { qualified: 0, not_qualified: {} }, yachi: { qualified: 19, not_qualified: { ownership_unverified: 1 } } },
};

/** every hit that does not qualify, with its reasons (階段のドネイト: the tally above only) */
const NOT_QUALIFIED: Record<string, string[]> = {
  stsd: [
    "2026-07-24 m2r1 yachi lock 32 (stsd): dpc",
    "2026-08-09 m5r8 yachi lock 82 (stsd): fragment",
    "2026-08-25 m8r6 yachi lock 190 (stsd): ownership_unverified",
  ],
  stmbcave: [
    "2026-07-22 m3r7 yachi lock 22 (stmbcave): not_whole_shape",
    "2026-07-22 m6r3 yachi lock 25 (stmbcave): not_whole_shape",
    "2026-07-22 m9r7 yachi lock 52 (stmbcave): not_whole_shape",
    "2026-07-24 m3r1 yachi lock 106 (stmbcave): not_whole_shape",
    "2026-07-24 m7r3 yachi lock 110 (stmbcave): not_whole_shape",
    "2026-07-24 m7r3 yachi lock 114 (stmbcave): not_whole_shape",
    "2026-07-28 m8r3 pinglamb lock 83 (stmbcave): not_whole_shape",
    "2026-08-01 m4r2 yachi lock 33 (stmbcave): not_whole_shape",
    "2026-08-09 m3r3 pinglamb lock 25 (stmbcave): not_whole_shape",
    "2026-08-09 m3r6 pinglamb lock 26 (stmbcave): not_whole_shape",
    "2026-08-14 m11r8 yachi lock 96 (stmbcave): not_whole_shape",
    "2026-08-19 m1r5 yachi lock 40 (stmbcave): not_whole_shape",
    "2026-08-19 m6r6 yachi lock 22 (stmbcave): not_whole_shape",
    "2026-08-19 m9r5 pinglamb lock 20 (stmbcave): not_whole_shape",
    "2026-08-19 m10r1 pinglamb lock 33 (stmbcave): not_whole_shape",
    "2026-08-25 m8r9 pinglamb lock 90 (stmbcave): not_whole_shape",
    "2026-09-03 m3r4 pinglamb lock 96 (stmbcave): not_whole_shape",
    "2026-09-03 m5r4 pinglamb lock 109 (stmbcave): not_whole_shape",
    "2026-09-03 m6r2 yachi lock 18 (stmbcave): not_whole_shape",
    "2026-09-10 m8r4 yachi lock 60 (stmbcave): not_whole_shape",
    "2026-09-11 m1r4 yachi lock 58 (stmbcave): not_whole_shape",
    "2026-09-17 m6r4 pinglamb lock 25 (stmbcave): not_whole_shape",
    "2026-09-18 m8r7 pinglamb lock 34 (stmbcave): not_whole_shape",
    "2026-09-18 m13r7 pinglamb lock 69 (stmbcave): not_whole_shape",
    "2026-09-18 m14r2 yachi lock 66 (stmbcave): not_whole_shape",
    "2026-09-18 m16r2 yachi lock 30 (stmbcave): not_whole_shape",
    "2026-09-19 m3r1 yachi lock 103 (stmbcave): not_whole_shape",
    "2026-09-19 m6r4 pinglamb lock 45 (stmbcave): not_whole_shape",
    "2026-09-19 m6r5 yachi lock 86 (stmbcave): not_whole_shape",
    "2026-09-19 m8r7 pinglamb lock 50 (stmbcave): not_whole_shape",
    "2026-09-19 m11r2 yachi lock 32 (stmbcave): not_whole_shape",
    "2026-09-19 m18r5 pinglamb lock 51 (stmbcave): not_whole_shape",
    "2026-10-03 m2r3 yachi lock 21 (stmbcave): not_whole_shape",
    "2026-10-03 m3r4 pinglamb lock 23 (stmbcave): not_whole_shape",
    "2026-10-03 m3r8 yachi lock 24 (stmbcave): not_whole_shape",
    "2026-10-03 m6r7 yachi lock 286 (stmbcave): not_whole_shape",
    "2026-10-03 m10r6 pinglamb lock 88 (stmbcave): not_whole_shape",
    "2026-10-03 m13r4 yachi lock 32 (stmbcave): not_whole_shape",
    "2026-10-03 m14r2 pinglamb lock 60 (stmbcave): not_whole_shape",
    "2026-10-03 m20r2 pinglamb lock 102 (stmbcave): not_whole_shape",
    "2026-10-09 m1r6 pinglamb lock 47 (stmbcave): not_whole_shape",
    "2026-10-09 m3r1 yachi lock 31 (stmbcave): not_whole_shape",
    "2026-10-09 m5r3 yachi lock 31 (stmbcave): not_whole_shape",
    "2026-10-09 m5r3 yachi lock 145 (stmbcave): not_whole_shape",
    "2026-10-09 m8r2 yachi lock 30 (stmbcave): not_whole_shape",
    "2026-10-09 m9r9 yachi lock 31 (stmbcave): not_whole_shape",
    "2026-10-09 m11r6 yachi lock 33 (stmbcave): not_whole_shape",
    "2026-10-12 m1r3 yachi lock 145 (stmbcave): not_whole_shape",
    "2026-10-20 m1r5 yachi lock 40 (stmbcave): not_whole_shape",
    "2026-10-20 m4r7 yachi lock 178 (stmbcave): not_whole_shape",
    "2026-10-22 m1r3 yachi lock 32 (stmbcave): not_whole_shape",
    "2026-10-22 m1r8 yachi lock 82 (stmbcave): not_whole_shape",
  ],
  imperialcross: [
    "2026-08-14 m8r1 yachi lock 38 (imperialcross): fragment",
  ],
  doubledagger: [
    "2026-07-24 m6r5 pinglamb lock 67 (doubledagger): not_whole_shape",
    "2026-07-28 m7r1 yachi lock 98 (doubledagger): not_whole_shape",
    "2026-07-28 m7r6 pinglamb lock 33 (doubledagger): not_whole_shape",
    "2026-08-01 m1r4 pinglamb lock 34 (doubledagger): not_whole_shape",
    "2026-08-01 m3r5 pinglamb lock 24 (doubledagger): not_whole_shape",
    "2026-08-01 m3r7 pinglamb lock 35 (doubledagger): not_whole_shape",
    "2026-08-01 m3r8 pinglamb lock 34 (doubledagger): not_whole_shape",
    "2026-08-01 m5r7 pinglamb lock 60 (doubledagger): not_whole_shape",
    "2026-08-09 m6r2 pinglamb lock 82 (doubledagger): not_whole_shape",
    "2026-08-09 m6r2 pinglamb lock 93 (doubledagger): not_whole_shape",
    "2026-08-14 m4r5 yachi lock 47 (doubledagger): not_whole_shape",
    "2026-08-14 m10r6 yachi lock 23 (doubledagger): not_whole_shape",
    "2026-08-19 m2r5 pinglamb lock 37 (doubledagger): not_whole_shape",
    "2026-08-19 m4r1 pinglamb lock 25 (doubledagger): not_whole_shape",
    "2026-08-25 m2r7 pinglamb lock 116 (doubledagger): not_whole_shape",
    "2026-09-03 m2r2 pinglamb lock 81 (doubledagger): not_whole_shape",
    "2026-09-03 m4r2 pinglamb lock 67 (doubledagger): not_whole_shape",
    "2026-09-10 m5r9 pinglamb lock 36 (doubledagger): not_whole_shape",
    "2026-09-11 m2r5 pinglamb lock 133 (doubledagger): not_whole_shape",
    "2026-09-11 m2r6 pinglamb lock 50 (doubledagger): not_whole_shape",
    "2026-09-17 m7r4 pinglamb lock 48 (doubledagger): not_whole_shape",
    "2026-09-19 m1r8 pinglamb lock 64 (doubledagger): not_whole_shape",
    "2026-09-19 m2r3 pinglamb lock 45 (doubledagger): not_whole_shape",
    "2026-10-09 m1r9 yachi lock 45 (doubledagger): not_whole_shape",
    "2026-10-09 m4r7 pinglamb lock 89 (doubledagger): not_whole_shape",
    "2026-10-09 m6r5 pinglamb lock 36 (doubledagger): not_whole_shape",
    "2026-10-09 m7r5 pinglamb lock 37 (doubledagger): not_whole_shape",
    "2026-10-09 m11r3 yachi lock 74 (doubledagger): not_whole_shape",
  ],
  btcannon: [],
  cutcopy: [
    "2026-09-18 m16r2 yachi lock 215 (cutcopy): fragment",
  ],
  dtcannon: [
    "2026-09-11 m4r5 yachi lock 107 (dtcannon): ownership_unverified",
  ],
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
  const RULES: [TechniqueQualifyMutants & { wholeShapeOff?: boolean }, string[]][] = [
    [{ allowFragments: true }, ['fragment']], [{ allowGarbage: true }, ['garbage_in_shape']],
    [{ allowSplit: true }, ['z_not_one_piece']], [{ noDpc: true }, ['dpc']], [{ wholeShapeOff: true }, ['not_whole_shape']],
    [{ allowFragments: true, allowGarbage: true, allowSplit: true, noDpc: true, wholeShapeOff: true },
     ['fragment', 'garbage_in_shape', 'z_not_one_piece', 'dpc', 'not_whole_shape']],
  ];
  const live = new Set<string>();
  for (const k of KEYS) {
    const P = TECHNIQUES[k]!;
    const a = art(k);
    const opts = QUALIFY_OPTIONS[k];
    const base = withWholeShape(P.transcriptionPath, techniqueQualifier(P.transcriptionPath, opts));
    for (const h of a.hits) expect(base(h, digestOf(h)), qName(h)).toEqual({ qualifies: h.qualifies, not_qualified: h.not_qualified });
    for (const [m, rules] of RULES) {
      const q = withWholeShape(P.transcriptionPath, techniqueQualifier(P.transcriptionPath, opts, m), { off: m.wholeShapeOff });
      const want = a.hits.filter((h: any) => h.not_qualified.every((x: string) => rules.includes(x))).map(qName);
      const got = a.hits.filter((h: any) => q(h, digestOf(h)).qualifies).map(qName);
      expect(got, `${k} ${JSON.stringify(m)}`).toEqual(want);
      if (a.hits.some((h: any) => h.not_qualified.some((x: string) => rules.includes(x)))) live.add(JSON.stringify(m));
    }
  }
  // every rule fails some hit in the corpus (a hit failing only it is not required: 階段's garbage hits also fail others)
  for (const [m] of RULES) expect(live.has(JSON.stringify(m)), JSON.stringify(m)).toBe(true);
}, 1_800_000);
