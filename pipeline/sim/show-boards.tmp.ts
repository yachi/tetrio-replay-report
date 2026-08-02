import { readFileSync } from 'node:fs';
import { emptyBoard, H, tspinAvailable, bestTspinLines } from './forecast-boards.ts';
const RAW = JSON.parse(readFileSync(`${import.meta.dir}/wiki-tspin-forecast-boards.json`,'utf8')) as {sec:string;rows:string[]}[];
const toBoard = (rows:string[]) => { const b = emptyBoard().map(r=>[...r]) as any[][]; const off=H-rows.length;
  rows.forEach((l,i)=>[...l].forEach((ch,c)=>{ if(ch!=='.'&&ch!=='?') b[off+i]![c]='I'; })); return b; };
const draw = (rows:string[]) => rows.map(r => '  │' + [...r].map(c => c==='.'?'·':c==='?'?'▒':'█').join('') + '│').join('\n');
const idx = process.argv.slice(2).map(Number);
for (const i of idx) {
  const x = RAW[i]!; const b = toBoard(x.rows);
  console.log(`\n[${i}] ${x.sec}`);
  console.log(draw(x.rows));
  console.log('  └' + '─'.repeat(10) + '┘');
  console.log(`  engine: tspinAvailable=${tspinAvailable(b as any)}  bestTspinLines=${bestTspinLines(b as any)}`);
}
