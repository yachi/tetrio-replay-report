/**
 * What one shiwehi.com MID-GAME TECHNIQUE page (STSD, …) hands the shared technique matcher
 * (`technique-facts.ts`). Types only, like `route-profile.ts` is for the route pages: every RULE is
 * in the matcher, once; a profile is data (which spins are opportunities, which strings the artefact
 * carries, which named lists it publishes, which files its hash covers). The SHAPES — the window,
 * the T cells, the follow-up slot — are not here either: they live in the technique's transcription
 * JSON, gated by `technique_transcription.py`, so the matcher reads exactly what the gate checked.
 *
 * Adding a Phase 1 technique whose shape this window predicate can express is: a transcription
 * (`extract_<x>_shapes.py` + JSON), a profile file, one line in `techniques.ts`, a test. 階段のドネイト
 * (Kaidan) was guessed here to need "a staircase over several locks"; measured, it does not — its
 * shape sits in the rows the TSD clears and the two rows under them, all on one board at the TSD's lock
 * (the window counts no steps and cannot tell a staircase from a flat stack). A
 * technique it cannot express needs a new `anchor` value: アンカーセット (Anchor Set) is the live case, a
 * J or L placement with no T-spin, whose drawings agree on no rectangle holding both the anchor and the
 * overhang (ROADMAP.md). That is an edit to `technique-facts.ts` — hashed by every technique artefact,
 * so it moves every one of their `emitter_md5` lines, loudly, and that is the cost to name when it
 * happens.
 */

import type { Hit, TechDigest } from './technique-facts.ts';

/** Which T-spin, by the engine's own credit and line count. */
export interface SpinKind { spin: 'full' | 'mini'; lines: number }

export interface TechniqueProfile {
  /** the `--technique` key and the tag every error message carries */
  key: string;
  tag: string;
  /** the gated transcription (`*-technique.json`) and the artefact this profile emits */
  transcriptionPath: string;
  artefactPath: string;
  /** the files `emitter_md5` hashes: an edit to any of them stales the artefact */
  hashFiles: { classifier: string[] };
  /** the opportunity: the primary scored spin (STSD: a full TSD). A variant whose transcription names
   *  another spin (欄干's TSS) is measured at that spin instead, which must be a `controlSpins` entry;
   *  under that variant this opportunity is counted among the controls in its place */
  opportunity: SpinKind;
  /** the controls: the same window at these other scored spins (a shape that fires more under the
   *  spin it is not about is a shape test) */
  controlSpins: { name: string; kind: SpinKind }[];
  /** how the window is placed. Only `spin_t_cells` exists: the lock's cells equal the variant's
   *  T cells under one translation. A variant whose transcription says `window_basis: rule` has no window at all:
   *  `detect` decides (基本的なドネイト's donation rule, `basicdonating-rule.ts`) */
  anchor: 'spin_t_cells';
  /** required by a `rule` variant: whether the shape stood at one scored lock (the board before it with the lock's
   *  cells added, the lock's cells, the rows it clears), its thumbnail box and its payoff well; `abl` relaxes one
   *  clause for the controls, named in `ablations` */
  detect?: {
    ablations: string[];
    match(d: TechDigest, i: number, withT: boolean[][], cells: { row: number; col: number }[], rows: number[],
          abl?: string): { columns: { col: number; hole_row: number; depth: number; cover: string }[];
                           well: { r: number; c: number };
                           box: { rows: [number, number]; cols: [number, number] } } | null;
  };
  /** how a garbage cell reads inside the window. Only `filled` exists */
  garbage: 'filled';
  artefact: { schema: string; means: string; notEligible: string; caveat: string };
  rules(): string[];
  /** the profile's named lists, from the hits; `name` is the shared `session mXrY player` prefix */
  lists(hits: any[], name: (h: any) => string): Record<string, string[]>;
  /** optional: whether a hit was BUILT as the technique, beyond the shape standing (社畜トレイン's four rules,
   *  `shachikutrain-qualify.ts`). A profile without it emits exactly what it did before the hook existed */
  qualify?: { rules: string[]; check(h: Hit, d: TechDigest): { qualifies: boolean; not_qualified: string[] } };
}
