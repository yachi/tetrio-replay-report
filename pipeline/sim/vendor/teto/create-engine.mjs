// Standalone port of @haelp/teto Classes.Game.createEngine (classes/game/index.mjs), inlined so the
// board oracle constructs an Engine WITHOUT importing classes/game — which drags in Logger/Player/Self
// and, transitively, the 16 MB networking client. The option mapping is copied verbatim from upstream;
// keep it in sync when re-vendoring the engine. `flat` is the version-19 .ttrm `options` object merged
// over the TL defaults (see oracle-source.ts).
import { Engine } from "./engine/index.mjs";

// `date` is OPT-IN and defaults to the wall clock, exactly as before, so every existing caller is
// unchanged. The engine reads it twice (garbage-queue class at 2025-05-06, opener phase at 2025-02-16),
// so a replay-faithful caller should pass the replay's own timestamp rather than inherit today's.
export function createEngine(options, gameid, players, date = undefined) {
  return new Engine({
    multiplayer: {
      opponents: players.map((o) => o.gameid).filter((id) => id !== gameid),
      passthrough: options.passthrough,
    },
    board: { width: options.boardwidth, height: options.boardheight, buffer: 20 },
    kickTable: options.kickset,
    options: {
      comboTable: options.combotable, garbageBlocking: options.garbageblocking, clutch: options.clutch,
      garbageTargetBonus: options.garbagetargetbonus, spinBonuses: options.spinbonuses, stock: options.stock,
    },
    queue: { minLength: 31, seed: options.seed, type: options.bagtype },
    garbage: {
      cap: { absolute: options.garbageabsolutecap, increase: options.garbagecapincrease, max: options.garbagecapmax,
             value: options.garbagecap, marginTime: options.garbagecapmargin },
      multiplier: { value: options.garbagemultiplier, increase: options.garbageincrease, marginTime: options.garbagemargin },
      boardWidth: options.boardwidth,
      garbage: { speed: options.garbagespeed, holeSize: options.garbageholesize },
      messiness: { change: options.messiness_change, nosame: options.messiness_nosame, timeout: options.messiness_timeout,
                   within: options.messiness_inner, center: options.messiness_center ?? false },
      bombs: options.usebombs, seed: options.seed, rounding: options.roundmode,
      openerPhase: options.openerphase, specialBonus: options.garbagespecialbonus,
    },
    pc: options.allclears ? { garbage: options.allclear_garbage, b2b: options.allclear_b2b } : false,
    b2b: {
      chaining: options.b2bchaining,
      charging: options.b2bcharging ? { at: options.b2bcharge_at, base: options.b2bcharge_base } : false,
    },
    gravity: { value: options.g, increase: options.gincrease, marginTime: options.gmargin },
    misc: {
      movement: { infinite: options.infinite_movement, lockResets: options.lockresets, lockTime: options.locktime,
                  may20G: options.gravitymay20g ?? false },
      allowed: { spin180: options.allow180, hardDrop: options.allow_harddrop, hold: options.display_hold,
                 undo: options.can_undo, retry: options.can_retry },
      infiniteHold: options.infinite_hold, stride: options.stride, username: options.username, date: date ?? new Date(),
    },
    handling: options.handling,
  });
}
