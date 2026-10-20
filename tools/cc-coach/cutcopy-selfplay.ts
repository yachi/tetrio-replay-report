// PILOT: does cold-clear, playing alone, build Cut Copies (千鳥格子)? Research only — nothing here feeds
// facts.json, an artefact under analysis/, a page or a claim. See FINDINGS-cutcopy-selfplay.md.
//
// Input: the JSONL `cc-coach` writes in COACH_MODE=selfplay (one game per line: seed, the dealt
// `queue`, every placement as {piece, hold, cells [x, row-top-down], kind, tspin, lines}).
//
// The replay core is `pipeline/sim/cc-selfplay.ts` (shared with the committed artefact
// `analysis/cutcopy-selfplay.json`); this script adds the pilot's tally and its near-miss diagnostic.
//
// THE ENGINE IS THE ARBITER. Each game is replayed through the repo's vendored Triangle engine (TETR.IO's
// TL ruleset at g = 0, the demo planner's own `newEngine`), with the dealt queue spliced in exactly as
// `route-demos.runDemo` does. For every placement the path is found by the planner's own `reach` (a BFS over
// the engine's moves, SRS+ kicks, 180 allowed) on a scratch engine, turned into key events by `inputsOf`, and
// played; the lock the ENGINE records is what is scored. A placement the engine cannot reproduce — the
// piece is not the one falling after the hold, no engine path reaches the cells, the engine's lines differ
// from cold-clear's — is COUNTED, and the game is cut there (its board would no longer be cold-clear's);
// spin-credit disagreements (cold-clear's T-spin rule vs the engine's) are counted and do not cut the game:
// the engine's credit is what the matcher reads. For a T the path is CHOSEN: the first `reach` path whose
// engine spin equals cold-clear's, else the first path — so a zero disagreement count means some engine path
// gives cold-clear's credit, not that cold-clear's own path does. Each finished game's final board is compared
// with cold-clear's own `final_field`. The reconstruction check `classify` runs cannot fail here (its cleared rows
// are computed from the same board and cells it re-derives from); the row map and the line count are what can.
//
// Each replayed game becomes a `TechDigest` (no garbage, every lock "verified": the prefix is the
// engine's own replay) and the corpus classifier `technique-facts.classify(CUTCOPY, …)` runs over them
// unchanged — the same scored-T-spin rule, the same reconstruction check, the same window predicate
// (both variants, both hands) and the same follow-up search as `analysis/cutcopy-facts.json`.
//
//   bun tools/cc-coach/cutcopy-selfplay.ts games.jsonl [out.json]
import { readFileSync, writeFileSync } from 'node:fs';
import { newEngine } from '../../pipeline/sim/route-demos.ts';
import { classify, loadTranscription, prepare, type TechDigest } from '../../pipeline/sim/technique-facts.ts';
import { CUTCOPY } from '../../pipeline/sim/technique-profile-cutcopy.ts';
import { H, W, rowsOf, replayGame, digestOf } from '../../pipeline/sim/cc-selfplay.ts';

const inFile = process.argv[2];
if (!inFile) throw new Error('usage: bun cutcopy-selfplay.ts games.jsonl|--control [out.json]');

/** POSITIVE CONTROL (`--control`): the committed constructed Cut Copy `analysis/cutcopy-own.json` (own.3.482),
 *  played by `runDemo` exactly as its test plays it, re-expressed as a self-play game line (queue + every lock's
 *  piece, hold, cells, lines, spin) and pushed through the SAME replay + classify path below. It must come out
 *  as one `cutcopy` hit with its follow-up fired, or this script cannot see what it is looking for. */
function controlGames(): any[] {
  const own = JSON.parse(readFileSync(`${import.meta.dir}/../../analysis/cutcopy-own.json`, 'utf8'));
  return own.demos.map((dm: any, k: number) => {
    const routes = { source: { fetched: own.engine.date.slice(0, 10) } };
    const inputs: [number, string, string][] = dm.inputs;
    const steps: any[] = [];
    const eng0 = newEngine(routes);
    eng0.queue.splice(0, eng0.queue.length, ...[...dm.seq.slice(1)].map((c: string) => c.toLowerCase()));
    eng0.initiatePiece(dm.seq[0].toLowerCase());
    let held = false, cells: [number, number][] = [];
    eng0.events.on('falling.new', (e: any) => { if (e.isHold) held = true; });
    eng0.events.on('falling.lock.pre', () => {
      cells = eng0.falling.absoluteBlocks.map(([x, y]: [number, number]) => [x, (H - 1) - y]);
    });
    eng0.events.on('falling.lock', (res: any) => {
      steps.push({ piece: String(res.mino).toUpperCase(), hold: held, cells, lines: res.lines,
                   kind: 'control', tspin: res.spin === 'none' ? 'None' : res.spin === 'mini' ? 'Mini' : 'Full' });
      held = false;
    });
    const by = new Map<number, any[]>();
    for (const [fr, type, key] of inputs) { if (!by.has(fr)) by.set(fr, []); by.get(fr)!.push({ frame: fr, type, data: { key, subframe: 0 } }); }
    for (let fr = 0; fr <= dm.frames; fr++) eng0.tick(by.get(fr) || []);
    return { id: `control-${dm.node}`, seed: k, queue: dm.seq, steps, nodes: null,
             final_field: rowsOf(eng0.board.state).map(r => r.replace(/[^.]/g, '#')) };
  });
}

const games: any[] = inFile === '--control' ? controlGames()
  : readFileSync(inFile, 'utf8').split('\n').filter(l => l.trim()).map(l => JSON.parse(l));

const tally = { games: games.length, games_complete: 0, pieces_cc: 0, pieces_replayed: 0,
  cut: {} as Record<string, number>, cut_examples: [] as string[], spin_credit_disagreed: 0,
  spin_examples: [] as string[], final_field_mismatch: 0, cc_dead: 0,
  cc_kinds: {} as Record<string, number>, engine_full_tsd: 0 };
const cut = (why: string, ex: string) => { tally.cut[why] = (tally.cut[why] ?? 0) + 1; if (tally.cut_examples.length < 20) tally.cut_examples.push(`${why}: ${ex}`); };
const digests: TechDigest[] = [];

games.forEach((g, gi) => {
  const r = replayGame(g);
  if (r.dead) tally.cc_dead++;
  tally.pieces_cc += r.steps.length;
  // a spin-credit disagreement is counted on a step that was replayed, before the next step can cut
  for (const ex of r.spinDisagreements) {
    tally.spin_credit_disagreed++;
    if (tally.spin_examples.length < 20) tally.spin_examples.push(ex);
  }
  r.locks.forEach((lk, j) => {
    if (lk.piece === 'T' && lk.spin === 'full' && lk.cleared === 2) tally.engine_full_tsd++;
    const k = r.steps[j]!.kind;
    tally.cc_kinds[k] = (tally.cc_kinds[k] ?? 0) + 1;
    tally.pieces_replayed++;
  });
  if (r.cut) cut(r.cut.why, r.cut.where);
  else {
    tally.games_complete++;
    const fin = r.finalRows!.map(x => x.replace(/[^.]/g, '#'));
    if (fin.join('') !== (g.final_field as string[]).join('')) tally.final_field_mismatch++;
  }
  digests.push(digestOf(g, r, gi));
});

const tr = loadTranscription(CUTCOPY.transcriptionPath);
const cls = classify(CUTCOPY, tr, digests);
// NEAR-MISS DIAGNOSTIC (pilot only, not the matcher's): at every full TSD whose T cells are the window's flat,
// nub-down T under some translation, the number of window cells (T excluded) that disagree with the board, the
// minimum over the two hands; per variant, a histogram. A cell off the board counts as disagreeing. 0 = a hit.
const near: Record<string, Record<string, number>> = {};
const nearEx: Record<string, string[]> = {};
for (const v of tr.variants) {
  const Ps = prepare(tr, v);
  near[v.id] = {}; nearEx[v.id] = [];
  for (const d of digests) for (const t of d.tspins) {
    const lk = d.locks[t.i]!;
    if (lk.spin !== 'full' || lk.cleared !== 2) continue;
    let best: number | null = null;
    for (const P of Ps) {
      const dr = Math.min(...lk.cells.map(q => q.row)) - Math.min(...P.T.map(x => x.r));
      const dc = Math.min(...lk.cells.map(q => q.col)) - Math.min(...P.T.map(x => x.c));
      const want = new Set(P.T.map(x => `${x.r + dr},${x.c + dc}`));
      if (!lk.cells.every(q => want.has(`${q.row},${q.col}`))) continue;
      let bad = 0;
      for (const x of P.cells) {
        if (x.v === 'T') continue;
        const R = x.r + dr, C = x.c + dc;
        if (R < 0 || R >= H || C < 0 || C >= W) { bad++; continue; }
        const filled = t.board[R]![C] !== '.';
        if ((x.v === '#') !== filled) bad++;
      }
      best = best === null ? bad : Math.min(best, bad);
    }
    const k = best === null ? 'T_not_flat_nub_down' : String(best);
    near[v.id]![k] = (near[v.id]![k] ?? 0) + 1;
    if (best !== null && best <= 2 && nearEx[v.id]!.length < 10) nearEx[v.id]!.push(`${d.file} lock ${t.i}: ${best} cell(s) off`);
  }
}
const hits = cls.hits.map(h => ({ seed: Number(h.file.slice(5)), game: h.match, variant: h.variant, lock: h.lock,
  hand: h.mirrored ? 'mirrored' : 'as_drawn', in_opener: h.in_opener, window: h.window_letters, followup: h.followup }));
const byVH: Record<string, number> = {};
for (const h of hits) byVH[`${h.variant}/${h.hand}`] = (byVH[`${h.variant}/${h.hand}`] ?? 0) + 1;
const out = { input: inFile, nodes: games[0]?.nodes ?? null, tally, denominators: cls.denominators,
  check: { ...cls.check, by_session: undefined }, hits_by_variant_hand: byVH,
  followup: Object.fromEntries(Object.entries(cls.perVariant).map(([k, v]: [string, any]) => [k, v.followup])),
  ablation: Object.fromEntries(Object.entries(cls.perVariant).map(([k, v]: [string, any]) => [k, v.ablation])),
  under_controls: Object.fromEntries(Object.entries(cls.perVariant).map(([k, v]: [string, any]) => [k, v.under])),
  off_board: cls.offBoard.length, near_miss_cells: near, near_miss_examples: nearEx, recon_dropped: cls.reconDropped, hits };
const txt = JSON.stringify(out, null, 1);
if (process.argv[3]) writeFileSync(process.argv[3], txt + '\n');
console.log(txt);
