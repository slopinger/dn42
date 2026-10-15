{
  description = "DN42 router tools for AS4242420125";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  outputs = { self, nixpkgs }: let
    systems = [ "x86_64-linux" "aarch64-linux" ];
    eachSystem = nixpkgs.lib.genAttrs systems;
  in {
    packages = eachSystem (system: let
      pkgs = nixpkgs.legacyPackages.${system};
      python = pkgs.python3.withPackages (p: [ p.paramiko ]);
    in {
      default = pkgs.stdenvNoCC.mkDerivation {
        pname = "dn42-tools";
        version = "0.1.0";
        src = self;
        nativeBuildInputs = [ pkgs.makeWrapper ];
        nativeCheckInputs = [ python pkgs.bash ];
        dontBuild = true;
        doCheck = true;
        checkPhase = ''
          bash -n deploy.sh bin/submit-registry.sh bird/dn42-update-roa.sh
          python -m py_compile bin/*.py bin/dn42ctl
          python bin/dn42ctl --help
        '';
        installPhase = ''
          mkdir -p $out/lib/dn42 $out/share/dn42 $out/bin
          cp bin/*.py bin/dn42ctl $out/lib/dn42/
          cp -r bird systemd registry $out/share/dn42/
          for script in dn42ctl autopeer_flipflap.py dn42-auto-peer-daemon.py; do
            makeWrapper ${python}/bin/python3 $out/bin/"$script" \
              --add-flags "$out/lib/dn42/$script" \
              --prefix PATH : ${pkgs.lib.makeBinPath [ pkgs.bird3 pkgs.iproute2 pkgs.wireguard-tools pkgs.systemd pkgs.iputils pkgs.git pkgs.openssh pkgs.coreutils ]}
          done
          install -m755 bird/dn42-update-roa.sh $out/bin/dn42-update-roa
          patchShebangs $out/bin/dn42-update-roa
          wrapProgram $out/bin/dn42-update-roa --prefix PATH : ${pkgs.lib.makeBinPath [ pkgs.curl pkgs.bird3 pkgs.coreutils pkgs.util-linux ]}
          substituteInPlace $out/lib/dn42/autopeer_flipflap.py \
            --replace-fail /usr/local/bin/dn42ctl $out/bin/dn42ctl
        '';
        meta = { license = pkgs.lib.licenses.mit; platforms = systems; mainProgram = "dn42ctl"; };
      };
    });
    checks = eachSystem (system: let
      pkgs = nixpkgs.legacyPackages.${system};
      empty = pkgs.writeText "empty-roa.conf" "";
      config = pkgs.writeText "dn42-bird-syntax.conf" (builtins.replaceStrings
        [ "/etc/bird/roa_dn42.conf" "/etc/bird/roa_dn42_v6.conf" "/etc/bird/peers/*.conf" ]
        [ "${empty}" "${empty}" "${empty}" ]
        (builtins.readFile ./bird/bird.conf));
    in {
      package = self.packages.${system}.default;
      bird = pkgs.runCommand "dn42-bird-syntax" { nativeBuildInputs = [ pkgs.bird3 ]; } ''
        bird -p -c ${config}
        touch $out
      '';
    });
    devShells = eachSystem (system: {
      default = nixpkgs.legacyPackages.${system}.mkShell {
        packages = with nixpkgs.legacyPackages.${system}; [ (python3.withPackages (p: [ p.paramiko ])) bird3 wireguard-tools ];
      };
    });
    nixosModules.default = import ./nix/module.nix { inherit self; };
  };
}
