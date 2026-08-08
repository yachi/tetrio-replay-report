# cc-oracle — MinusKelvin/cold-clear's T-slot detectors, built from the ORIGINAL Rust and exposed
# as a line-oriented oracle.
#
# WHY A DERIVATION AND NOT A CHECKOUT. `pipeline/sim/cc-tslot.ts` is a hand port of those detectors,
# cross-checked against our BFS over 7,544 corpus boards with 0 genuine disagreements. Its own header
# carries the caveat that it has never been run against the Rust original. Two readings of one source
# agreeing is weaker evidence than it looks: if the port misread the Rust, the misreading is on both
# sides. This builds the original and makes that check possible without putting a toolchain, a
# checkout or a target/ directory anywhere near the working tree.
#
# THE PATCH IS THE INTERESTING PART. cold-clear's detectors are private — `mod standard;` is not
# `pub`, and every `detect_shape!` function, `cave_tslot`, `cutout_tslot` and `Cutout` are private
# too. So the oracle cannot be built by depending on the crate; the module has to be opened up.
# `expose-detectors.patch` does exactly that and nothing else: it adds `pub` in six places and
# changes no logic. Keeping it as a pinned patch against a pinned rev is the point — a hand-edited
# clone would drift silently and could not be reviewed.
{ lib, rustPlatform, fetchFromGitHub }:

rustPlatform.buildRustPackage rec {
  pname = "cc-oracle";
  version = "0-unstable-279edd7";

  src = fetchFromGitHub {
    owner = "MinusKelvin";
    repo = "cold-clear";
    rev = "279edd7c3177ff8077f6a930193397814b281f27";
    hash = "sha256-qyXGJ9JTnYQF7Ro1c5/jzZqd9m5CtMnr9X/ZpMYAuwM=";
  };

  patches = [ ./expose-detectors.patch ];

  # The oracle itself is ours; it lives beside cold-clear's sources rather than in them so that the
  # patch stays reviewable as "six `pub`s and nothing else".
  postPatch = ''
    mkdir -p bot/src/bin
    cp ${./cc-oracle.rs} bot/src/bin/cc-oracle.rs
    # `cargoSetupPostPatchHook` diffs src's Cargo.lock against the vendored one and aborts if it is
    # absent. Upstream gitignores it, so it is placed here — after `patches`, before the hook.
    cp ${./Cargo.lock} Cargo.lock
  '';

  # UPSTREAM SHIPS NO LOCKFILE — `Cargo.lock` is in cold-clear's .gitignore, so it is absent from
  # the tarball and a plain `cargoHash` build fails with "No such file or directory: 'Cargo.lock'".
  # It is vendored here instead, which is what makes the build reproducible at all: without it the
  # resolver would pick whatever crates.io holds on the day, and "the original Rust" would mean a
  # different program each time. The lock is generated against the TRIMMED workspace above, so it
  # carries two git dependencies rather than six.
  cargoLock = {
    lockFile = ./Cargo.lock;
    outputHashes = {
      "pcf-0.1.0" = "sha256-2/Y5thDN5fwthk+I/D7pORe7yQ1H0UpNjVvAeSYpD5Q=";
      "webutil-0.1.0" = "sha256-Zg98VmCUd/ZTlRTfTfkPJh4xX0QrepGxICbszebQw0I=";
    };
  };

  # Only the bot crate and its path deps. The workspace also holds a graphical client and an
  # optimiser; neither is wanted and neither would build without a display stack.
  cargoBuildFlags = [ "-p" "cold-clear" "--bin" "cc-oracle" ];
  cargoTestFlags = cargoBuildFlags;
  doCheck = false; # upstream's tests are the bot's, not ours, and several need a book file

  meta = with lib; {
    description = "cold-clear's T-slot detectors as a stdin/stdout differential oracle";
    homepage = "https://github.com/MinusKelvin/cold-clear";
    license = licenses.mpl20;
    mainProgram = "cc-oracle";
  };
}
