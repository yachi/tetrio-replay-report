{
  # Nix entry point for the differential oracle only. The report pipeline itself is bun + python +
  # Dafny and is not packaged here; this exists so that checking `pipeline/sim/cc-tslot.ts` against
  # the ORIGINAL cold-clear needs no Rust toolchain, no checkout and no `target/` on the host.
  description = "cold-clear T-slot detectors as a differential oracle for the T-Spin Forecast metric";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    nix2container = {
      url = "github:nlewo/nix2container";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, nix2container }:
    let
      # aarch64-darwin builds the binary the harness runs directly; aarch64-linux is what goes in
      # the container image, since Apple's runtime runs Linux VMs.
      systems = [ "aarch64-darwin" "aarch64-linux" ];
      forAll = f: nixpkgs.lib.genAttrs systems (s: f s nixpkgs.legacyPackages.${s});
    in
    {
      packages = nixpkgs.lib.recursiveUpdate
        (forAll (system: pkgs: {
          cc-oracle = pkgs.callPackage ./nix/cold-clear-oracle { };
          default = self.packages.${system}.cc-oracle;
        }))
        {
          # The OCI image for services.containerization.images.cc-oracle. Built from the
          # aarch64-linux package, so it needs `linux-builder.aarch64.enable = true` and two
          # rebuilds — the first starts the builder, the second builds and loads this.
          aarch64-darwin.cc-oracle-image =
            nix2container.packages.aarch64-darwin.nix2container.buildImage {
              name = "cc-oracle";
              tag = "latest";
              config.Cmd = [ "${self.packages.aarch64-linux.cc-oracle}/bin/cc-oracle" ];
            };
        };

      devShells = forAll (system: pkgs: {
        default = pkgs.mkShell {
          packages = [ self.packages.${system}.cc-oracle ];
        };
      });
    };
}
