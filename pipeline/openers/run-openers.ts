/**
 * Which opener did each round actually play?
 *
 * For every verified round with a CLEAN first bag — seven locks, no line clear, no garbage, all
 * inside the verified prefix — the board is compared with every 28-cell catalogue page, exactly and
 * by Hamming distance, in both handednesses.
 *
 *   REPLAY_DIR is set per session by the loop below; pass session dirs as arguments.
 *   bun run pipeline/openers/run-openers.ts sessions/2026-07-22 [...]
 */
import { loadCases, runCase, verifiedIndex } from '../sim/verified-prefix.ts';
import { forecastMetric } from '../sim/forecast.ts';
import { loadCatalogue, prepare, occGrid, rowsFromBoard, exactMatches, nearest, isCSpin } from './match.ts';

const cat = loadCatalogue();
const prepared = prepare(cat.pages);
const cspin = prepared.filter(p => isCSpin(p.name));

export interface RoundResult {
  session: string; user: string; file: string; round: number; clean: boolean;
  exact?: { asDrawn: string[]; asMirror: string[] };
  best?: { d: number; name: string; mirrored: boolean };
  bestCSpin?: { d: number; name: string; mirrored: boolean };
  sbTriple?: boolean; reTriple?: boolean;
}

export function analyse(sessions: string[]): RoundResult[] {
  const out: RoundResult[] = [];
  for (const session of sessions) {
    process.env.REPLAY_DIR = session;
    for (const c of loadCases(session)) {
      const r = runCase(c, {});
      const v = verifiedIndex(r, c.truth);
      const base = { session: session.split('/').pop()!, user: c.user, file: c.file, round: c.round };
      if (v < 6) { out.push({ ...base, clean: false }); continue; }
      let clean = true;
      for (let i = 0; i <= 6; i++) if (r.locks[i]!.cleared > 0) clean = false;
      for (const g of r.garbageEvents) if (g.lockIndex <= 6) clean = false;
      if (!clean) { out.push({ ...base, clean: false }); continue; }
      const rows = rowsFromBoard(r.boards[6]! as (string | null)[][]);
      if (!rows) { out.push({ ...base, clean: false }); continue; }
      const grid = occGrid(rows);
      const recs = forecastMetric(r, true).records.filter(x => x.lockIndex <= v);
      out.push({ ...base, clean: true,
        exact: exactMatches(grid, prepared),
        best: nearest(grid, prepared),
        bestCSpin: nearest(grid, cspin),
        sbTriple: recs.some(x => x.kind === 'self_built' && x.lines === 3),
        reTriple: recs.some(x => x.kind === 'reactive' && x.lines === 3) });
    }
  }
  return out;
}

if (import.meta.main) {
  // argv is read HERE, not at module scope: this file is imported by openers.test.ts, and a
  // top-level throw on a missing argument would make the whole suite fail to load.
  const SESSIONS = process.argv.slice(2);
  if (!SESSIONS.length) throw new Error('usage: bun run run-openers.ts <session dir> [...]');
  console.log(`catalogue: ${cat.pages.length} pages, ${new Set(cat.pages.map(p => p.name)).size} openers, `
    + `${new Set(cspin.map(p => p.name)).size} of them C-Spin (${cspin.length} pages)`);
  console.log(`data.json sha256 ${cat.provenance.data_json_sha256}\n`);
  const res = analyse(SESSIONS);
  const clean = res.filter(r => r.clean);
  const band = (d: number) => (d === 0 ? '0' : d <= 2 ? '1-2' : d <= 4 ? '3-4' : d <= 8 ? '5-8' : d <= 14 ? '9-14' : '15+');
  const hist = (rs: RoundResult[], k: 'best' | 'bestCSpin') => {
    const b: Record<string, number> = { '0': 0, '1-2': 0, '3-4': 0, '5-8': 0, '9-14': 0, '15+': 0 };
    for (const r of rs) b[band(r[k]!.d)]!++;
    return Object.entries(b).map(([n, c]) => `${n}:${String(c).padStart(3)}`).join('  ');
  };
  console.log(`rounds with a verified clean 7-piece first bag: ${clean.length} of ${res.length}\n`);
  console.log(`cells from the nearest catalogued opener   ${hist(clean, 'best')}`);
  console.log(`cells from the nearest C-SPIN opener       ${hist(clean, 'bestCSpin')}`);
  const sb = clean.filter(r => r.sbTriple), re = clean.filter(r => r.reTriple);
  console.log(`\nrounds holding a self_built Triple (${sb.length})   ${hist(sb, 'bestCSpin')}`);
  console.log(`rounds holding a reactive Triple  (${re.length})   ${hist(re, 'bestCSpin')}`);

  const exact = clean.filter(r => r.exact!.asDrawn.length || r.exact!.asMirror.length);
  console.log(`\nexact first-bag matches: ${exact.length}`);
  const names = new Map<string, number>();
  // count ROUNDS per name: a symmetric field matches both as drawn and mirrored, and counting
  // entries would double every one of them
  for (const r of exact) for (const n of new Set([...r.exact!.asDrawn, ...r.exact!.asMirror]))
    names.set(n, (names.get(n) ?? 0) + 1);
  for (const [n, k] of [...names].sort((a, b) => b[1] - a[1]))
    console.log(`  ${String(k).padStart(3)}  ${n.slice(0, 88)}`);
}
