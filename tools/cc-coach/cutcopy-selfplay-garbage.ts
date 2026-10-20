// PILOT (research only): cold-clear self-play WITH received garbage, replayed through the repo's engine, and the
// corpus Cut Copy classifier run over it. Nothing here feeds facts.json, an artefact under analysis/, a page or a
// claim. See FINDINGS-cutcopy-selfplay.md, section "With received garbage".
//
// Input: the JSONL cc-coach writes in COACH_MODE=selfplay when its input carries a `garbage` schedule (made by
// selfplay-garbage-input.py): the dealt `queue`, the echoed `garbage` schedule, and every placement with its
// board after the lock and its garbage (`field`) and the hole columns inserted on that lock (`garbage_cols`).
//
// The replay is cc-selfplay.ts's (same engine, same `reach` + `inputsOf`, the same per-lock checks), copied
// here rather than edited there, because analysis/cutcopy-selfplay.json hashes that file. What this copy adds:
//   * the GARBAGE RULE, re-derived independently from the echoed schedule (it never reads cold-clear's
//     `garbage_cols` to decide what to insert): an attack with after_piece j joins a pending list after lock j;
//     pending rows enter, front first, on a lock that clears nothing, at most 8 per lock. The rows are inserted
//     into the engine with the engine's own `board.insertGarbage` (one-hole rows), after the lock.
//   * a check after EVERY placement: the inserted hole columns equal cold-clear's `garbage_cols`, and the engine's
//     board (occupancy) equals cold-clear's `field`. Any disagreement CUTS the game with a named reason —
//     garbage_mismatch, board_mismatch — exactly like the replay's own cuts; none is ignored.
//   * garbage_spawn_overlap: the engine spawns the next piece before the rows are inserted (they are inserted after
//     its lock event), so a row pushing the stack into the spawned piece is a named cut, never a silent overlap.
// Each game becomes a TechDigest whose locks carry the garbage rows inserted on them, the row map checked against
// the engine's board after the insertion — the corpus digest's own convention — and classify(CUTCOPY, …) runs
// unchanged, so `garbage_in_window` is the matcher's own.
//
//   bun tools/cc-coach/cutcopy-selfplay-garbage.ts games-garbage.jsonl [out.json]
import { readFileSync, writeFileSync } from 'node:fs';
import { newEngine, reach, inputsOf } from '../../pipeline/sim/route-demos.ts';
import { classify, loadTranscription, type LockLite, type TSpinLock, type TechDigest } from '../../pipeline/sim/technique-facts.ts';
import { CUTCOPY } from '../../pipeline/sim/technique-profile-cutcopy.ts';
import { H, W, rowsOf, SELFPLAY_ENGINE_ROUTES } from '../../pipeline/sim/cc-selfplay.ts';

const CAP = 8;
const SPIN_OF_CC: Record<string, string | null> = { Full: 'normal', Mini: 'mini', None: null };
const gridOf = (st: any[][]) => Array.from({ length: H }, (_, y) =>
  Array.from({ length: W }, (_, x) => { const t = st[y]?.[x]; return t == null ? null : String(t.mino); }));
const occ = (rows: string[]) => rows.map(r => r.replace(/[^.]/g, '#'));
const trimTop = (rows: string[]) => { const i = rows.findIndex(r => r.includes('#')); return i < 0 ? [] : rows.slice(i); };

interface Out { cut: { why: string; where: string } | null; locks: LockLite[]; tspins: TSpinLock[]; dead: boolean;
                steps: number; garbageRows: number; spinDisagreements: string[] }

function replay(g: any): Out {
  const seq: string = g.queue;
  const steps = (g.steps as any[]).filter(s => !s.dead);
  const sched = new Map<number, [number, number][]>();
  for (const a of g.garbage) { if (!sched.has(a.after_piece)) sched.set(a.after_piece, []); sched.get(a.after_piece)!.push([a.lines, a.col]); }
  const scratch = newEngine(SELFPLAY_ENGINE_ROUTES);
  const eng = newEngine(SELFPLAY_ENGINE_ROUTES);
  eng.queue.splice(0, eng.queue.length, ...[...seq.slice(1)].map(c => c.toLowerCase()));
  eng.initiatePiece(seq[0]!.toLowerCase());
  let pre: { board: string[]; cells: { row: number; col: number }[] } | null = null;
  let boardBefore: string[] = [];
  let lockRes: any = null;
  eng.events.on('falling.lock.pre', () => {
    pre = { board: boardBefore,
            cells: eng.falling.absoluteBlocks.map(([x, y]: [number, number]) => ({ row: (H - 1) - y, col: x })) };
  });
  eng.events.on('falling.lock', (res: any) => { lockRes = res; });
  let frame = 0;
  const tickTo = (events: any[], until: number) => {
    const by = new Map<number, any[]>();
    for (const e of events) { if (!by.has(e.frame)) by.set(e.frame, []); by.get(e.frame)!.push(e); }
    for (; frame <= until; frame++) eng.tick(by.get(frame) || []);
  };
  const locks: LockLite[] = [], tspins: TSpinLock[] = [], spinDisagreements: string[] = [];
  let pending: [number, number][] = [];
  let garbageRows = 0;
  let cut: Out['cut'] = null;
  for (let j = 0; j < steps.length; j++) {
    const s = steps[j]!;
    const where = `seed ${g.seed} lock ${j}`;
    const cur = String(eng.falling.symbol).toUpperCase();
    const placed = s.hold ? (eng.held != null ? String(eng.held).toUpperCase() : String(eng.queue[0]).toUpperCase()) : cur;
    if (placed !== s.piece) { cut = { why: 'piece_mismatch', where: `${where} cc ${s.piece} engine ${placed}` }; break; }
    const target = s.cells.map(([x, r]: [number, number]) => ((H - 1) - r) * W + x);
    const paths = reach(scratch, gridOf(eng.board.state), s.piece, target);
    if (!paths.length) { cut = { why: 'no_engine_path', where: `${where} ${s.piece} ${JSON.stringify(s.cells)}` }; break; }
    const want = SPIN_OF_CC[s.tspin] ?? null;
    const path = s.piece === 'T' ? (paths.find(p => p.spin === want) ?? paths[0]!) : paths[0]!;
    const { inputs, frames } = inputsOf([{ hold: s.hold, edges: path.edges } as any]);
    const base = frame;
    pre = null; lockRes = null; boardBefore = rowsOf(eng.board.state);
    tickTo(inputs.map(([f, type, k]) => ({ frame: base + f, type, data: { key: k, subframe: 0 } })), base + frames);
    if (!lockRes || !pre) { cut = { why: 'no_lock', where }; break; }
    const p = pre as { board: string[]; cells: { row: number; col: number }[] };
    const got = p.cells.map(q => ((H - 1) - q.row) * W + q.col).sort((a, b) => a - b).join(',');
    if (got !== [...target].sort((a, b) => a - b).join(',')) { cut = { why: 'cells_mismatch', where }; break; }
    if (lockRes.lines !== s.lines) { cut = { why: 'lines_mismatch', where: `${where} cc ${s.lines} engine ${lockRes.lines}` }; break; }
    const espin = lockRes.spin === 'none' ? null : lockRes.spin === 'mini' ? 'mini' : 'normal';
    if (s.piece === 'T' && espin !== want)
      spinDisagreements.push(`${where} cc ${s.kind}/${s.tspin} engine ${lockRes.spin} lines ${lockRes.lines}`);
    // the garbage rule, re-derived from the schedule
    pending.push(...(sched.get(j) ?? []));
    const cols: number[] = [];
    if (lockRes.lines === 0 && pending.length) {
      const rest: [number, number][] = [];
      for (const [amount, col] of pending) {
        const take = Math.min(amount, CAP - cols.length);
        for (let k = 0; k < take; k++) {
          eng.board.insertGarbage({ amount: 1, size: 1, column: col, bombs: false, isBeginning: k === 0, isEnd: k === take - 1 });
          cols.push(col);
        }
        if (take < amount) rest.push([amount - take, col]);
      }
      pending = rest;
    }
    garbageRows += cols.length;
    if (JSON.stringify(cols) !== JSON.stringify(s.garbage_cols)) {
      cut = { why: 'garbage_mismatch', where: `${where} cc ${JSON.stringify(s.garbage_cols)} engine ${JSON.stringify(cols)}` }; break;
    }
    const after = rowsOf(eng.board.state);
    if (trimTop(occ(after)).join('|') !== (s.field as string[]).join('|')) { cut = { why: 'board_mismatch', where }; break; }
    // the row map, the corpus digest's convention: board before + cells, cleared rows out, garbage rows in
    const g2 = p.board.map(r => [...r].map(c => c !== '.'));
    for (const q of p.cells) if (q.row >= 0 && q.row < H) g2[q.row]![q.col] = true;
    const clearedRows: number[] = [];
    for (let r = 0; r < H; r++) if (g2[r]!.every(Boolean)) clearedRows.push(r);
    const kept = g2.filter((_, r) => !clearedRows.includes(r));
    while (kept.length < H) kept.unshift(new Array(W).fill(false));
    const pred = kept.slice(cols.length);
    const mapOk = pred.every((row, r) => row.every((x, c) => x === (after[r]![c] !== '.')));
    const spin = lockRes.spin === 'none' ? 'none' : lockRes.spin === 'mini' ? 'mini' : 'full';
    locks.push({ piece: s.piece, spin, cleared: lockRes.lines, cells: p.cells, clearedRows, garbage: cols.length, mapOk });
    if (s.piece === 'T' && spin !== 'none' && lockRes.lines > 0) tspins.push({ i: j, board: p.board });
    // rows inserted after the engine already spawned the next piece: an overlap is a named cut
    if (cols.length && j + 1 < steps.length) {
      const bad = eng.falling.absoluteBlocks.some(([x, y]: [number, number]) => y < 0 || y >= eng.board.state.length || eng.board.state[y]?.[x] != null);
      if (bad) { cut = { why: 'garbage_spawn_overlap', where }; break; }
    }
  }
  return { cut, locks, tspins, dead: (g.steps as any[]).some(s => s.dead), steps: steps.length, garbageRows, spinDisagreements };
}

const inFile = process.argv[2];
if (!inFile) throw new Error('usage: bun cutcopy-selfplay-garbage.ts games-garbage.jsonl [out.json]');
const games: any[] = readFileSync(inFile, 'utf8').split('\n').filter(l => l.trim()).map(l => JSON.parse(l));
const tally = { games: games.length, games_complete: 0, cc_dead: 0, pieces_cc: 0, pieces_replayed: 0,
  garbage_rows_offered: 0, garbage_rows_inserted_engine: 0, cut: {} as Record<string, number>, cut_examples: [] as string[],
  spin_credit_disagreed: 0, rowmap_unverified: 0, engine_full_tsd: 0, cc_tsd: 0 };
const digests: TechDigest[] = [];
games.forEach((g, gi) => {
  if (!Array.isArray(g.garbage)) throw new Error(`${g.id}: no garbage schedule (use cutcopy-selfplay.ts for no-garbage games)`);
  const r = replay(g);
  if (r.dead) tally.cc_dead++;
  tally.pieces_cc += r.steps;
  tally.pieces_replayed += r.locks.length;
  tally.garbage_rows_offered += g.garbage.reduce((a: number, x: any) => a + x.lines, 0);
  tally.garbage_rows_inserted_engine += r.garbageRows;
  tally.spin_credit_disagreed += r.spinDisagreements.length;
  for (const lk of r.locks) { if (!lk.mapOk) tally.rowmap_unverified++; if (lk.piece === 'T' && lk.spin === 'full' && lk.cleared === 2) tally.engine_full_tsd++; }
  tally.cc_tsd += (g.steps as any[]).slice(0, r.locks.length).filter(s => s.kind === 'tsd').length;
  if (r.cut) { tally.cut[r.cut.why] = (tally.cut[r.cut.why] ?? 0) + 1; if (tally.cut_examples.length < 30) tally.cut_examples.push(`${r.cut.why}: ${r.cut.where}`); }
  else tally.games_complete++;
  digests.push({ session: 'selfplay-garbage', file: `seed-${g.seed}`, round: 0, match: gi + 1, user: 'cold-clear',
                 v: r.locks.length - 1, locks: r.locks, tspins: r.tspins });
});
const tr = loadTranscription(CUTCOPY.transcriptionPath);
const cls = classify(CUTCOPY, tr, digests);
const hits = cls.hits.map(h => ({ seed: Number(h.file.slice(5)), variant: h.variant, lock: h.lock,
  hand: h.mirrored ? 'mirrored' : 'as_drawn', in_opener: h.in_opener, garbage_in_window: h.garbage_in_window,
  window: h.window_letters, followup: h.followup }));
const byV: Record<string, { hits: number; garbage_in_window: number; followup_fired: number }> = {};
for (const h of hits) {
  const b = (byV[h.variant] ??= { hits: 0, garbage_in_window: 0, followup_fired: 0 });
  b.hits++; if (h.garbage_in_window) b.garbage_in_window++; if ((h.followup as any)?.fired) b.followup_fired++;
}
const out = { input: inFile, nodes: games[0]?.nodes ?? null, tally, denominators: cls.denominators,
  check: { ...cls.check, by_session: undefined }, hits_by_variant: byV,
  ablation: Object.fromEntries(Object.entries(cls.perVariant).map(([k, v]: [string, any]) => [k, v.ablation])),
  off_board: cls.offBoard.length, recon_dropped: cls.reconDropped, hits };
const txt = JSON.stringify(out, null, 1);
if (process.argv[3]) writeFileSync(process.argv[3], txt + '\n');
console.log(txt);
