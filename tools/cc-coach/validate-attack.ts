import { priceLock } from './attack.ts';
import { readFileSync, writeFileSync, readdirSync } from 'fs';
// the ruleset (b2bchaining, combotable, ...) is read from the session's first replay
const firstReplay = () => { const d = process.env.REPLAY_DIR!; return d + '/' + readdirSync(d).filter(f => f.endsWith('.ttrm')).sort()[0]; };
const P = readFileSync('positions.jsonl', 'utf8').trim().split('\n').map(l => JSON.parse(l));
const opts = JSON.parse(readFileSync(firstReplay(), 'utf8')).replay.rounds[0][0].replay.options;
let ok = 0, bad = 0, ctrBad = 0; const ex: any[] = [];
for (let i = 0; i < P.length; i++) {
  const p = P[i], nx = P[i + 1];
  const pl = p.played;
  const r = priceLock({ b2b: p.b2b, combo: p.combo }, pl.lines, pl.spin, pl.piece, false, { ...opts, garbagemultiplier: p.gmult });
  if (nx && nx.id.split('/').slice(0, 3).join('/') === p.id.split('/').slice(0, 3).join('/')) {
    if (nx.b2b !== r.ctr.b2b || nx.combo !== r.ctr.combo) ctrBad++;
  }
  // played.sent includes the separate all-clear event if any; ignore pc rounds via tolerance 10
  if (r.attack === pl.raw || r.attack + 10 === pl.raw) ok++; else { bad++; if (ex.length < 8) ex.push({ id: p.id, pl, b2b: p.b2b, combo: p.combo, mine: r.attack }); }
}
console.log({ ok, bad, ctrBad, ex });
let explained = 0, unexplained: any[] = [];
for (let i = 0; i < P.length; i++) {
  const p = P[i], pl = p.played;
  const r = priceLock({ b2b: p.b2b, combo: p.combo }, pl.lines, pl.spin, pl.piece, false, { ...opts, garbagemultiplier: p.gmult });
  if (r.attack === pl.raw || r.attack + 10 === pl.raw) continue;
  if (pl.raw < r.attack && p.incoming > 0 && r.attack - pl.raw <= p.incoming) explained++;
  else unexplained.push({ id: p.id, sent: pl.raw, mine: r.attack, inc: p.incoming, lines: pl.lines, spin: pl.spin, tanked: pl.tanked });
}
console.log('cancel-explained', explained, 'unexplained', unexplained.length, unexplained.slice(0, 10));
