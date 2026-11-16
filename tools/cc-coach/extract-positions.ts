// Extract every decision point (one per piece locked) from .ttrm replays, as JSONL for the
// cold-clear coach. The extraction is pipeline/sim/cc-positions.ts; this keeps `clutch: false`, as
// this tool always has (it feeds the bot, not a published figure).
import { loadCases } from '../../pipeline/sim/verified-prefix.ts';
import { extractPositions } from '../../pipeline/sim/cc-positions.ts';
import { writeFileSync } from 'fs';

const dir = process.env.REPLAY_DIR!;
const out: string[] = [];
const roundsMeta: any[] = [];
for (const c of loadCases(dir)) {
  const { positions, meta } = extractPositions(c, { clutch: false });
  roundsMeta.push(meta);
  for (const p of positions) out.push(JSON.stringify(p));
}
writeFileSync(process.env.OUT!, out.join('\n') + '\n');
writeFileSync(process.env.OUT! + '.rounds.json', JSON.stringify(roundsMeta, null, 1));
console.error('positions', out.length, 'rounds', roundsMeta.length,
  'roundOk', roundsMeta.filter(r => r.roundOk).length, 'bagOk', roundsMeta.filter(r => r.bagOk).length);
