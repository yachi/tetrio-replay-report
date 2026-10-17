/**
 * What one mid-game technique page hands the shared CONSTRUCTED-DEMO planner (`technique-demos.ts`).
 * Types only. It is a file of its own, not a field of `TechniqueProfile` (`technique-profile.ts`),
 * because that file and the technique's profile are hashed by the corpus artefact's `emitter_md5`:
 * a demo-only edit must never stale the corpus artefact, and the other way round.
 *
 * A demo starts from an EMPTY board, as every decoder in this repo does (the TS one, the page's
 * Python one and the inlined player). The page's terrain is therefore BUILT from real pieces the
 * planner chooses, never seeded: the drawing's grey cells are ours, and the artefact says so.
 */
export interface TechniqueDemoProfile {
  key: string;
  tag: string;
  transcriptionPath: string;
  artefactPath: string;
  /** the files `planner_md5` hashes: an edit to any of them stales the demo artefact */
  hashFiles: { planner: string[] };
  /** the variant whose stood T every demo fires (STSD: `stsd`) */
  variant: string;
  /** one demo per entry: the page's build board (its grey terrain under the page's own pieces), and
   *  the terrain board whose grey cells the planner builds first. A chain the planner cannot build is
   *  published as unbuilt with the planner's measured reason, never dropped */
  chains: { node: string; terrain: string }[];
  /** boards no demo can stand on, with the reason (garbage cannot be dealt in a constructed demo) */
  unbuilt: Record<string, string>;
  artefact: { schema: string; means: string; notEligible: string; caveat: string };
  rules(): string[];
}
