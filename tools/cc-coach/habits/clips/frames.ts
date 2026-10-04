// Stage 3 (per seed): frame data for each position, both sides, adapted from build-frames-p.ts.
// Self-checks per clip (any false => the clip is dropped downstream):
//   humanBoardsReproduce : human board after every step (placed, cleared, recorded garbage) == next
//                          recorded decision's field (occupancy, garbage distinguished)
//   humanAttackMatches   : priceLock(start counters, lines, spin) == the replay's own raw attack
//                          (or raw - 10, the separate all-clear event), with each file's own options
//                          and the lock-time garbage multiplier, as corpus-validate-attack.ts does
//   ccFinalMatchesHarness: cold-clear's rebuilt final board == the harness's own final_field
//   ccLinesAndGarbage    : rebuilt lines and inserted garbage == the harness's per-step values
// usage: bun frames.ts <seed>
import { priceLock } from '../../attack.ts';
import { readFileSync, writeFileSync } from 'fs';
const S = process.env.CC_WORK!;
const D = process.env.HCD ?? S + '/scen/hclips';
const seed = process.argv[2];
const IN = readFileSync(D + '/rollin.jsonl', 'utf8').trim().split('\n').map(l => JSON.parse(l));
const CC = new Map(readFileSync(`${D}/roll-s${seed}.jsonl`, 'utf8').trim().split('\n').map(l => { const o = JSON.parse(l); return [o.id, o]; }));
const P = new Map(readFileSync(D + '/windows.jsonl', 'utf8').trim().split('\n').map(l => { const o = JSON.parse(l); return [o.id, o]; }));
const dirOf = (session: string) => session === '2026-10-03' ? `${S}/replays` : `/home/user/tetrio-replay-report/sessions/${session}`;
const optCache = new Map<string, any>();
const optsFor = (p: any) => {
  const k = p.session + '/' + p.file + '/' + p.round + '/' + p.user;
  if (!optCache.has(k)) {
    const j = JSON.parse(readFileSync(`${dirOf(p.session)}/${p.file}`, 'utf8'));
    const rd = j.replay.rounds[p.round].find((x: any) => x.username === p.user) ?? j.replay.rounds[p.round][0];
    optCache.set(k, rd.replay.options);
  }
  return optCache.get(k);
};
const occ = (f: string[]) => f.map(r => r.split('').map(c => c === '.' ? '.' : c === 'G' ? 'G' : 'X').join(''));
function place(field: string[], cells: number[][], tag: string) {
  const g = field.map(r => r.split(''));
  for (const [c, r] of cells) { if (g[r][c] !== '.') throw new Error(`overlap at ${c},${r}`); g[r][c] = tag; }
  const cleared: number[] = []; g.forEach((r, i) => { if (!r.includes('.')) cleared.push(i); });
  const kept = g.filter(r => r.some(ch => ch === '.'));
  const lines = 40 - kept.length;
  while (kept.length < 40) kept.unshift('..........'.split(''));
  return { field: kept.map(r => r.join('')), lines, cleared };
}
function insert(field: string[], amount: number, col: number) {
  let g = field.slice();
  for (let i = 0; i < amount; i++) g = [...g.slice(1), Array.from({ length: 10 }, (_, x) => x === col ? '.' : 'G').join('')];
  return g;
}
const out: any[] = []; const checks: any[] = [];
for (const st of IN) {
  const k = st.id.replace(/\/\d+$/, ''), l0 = st.lock;
  const opts = optsFor(st);
  // lock-time multiplier of human step j = the next decision's gmult (captured inside the lock handler)
  const gLock = (j: number) => P.get(`${k}/${l0 + j + 1}`)!.gmult;
  let f = st.field.slice(); let ctr = { b2b: st.b2b, combo: st.combo };
  const human: any[] = []; let hOk = true, aOk = true; const why: string[] = [];
  try { for (let j = 0; j < st.k; j++) {
    const p = P.get(`${k}/${l0 + j}`)!; const pl = p.played;
    const r = place(f, pl.cells, pl.piece);
    let after = r.field; for (const t of pl.tanks) after = insert(after, t.amount, t.column);
    const x = priceLock(ctr, pl.lines, pl.spin, pl.piece, false, { ...opts, garbagemultiplier: gLock(j) }); ctr = x.ctr;
    if (!(x.attack === pl.raw || x.attack + 10 === pl.raw)) { aOk = false; why.push(`human step ${j + 1} attack ${x.attack} vs raw ${pl.raw}`); }
    if (r.lines !== pl.lines) { hOk = false; why.push(`human step ${j + 1} lines ${r.lines} vs ${pl.lines}`); }
    human.push({ piece: pl.piece, hold: pl.piece !== p.current, cells: pl.cells, lines: r.lines, cleared: r.cleared, spin: pl.spin, attack: pl.raw,
      b2b: ctr.b2b, combo: ctr.combo, garbage: pl.tanks.reduce((a: number, t: any) => a + t.amount, 0), tanks: pl.tanks, after,
      current: p.current, holdPiece: p.hold, next: p.next, verified: p.verified, incoming: p.incoming });
    const nx = P.get(`${k}/${l0 + j + 1}`);
    if (!nx || JSON.stringify(occ(after)) !== JSON.stringify(occ(nx.field))) { hOk = false; why.push(`human step ${j + 1} board != recorded`); }
    f = after;
  } } catch (e) { hOk = false; why.push('human rebuild threw: ' + (e as Error).message); }
  const cc = CC.get(st.id); let ccOk = true, lgOk = true; const ccs: any[] = [];
  if (!cc) { ccOk = false; why.push('no harness output'); }
  else {
    f = st.field.slice(); ctr = { b2b: st.b2b, combo: st.combo }; let pending: number[][] = [];
    try {
      for (let j = 0; j < cc.steps.length; j++) {
        const s = cc.steps[j]; if (s.dead) { ccs.push({ dead: true, why: s.why ?? 'no legal placement' }); break; }
        const r = place(f, s.cells, s.piece);
        if (r.lines !== s.lines) { lgOk = false; why.push(`cc step ${j + 1} lines`); }
        let after = r.field;
        for (const t of st.garbage_schedule[j] ?? []) pending.push([t.amount, t.column]);
        let gin = 0;
        if (r.lines === 0 && pending.length) { for (const [a, c] of pending) { after = insert(after, a, c); gin += a; } pending = []; }
        if (gin !== s.garbage_in) { lgOk = false; why.push(`cc step ${j + 1} garbage`); }
        const spin = s.piece !== 'T' ? 'none' : s.tspin === 'Full' ? 'normal' : s.tspin === 'Mini' ? 'mini' : 'none';
        const x = priceLock(ctr, r.lines, spin, s.piece, s.pc, { ...opts, garbagemultiplier: gLock(j) }); ctr = x.ctr;
        ccs.push({ piece: s.piece, hold: s.hold, cells: s.cells, lines: r.lines, cleared: r.cleared, spin, kind: s.kind, attack: x.attack + x.pcBonus,
          b2b: ctr.b2b, combo: ctr.combo, garbage: gin, after });
        f = after;
      }
    } catch (e) { ccOk = false; why.push('cc rebuild threw: ' + (e as Error).message); }
    if (ccOk) ccOk = JSON.stringify(occ(f).map(r => r.replace(/[XG]/g, '#'))) === JSON.stringify(cc.final_field);
    if (!ccOk) why.push('cc final board != harness');
  }
  const c = { id: st.id, humanBoardsReproduce: hOk, humanAttackMatches: aOk, ccFinalMatchesHarness: ccOk, ccLinesAndGarbage: lgOk, why };
  checks.push(c);
  out.push({ id: st.id, ok: hOk && aOk && ccOk && lgOk, human, cc: ccs, harness_final_shape: cc?.final_shape ?? null });
}
writeFileSync(`${D}/frames-s${seed}.json`, JSON.stringify(out));
writeFileSync(`${D}/frames-check-s${seed}.json`, JSON.stringify(checks));
const bad = checks.filter(c => !(c.humanBoardsReproduce && c.humanAttackMatches && c.ccFinalMatchesHarness && c.ccLinesAndGarbage));
console.log(`seed ${seed}: ${checks.length} positions, ${bad.length} failing`, JSON.stringify(bad.slice(0, 5)));
