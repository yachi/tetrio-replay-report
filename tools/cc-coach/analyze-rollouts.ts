// Price both sides of every rollout window with TETR.IO's own attack formula (the vendored
// engine's garbageCalcV2), and summarise the human vs cold-clear on identical positions, pieces
// and received garbage.
import { priceLock } from './attack.ts';
import { readFileSync, writeFileSync, readdirSync } from 'fs';
// the ruleset (b2bchaining, combotable, ...) is read from the session's first replay
const firstReplay = () => { const d = process.env.REPLAY_DIR!; return d + '/' + readdirSync(d).filter(f => f.endsWith('.ttrm')).sort()[0]; };
const IN = process.argv[2] ?? 'rollouts.jsonl', OUT = process.argv[3] ?? 'rollouts.out.jsonl';
const W = new Map<string, any>(readFileSync(IN, 'utf8').trim().split('\n').map(l => { const o = JSON.parse(l); return [o.id, o]; }));
const R = readFileSync(OUT, 'utf8').trim().split('\n').map(l => JSON.parse(l));
const opts = JSON.parse(readFileSync(firstReplay(), 'utf8')).replay.rounds[0][0].replay.options;

const shape = (field: string[]) => {
  const h = Array(10).fill(0); let holes = 0;
  for (let c = 0; c < 10; c++) { let top = -1; for (let r = 0; r < 40; r++) if (field[r][c] !== '.') { top = r; break; } h[c] = top < 0 ? 0 : 40 - top;
    if (top >= 0) for (let r = top; r < 40; r++) if (field[r][c] === '.') holes++; }
  let bump = 0; for (let c = 0; c < 9; c++) bump += Math.abs(h[c] - h[c + 1]);
  return { max_h: Math.max(...h), holes, bump };
};
const ccSpin = (s: any) => s.piece !== 'T' ? 'none' : (s.tspin === 'Full' ? 'normal' : s.tspin === 'Mini' ? 'mini' : 'none');
const tally = () => ({ windows: 0, attack: 0, pieces: 0, lines: 0, tsd: 0, tst: 0, tss: 0, mini: 0, quad: 0, pc: 0, b2bEnd: 0, holes: 0, maxh: 0, dead: 0, burned: 0 });
const out: any[] = [];
const agg: Record<string, { human: any; cc: any; diffs: number[]; validate: number }> = {};
for (const r of R) {
  const w = W.get(r.id)!; const user = w.user;
  agg[user] ??= { human: tally(), cc: tally(), diffs: [], validate: 0 };
  const A = agg[user];
  // human
  let ctr = { b2b: w.b2b, combo: w.combo }, hAtk = 0, hRaw = 0; const h = tally();
  for (const p of w.player_window) {
    const x = priceLock(ctr, p.lines, p.spin, p.piece, false, opts); ctr = x.ctr; hAtk += x.attack; hRaw += p.raw;
    h.lines += p.lines; h.pieces++;
    if (p.piece === 'T' && p.spin === 'normal' && p.lines > 0) { if (p.lines === 2) h.tsd++; else if (p.lines === 3) h.tst++; else h.tss++; }
    if (p.spin === 'mini' && p.lines > 0) h.mini++;
    if (p.spin === 'none' && p.lines === 4) h.quad++;
    if (p.spin === 'none' && p.lines > 0 && p.lines < 4) h.burned += p.lines;
  }
  if (hAtk === hRaw || hAtk + 10 === hRaw) A.validate++;
  const hs = shape(w.player_end.field);
  // cold-clear
  ctr = { b2b: w.b2b, combo: w.combo }; let cAtk = 0; const c = tally(); let dead = false;
  for (const s of r.steps) {
    if (s.dead) { dead = true; break; }
    const sp = ccSpin(s);
    const x = priceLock(ctr, s.lines, sp, s.piece, s.pc, opts); ctr = x.ctr; cAtk += x.attack + x.pcBonus;
    c.lines += s.lines; c.pieces++;
    if (sp === 'normal' && s.lines > 0) { if (s.lines === 2) c.tsd++; else if (s.lines === 3) c.tst++; else c.tss++; }
    if (sp === 'mini' && s.lines > 0) c.mini++;
    if (sp === 'none' && s.lines === 4) c.quad++;
    if (s.pc) c.pc++;
    if (sp === 'none' && s.lines > 0 && s.lines < 4) c.burned += s.lines;
  }
  const cs = shape(r.final_field);
  for (const [T, atk, sh, b2bEnd, d] of [[A.human, hAtk, hs, w.player_end.b2b >= 0, false], [A.cc, cAtk, cs, ctr.b2b >= 0, dead]] as any[]) {
    T.windows++; T.attack += atk; T.holes += sh.holes; T.maxh += sh.max_h; T.b2bEnd += b2bEnd ? 1 : 0; T.dead += d ? 1 : 0;
  }
  for (const k of ['pieces', 'lines', 'tsd', 'tst', 'tss', 'mini', 'quad', 'pc', 'burned'] as const) { A.human[k] += (h as any)[k]; A.cc[k] += (c as any)[k]; }
  A.diffs.push(cAtk - hAtk);
  out.push({ id: r.id, user, lock: w.lock, human: { ...h, attack: hAtk, end: hs, b2bEnd: w.player_end.b2b }, cc: { ...c, attack: cAtk, end: cs, b2bEnd: ctr.b2b, dead }, diff: cAtk - hAtk,
    start_height: shape(w.field).max_h, start_b2b: w.b2b });
}
writeFileSync(OUT.replace('.jsonl', '.priced.jsonl'), out.map(o => JSON.stringify(o)).join('\n') + '\n');
for (const [u, A] of Object.entries(agg)) {
  const d = A.diffs.slice().sort((a, b) => a - b), n = d.length;
  const per = (T: any) => ({ APP: +(T.attack / T.pieces).toFixed(3), atk_per_window: +(T.attack / T.windows).toFixed(2),
    tsd_per100: +(100 * T.tsd / T.pieces).toFixed(2), tst_per100: +(100 * T.tst / T.pieces).toFixed(2), tss_per100: +(100 * T.tss / T.pieces).toFixed(2),
    quad_per100: +(100 * T.quad / T.pieces).toFixed(2), burned_lines_per100: +(100 * T.burned / T.pieces).toFixed(1),
    lines_per_piece: +(T.lines / T.pieces).toFixed(3), end_holes: +(T.holes / T.windows).toFixed(2), end_maxh: +(T.maxh / T.windows).toFixed(2),
    b2b_alive_at_end: +(T.b2bEnd / T.windows).toFixed(3), dead: T.dead, pc: T.pc });
  console.log(u, 'windows', n, 'human-attack-priced==replay-raw', A.validate, '/', n);
  console.log('  human', per(A.human));
  console.log('  cc   ', per(A.cc));
  console.log('  cc-human attack/window: median', d[n >> 1], 'p10', d[Math.floor(n * .1)], 'p90', d[Math.floor(n * .9)], 'cc ahead', d.filter(x => x > 0).length, 'tie', d.filter(x => x === 0).length, 'human ahead', d.filter(x => x < 0).length);
}
