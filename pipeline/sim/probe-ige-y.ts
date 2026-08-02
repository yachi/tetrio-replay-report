/**
 * What is the `y` field on a garbage ige event?
 *
 * Motivation: the attack stream is too coarse an oracle (~1.7 pre-garbage attacks per ~19
 * pieces) to localise a ~1.5%-per-piece placement error. `y` is present on all 2209 garbage
 * events and takes values in exactly 20..39 — the visible playfield rows, never the buffer —
 * so it is a board row. If it encodes the SENDER's board, it is a per-attack board oracle
 * an order of magnitude denser than the attack stream itself.
 *
 * Method: only compare on attacks the sim already reproduces exactly (matched frame AND
 * amount within the round's verified prefix). On those the sim's board is trustworthy, so
 * any stable relationship is a property of the format, not of the sim's errors.
 *
 * Candidates tested, all on the SENDER's board at the moment of the attack:
 *   pieceBottom  — lowest row of the locking piece
 *   pieceTop     — highest row of the locking piece
 *   stackTop     — topmost non-empty row after the clear
 * and on the RECEIVER's board: its stackTop at the arrival frame.
 */
import { readFileSync, readdirSync } from 'node:fs';
import { simulate, DEFAULT_TABLE } from './sim.ts';
import { replayDir } from './verified-prefix.ts';
const DIR = replayDir();
const opts = {garbagespeed:30, garbagecap:8, locktime:60, gravity:0.0167, sdfMode:'abs' as const,
              insertMode:'onPlace' as const, cancelMode:'all' as const, acEmit:'separate' as const,
              subframe:true, blockout:'shiftup' as const, kickset:'SRS+' as const};

const build = (rp:any) => ({
  ev: rp.events.filter((e:any)=>e.type==='keydown'||e.type==='keyup')
    .map((e:any)=>({frame:e.frame, sub:e.data.subframe??0, type:e.type, key:e.data.key})),
  gin: rp.events.filter((e:any)=>e.type==='ige'&&e.data.type==='interaction'&&e.data.data?.type==='garbage')
    .map((e:any)=>({frame:e.frame, amt:e.data.data.amt, x:e.data.data.x, size:e.data.data.size})),
});

const hits: Record<string, number> = {lowestClearedRow:0, highestClearedRow:0, pieceBottom:0, pieceTop:0, stackTopAfter:0, recvStackTop:0};
let n = 0;
const samples: string[] = [];
const delta = new Map<string, Map<number, number>>();

for (const f of readdirSync(DIR).filter(x=>x.endsWith('.ttrm')).sort()) {
  const d = JSON.parse(readFileSync(`${DIR}/${f}`,'utf8'));
  for (const rnd of d.replay.rounds) { if (rnd.length!==2) continue;
    const P = rnd.map((p:any)=>({rp:p.replay, gameid:p.replay.options.gameid, user:p.username}));
    for (const [me,other] of [[P[0],P[1]],[P[1],P[0]]] as any[]) {
      const A = build(me.rp), B = build(other.rp);
      const rMe = simulate(A.ev, A.gin, me.rp.options.handling, me.rp.options.seed, me.rp.frames, DEFAULT_TABLE, opts);
      const rOther = simulate(B.ev, B.gin, other.rp.options.handling, other.rp.options.seed, other.rp.frames, DEFAULT_TABLE, opts);
      // ground truth: attacks I sent, with their full payload
      const truth = other.rp.events.filter((e:any)=>e.type==='ige'&&e.data.type==='interaction'
        && e.data.data?.type==='garbage' && e.data.data.gameid===me.gameid)
        .map((e:any)=>({frame:e.data.data.frame??e.frame, amt:e.data.data.amt, y:e.data.data.y, x:e.data.data.x}))
        .sort((a:any,b:any)=>a.frame-b.frame);
      const mine = rMe.records.filter(x=>x.sent>0);
      for (let i=0;i<Math.min(mine.length,truth.length);i++) {
        const a = mine[i]!, b = truth[i]!;
        if (Math.abs(a.frame-b.frame)>25 || a.sent!==b.amt) break;   // verified prefix only
        n++;
        const rows = a.cells.map(c=>c.row);
        const pieceBottom = Math.max(...rows), pieceTop = Math.min(...rows);
        const li = rMe.records.indexOf(a);
        const board = rMe.boards[li] ?? [];
        let st = board.length; for (let y2=0;y2<board.length;y2++) if (board[y2].some((c:any)=>c!==null)) { st=y2; break; }
        // receiver's stack top at the arrival frame
        let ri = -1; for (let k=0;k<rOther.locks.length;k++) if (rOther.locks[k]!.frame<=b.frame) ri=k;
        const rb = rOther.boards[ri] ?? [];
        let rst = rb.length; for (let y2=0;y2<rb.length;y2++) if (rb[y2].some((c:any)=>c!==null)) { rst=y2; break; }
        const cr = a.clearedRows;
        const lowestCleared = cr.length ? Math.max(...cr) : -1;
        const highestCleared = cr.length ? Math.min(...cr) : -1;
        if (lowestCleared===b.y) hits.lowestClearedRow++;
        if (highestCleared===b.y) hits.highestClearedRow++;
        if (pieceBottom===b.y) hits.pieceBottom++;
        if (pieceTop===b.y) hits.pieceTop++;
        if (st===b.y) hits.stackTopAfter++;
        if (rst===b.y) hits.recvStackTop++;
        {
          const key = `lines=${a.lines} spin=${a.spin}`;
          if (!delta.has(key)) delta.set(key, new Map());
          const m = delta.get(key)!; const dv = b.y - lowestCleared;
          m.set(dv, (m.get(dv) ?? 0) + 1);
        }
        if (samples.length<20) samples.push(`  y=${String(b.y).padStart(2)} amt=${String(b.amt).padStart(2)} lines=${a.lines} | clearedRows=[${cr.join(',')}] pieceBottom=${pieceBottom}`);
      }
    }}}

console.log(`verified-prefix attacks compared: ${n}`);
for (const [k,v] of Object.entries(hits).sort((a,b)=>b[1]-a[1]))
  console.log(`  y === ${k.padEnd(15)} ${v}/${n} = ${(100*v/n).toFixed(1)}%`);
console.log('\ny - lowestClearedRow, by clear type (delta: count):');
for (const [k,m] of [...delta].sort()) {
  const tot = [...m.values()].reduce((a,b)=>a+b,0);
  const parts = [...m].sort((a,b)=>b[1]-a[1]).map(([d,c])=>`${d>=0?'+':''}${d}: ${c}`).join('  ');
  console.log(`  ${k.padEnd(22)} n=${String(tot).padStart(3)}   ${parts}`);
}
