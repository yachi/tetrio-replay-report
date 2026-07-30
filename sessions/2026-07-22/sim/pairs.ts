/**
 * Per-round paired observations: winner's value vs loser's value, for each forecast metric.
 *
 * Extracted from auc.ts so the AUC report and the power analysis run off ONE pairing
 * implementation. Simulating 158 rounds twice over takes ~2 minutes, so results are cached to
 * pairs-cache.json keyed by the rule; delete that file to force a re-run.
 */
import { readFileSync, readdirSync, writeFileSync, existsSync } from 'node:fs';
import { simulate, DEFAULT_TABLE } from './sim.ts';
import { forecastMetric } from './forecast.ts';

export const METRICS = ['forecast rate', 'forecast per piece', 'forecast count', 'tucked T-spins'] as const;
export type Metric = (typeof METRICS)[number];
const KEY: Record<Metric, string> = {
  'forecast rate': 'rate', 'forecast per piece': 'perPiece',
  'forecast count': 'fc', 'tucked T-spins': 'n',
};

export interface Row {
  file: string; round: number; W: string; L: string;
  vals: Record<string, { alive: boolean; n: number; fc: number; rate: number | null; perPiece: number | null; verified: number }>;
}

const DIR = (process.env.REPLAY_DIR ?? `${import.meta.dir}/..`);
const opts = { garbagespeed: 30, garbagecap: 8, locktime: 30, gravity: 0.02, sdfMode: 'abs' as const,
               insertMode: 'onPlace' as const, cancelMode: 'all' as const };

export function collectRows(strict = true): Row[] {
  const cache = `${import.meta.dir}/pairs-cache.json`;
  if (existsSync(cache)) {
    const c = JSON.parse(readFileSync(cache, 'utf8'));
    if (c[String(strict)]) return c[String(strict)] as Row[];
  }
  const rows: Row[] = [];
  for (const file of readdirSync(DIR).filter(f => f.endsWith('.ttrm')).sort()) {
    const d = JSON.parse(readFileSync(`${DIR}/${file}`, 'utf8'));
    d.replay.rounds.forEach((rnd: any, ri: number) => {
      if (rnd.length !== 2) return;
      const P = rnd.map((p: any) => ({ p, rp: p.replay, gameid: p.replay.options.gameid }));
      const vals: Row['vals'] = {};
      for (const [me, other] of [[P[0], P[1]], [P[1], P[0]]] as any[]) {
        const ev = me.rp.events.filter((e: any) => e.type === 'keydown' || e.type === 'keyup')
          .map((e: any) => ({ frame: e.frame, sub: e.data.subframe ?? 0, type: e.type, key: e.data.key }));
        const gin = me.rp.events.filter((e: any) => e.type === 'ige' && e.data.type === 'interaction' && e.data.data?.type === 'garbage')
          .map((e: any) => ({ frame: e.frame, amt: e.data.data.amt, x: e.data.data.x, size: e.data.data.size }));
        const truth = other.rp.events.filter((e: any) => e.type === 'ige' && e.data.type === 'interaction'
          && e.data.data?.type === 'garbage' && e.data.data.gameid === me.gameid)
          .map((e: any) => ({ frame: e.data.data.frame ?? e.frame, amt: e.data.data.amt }))
          .sort((a: any, b: any) => a.frame - b.frame);
        const r = simulate(ev, gin, me.rp.options.handling, me.rp.options.seed, me.rp.frames, DEFAULT_TABLE, opts);
        const mine = r.records.filter(x => x.sent > 0);
        let vf = -1;
        for (let i = 0; i < Math.min(mine.length, truth.length); i++) {
          if (Math.abs(mine[i]!.frame - truth[i]!.frame) <= 25 && mine[i]!.sent === truth[i]!.amt) vf = mine[i]!.frame; else break;
        }
        let vIdx = -1;
        for (let i = 0; i < r.locks.length; i++) if (r.locks[i]!.frame <= vf) vIdx = i;
        const recs = vIdx < 0 ? [] : forecastMetric(r, strict).records.filter(x => x.lockIndex <= vIdx);
        const fc = recs.filter(x => x.kind !== 'reactive').length;
        vals[me.p.username] = { alive: me.p.alive, n: recs.length, fc,
          rate: recs.length ? fc / recs.length : null,
          perPiece: vIdx >= 0 ? fc / (vIdx + 1) : null, verified: vIdx + 1 };
      }
      const names = Object.keys(vals);
      if (names.length !== 2) return;
      const [a, b] = names as [string, string];
      const W = vals[a]!.alive ? a : b, L = vals[a]!.alive ? b : a;
      if (vals[W]!.alive === vals[L]!.alive) return;
      rows.push({ file, round: ri, W, L, vals });
    });
  }
  const prev = existsSync(cache) ? JSON.parse(readFileSync(cache, 'utf8')) : {};
  writeFileSync(cache, JSON.stringify({ ...prev, [String(strict)]: rows }));
  return rows;
}

/** Winner-vs-loser pairs for one metric, with the round they came from (for clustered resampling). */
export function pairsFor(rows: Row[], m: Metric): { win: number; lose: number; file: string }[] {
  const k = KEY[m];
  const out: { win: number; lose: number; file: string }[] = [];
  for (const r of rows) {
    const w = (r.vals[r.W] as any)[k], l = (r.vals[r.L] as any)[k];
    if (w === null || l === null) continue;
    out.push({ win: w, lose: l, file: r.file });
  }
  return out;
}

export const auc = (P: { win: number; lose: number }[]) => {
  const wins = P.filter(p => p.win > p.lose).length, ties = P.filter(p => p.win === p.lose).length;
  return { wins, ties, losses: P.length - wins - ties, n: P.length, auc: 100 * (wins + 0.5 * ties) / P.length };
};
