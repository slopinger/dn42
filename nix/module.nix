{ self }: { config, lib, pkgs, ... }: let
  inherit (lib) mkOption types;
  cfg = config.services.slop-dn42;
  roaDir = "/var/lib/dn42-roa";

  peerOptions = { name, ... }: {
    options = {
      asn = mkOption { type = types.ints.unsigned; description = "Peer AS number."; };
      publicKey = mkOption { type = types.str; description = "Peer WireGuard public key."; };
      endpoint = mkOption {
        type = types.nullOr types.str;
        default = null;
        example = "[2001:db8::1]:20125";
        description = "Peer WireGuard endpoint; null when the peer connects to us.";
      };
      listenPort = mkOption { type = types.port; description = "Local WireGuard UDP port for this tunnel."; };
      interface = mkOption {
        type = types.strMatching ".{1,15}";
        default = "dn_" + lib.substring 0 12 name;
        defaultText = lib.literalExpression ''"dn_" + lib.substring 0 12 name'';
        description = "Tunnel interface name (at most 15 characters).";
      };
      localAddress = mkOption {
        type = types.str;
        default = "fe80::125/64";
        description = "Our link-local address on the tunnel.";
      };
      neighbor = mkOption { type = types.str; description = "Peer link-local address used for the BGP session."; };
      extraAddresses = mkOption {
        type = types.listOf types.str;
        default = [ ];
        description = "Additional local tunnel addresses (e.g. our DN42 IPv4 as /32).";
      };
      extraRoutes = mkOption {
        type = types.listOf types.str;
        default = [ ];
        description = "Additional on-link destinations (e.g. the peer's DN42 IPv4).";
      };
      birdConfig = mkOption {
        type = types.lines;
        default = "";
        description = "Extra statements for this peer's BIRD protocol block.";
      };
    };
  };

  protocolName = name: "dn42_" + builtins.replaceStrings [ "-" "." ] [ "_" "_" ] name;
  peerBird = name: peer: ''
    # DN42 Peer: ${name} (AS${toString peer.asn})
    protocol bgp ${protocolName name} from dnpeers {
        enable extended messages on;
        neighbor ${peer.neighbor} as ${toString peer.asn};
        interface "${peer.interface}";
        direct;
        ipv4 {
            extended next hop on;
        };
    ${peer.birdConfig}}
  '';
  peersConfig = lib.concatStrings (lib.mapAttrsToList peerBird cfg.peers) + cfg.peerConfig;

  birdConfig = builtins.replaceStrings
    [ "/etc/bird/roa_dn42" ''include "/etc/bird/peers/*.conf";'' ]
    [ "${roaDir}/roa_dn42" peersConfig ]
    (builtins.readFile ../bird/bird.conf);

  # Keep the last good tables when the download fails; start with empty tables on
  # first boot so BIRD comes up (all routes are ROA-unknown until the next run).
  updater = pkgs.writeShellScript "dn42-update-roa" ''
    set -euo pipefail
    cd ${roaDir}
    trap 'rm -f roa4.new roa6.new' EXIT
    if ${pkgs.curl}/bin/curl --max-time 60 -fsSL https://dn42.burble.com/roa/dn42_roa_bird2_4.conf -o roa4.new &&
       ${pkgs.curl}/bin/curl --max-time 60 -fsSL https://dn42.burble.com/roa/dn42_roa_bird2_6.conf -o roa6.new; then
      chmod 644 roa4.new roa6.new
      mv roa4.new roa_dn42.conf
      mv roa6.new roa_dn42_v6.conf
    else
      echo "ROA download failed; keeping the cached tables" >&2
      for file in roa_dn42.conf roa_dn42_v6.conf; do
        [ -e "$file" ] || install -m 644 /dev/stdin "$file" </dev/null
      done
    fi
  '';
in {
  options.services.slop-dn42 = {
    enable = lib.mkEnableOption "AS4242420125 DN42 router configuration";
    package = mkOption { type = types.package; default = self.packages.${pkgs.stdenv.hostPlatform.system}.default; description = "DN42 tooling package."; };
    privateKeyFile = mkOption {
      type = types.str;
      default = "/etc/wireguard/dn42.key";
      description = "Runtime WireGuard private key shared by all tunnels; never a store path.";
    };
    peers = mkOption {
      type = types.attrsOf (types.submodule peerOptions);
      default = { };
      description = "WireGuard tunnels and BGP sessions, keyed by peer name.";
    };
    peerConfig = mkOption { type = types.lines; default = ""; description = "Additional raw BIRD peer configuration."; };
  };
  config = lib.mkIf cfg.enable {
    assertions = let
      ports = lib.mapAttrsToList (_: p: p.listenPort) cfg.peers;
      ifaces = lib.mapAttrsToList (_: p: p.interface) cfg.peers;
    in [
      { assertion = lib.allUnique ports; message = "services.slop-dn42.peers: listenPort values must be unique"; }
      { assertion = lib.allUnique ifaces; message = "services.slop-dn42.peers: interface names must be unique"; }
    ];
    environment.systemPackages = [ cfg.package ];
    boot.kernel.sysctl = { "net.ipv4.ip_forward" = 1; "net.ipv6.conf.all.forwarding" = 1; };
    systemd.network.enable = true;
    systemd.network.netdevs = {
      "20-dn42-dummy".netdevConfig = { Name = "dn42-dummy"; Kind = "dummy"; };
    } // lib.mapAttrs' (name: peer: lib.nameValuePair "30-${peer.interface}" {
      netdevConfig = {
        Name = peer.interface;
        Kind = "wireguard";
        Description = "DN42 WireGuard peer ${name} (AS${toString peer.asn})";
      };
      wireguardConfig = { PrivateKeyFile = cfg.privateKeyFile; ListenPort = peer.listenPort; };
      wireguardPeers = [ ({
        PublicKey = peer.publicKey;
        AllowedIPs = [ "0.0.0.0/0" "::/0" ];
        PersistentKeepalive = 25;
      } // lib.optionalAttrs (peer.endpoint != null) { Endpoint = peer.endpoint; }) ];
    }) cfg.peers;
    systemd.network.networks = {
      "20-dn42-dummy" = {
        matchConfig.Name = "dn42-dummy";
        address = [ "172.22.64.129/27" "fdd4:af47:dcfa::1/48" ];
      };
    } // lib.mapAttrs' (_: peer: lib.nameValuePair "30-${peer.interface}" {
      matchConfig.Name = peer.interface;
      address = [ peer.localAddress ] ++ peer.extraAddresses;
      networkConfig = { LinkLocalAddressing = "ipv6"; IPv6AcceptRA = false; };
      routes = map (dest: { Destination = dest; Scope = "link"; }) ([ peer.neighbor ] ++ peer.extraRoutes);
    }) cfg.peers;
    # networkd reads the tunnel key; the file itself is provisioned out of band.
    systemd.tmpfiles.rules = [ "z ${cfg.privateKeyFile} 0640 root systemd-network -" ];

    services.bird = {
      enable = true;
      package = pkgs.bird3;
      config = birdConfig;
      # The ROA tables are runtime state: check against empty ones (replaces the symlink to $out).
      preCheckConfig = ''
        sed 's|${roaDir}/|./|' bird.conf > checked.conf
        mv checked.conf bird.conf
        touch roa_dn42.conf roa_dn42_v6.conf
      '';
    };
    systemd.services.bird = { wants = [ "dn42-update-roa.service" ]; after = [ "dn42-update-roa.service" ]; };
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
