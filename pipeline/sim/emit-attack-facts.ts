/**
 * Where each player's attack comes from — per clear type, per window, per attack component.
 *
 *   REPLAY_DIR=sessions/2026-10-09 bun pipeline/sim/emit-attack-facts.ts \
 *     --out sessions/2026-10-09/sim/attack-facts.json
 *
 * Every player-round is re-run through the vendored Triangle engine (byte-identical to @haelp/teto)
 * and every lock's `res.rawGarbage` is read. That field is the attack BEFORE the engine cancels it
 * against incoming garbage, i.e. the quantity the replay's `results.stats.garbage.attack` counts —
 * NOT `oracle-source.ts`'s `records[].attack`, which is `res.garbage` after the cancel loop and
 * sums to about 80% of the replay's total. Using the post-cancel field makes a T-spin Triple look
 * worth 4.9 lines instead of 6.1, so the choice is not cosmetic.
 *
 * TWO ANCHORS, the denominator-anchor route the opener section already uses:
 *   - attack: the engine's per-round sum of `rawGarbage` against the replay's own attack counter.
 *   - counts: the engine's per-round clear-type counts against the replay's own `clears.*`
 *     counters, every kind (singles to quads, the T-spin kinds, the minis). Both counters are read
 *     out of the `.ttrm` by `extract.py` and `extract2.ts` independently, so where the anchor
 *     agrees, the COUNT columns are as trustworthy as facts.json. Which clear CARRIED how much
 *     attack, and the base/B2B/combo split, have no second implementation: they stay quarantined,
 *     which is why the artefact says `report_eligible: false`.
 *
 * Denominators are the replay's `piecesplaced`, never the engine's lock count — the two differ in
 * a handful of rounds where the engine locks one or two pieces past the game's end (named in the
 * test). A window's pieces are `min(pieces, WINDOW_PIECES)` and the rest; a lock is in the opener
 * window when its 1-based index is at most WINDOW_PIECES, so a lock past `pieces` lands in `mid`.
 *
 * The artefact carries THIS SESSION's counts only. Corpus figures are rolled up by
 * `analysis/app_decomposition.py` from all of these, because a per-session file cannot see the
 * other sessions and so has no way to check a corpus figure (the `29-34%` lesson in CLAUDE.md).
 */
import { writeFileSync } from 'node:fs';
import { basename } from 'node:path';
import { loadCases, replayDir, type Case } from './verified-prefix.ts';
import { createEngine } from './vendor/teto/create-engine.mjs';
import { TL_DEFAULTS } from './oracle-source.ts';
import { WINDOW_PIECES } from './opener-window.ts';

/** Clear classes, in print order, each with the replay counter that anchors its count and the
 *  TETR.IO base attack (Triangle `damageCalc`; tetris.wiki/Garbage). */
export const CLASSES = [
  { key: 'S', counter: 'singles', base: 0 },
  { key: 'D', counter: 'doubles', base: 1 },
  { key: 'T', counter: 'triples', base: 2 },
  { key: 'Q', counter: 'quads', base: 4 },
  { key: 'TSS', counter: 'tspinsingles', base: 2 },
  { key: 'TSD', counter: 'tspindoubles', base: 4 },
  { key: 'TST', counter: 'tspintriples', base: 6 },
  { key: 'mTSS', counter: 'minitspinsingles', base: 0 },
  { key: 'mTSD', counter: 'minitspindoubles', base: 1 },
] as const;
export type ClassKey = typeof CLASSES[number]['key'];
const BASE: Record<string, number> = Object.fromEntries(CLASSES.map(c => [c.key, c.base]));

/** A lock's class from the engine's own lines + spin. Anything outside CLASSES (a penta, a mini
 *  triple, a T-spin quad) THROWS: no such clear exists in this corpus, and folding one into a
 *  neighbouring class would be the `?? 0` defect with a different spelling. */
export function classify(lines: number, spin: string): ClassKey {
  const full = spin === 'normal' || spin === 'full';
  const k = full ? (['', 'TSS', 'TSD', 'TST'][lines])
    : spin === 'mini' ? (['', 'mTSS', 'mTSD'][lines])
    : (['', 'S', 'D', 'T', 'Q'][lines]);
  if (!k) throw new Error(`emit-attack-facts: unclassifiable clear (lines ${lines}, spin ${spin})`);
  return k as ClassKey;
}

/** TETR.IO's back-to-back level (skysomorphic/tetrio-attack-calculator `b2bCountToLevel`) — the
 *  same table `sim.ts`'s `b2bLevel` pins; duplicated here only as the INTEGER model the component
 *  split is measured against, and the engine's own value always wins (see `residual`). */
function b2bLevel(b: number): number {
  for (const [t, l] of [[0, 0], [2, 1], [7, 2], [23, 3], [66, 4], [184, 5], [503, 6], [1369, 7]] as const)
    if (b <= t) return l;
  return 8;
}

export type Components = { base: number; b2b: number; combo: number; allclear: number; residual: number };
const zeroComponents = (): Components => ({ base: 0, b2b: 0, combo: 0, allclear: 0, residual: 0 });

/**
 * One clear's attack split into parts that SUM to the engine's value exactly. base, b2b and combo
 * follow the integer formula; `allclear` is the Perfect Clear's own garbage entry (the engine
 * appends it last); `residual` is whatever the engine sent beyond that model — the garbage
 * multiplier past `garbagemargin`, and the engine's fractional `log1p(b2b·0.8)` level surviving
 * the combo multiplier before the floor. It is printed as its own column so the parts add up to a
 * measured total rather than to a model of it.
 */
export function split(cls: ClassKey, lines: number, b2b: number, combo: number, raw: number, pc: number): Components {
  const line = raw - pc;
  if (lines === 0) return { ...zeroComponents(), allclear: pc, residual: line };
  const base = BASE[cls]!;
  const difficult = lines >= 4 || cls.startsWith('TS') || cls.startsWith('mTS');
  const b = difficult && b2b > 0 ? b2bLevel(b2b) : 0;
  let a = base + b;
  if (combo > 0) a = a === 0 ? Math.floor(Math.log1p(combo * 1.25)) : Math.floor(a * (1 + 0.25 * combo));
  return { base, b2b: b, combo: a - base - b, allclear: pc, residual: line - a };
}

type ClassCell = { n: number; attack: number };
type Window = { pieces: number; attack: number; lines: number; classes: Record<string, ClassCell>; components: Components };
const emptyWindow = (): Window => ({
  pieces: 0, attack: 0, lines: 0,
  classes: Object.fromEntries(CLASSES.map(c => [c.key, { n: 0, attack: 0 }])), components: zeroComponents(),
});

/** One player-round through the engine: every lock's raw attack, class and components. */
export function runRound(c: Case) {
  const player = c.rawPlayer, o = player.replay.options;
  const players = c.rawRound!.map((p: any) => ({ gameid: p.replay.options.gameid, userid: p.id, username: p.username }));
  const eng: any = createEngine({ ...TL_DEFAULTS, ...o, g: o.g ?? TL_DEFAULTS.g }, o.gameid, players);
  const byFrame = new Map<number, any[]>();
  for (const e of player.replay.events) { if (!byFrame.has(e.frame)) byFrame.set(e.frame, []); byFrame.get(e.frame)!.push(e); }
  const locks: { i: number; cls: ClassKey | null; lines: number; raw: number; parts: Components }[] = [];
  eng.events.on('falling.lock', (res: any) => {
    const i = locks.length + 1;
    const g = (res.rawGarbage ?? []) as number[];
    const raw = g.reduce((a, b) => a + b, 0);
    if (res.surge) throw new Error(`emit-attack-facts: surge in ${c.file} r${c.round} — b2bcharging is assumed off`);
    if (res.lines === 0) {
      if (raw !== 0) throw new Error(`emit-attack-facts: attack without a clear in ${c.file} r${c.round} lock ${i}`);
      locks.push({ i, cls: null, lines: 0, raw: 0, parts: zeroComponents() });
      return;
    }
    const cls = classify(res.lines, res.spin);
    const pc = eng.board.perfectClear ? g[g.length - 1]! : 0;
    const st = res.stats;
    locks.push({ i, cls, lines: res.lines, raw, parts: split(cls, res.lines, Math.max(st.b2b, 0), Math.max(st.combo, 0), raw, pc) });
  });
  const maxF = player.replay.frames ?? 20000;
  try { for (let f = 0; f <= maxF; f++) { const r = eng.tick(byFrame.get(f) || []); if (r && r.topout) break; } } catch { /* topout */ }
  return locks;
}

export function build(dir: string) {
  const anchorAttack = { rounds: 0, agree: 0, exceptions: [] as any[] };
  const anchorCounts = { rounds: 0, agree: 0, unknown: 0, exceptions: [] as any[] };
  const lockExtra: any[] = [];
  const P: Record<string, any> = {};
  const M: Record<string, any> = {};
  for (const c of loadCases(dir)) {
    const st = c.rawPlayer.replay.results.stats;
    const pieces = st.piecesplaced as number, replayAtk = st.garbage.attack as number;
    if (!Number.isInteger(pieces) || !Number.isInteger(replayAtk))
      throw new Error(`emit-attack-facts: ${c.file} r${c.round} ${c.user} has no piecesplaced/garbage.attack`);
    const locks = runRound(c);
    const engAtk = locks.reduce((a, l) => a + l.raw, 0);
    anchorAttack.rounds++;
    if (engAtk === replayAtk) anchorAttack.agree++;
    else anchorAttack.exceptions.push({ file: c.file, round: c.round, user: c.user, engine: engAtk, replay: replayAtk });
    if (locks.length !== pieces) lockExtra.push({ file: c.file, round: c.round, user: c.user, locks: locks.length, pieces });

    // count anchor: every class against its replay counter. A missing counter is UNKNOWN, never 0.
    anchorCounts.rounds++;
    const present = CLASSES.every(k => typeof c.clears[k.counter] === 'number');
    if (!present) anchorCounts.unknown++;
    else {
      const diff: Record<string, [number, number]> = {};
      for (const k of CLASSES) {
        const sim = locks.filter(l => l.cls === k.key).length, real = c.clears[k.counter]!;
        if (sim !== real) diff[k.key] = [sim, real];
      }
      if (Object.keys(diff).length === 0) anchorCounts.agree++;
      else anchorCounts.exceptions.push({ file: c.file, round: c.round, user: c.user, engine_vs_replay: diff });
    }

    const p = (P[c.user] ??= { user: c.user, rounds: 0, pieces: 0, attack: 0, lines: 0,
                                windows: { opener: emptyWindow(), mid: emptyWindow() } });
    p.rounds++; p.pieces += pieces; p.attack += replayAtk; p.lines += st.lines as number;
    const op = Math.min(pieces, WINDOW_PIECES);
    p.windows.opener.pieces += op; p.windows.mid.pieces += pieces - op;
    const m = (M[`${c.file}|${c.user}`] ??= { file: c.file, user: c.user, pieces: 0, attack: 0,
                                             opener_pieces: 0, opener_attack: 0,
                                             n: Object.fromEntries(CLASSES.map(k => [k.key, 0])) });
    m.pieces += pieces; m.attack += replayAtk; m.opener_pieces += op;
    for (const l of locks) {
      const w: Window = l.i <= WINDOW_PIECES ? p.windows.opener : p.windows.mid;
      if (l.i <= WINDOW_PIECES) m.opener_attack += l.raw;
      w.attack += l.raw; w.lines += l.lines;
      for (const k of Object.keys(l.parts) as (keyof Components)[]) w.components[k] += l.parts[k];
      if (l.cls) { w.classes[l.cls]!.n++; w.classes[l.cls]!.attack += l.raw; m.n[l.cls]++; }
    }
  }
  const byUser = (a: { user: string }, b: { user: string }) => a.user < b.user ? -1 : a.user > b.user ? 1 : 0;
  return {
    schema: 'attack-facts/1',
    session: basename(dir),
    report_eligible: false,
    source: 'vendored Triangle engine (pipeline/sim/vendor/teto), res.rawGarbage per lock — attack before cancellation',
    window_pieces: WINDOW_PIECES,
    classes: CLASSES.map(k => ({ key: k.key, replay_counter: k.counter, base: k.base })),
    denominators: 'pieces = results.stats.piecesplaced (the replay\'s, never the engine lock count); '
      + 'opener pieces = min(pieces, window_pieces) per round, mid = the rest; players[].attack is the '
      + 'replay\'s garbage.attack, windows[].attack is the engine\'s and differs from it only in '
      + 'anchor.attack.exceptions',
    components_mean: 'base = TETR.IO table value; b2b = integer back-to-back level; combo = the combo '
      + 'multiplier\'s addition; allclear = the Perfect Clear\'s own garbage entry; residual = engine '
      + 'attack beyond that integer model (garbage multiplier past garbagemargin, fractional b2b level). '
      + 'The five sum to the engine attack exactly.',
    not_eligible_because: [
      'attack per clear and its component split come from one engine with no second implementation',
    ],
    anchor: {
      attack: anchorAttack,
      counts: anchorCounts,
      engine_locks_past_game_end: lockExtra,
    },
    players: Object.values(P).sort(byUser),
    per_match: Object.values(M).sort((a, b) => a.file < b.file ? -1 : a.file > b.file ? 1 : byUser(a, b)),
  };
}

export const serialise = (x: unknown) => JSON.stringify(x, null, 1) + '\n';

if (import.meta.main) {
  const outIx = process.argv.indexOf('--out');
  const dir = replayDir();
  const out = build(dir);
  if (outIx > 0) writeFileSync(process.argv[outIx + 1]!, serialise(out));
  const a = out.anchor;
  console.log(`${out.session}: attack anchor ${a.attack.agree}/${a.attack.rounds}, `
    + `count anchor ${a.counts.agree}/${a.counts.rounds} (unknown ${a.counts.unknown}), `
    + `engine locks past game end ${a.engine_locks_past_game_end.length}`);
  for (const e of [...a.attack.exceptions, ...a.counts.exceptions]) console.log('  exception', JSON.stringify(e));
}
