/**
 * 千鳥格子 (Cut Copy) in COLD-CLEAR SELF-PLAY (`analysis/cutcopy-selfplay.json`, from `pipeline/sim/emit-cutcopy-selfplay.ts`;
 * the build is `cutcopy-selfplay.ts`, the replay core `cc-selfplay.ts`, shared with tools/cc-coach/cutcopy-selfplay.ts).
 *
 * What this file re-derives, each from the committed placements alone:
 *
 *   * every committed game replayed through the engine again, the corpus classifier run again, and the whole
 *     artefact rebuilt byte for byte (the build throws unless each game's hits are the scan's);
 *   * the hits are exactly the named list `HITS` below (seed, lock, variant, hand, follow-up), in the scan and in
 *     the games — a new hit, a lost one or a moved one is a red build to investigate, never a bound;
 *   * each timeline decoded from an empty board on its own (`decodeTimeline`): every lock lands on cold-clear's
 *     own cells; the board before each hit's T matches the window (`windowMatch`, in the hit's hand); the hit's T
 *     and a fired follow-up's T are full T-spins clearing two;
 *   * the committed games are the scan's hit games, each cut `tail` locks after the last lock deciding a hit.
 *
 * What it does NOT re-derive: the scan's summary (`scan`: games, pieces, cuts, scored TSDs, hits), which needs the
 * bot's whole output (not committed; its md5 is in `provenance`). Re-run the emitter on the regenerated JSONL.
 *
 * NOT CORPUS DATA, NOT A SOURCE'S DRAWING AND NOT OURS: a bot played these games alone, with no garbage.
 *
 * Run: bun test pipeline/openers/cutcopy-selfplay.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { SELFPLAY_PATH, inputMd5s, rebuild, serialise } from '../sim/cutcopy-selfplay.ts';
import { decodeTimeline, queueStates, placeCells, WIDTH, ROWS } from '../sim/emit-replay.ts';
import { prepare, windowMatch, loadTranscription } from '../sim/technique-facts.ts';
import { CUTCOPY } from '../sim/technique-profile-cutcopy.ts';

const committedText = readFileSync(SELFPLAY_PATH, 'utf8');
const committed = JSON.parse(committedText);
const TR = loadTranscription(CUTCOPY.transcriptionPath);

/** THE NAMED LIST: [seed, hit lock, variant, hand, follow-up lock, fired]. */
const HITS: [number, number, string, string, number, boolean][] = [
  [48, 81, 'cutcopy', 'as_drawn', 86, true],
  [65, 19, 'cutcopy', 'mirrored', 23, true],
  [83, 58, 'cutcopy', 'mirrored', 59, true],
  [87, 11, 'cutcopy', 'mirrored', 13, true],
  [118, 131, 'cutcopy', 'mirrored', 134, true],
  [118, 144, 'cutcopy', 'as_drawn', 149, true],
  [136, 83, 'uncut', 'as_drawn', 84, true],
  [173, 193, 'cutcopy', 'mirrored', 196, true],
  [176, 80, 'cutcopy', 'as_drawn', 88, true],
  [186, 27, 'cutcopy', 'as_drawn', 28, false],
  [193, 26, 'cutcopy', 'as_drawn', 32, true],
  [195, 135, 'cutcopy', 'mirrored', 141, true],
];
const row = (seed: number, h: any) => [seed, h.lock, h.variant, h.hand, h.followup.lock, h.followup.fired];

test('the artefact is quarantined and labelled as self-play', () => {
  expect(committed.schema).toBe('technique-selfplay/1');
  expect(committed.report_eligible).toBe(false);
  expect(committed.constructed).toBe(true);
  expect(committed.selfplay).toBe(true);
  expect(committed.own).toBeUndefined();
  expect(committed.provenance.rev).toMatch(/^[0-9a-f]{40}$/);
  expect(committed.provenance.games_jsonl_md5).toMatch(/^[0-9a-f]{32}$/);
});

test('the artefact is current: every input it hashes is the file on disk', () => {
  expect(committed.inputs).toEqual(inputMd5s());
});

test('the hits are exactly the named list, in the scan and in the committed games', () => {
  expect(committed.scan.hits.map((h: any) => row(h.seed, h))).toEqual(HITS);
  expect(committed.games.flatMap((g: any) => g.hits.map((h: any) => row(g.seed, h)))).toEqual(HITS);
  expect(committed.games.map((g: any) => g.seed)).toEqual([...new Set(HITS.map(h => h[0]))]);
});

test('each game is cut `tail` locks after the last lock deciding a hit (or at the game\'s end)', () => {
  for (const g of committed.games) {
    const decides = Math.max(...g.hits.map((h: any) => Math.max(h.lock, h.followup.lock ?? h.lock)));
    // cut `tail` after the deciding lock; a game shorter than that is committed whole (`select`'s Math.min),
    // and the only way that can happen is the game ending, so its length must then be the game's whole length
    const want = decides + committed.tail + 1;
    if (g.placements.length !== want) {
      expect(g.placements.length).toBeLessThan(want);
      expect(g.placements.length).toBe(committed.scan.pieces_per_game);
    }
    expect(g.locks.length).toBe(g.placements.length);
    expect(g.node).toBe(`selfplay.${g.seed}`);
  }
});

test('rebuilt from the committed placements alone: byte for byte the committed artefact', () => {
  expect(serialise(rebuild(committed))).toBe(committedText);
}, 120_000);

test('each timeline, decoded on its own: cold-clear\'s cells, the window, two full TSDs', () => {
  const preps = Object.fromEntries(TR.variants.map((v: any) => [v.id, prepare(TR, v)]));
  for (const g of committed.games) {
    const boards: (string | null)[][][] = [];
    decodeTimeline(g.seq, g.locks, (bd, i) => { boards[i] = bd.map(r => [...r]); });
    const q = queueStates(g.seq, g.locks);
    g.placements.forEach((p: any, i: number) => {
      expect(q[i]!.piece).toBe(p.piece);
      const want = p.cells.map(([x, r]: [number, number]) => (ROWS - 1 - r) * WIDTH + x).sort((a: number, b: number) => a - b);
      expect([...placeCells(p.piece, g.locks[i][1])].sort((a, b) => a - b)).toEqual(want);
      expect(g.locks[i][2]).toBe(p.lines);
    });
    for (const h of g.hits) {
      const before = boards[h.lock - 1]!;
      const topFirst = [...before].reverse().map(r => r.map(c => c ?? '.').join(''));
      const cells = [...placeCells('T', g.locks[h.lock][1])]
        .map(c => ({ row: ROWS - 1 - Math.floor(c / WIDTH), col: c % WIDTH }));
      const P = preps[h.variant][h.hand === 'mirrored' ? 1 : 0];
      expect(windowMatch(topFirst, cells, P)).toBeTruthy();
      expect(windowMatch(topFirst, cells, preps[h.variant][h.hand === 'mirrored' ? 0 : 1])).toBeFalsy();
      const ts = h.followup.fired ? [h.lock, h.followup.lock] : [h.lock];
      for (const i of ts) {
        expect(q[i]!.piece).toBe('T');
        expect(g.locks[i][3]).toBe(2);
        expect(g.locks[i][2]).toBe(2);
      }
    }
  }
});
