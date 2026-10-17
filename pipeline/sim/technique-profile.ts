/**
 * What one shiwehi.com MID-GAME TECHNIQUE page (STSD, …) hands the shared technique matcher
 * (`technique-facts.ts`). Types only, like `route-profile.ts` is for the route pages: every RULE is
 * in the matcher, once; a profile is data (which spins are opportunities, which strings the artefact
 * carries, which named lists it publishes, which files its hash covers). The SHAPES — the window,
 * the T cells, the follow-up slot — are not here either: they live in the technique's transcription
 * JSON, gated by `technique_transcription.py`, so the matcher reads exactly what the gate checked.
 *
 * Adding a Phase 1 technique whose shape this window predicate can express is: a transcription
 * (`extract_<x>_shapes.py` + JSON), a profile file, one line in `techniques.ts`, a test. A technique
 * it cannot express (a staircase over several locks) needs a new `anchor` value, which is an edit to
 * `technique-facts.ts` — hashed by every technique artefact, so it moves every one of their
 * `emitter_md5` lines, loudly, and that is the cost to name when it happens.
 */

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
  /** the opportunity: the scored spin each variant is measured at (STSD: a full TSD) */
  opportunity: SpinKind;
  /** the controls: the same window at these other scored spins (a shape that fires more under the
   *  spin it is not about is a shape test) */
  controlSpins: { name: string; kind: SpinKind }[];
  /** how the window is placed. Only `spin_t_cells` exists: the lock's cells equal the variant's
   *  T cells under one translation */
  anchor: 'spin_t_cells';
  /** how a garbage cell reads inside the window. Only `filled` exists */
  garbage: 'filled';
  artefact: { schema: string; means: string; notEligible: string; caveat: string };
  rules(): string[];
  /** the profile's named lists, from the hits; `name` is the shared `session mXrY player` prefix */
  lists(hits: any[], name: (h: any) => string): Record<string, string[]>;
}
