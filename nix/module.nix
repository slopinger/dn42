{ self }: { config, lib, pkgs, ... }: let
  cfg = config.services.slop-dn42;
  birdConfig = builtins.replaceStrings
    [ "/etc/bird/roa_dn42" "/etc/bird/peers/*.conf" ]
    [ "/var/lib/dn42-roa/roa_dn42" "${pkgs.writeText "dn42-peers.conf" cfg.peerConfig}" ]
    (builtins.readFile ../bird/bird.conf);
  updater = pkgs.writeShellScript "dn42-update-roa" ''
    set -euo pipefail
    cd /var/lib/dn42-roa
    trap 'rm -f roa4.new roa6.new' EXIT
    ${pkgs.curl}/bin/curl -fsSL https://dn42.burble.com/roa/dn42_roa_bird2_4.conf -o roa4.new
    ${pkgs.curl}/bin/curl -fsSL https://dn42.burble.com/roa/dn42_roa_bird2_6.conf -o roa6.new
    chmod 644 roa4.new roa6.new
    mv roa4.new roa_dn42.conf
    mv roa6.new roa_dn42_v6.conf
  '';
in {
  options.services.slop-dn42 = {
    enable = lib.mkEnableOption "AS4242420125 DN42 router configuration";
    package = lib.mkOption { type = lib.types.package; default = self.packages.${pkgs.stdenv.hostPlatform.system}.default; description = "DN42 tooling package."; };
    peerConfig = lib.mkOption { type = lib.types.lines; default = ""; description = "Additional BIRD peer configuration. Configure WireGuard tunnels separately using runtime private-key files."; };
  };
  config = lib.mkIf cfg.enable {
    environment.systemPackages = [ cfg.package ];
    boot.kernel.sysctl = { "net.ipv4.ip_forward" = 1; "net.ipv6.conf.all.forwarding" = 1; };
    systemd.network.enable = true;
    systemd.network.netdevs."20-dn42-dummy" = { netdevConfig = { Name = "dn42-dummy"; Kind = "dummy"; }; };
    systemd.network.networks."20-dn42-dummy" = {
      matchConfig.Name = "dn42-dummy";
      address = [ "172.22.64.129/27" "fdd4:af47:dcfa::1/48" ];
      networkConfig.LinkLocalAddressing = "no";
    };
    services.bird = { enable = true; package = pkgs.bird3; config = birdConfig; checkConfig = false; };
    systemd.services.bird = { requires = [ "dn42-update-roa.service" ]; after = [ "dn42-update-roa.service" ]; };
    systemd.services.dn42-update-roa = {
      description = "Download DN42 ROA tables";
      wants = [ "network-online.target" ];
      after = [ "network-online.target" ];
      serviceConfig = {
        Type = "oneshot";
        StateDirectory = "dn42-roa";
        ExecStart = updater;
        ExecStartPost = "-${pkgs.bird3}/bin/birdc configure";
        PrivateTmp = true;
        ProtectSystem = "strict";
        ProtectHome = true;
      };
    };
    systemd.timers.dn42-update-roa = {
      wantedBy = [ "timers.target" ];
      timerConfig = { OnCalendar = "hourly"; RandomizedDelaySec = 300; Persistent = true; };
    };
  };
}
