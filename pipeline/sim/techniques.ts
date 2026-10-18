/**
 * The mid-game technique profiles by `--technique` key: the one table the technique CLIs read
 * (the sibling of `route-openers.ts`). Adding a technique is a profile file and one line here.
 */
import type { TechniqueProfile } from './technique-profile.ts';
import type { CrossRoute } from './technique-facts.ts';
import { STSD } from './technique-profile-stsd.ts';
import type { TechniqueDemoProfile } from './technique-demo-profile.ts';
import { STSD_DEMOS } from './technique-demos-stsd.ts';

export const TECHNIQUES: Record<string, TechniqueProfile & { crossRoute?: CrossRoute }> = { stsd: STSD };
/** each technique's constructed-demo half, by the same key */
export const TECHNIQUE_DEMOS: Record<string, TechniqueDemoProfile> = { stsd: STSD_DEMOS };

/** `--technique <key>` out of argv, or a loud failure naming the keys there are. */
export function techniqueFromArgv(argv: string[]) {
  const ix = argv.indexOf('--technique');
  const key = ix > 0 ? argv[ix + 1] : undefined;
  const P = key ? TECHNIQUES[key] : undefined;
  if (!P) throw new Error(`--technique must be one of ${Object.keys(TECHNIQUES).join(', ')} (got ${key ?? 'nothing'})`);
  return P;
}
