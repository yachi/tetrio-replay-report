# `cc-oracle` — the original cold-clear, hermetically

`pipeline/sim/cc-tslot.ts` is a hand port of cold-clear's six T-slot detectors, cross-checked against
our BFS over 7,544 corpus boards with 0 genuine disagreements. Its header has always carried the
caveat that it **has never been run against the Rust original**. Two readings of one source agreeing
is weaker than it looks: a misreading would sit on both sides of the comparison.

This packages the original so that check can be made, without a toolchain, a checkout or a `target/`
directory anywhere near the working tree.

```bash
nix build .#cc-oracle          # aarch64-darwin, ~1 min cold, seconds warm
./result/bin/cc-oracle < boards.txt
```

Input is **40 rows of 10 characters per board**, `.` empty and anything else filled, **top-down**
(row 0 is the top of the field, matching this repo). One JSON line out per board:

```
{"any":true,"hits":["tst_twist_right"],"lines":2}
```

`lines` is `cutout_tslot`'s line count — the max over the detected slots, i.e. the quantity
`bestTspinLines` computes on our side and the one the forecast metric consumes. `pipeline/sim/
cross-tslot-count.ts` differentials the two over the whole corpus; CI's `oracle-image` job runs it.

## Three things that were not obvious, all of which cost a build

**The detectors are private.** `mod standard;` is not `pub`, and every `detect_shape!` function plus
`cave_tslot`, `cutout_tslot` and `Cutout` are private. You cannot get at them by depending on the
crate. `expose-detectors.patch` adds `pub` in six places and changes no logic; keeping it as a pinned
patch against a pinned rev is deliberate, because a hand-edited clone drifts and cannot be reviewed.

**Upstream ships no `Cargo.lock`.** It is gitignored, so it is absent from the GitHub tarball, and a
plain `cargoHash` build fails with `No such file or directory: 'Cargo.lock'`. `Cargo.lock` here is
vendored for that reason — and it is what makes the build reproducible at all. Without it the
resolver picks whatever crates.io holds that day, so "the original Rust" would mean a different
program on every build.

**cold-clear is y-UP.** `Board::set_field` walks `y` ascending and records
`column_heights[x] = y + 1`, so its `field[0]` is the **bottom** row. The flip lives in
`cc-oracle.rs`, once. Getting it wrong does not error — every board reports no detections, which
reads as agreement rather than as a bug. It is the reason the smoke test below asserts a *positive*.

## Smoke test — an oracle that detects nothing agrees with everything

```
empty field                        -> {"any":false,"hits":[]}
a TSD our engine scores 2          -> {"any":true,"hits":["sky_tslot_right"]}
a corpus board our engine scores 3 -> {"any":true,"hits":["tst_twist_right"]}
```

Run this before trusting any differential result. The middle and last lines are the ones that matter.

## The workspace is trimmed

The root `Cargo.toml` is cut to `bot`, `libtetris` and `opening-book` by the same patch. That drops
five git dependencies the binary never touches (game-util-rs at two revs, gilrs, gilrs-core,
webutil), leaving two (`pcf`, `webutil`) in the lock and a much smaller vendor.

## Running it in a container instead — UNVERIFIED

The derivation above is native `aarch64-darwin` and needs no container: cold-clear is portable Rust
and builds on macOS in seconds. If you would rather it ran in a Linux container under
[nix-apple-container](https://github.com/halfwhey/nix-apple-container), the flake exposes an image
built from the `aarch64-linux` package:

```nix
{ inputs, ... }: {
  imports = [ inputs.nix-apple-container.darwinModules.default ];

  services.containerization = {
    enable = true;
    linux-builder.aarch64.enable = true;   # required to build the aarch64-linux package

    images.cc-oracle = inputs.tetrio-replay-report.packages.aarch64-darwin.cc-oracle-image;

    containers.cc-oracle = {
      image = "cc-oracle:latest";
      autoStart = false;                   # it is a filter, not a service
    };
  };
}
```

Rebuild twice — the first `darwin-rebuild switch` starts the builder, the second builds and loads the
image. Then pipe boards through `container run -i cc-oracle`.

**What is verified and what is not.** The derivation, the patch, the vendored lock, the trimmed
workspace and the smoke test above were all built and run on aarch64-darwin; `nix build .#cc-oracle`
produces a binary whose output is byte-identical to an ad-hoc `cargo build` of the same rev. The
container path was **not** run: it needs `darwin-rebuild switch` (root) and the Apple `container`
runtime, neither of which was available here. `packages.aarch64-darwin.cc-oracle-image` and
`packages.aarch64-linux.cc-oracle` evaluate, but have not been built.

Note also that the container buys isolation, not capability — nothing here needs Linux, and the
native derivation already leaves nothing on the host outside `/nix/store`.

## What this can and cannot settle

It checks **T-slot availability** — one input to the forecast rules, the quantity behind
`bestTspin`, `improved`, `availAtRoof` and `availAtSpin`. It says nothing about the forecast rules
themselves: cold-clear has no notion of roof provenance, of clause 2's pre-existing hole, of gap
closure or of clause 4, and this project's own survey found no prior art for the metric anywhere.

**`cutout_tslot` — done (2026-08-09).** It gives the LINE COUNT of a slot, and `cc-tslot.ts` omits
it, so the cross-check used to be presence-only while the metric consumes `bestTspinLines`. The
oracle now emits `lines` and `cross-tslot-count.ts` differentials it against our count over every
verified-prefix board: **1,831 slots where both fire, all counts agree; 0 line-clearing slots
missed.** So the quantity the metric actually uses is now checked against the Rust original, not just
against our own second BFS. (The 588 boards where we score a line clear and cold-clear's *named*
opener detectors do not are general T-spins — e.g. a plain single into a well — outside cold-clear's
sky/tst/fin/cave vocabulary; each is a genuine hard-drop-reachable spin, not an over-count.)

Still open, per `ROADMAP.md`:

- **multi-slot cutout** — cold-clear counts several slots by cutting each out and re-detecting, which
  the roadmap notes is "precisely the fix for the scalar problem". Having the reference implementation
  to differential-test against de-risks building ours.
