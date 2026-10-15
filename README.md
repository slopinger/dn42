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
| **Registry Signing Key** | `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOTofPAGRTdGiTl7oeIWupx4euhHVkR3TyPsECnq2fWJ` | `slop@freifick.net` (`~/.ssh/id_ed25519_signing`) |
| **Maintainer Handle** | `SLOP-MNT` | Authenticated with SSH commit signing key |
| **Person Handle** | `SLOP-DN42` | Contact email `slop@freifick.net` |

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

2. **Active Backbone Peerings**:
   - **FlipFlap Warsaw** (`pl-waw1.flap42.eu`): WireGuard on port 20266, BGP Established (`dn42_flipflap_waw`).
   - **FlipFlap Frankfurt** (`de-fra1.flap42.eu`): WireGuard on port 20263, BGP Established (`dn42_flipflap_fra`).
   - Route stats: Exchanging 2,893 IPv4 paths and 2,651 IPv6 paths across 1,447 global DN42 networks. Extended Next Hop (RFC 8950) active.

3. **Continuous Autopeering**:
   - `dn42-auto-peer.service` runs continuously in the background, checking upstream git sync on community nodes (FlipFlap Amsterdam `nl-ams2`, Paris `fr-par1`, Kioubit `AS4242423914`, Natlan `AS4242420028`), establishing additional WireGuard tunnels, and refreshing ROA validation tables.

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
