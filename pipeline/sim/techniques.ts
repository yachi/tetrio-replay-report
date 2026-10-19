/**
 * The mid-game technique profiles by `--technique` key: the one table the technique CLIs read
 * (the sibling of `route-openers.ts`). Adding a technique is a profile file and one line here.
 */
import type { TechniqueProfile } from './technique-profile.ts';
import type { CrossRoute } from './technique-facts.ts';
import { STSD } from './technique-profile-stsd.ts';
import { STMBCAVE } from './technique-profile-stmbcave.ts';
import { IMPERIALCROSS } from './technique-profile-imperialcross.ts';
import { DOUBLEDAGGER } from './technique-profile-doubledagger.ts';
import { BTCANNON } from './technique-profile-btcannon.ts';
import { CUTCOPY } from './technique-profile-cutcopy.ts';
import { SHACHIKUTRAIN } from './technique-profile-shachikutrain.ts';
import type { TechniqueDemoProfile } from './technique-demo-profile.ts';
import { STSD_DEMOS } from './technique-demos-stsd.ts';
import { STMBCAVE_DEMOS } from './technique-demos-stmbcave.ts';
import { IMPERIALCROSS_DEMOS } from './technique-demos-imperialcross.ts';
import { DOUBLEDAGGER_DEMOS } from './technique-demos-doubledagger.ts';
import { BTCANNON_DEMOS } from './technique-demos-btcannon.ts';
import { CUTCOPY_DEMOS } from './technique-demos-cutcopy.ts';
import { SHACHIKUTRAIN_DEMOS } from './technique-demos-shachikutrain.ts';

export const TECHNIQUES: Record<string, TechniqueProfile & { crossRoute?: CrossRoute }> = {
  stsd: STSD, stmbcave: STMBCAVE, imperialcross: IMPERIALCROSS, doubledagger: DOUBLEDAGGER, btcannon: BTCANNON,
  cutcopy: CUTCOPY, shachikutrain: SHACHIKUTRAIN,
};
/** each technique's constructed-demo half, by the same key */
export const TECHNIQUE_DEMOS: Record<string, TechniqueDemoProfile> = {
  stsd: STSD_DEMOS, stmbcave: STMBCAVE_DEMOS, imperialcross: IMPERIALCROSS_DEMOS,
  doubledagger: DOUBLEDAGGER_DEMOS, btcannon: BTCANNON_DEMOS, cutcopy: CUTCOPY_DEMOS,
  shachikutrain: SHACHIKUTRAIN_DEMOS,
};

/** `--technique <key>` out of argv, or a loud failure naming the keys there are. */
export function techniqueFromArgv(argv: string[]) {
  const ix = argv.indexOf('--technique');
  const key = ix > 0 ? argv[ix + 1] : undefined;
  const P = key ? TECHNIQUES[key] : undefined;
  if (!P) throw new Error(`--technique must be one of ${Object.keys(TECHNIQUES).join(', ')} (got ${key ?? 'nothing'})`);
  return P;
}
