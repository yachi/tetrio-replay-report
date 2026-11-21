/**
 * The 意外 T-spin (accidental TSD / TST) technique profile for `technique-facts.ts`, yachi's request
 * (「Add 中盤，accidental tsd tst」, with a phone video of one of each). Data only; the variants are the gated
 * transcription `pipeline/openers/accidental-technique.json`.
 *
 * NO WINDOW. The rule (yachi: 「打完一個T-spin,佢清行之前 TST 嗰四格係被蓋住嘅。清完之後,嗰四格啱啱變成一個
 * 露天嘅TST位。再加多一粒就即食tst」) is one variant, `tst`, `window_basis: spin_rule`, so the profile's `detect`
 * decides, and it reads the round's locks from the previous T-spin to the TST: the TST's cells were covered before that
 * T-spin, its clear opens at least one of the slot's columns to the sky, pieces placed after it roof that column, and
 * the next T fires the TST. The slot itself (the T rows and the row under them, the T's columns and one each side) must
 * already be complete right after that clear: only the roof is added (yachi, 2026-11-21: 「影片食完tst ,擺完頂就食得，
 * 唔洗點砌，啲examples 要砌好多，唔算」). (A stricter reading, the whole slot roofless and one piece over the nub, failed
 * the video's own pair.) The video's own TSD is the T-spin
 * before its TST. What makes a hit accidental is also the qualify hook (`accidental-qualify.ts`): mid-game, no other
 * page's window, no opener route. No payoff and no follow-up: the hit is the spin itself (`no_followup`).
 */
import type { TechniqueProfile } from './technique-profile.ts';
import type { TechDigest } from './technique-facts.ts';
import { OTHER_PAGES, accidentalQualifier } from './accidental-qualify.ts';
import { ROUTE_ARTEFACTS, ROUTE_LOCKS } from './basicdonating-qualify.ts';

const SIM = import.meta.dir;
const OPENERS = `${SIM}/../openers`;
const REPO = `${SIM}/../..`;
const TRANSCRIPTION = `${OPENERS}/accidental-technique.json`;

const H = 40, W = 10;

/** each ablation drops one clause of the rule, at the opportunity (a full TST): `no_next_t` lets a T lock between the
 *  two spins, `no_exposed` drops "covered before i's clear", `no_access` drops "a T column opened to the sky by
 *  i's clear", `no_new_roof` drops "that column roofed by a piece placed after i", `no_slot_built` drops "the slot
 *  box already complete right after i's clear" */
export const ACCIDENTAL_ABLATIONS = ['no_next_t', 'no_exposed', 'no_access', 'no_new_roof', 'no_slot_built'];

/** row r of the board before a lock that clears `cleared`: the row it was before the clear (-1: a row the clear
 *  brought in empty at the top) */
const keptIdxOf = (cleared: number[]) => {
  const cl = new Set(cleared);
  const k: number[] = [];
  for (let r = 0; r < H; r++) if (!cl.has(r)) k.push(r);
  while (k.length < H) k.unshift(-1);
  return k;
};

type C = { row: number; col: number };
/** every cell is empty or one of `cells` all the way up its column */
const openToSky = (b: string[][], cells: C[]) => cells.every(c => {
  for (let r = 0; r < c.row; r++) if (b[r]![c.col] !== '.' && !cells.some(t => t.row === r && t.col === c.col)) return false;
  return true;
});

/** The rule, at a full TST at lock j (`jx`): the previous T-spin i of the round cleared lines; no T locks between them;
 *  j's four T cells, mapped back through every clear and garbage insertion between, are rows that stood after i's clear
 *  (none is a new row) and empty right after it, and were covered before it (exposed: a filled cell over them, or a
 *  row i cleared, or a cell i's own T filled); ACCESS: the top T cell of at least one of j's columns is open to the sky
 *  right after i's clear; ROOF: over at least one such column, the lowest filled cell above the T before j was placed
 *  by a piece after i (any number of roof pieces); SLOT BUILT: every filled cell before j in the slot box (the T rows and
 *  the row under them, the T's columns and one each side) stood there right after i's clear, so nothing between i and j
 *  built the slot, only the roof above it. Every lock from i to j-1 must
 *  pass its row-map check. The box (full width, two rows above the T to one under it) is display only. */
export function accidentalDetect(d: TechDigest, jx: number, _withT: unknown, T: C[], rows: number[], abl?: string,
                                 variant?: string) {
  if (variant !== 'tst') throw new Error(`accidental: unknown variant ${variant}`);
  if (rows.length !== 3) return null;
  const q = d.tspins.findIndex(t => t.i === jx);
  if (q < 1) return null;
  const ti = d.tspins[q - 1]!, tj = d.tspins[q]!, i = ti.i, j = jx;
  const li = d.locks[i]!;
  if (li.cleared === 0) return null;
  for (let k = i; k < j; k++) if (!d.locks[k]!.mapOk) return null;
  if (abl !== 'no_next_t' && d.locks.slice(i + 1, j).some(l => l.piece === 'T')) return null;
  // a row of the board before j, back to the board right after i's clear (before i's garbage); -1 for a row that is
  // garbage or came in empty after i's clear
  const back = (r0: number) => {
    let r = r0;
    for (let k = j - 1; k > i; k--) {
      const l = d.locks[k]!;
      if (r >= H - l.garbage) return -1;
      r = keptIdxOf(l.clearedRows)[r + l.garbage]!;
      if (r < 0) return -1;
    }
    if (r >= H - li.garbage) return -1;
    return r + li.garbage;
  };
  const g = ti.board.map(s => s.split(''));
  for (const c of li.cells) g[c.row]![c.col] = 'T';
  const kiI = keptIdxOf(li.clearedRows);
  const kept = kiI.map(r => r < 0 ? Array(W).fill('.') : g[r]!.slice());
  const mT = T.map(c => ({ row: back(c.row), col: c.col }));
  if (mT.some(c => c.row < 0)) return null;
  if (!mT.every(c => kept[c.row]![c.col] === '.')) return null;
  const pre = mT.map(c => ({ row: kiI[c.row]!, col: c.col }));
  // a row i's own clear brought in empty is a new row too
  if (pre.some(c => c.row < 0)) return null;
  const exposed = !openToSky(g, pre) || pre.some(c => g[c.row]![c.col] !== '.');
  if (abl !== 'no_exposed' && !exposed) return null;
  // which lock after i owns each cell of the board before j
  const fwd = (k: number, c: C) => {
    let r = c.row;
    for (let m = k; m < j; m++) {
      const l = d.locks[m]!;
      if (l.clearedRows.includes(r)) return -1;
      r += l.clearedRows.filter(x => x > r).length;
      r -= l.garbage;
      if (r < 0) return -1;
    }
    return r;
  };
  const own = new Map<string, number>();
  for (let k = i + 1; k < j; k++) for (const c of d.locks[k]!.cells) {
    const r = fwd(k, c);
    if (r >= 0) own.set(`${r},${c.col}`, k);
  }
  // the top T cell of each of j's columns; ACCESS: at least one of them is open to the sky right after i's clear
  const tops = T.filter(c => !T.some(t => t.col === c.col && t.row < c.row));
  const opened = tops.filter(c => openToSky(kept, [{ row: back(c.row), col: c.col }]));
  const access = abl === 'no_access' ? tops : opened;
  if (access.length === 0) return null;
  // ROOF: over such a column, the lowest filled cell above the T before j was placed after i
  const bj = tj.board;
  const roofs = new Set<number>();
  for (const c of access) for (let r = c.row - 1; r >= 0; r--) {
    if (bj[r]![c.col] === '.') continue;
    const k = own.get(`${r},${c.col}`);
    if (k !== undefined) roofs.add(k);
    break;
  }
  if (abl !== 'no_new_roof' && roofs.size === 0) return null;
  const rs = T.map(c => c.row);
  const r0 = Math.min(...rs), r1 = Math.max(...rs);
  // SLOT BUILT (yachi: 「擺完頂就食得，唔洗點砌」): the slot box, the T rows and the row under them, the T's columns
  // and one each side, was already complete right after i's clear: every filled cell of it before j stood there then
  if (abl !== 'no_slot_built') {
    const cs = T.map(c => c.col);
    const c0 = Math.max(0, Math.min(...cs) - 1), c1 = Math.min(W - 1, Math.max(...cs) + 1);
    for (let r = r0; r <= Math.min(H - 1, r1 + 1); r++) for (let c = c0; c <= c1; c++) {
      if (bj[r]![c] === '.' || T.some(t => t.row === r && t.col === c)) continue;
      const mr = back(r);
      if (mr < 0 || kept[mr]![c] === '.') return null;
    }
  }
  return { columns: [], box: { rows: [Math.max(0, r0 - 2), Math.min(H - 1, r1 + 1)] as [number, number],
                               cols: [0, W - 1] as [number, number] },
           rule: { prev_spin_lock: i, roof_locks: [...roofs].sort((a, b) => a - b) } };
}

const tag = (h: any) => `lock ${h.lock} ${h.variant}`;

export const ACCIDENTAL: TechniqueProfile = {
  key: 'accidental',
  tag: 'accidental',
  transcriptionPath: TRANSCRIPTION,
  artefactPath: `${REPO}/analysis/accidental-facts.json`,
  hashFiles: {
    classifier: [`${SIM}/technique-facts.ts`, `${SIM}/technique-profile.ts`, `${SIM}/technique-profile-accidental.ts`,
                 `${SIM}/emit-technique-facts.ts`, `${SIM}/route-facts.ts`, `${SIM}/accidental-qualify.ts`,
                 `${SIM}/basicdonating-qualify.ts`,
                 ...OTHER_PAGES.map(k => `${OPENERS}/${k}-technique.json`),
                 ...ROUTE_ARTEFACTS.map(k => `${REPO}/analysis/${k}-facts.json`)],
  },
  opportunity: { spin: 'full', lines: 3 },
  controlSpins: [
    { name: 'TSD', kind: { spin: 'full', lines: 2 } },
    { name: 'TSS', kind: { spin: 'full', lines: 1 } },
    { name: 'mini_TSS', kind: { spin: 'mini', lines: 1 } },
    { name: 'mini_TSD', kind: { spin: 'mini', lines: 2 } },
  ],
  anchor: 'spin_t_cells',
  detect: { ablations: ACCIDENTAL_ABLATIONS, match: accidentalDetect as any },
  garbage: 'filled',
  artefact: {
    schema: 'technique-facts/1',
    means: 'For every scored T-spin in the corpus (a T with an engine spin credit that cleared lines, inside '
      + 'the verified prefix, passing the reconstruction check), whether it was a full T-spin Triple whose slot the '
      + 'previous T-spin\'s clear left complete and opened to the sky in at least one column, pieces placed after it only roofing it (variant tst), and, through qualify, whether '
      + 'no technique page and no opener route owns it: an accidental T-spin (意外 T-spin, yachi\'s 「accidental tsd tst」).',
    notEligible: 'simulator output: which T-spin a lock was is read off the vendored Triangle '
      + 'engine\'s boards, and nothing on the corpus side has a second implementation of it. No claim id, '
      + 'no badge, no figure in a report.',
    caveat: 'the page is defined by exclusion: a hit qualifies when no other page\'s window fires at its T and no opener '
      + 'route reaches it, so a page added later moves its count. Garbage is read as FILLED. The rule reads the T\'s cells '
      + 'mapped back to the board after the previous T-spin, and who placed the lowest filled cell over an opened T column; the box (full width, '
      + 'two rows above the T to one under it) is drawn and read for garbage_in_window only, never as a shape. Counts '
      + 'only, always N / M with the denominator.',
  },
  rules: () => [
    'opportunity: a full TST (3 lines) at a 0-based lock index <= the verified index, whose board-before plus its cells '
      + 'makes exactly the rows the engine recorded clearing (the reconstruction check, counted exactly as '
      + 'opener-facts.json donation.check counts it)',
    'match (no window): the previous T-spin i of the round cleared at least one line; no T locks between i and the TST j; '
      + 'every lock from i to j-1 passes its row-map check; j\'s four T cells, mapped back through every clear and '
      + 'garbage insertion, land on rows that stood after i\'s clear, and are empty there '
      + 'and covered before it (a filled cell over them, a row i cleared, or i\'s own T); the top T cell of at least one of '
      + 'j\'s columns is open to the sky right after i\'s clear (access), and over at least one such column the lowest '
      + 'filled cell before j was placed after i (the roof; any number of pieces); every filled cell before j in the slot box '
      + '(the T rows and the row under them, the T\'s columns and one each side) stood there right after i\'s clear, so '
      + 'only the roof is built between the two spins (slot built). No gap cap. The box is display only',
    'no follow-up and no payoff: the hit is the spin itself (no_followup)',
    'controls: the same rule at the profile\'s other scored spins; ablations no_next_t, no_exposed, no_access, '
      + 'no_new_roof and no_slot_built each drop one clause, at the opportunity; orientation_baseline = opportunities whose T is stood up',
  ],
  qualify: {
    rules: [
      'in_opener: the T locks inside the opener window (0-based lock <= WINDOW_PIECES); the page is mid-game only',
      `other_page: another technique page's window (${OTHER_PAGES.join(', ')}; any variant clearing the same rows, either hand) fires at the same T, so the T is that page's; 基本的なドネイト is not read`,
      `opener_route: the round is a case of an opener route page (${ROUTE_ARTEFACTS.join(', ')}) that matched a bag-2 board, and the T locks within ${ROUTE_LOCKS} locks after that match, so the T is the route's own continuation`,
      'opener_spin: the T is the bag-1 T-spin an opener route page draws (bag1.spin of a case in the same artefacts)',
      'qualifies iff none applies; the spin happened at every hit either way',
    ],
    check: accidentalQualifier(OPENERS, `${REPO}/analysis`),
  },
  lists: (hits, name) => ({
    accidental_hits: hits.map(h => `${name(h)} ${tag(h)}`),
    accidental_qualified: hits.filter(h => h.qualifies).map(h => `${name(h)} ${tag(h)}`),
    garbage_in_window: hits.filter(h => h.garbage_in_window).map(h => `${name(h)} lock ${h.lock}`),
  }),
};
