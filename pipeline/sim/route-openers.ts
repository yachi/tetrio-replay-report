/**
 * The opener route profiles by `--opener` key: the one table the route CLIs read. Adding an opener
 * is a profile file and one line here; nothing else names the openers.
 */
import type { RouteProfile } from './route-profile.ts';
import { MEISOU } from './route-profile-meisou.ts';
import { HONEYCUP } from './route-profile-honeycup.ts';
import { MOUNTAINOUS2 } from './route-profile-mountainous2.ts';
import { STICKSPIN } from './route-profile-stickspin.ts';
import { GAMUSHIRO } from './route-profile-gamushiro.ts';
import { SDPCSPIN } from './route-profile-sdpcspin.ts';
import { HDGAMUSHIRO } from './route-profile-hdgamushiro.ts';

export const OPENERS: Record<string, RouteProfile> = { meisou: MEISOU, honeycup: HONEYCUP, mountainous2: MOUNTAINOUS2,
                                                   stickspin: STICKSPIN, gamushiro: GAMUSHIRO,
                                                   sdpcspin: SDPCSPIN, hdgamushiro: HDGAMUSHIRO };

/** `--opener <key>` out of argv, or a loud failure naming the keys there are. */
export function openerFromArgv(argv: string[]): RouteProfile {
  const ix = argv.indexOf('--opener');
  const key = ix > 0 ? argv[ix + 1] : undefined;
  const P = key ? OPENERS[key] : undefined;
  if (!P) throw new Error(`--opener must be one of ${Object.keys(OPENERS).join(', ')} (got ${key ?? 'nothing'})`);
  return P;
}
