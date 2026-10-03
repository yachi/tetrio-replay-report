// Frame-by-frame data for each clip, both sides, with TETR.IO attack per lock. Self-checks:
// the human's simulated board after every step == the next recorded decision's field, and
// cold-clear's simulated final board == the harness's own final_field.
import { priceLock } from '../attack.ts';
import { readFileSync, writeFileSync } from 'fs';
const IN = readFileSync(process.env.OUT + '/clips-in.jsonl', 'utf8').trim().split('\n').map(l => JSON.parse(l));
const CC = new Map(readFileSync(process.env.OUT + '/clips-cc.jsonl', 'utf8').trim().split('\n').map(l => { const o = JSON.parse(l); return [o.id, o]; }));
const P = new Map(readFileSync('positions.jsonl', 'utf8').trim().split('\n').map(l => { const o = JSON.parse(l); return [o.id, o]; }));
const opts = JSON.parse(readFileSync(process.env.REPLAY_DIR + '/' + require('fs').readdirSync(process.env.REPLAY_DIR).filter((f: string) => f.endsWith('.ttrm')).sort()[0], 'utf8')).replay.rounds[0][0].replay.options;
const occ = (f: string[]) => f.map(r => r.split('').map(c => c === '.' ? '.' : c === 'G' ? 'G' : 'X').join(''));
function place(field: string[], cells: number[][], tag: string) {
  const g = field.map(r => r.split(''));
  for (const [c, r] of cells) { if (g[r][c] !== '.') throw new Error(`overlap at ${c},${r}`); g[r][c] = tag; }
  const kept = g.filter(r => r.some(ch => ch === '.'));
  const lines = 40 - kept.length;
  while (kept.length < 40) kept.unshift('..........'.split(''));
  return { field: kept.map(r => r.join('')), lines };
}
function insert(field: string[], amount: number, col: number) {
  let g = field.slice();
  for (let i = 0; i < amount; i++) g = [...g.slice(1), Array.from({ length: 10 }, (_, x) => x === col ? '.' : 'G').join('')];
  return g;
}
const clips: any[] = []; const checks: any[] = [];
for (const st of IN) {
  const k = st.id.replace(/\/\d+$/, ''), l0 = st.lock;
  // human
  let f = st.field.slice(); let ctr = { b2b: st.b2b, combo: st.combo };
  const human: any[] = []; let hOk = true;
  for (let j = 0; j < st.k; j++) {
    const p = P.get(`${k}/${l0 + j}`)!; const pl = p.played;
    const before = f; const r = place(f, pl.cells, pl.piece);
    let after = r.field; for (const t of pl.tanks) after = insert(after, t.amount, t.column);
    const x = priceLock(ctr, pl.lines, pl.spin, pl.piece, false, opts); ctr = x.ctr;
    human.push({ piece: pl.piece, hold: pl.piece !== p.current, cells: pl.cells, lines: r.lines, spin: pl.spin, attack: x.attack, b2b: ctr.b2b, combo: ctr.combo, garbage: pl.tanks.reduce((a: number, t: any) => a + t.amount, 0), before, after, current: p.current, holdPiece: p.hold, next: p.next });
    const nx = P.get(`${k}/${l0 + j + 1}`);
    if (nx && JSON.stringify(occ(after)) !== JSON.stringify(occ(nx.field))) hOk = false;
    f = after;
  }
  // cold-clear
  const cc = CC.get(st.id)!; f = st.field.slice(); ctr = { b2b: st.b2b, combo: st.combo };
  const ccs: any[] = []; let pending: number[][] = [];
  for (let j = 0; j < cc.steps.length; j++) {
    const s = cc.steps[j]; if (s.dead) { ccs.push({ dead: true }); break; }
    const before = f; const r = place(f, s.cells, s.piece);
    if (r.lines !== s.lines) throw new Error('line mismatch ' + st.id);
    let after = r.field;
    for (const t of st.garbage_schedule[j] ?? []) pending.push([t.amount, t.column]);
    let gin = 0;
    if (r.lines === 0 && pending.length) { for (const [a, c] of pending) { after = insert(after, a, c); gin += a; } pending = []; }
    if (gin !== s.garbage_in) throw new Error('garbage mismatch ' + st.id);
    const spin = s.piece !== 'T' ? 'none' : s.tspin === 'Full' ? 'normal' : s.tspin === 'Mini' ? 'mini' : 'none';
    const x = priceLock(ctr, r.lines, spin, s.piece, s.pc, opts); ctr = x.ctr;
    ccs.push({ piece: s.piece, hold: s.hold, cells: s.cells, lines: r.lines, spin, attack: x.attack + x.pcBonus, b2b: ctr.b2b, combo: ctr.combo, garbage: gin, before, after });
    f = after;
  }
  const ccOk = JSON.stringify(occ(f).map(r => r.replace(/[XG]/g, '#'))) === JSON.stringify(cc.final_field);
  checks.push({ id: st.id, humanBoardsReproduce: hOk, ccFinalMatchesHarness: ccOk });
  clips.push({ id: st.id, source: st.clip_source, start: { field: st.field, current: st.current, hold: st.hold, next: st.next, b2b: st.b2b, combo: st.combo, incoming: st.incoming }, future: st.future, human, cc: ccs,
    totals: { human: human.reduce((a, s) => a + s.attack, 0), cc: ccs.reduce((a, s) => a + (s.attack ?? 0), 0) } });
}
writeFileSync(process.env.OUT + '/clips.json', JSON.stringify(clips));
console.log(checks, clips.map(c => [c.id, c.source, c.totals]));
