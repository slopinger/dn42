# DN42 Peering & BGP Routing for `slop` (AS4242420125)

This repository contains the complete DN42 network configuration, automated tooling, systemd services, and registry object definitions for the **slop** autonomous network (`AS4242420125`).

---

## 🌐 Network Allocation Details

Configured resources and prepared registry objects are listed below. Verify registry acceptance separately; a local object or running router is not proof of accepted registration.

| Parameter | Value | Details |
|---|---|---|
| **Autonomous System Number (ASN)** | `AS4242420125` | Configured local ASN; verify registry acceptance separately |
| **IPv6 Prefix** | `fdd4:af47:dcfa::/48` | RFC 4193 ULA generated via host MAC (`ens18`) + NTP timestamp |
| **IPv4 Subnet** | `172.22.64.128/27` | Configured prefix matching the prepared registry objects and live router |
| **Router IPv4 (Dummy Loopback)** | `172.22.64.129/27` | Interface `dn42-dummy` |
| **Router IPv6 (Dummy Loopback)** | `fdd4:af47:dcfa::1/48` | Interface `dn42-dummy` |
| **WireGuard Public Key** | `sgYSxYeBQX9IMbcj7zv6UxYYq7QQPDfMdaxHFlTeckY=` | Private key at `/etc/wireguard/dn42.key` (0640, root:systemd-network) |
| **Registry Signing Key** | `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOTofPAGRTdGiTl7oeIWupx4euhHVkR3TyPsECnq2fWJ` | `slopmoder@tutamail.com` (`~/.ssh/id_ed25519_signing`) |
| **Maintainer Handle** | `SLOP-MNT` | Authenticated with SSH commit signing key |
| **Person Handle** | `SLOP-DN42` | Contact email `slopmoder@tutamail.com` |

---

## 🏗 System Architecture & Components

1. **Kernel Forwarding (`sysctl`)**:
   - `net.ipv4.ip_forward = 1`
   - `net.ipv6.conf.all.forwarding = 1`
   - Stored in `/etc/sysctl.d/99-dn42.conf`.

2. **Loopback Interface (`dn42-dummy`)**:
   - Managed via `systemd-networkd` (`/etc/systemd/network/20-dn42-dummy.netdev` and `20-dn42-dummy.network`).
   - Ensures local addresses `172.22.64.129/27` and `fdd4:af47:dcfa::1/48` are always online so BIRD can bind and install routes to the kernel without netlink failures.

3. **BIRD 3 Routing Daemon**:
   - Config file: `/etc/bird/bird.conf` (symlinked from `/etc/bird.conf`).
   - Router ID: `172.22.64.129`.
   - Master tables `master4` and `master6`.
   - Validates incoming route announcements against DN42 Route Origin Authorization (ROA) tables (`dn42_roa` and `dn42_roa_v6`) downloaded from Burble's live mirror.
   - Rejects bogons, out-of-range subnets, and routes failing ROA validation.
   - Dynamic peer include directory: `/etc/bird/peers/*.conf`.

4. **Automated ROA Updater**:
   - Script: `/usr/local/bin/dn42-update-roa.sh`
   - Systemd Service & Timer: `dn42-update-roa.service` and `dn42-update-roa.timer` (runs hourly to fetch updated ROA rules and reloads BIRD).

5. **CLI Management Tool (`dn42ctl`)**:
   - Installed at `/usr/local/bin/dn42ctl`.
   - Manage peers, check BGP sessions, inspect routing tables, and view node health.

---

## 🛠 Repository Directory Structure

```text
├── LICENSE                      # MIT License
├── README.md                    # This documentation
├── deploy.sh                    # Automated installer & service configuration script
├── bin/
│   └── dn42ctl                  # CLI control utility
├── bird/
│   ├── bird.conf                # BIRD 3 configuration with ROA checks & peer template
│   └── dn42-update-roa.sh       # Script to fetch live ROA tables and reconfigure BIRD
├── registry/
│   └── data/                    # Prepared DN42 registry objects
│       ├── aut-num/
│       │   └── AS4242420125
│       ├── inet6num/
│       │   └── fdd4:af47:dcfa::_48
│       ├── inetnum/
│       │   └── 172.22.64.128_27
│       ├── mntner/
│       │   └── SLOP-MNT
│       ├── person/
│       │   └── SLOP-DN42
│       ├── route/
│       │   └── 172.22.64.128_27
│       └── route6/
│           └── fdd4:af47:dcfa::_48
└── systemd/
    ├── 20-dn42-dummy.netdev     # systemd-networkd dummy netdev
    ├── 20-dn42-dummy.network    # systemd-networkd dummy IP assignment
    ├── 99-dn42.conf             # sysctl IP forwarding settings
    ├── dn42-update-roa.service  # ROA update systemd service
    └── dn42-update-roa.timer    # Hourly systemd timer
```

---

## 🚀 Usage & Commands

### 1. Check Node Status
```bash
dn42ctl status
```
Outputs:
- Local ASN, router IPs, and WireGuard public key.
- Dummy loopback interface carrier status.
- BIRD 3 daemon status and loaded ROA table counts.
- Configured BGP peer sessions.

### 2. View Active Peers and Protocols
```bash
dn42ctl peers
```
Equivalent to `birdc show protocols`.

### 3. Inspect Routing Table
```bash
# View all routes
dn42ctl routes

# Filter by specific prefix
dn42ctl routes 172.20.0.0/14
```

### 4. Add a Peer Session
To establish a peer session (WireGuard + MP-BGP over IPv6 LL):
```bash
sudo dn42ctl add-peer <name> \
    --asn <PEER_ASN> \
    --endpoint <HOST:PORT> \
    --pubkey <WIREGUARD_PUBKEY> \
    --peer-ll-v6 <PEER_LINK_LOCAL> \
    --my-ll-v6 <MY_LINK_LOCAL>
```
This automatically creates the systemd-networkd WireGuard device, the BIRD peer config in `/etc/bird/peers/<name>.conf`, and reloads networkd and BIRD.

### 5. Remove a Peer Session
```bash
sudo dn42ctl del-peer <name>
```

### 6. Update ROA Tables Manually
```bash
dn42ctl update-roa
```

---

## 📝 Registration & Peering Status

1. **Registry Registration**:
   - Pull Request: [https://git.dn42.dev/dn42/registry/pulls/7531](https://git.dn42.dev/dn42/registry/pulls/7531)
   - Status: **MERGED** into `dn42registry/master` on 2026-10-15 (commit `4513a83f3`).
   - Objects: `AS4242420125`, `172.22.64.128/27`, `fdd4:af47:dcfa::/48`, `SLOP-MNT`, `SLOP-DN42`.

2. **Active Backbone Peerings (39 Established BGP Sessions)**:
   - **iEdon-Net Nürnberg** (`AS4242422189`, `de-nue.dn42.iedon.net:32769`): WireGuard port 22189, BGP Established (`dn42_iedon_nue`, ~15ms, 1,280 v4 / 1,227 v6 routes).
   - **iEdon-Net Amsterdam** (`AS4242422189`, `nl-ams.dn42.iedon.net:41254`): WireGuard port 22190, BGP Established (`dn42_iedon_ams`, ~21ms, 1,280 v4 / 1,227 v6 routes).
   - **iEdon-Net Paris** (`AS4242422189`, `fr-cdg.dn42.iedon.net:57008`): WireGuard port 22191, BGP Established (`dn42_iedon_cdg`, ~18ms, 1,280 v4 / 1,227 v6 routes).
   - **iEdon-Net London** (`AS4242422189`, `uk-lon.dn42.iedon.net:49994`): WireGuard port 22192, BGP Established (`dn42_iedon_lon`, ~21ms, 1,280 v4 / 1,227 v6 routes).
   - **iEdon-Net Warsaw** (`AS4242422189`, `pl-waw.dn42.iedon.net:40928`): WireGuard port 22193, BGP Established (`dn42_iedon_waw`, ~20ms, 1,280 v4 / 1,227 v6 routes).
   - **iEdon-Net San Jose** (`AS4242422189`, `us-sjc.dn42.iedon.net:45694`): WireGuard port 22194, BGP Established (`dn42_iedon_sjc`, ~141ms, 1,280 v4 / 1,227 v6 routes).
   - **iEdon-Net Hong Kong** (`AS4242422189`, `hk-hkg.dn42.iedon.net:46615`): WireGuard port 22195, BGP Established (`dn42_iedon_hkg`, ~197ms, 1,280 v4 / 1,227 v6 routes).
   - **iEdon-Net Singapore** (`AS4242422189`, `sg-sin.dn42.iedon.net:32827`): WireGuard port 22196, BGP Established (`dn42_iedon_sin`, ~172ms, 1,280 v4 / 1,227 v6 routes).
   - **FlipFlap Frankfurt** (`AS4242420263`, `de-fra1.flap42.eu`): WireGuard port 20263, BGP Established (`dn42_flipflap_fra`, ~11ms).
   - **FlipFlap Warsaw** (`AS4242420263`, `pl-waw1.flap42.eu`): WireGuard port 20266, BGP Established (`dn42_flipflap_waw`, ~21ms).
   - **Kioubit Nuremberg** (`AS4242423914`, `de2.g-load.eu`): WireGuard port 20391, BGP Established (`dn42_kioubit_de2`, ~17ms).
   - **Kioubit Paris** (`AS4242423914`, `fr1.g-load.eu`): WireGuard port 20392, BGP Established (`dn42_kioubit_fr1`, ~19ms).
   - **Kioubit London** (`AS4242423914`, `uk1.g-load.eu`): WireGuard port 20393, BGP Established (`dn42_kioubit_uk1`, ~16ms).
   - **RoutedBits Amsterdam** (`AS4242420207`, `router.ams1.routedbits.com`): WireGuard port 20208, BGP Established (`dn42_routedbits_ams`, ~8ms).
   - **RoutedBits Frankfurt** (`AS4242420207`, `router.fra1.routedbits.com`): WireGuard port 20207, BGP Established (`dn42_routedbits_fra`, ~4ms).
   - **Pilz** (`AS4242420663`, `94.142.240.36:125`): WireGuard port 20663, BGP Established (`dn42_pilz`, PR pilz0/nixos-config#6 merged).
   - **Sabrina** (`AS4242421810`, `de42.sabrinaishere.party:20125`): WireGuard port 21810, BGP Established (`dn42_sabrina_de`, ~20ms).
   - **HEADSCARF175 Amsterdam** (`AS4242420842`, `45.137.198.52:20125`): WireGuard port 20842, BGP Established (`dn42_headscarf_ams`, ~5.3ms, 1,290 v4 / 1,250 v6 routes).
   - **Nedifinita Falkenstein** (`AS4242420454`, `[2001:470:1f0b:ff:1::8f]:30125`): WireGuard port 20454, BGP Established (`dn42_nedifinita_de1`, ~14ms, 1,336 v4 / 1,321 v6 routes).
   - **Nedifinita Amsterdam** (`AS4242420454`, `143.20.154.8:30125`): WireGuard port 20455, BGP Established (`dn42_nedifinita_nl0`, ~9.9ms, 1,338 v4 / 1,332 v6 routes).
   - **AndyYJF Frankfurt** (`AS4242422921`, `156.226.175.73:20125`): WireGuard port 22921, BGP Established (`dn42_andyyjf_fra`, ~4ms, 1,380 v4 / 1,254 v6 routes).
   - **AndyYJF Los Angeles** (`AS4242422921`, `45.202.243.95:20125`): WireGuard port 22922, BGP Established (`dn42_andyyjf_lax`, ~149ms, 1,421 v4 / 1,274 v6 routes).
   - **Nyaw Tokyo** (`AS4242420291`, `jp-tyo-1.dn42.nyaw.xyz:20125`): WireGuard port 20291, BGP Established (`dn42_nyaw_tyo1`, ~219ms).
   - **IRIS-AS Amsterdam** (`AS4242421023`, `[2001:bc8:1640:5afb:dc00:ff:fe60:6beb]:20125`): WireGuard port 21023, BGP Established (`dn42_iris_ams01`, ~17.8ms, 1,443 v4 / 1,338 v6 routes, PR #177 applied).
   - **moe233 Amsterdam** (`AS4242420253`, `[2001:bc8:1640:5bb5:dc00:ff:fe60:c33f]:20125`): WireGuard port 20253, BGP Established (`dn42_moe233_ams`, ~18ms, 1,431 v4 / 1,340 v6 routes).
   - **KSKB Neo Amsterdam** (`AS4201271111`, `20.54.218.128:25026`): WireGuard port 21817, BGP Established (`dn42_kskb_nl`, ~10ms, 1,191 v4 / 1,163 v6 routes).
   - **KSKB Neo Zurich** (`AS4201271111`, `20.203.134.45:1029`): WireGuard port 21818, BGP Established (`dn42_kskb_ch`, ~14ms).
   - **KSKB Neo Toronto** (`AS4201271111`, `20.48.129.103:13057`): WireGuard port 21819, BGP Established (`dn42_kskb_ca`, ~90ms).
   - **KSKB Neo US West** (`AS4201271111`, `20.190.10.218:1025`): WireGuard port 21820, BGP Established (`dn42_kskb_usw`, ~145ms).
   - **Yuyuko Network Amsterdam** (`AS4242421117`, `nl01.dn42.yuyuko.com:20125`): WireGuard port 21117, BGP Established (`dn42_yuyuko_nl`, ~18ms, 1,124 v4 / 1,122 v6 routes).
   - **Yuyuko Network Paris** (`AS4242421117`, `fr01.dn42.yuyuko.com:20125`): WireGuard port 21118, BGP Established (`dn42_yuyuko_fr`, ~14.3ms, 1,124 v4 / 1,122 v6 routes).
   - **Yuyuko Network Warsaw** (`AS4242421117`, `pl01.dn42.yuyuko.com:20125`): WireGuard port 21119, BGP Established (`dn42_yuyuko_pl`, ~24.5ms, 1,123 v4 / 1,121 v6 routes).
   - **Yuyuko Network San Jose** (`AS4242421117`, `us01.dn42.yuyuko.com:20125`): WireGuard port 21120, BGP Established (`dn42_yuyuko_us`, ~151ms).
   - **Yuyuko Network Tokyo** (`AS4242421117`, `jp01.dn42.yuyuko.com:20125`): WireGuard port 21121, BGP Established (`dn42_yuyuko_jp`, ~242ms).
   - **Yuyuko Network Hong Kong 1** (`AS4242421117`, `hk01.dn42.yuyuko.com:20125`): WireGuard port 21122, BGP Established (`dn42_yuyuko_hk01`, ~242ms).
   - **Yuyuko Network Hong Kong 2** (`AS4242421117`, `hk02.dn42.yuyuko.com:20125`): WireGuard port 21123, BGP Established (`dn42_yuyuko_hk02`, ~252ms).
   - **JK-Network Hong Kong** (`AS4242422717`, `hk.vm.whojk.com:23952`): WireGuard port 22717, configured (`dn42_whojk_hk`, upstream host unreachable).
   - **JK-Network Taiwan** (`AS4242422717`, `tw.vm.whojk.com:23014`): WireGuard port 22718, BGP Established (`dn42_whojk_tw`, ~190ms, 1,318 v4 / 1,339 v6 routes).
   - **Maiyun** (`AS4242420893`, Toronto): WireGuard port 20893, BGP Established (`dn42_maiyun_ca04`, PR [myzhang1029/dn42-config-pub#25](https://github.com/myzhang1029/dn42-config-pub/pull/25) merged).
   - **Baragoon Frankfurt** (`AS4242421732`, `chr-fr01.as215887.net:20125`): WireGuard port 20125, BGP Established (`dn42_baragoon_fra`, PR [baragoon/dn42-as4242421732#35](https://github.com/baragoon/dn42-as4242421732/pull/35) merged).
   - **HIGHDEF-AS Frankfurt** (`AS4242421080`, `fra.peer.highdef.network:20125`): WireGuard port 21080, PR [jlu5/ansible-dn42#172](https://github.com/jlu5/ansible-dn42/pull/172) open, ~4.5ms.
   - **Zebreus** (`AS4242421403`, Falkenstein/Nuremberg): Peering request opened on GitHub Issue [zebreus/nixos-config#7](https://github.com/zebreus/nixos-config/issues/7). Port 21403 reserved.
   - **SCARJIT Network** (`AS4242420257`, Germany): WireGuard port 20257, BGP session configured, peering request opened on GitHub Issue [Scarjit/dn42-setup#3](https://github.com/Scarjit/dn42-setup/issues/3).
   - **JoyfulReaper** (`AS4242420425`, Wurstcase Frankfurt / Clanker NY): WireGuard port 20425 reserved, peering request submitted via DN42 internal portal `joyfulreaper.dn42` (`http://[fdf0:e12c:5528::50]/`).
   - **0pera** (`AS4242423077`, Frankfurt): WireGuard port 23077, PR [0pera/dn42-peering#1](https://github.com/0pera/dn42-peering/pull/1) submitted.
   - **NATLAN** (`AS4242420028`, Frankfurt & Los Angeles): WireGuard ports 20028 & 20029 provisioned on API (requests 39 & 40).
   - Route stats: Full table exchange with Extended Next Hop (RFC 8950), 39 Established BGP sessions, 101,470+ routes active across 4 tables (master4, master6, ROAv4, ROAv6).
   - Anycast DNS Reachability: `172.20.0.53` and `fd42:d42:d42:54::1` verified with 0% packet loss (<18ms). Internal domain resolution tested (`kioubit.dn42` -> `172.20.14.43`, `burble.dn42` -> `172.20.129.3`).

3. **Continuous Autopeering**:
   - `dn42-auto-peer.service` runs continuously in the background, checking upstream git sync on community nodes (FlipFlap, Kioubit, Natlan, Sabrina, Headscarf), establishing additional WireGuard tunnels, and refreshing ROA validation tables. Tooling suite in `bin/` includes `autopeer_flipflap.py`, `autopeer_kioubit.py`, `autopeer_natlan.py`, `autopeer_sabrina.py`, and `autopeer_headscarf.py`.

## Nix packaging

`nix build` packages dn42ctl, the peering helpers and ROA updater with their
Python/Paramiko and command dependencies. `nix run . -- --help` is read-only.
`nix flake check` checks Python/shell syntax and BIRD configuration syntax
with empty ROA/peer fixtures; it never provisions tunnels or contacts peers.
`nix develop` supplies Python/Paramiko, BIRD 3 and WireGuard tooling. Linux
x86_64/aarch64 packages are defined; x86_64 is the validation host.

Import `inputs.dn42.nixosModules.default` and enable `services.slop-dn42.enable`
for this specific ASN/allocation: forwarding, the dummy interface, BIRD and an
hourly ROA timer. `package` overrides tooling and `peerConfig` supplies BIRD
peer definitions. Configure WireGuard tunnels declaratively in the host, using
runtime private-key files; no secret belongs in Nix expressions/the store.
The module deliberately leaves WAN settings alone. ROAs live in
`/var/lib/dn42-roa`; BIRD requires the initial download, so failure prevents
startup rather than silently using an empty ROA set. Build-time BIRD checks use
fixtures because runtime ROAs are not present in the store.

The imperative `dn42ctl add-peer` and auto-peer daemon target the existing Arch
installation; they are not enabled by the NixOS module and must not be used to
modify declarative NixOS network configuration. Existing Arch deployment uses
`./deploy.sh`. The daemon checks the public registry PR without credentials and
uses its own Python interpreter for the adjacent FlipFlap helper. Previously
committed credentials have been removed from current source; history still
contains them and the affected external credential needs rotation.
