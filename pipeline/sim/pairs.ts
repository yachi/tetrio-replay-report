/**
 * Per-round paired observations: winner's value vs loser's value, for each forecast metric.
 *
 * Extracted from auc.ts so the AUC report and the power analysis run off ONE pairing
 * implementation. Simulating 158 rounds twice over takes ~2 minutes, so results are cached to
 * pairs-cache.json keyed by the rule; delete that file to force a re-run.
 */
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { forecastMetric } from './forecast.ts';
import { loadCases, runCase, verifiedIndex, replayDir} from './verified-prefix.ts';

export const METRICS = ['forecast rate', 'forecast per piece', 'forecast count', 'tucked T-spins',
                        'separation-weighted'] as const;
export type Metric = (typeof METRICS)[number];
const KEY: Record<Metric, string> = {
  'forecast rate': 'rate', 'forecast per piece': 'perPiece',
  'forecast count': 'fc', 'tucked T-spins': 'n', 'separation-weighted': 'sepw',
};

export interface Row {
  file: string; round: number; W: string; L: string;
  vals: Record<string, { alive: boolean; n: number; fc: number; rate: number | null;
                         perPiece: number | null; sepw: number | null; verified: number }>;
}

/** `strict` is the forecast RULE (strict vs loose T-spin classification).
 *  `strictRows` is the verified-prefix GATE (whether the ige row oracle must agree). */
export function collectRows(strict = true, strictRows = true): Row[] {
  // Bump CACHE_V whenever the row shape or the sim settings change. A stale cache silently
  // yields rows missing the new field, which read as undefined and score as TIES — the
  // separation-weighted metric first appeared as 0 decided / 79 ties for exactly that reason.
  const CACHE_V = 4;
  // The REPLAY DIRECTORY is part of the key. It was not, and the cache is a single file
  // beside the code rather than beside the session, so one run with REPLAY_DIR pointed at
  // another session would have written that session's rows under this one's key — and the
  // next 2026-07-22 run would have read them back as its own, silently. Nothing consumed
  // this from more than one session until the metric was extended to all four, so the bug
  // was latent rather than harmless. Keyed, and CACHE_V bumped so every existing entry
  // (written without a directory) is discarded rather than matched by accident.
  const dir = replayDir();
  const cacheKey = `v${CACHE_V}|${strict}|rows=${strictRows}|dir=${resolve(dir)}`;
  const cache = `${import.meta.dir}/pairs-cache.json`;
  if (existsSync(cache)) {
    const c = JSON.parse(readFileSync(cache, 'utf8'));
    if (c[cacheKey]) return c[cacheKey] as Row[];
  }
  const rows: Row[] = [];
  const byRound = new Map<string, { file: string; round: number; vals: Row['vals'] }>();
  for (const c of loadCases()) {
    const r = runCase(c);
    const vIdx = verifiedIndex(r, c.truth, strictRows);
    const recs = vIdx < 0 ? [] : forecastMetric(r, strict).records.filter(x => x.lockIndex <= vIdx);
    const fcRecs = recs.filter(x => x.kind !== 'reactive');
    const fc = fcRecs.length;
    // Separation-weighted score. `forecast rate` is fc/n over a handful of T-spins, so it
    // lands on the same few rationals for both players and TIES 54% of pairs — ties are
    // scored as half a win, which drags AUC toward 50% regardless of effect size.
    // Weighting each forecast by how many pieces ahead the roof was set is both finer
    // grained (far fewer exact ties) and closer to the construct: a roof placed 8 pieces
    // before the T is stronger evidence of intent than one placed 1 piece before.
    const sepw = recs.length
      ? fcRecs.reduce((a, x) => a + Math.max(x.separation, 0), 0) / recs.length
      : null;
    const k = `${c.file}#${c.round}`;
    if (!byRound.has(k)) byRound.set(k, { file: c.file, round: c.round, vals: {} });
    byRound.get(k)!.vals[c.user] = { alive: c.alive, n: recs.length, fc,
      rate: recs.length ? fc / recs.length : null,
      perPiece: vIdx >= 0 ? fc / (vIdx + 1) : null, sepw, verified: vIdx + 1 };
  }
  for (const { file, round, vals } of byRound.values()) {
    const names = Object.keys(vals);
    if (names.length !== 2) continue;
    const [a, b] = names as [string, string];
    const W = vals[a]!.alive ? a : b, L = vals[a]!.alive ? b : a;
    if (vals[W]!.alive === vals[L]!.alive) continue;
    rows.push({ file, round, W, L, vals });
  }
  const prev = existsSync(cache) ? JSON.parse(readFileSync(cache, 'utf8')) : {};
  writeFileSync(cache, JSON.stringify({ ...prev, [cacheKey]: rows }));
  return rows;
}

/** Winner-vs-loser pairs for one metric, with the round they came from (for clustered resampling). */
export function pairsFor(rows: Row[], m: Metric): { win: number; lose: number; file: string }[] {
  const k = KEY[m];
  const out: { win: number; lose: number; file: string }[] = [];
  for (const r of rows) {
    const w = (r.vals[r.W] as any)[k], l = (r.vals[r.L] as any)[k];
    // == null catches undefined too: a missing field must never be scored as a tie
    if (w == null || l == null) continue;
    if (!Number.isFinite(w) || !Number.isFinite(l)) throw new Error(`non-finite ${m}: ${w} ${l}`);
    out.push({ win: w, lose: l, file: r.file });
  }
  return out;
}

export const auc = (P: { win: number; lose: number }[]) => {
  const wins = P.filter(p => p.win > p.lose).length, ties = P.filter(p => p.win === p.lose).length;
  return { wins, ties, losses: P.length - wins - ties, n: P.length, auc: 100 * (wins + 0.5 * ties) / P.length };
};

// Lanczos log-gamma, so the binomial tail below is exact enough at any n this corpus reaches.
const lgamma = (z: number): number => {
  const g = [676.5203681218851, -1259.1392167224028, 771.32342877765313, -176.61502916214059,
             12.507343278686905, -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7];
  if (z < 0.5) return Math.log(Math.PI / Math.sin(Math.PI * z)) - lgamma(1 - z);
  z -= 1; let x = 0.99999999999980993;
  for (let i = 0; i < g.length; i++) x += g[i]! / (z + i + 1);
  const t = z + g.length - 0.5;
  return 0.5 * Math.log(2 * Math.PI) + (z + 0.5) * Math.log(t) - t + Math.log(x);
};
const logC = (n: number, k: number) => lgamma(n + 1) - lgamma(k + 1) - lgamma(n - k + 1);
/** P(X >= k) for X ~ Binom(n, p). */
export const binomTail = (k: number, n: number, p: number) => {
  const pmf = (i: number) => p === 0 ? (i === 0 ? 1 : 0) : p === 1 ? (i === n ? 1 : 0)
    : Math.exp(logC(n, i) + i * Math.log(p) + (n - i) * Math.log(1 - p));
  let s = 0; for (let i = k; i <= n; i++) s += pmf(i); return s;
};

/**
 * Exact TWO-sided sign-test p on the decided pairs — the round-level p the report quotes.
 *
 * Lives here rather than in auc-power.ts because the emitter needs the same number, and a
 * second implementation of a published p-value is how two figures that must agree stop
 * agreeing. Same reason `pairsFor` is here: one pairing, every consumer.
 *
 * `null`, not NaN, when nothing was decided. A p-value over an empty sample does not exist,
 * and NaN has reached a printed figure in this repo before.
 */
export const exactSignP = (wins: number, losses: number): number | null => {
  const dec = wins + losses;
  if (dec === 0) return null;
  return Math.min(1, 2 * Math.min(binomTail(wins, dec, 0.5), binomTail(losses, dec, 0.5)));
};
