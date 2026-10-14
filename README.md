# DN42 Peering & BGP Routing for `slop` (AS4242420125)

This repository contains the complete DN42 network configuration, automated tooling, systemd services, and registry object definitions for the **slop** autonomous network (`AS4242420125`).

---

## 🌐 Network Allocation Details

The following resources have been allocated and validated against the live DN42 Registry database:

| Parameter | Value | Details |
|---|---|---|
| **Autonomous System Number (ASN)** | `AS4242420125` | Validated free in standard range `4242420000–4242423999` |
| **IPv6 Prefix** | `fdd4:af47:dcfa::/48` | RFC 4193 ULA generated via host MAC (`ens18`) + NTP timestamp |
| **IPv4 Subnet** | `172.20.0.96/27` | Allocated from parent block `172.20.0.0/18` (policy: open) |
| **Router IPv4 (Dummy Loopback)** | `172.20.0.97/27` | Interface `dn42-dummy` |
| **Router IPv6 (Dummy Loopback)** | `fdd4:af47:dcfa::1/48` | Interface `dn42-dummy` |
| **WireGuard Public Key** | `sgYSxYeBQX9IMbcj7zv6UxYYq7QQPDfMdaxHFlTeckY=` | Private key at `/etc/wireguard/dn42.key` (mode 600) |
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
   - Ensures local addresses `172.20.0.97/27` and `fdd4:af47:dcfa::1/48` are always online so BIRD can bind and install routes to the kernel without netlink failures.

3. **BIRD 3 Routing Daemon**:
   - Config file: `/etc/bird/bird.conf` (symlinked from `/etc/bird.conf`).
   - Router ID: `172.20.0.97`.
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
│       │   └── 172.20.0.96_27
│       ├── mntner/
│       │   └── SLOP-MNT
│       ├── person/
│       │   └── SLOP-DN42
│       ├── route/
│       │   └── 172.20.0.96_27
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

## 📝 Next Steps to Finalize DN42 Membership

Because DN42 is a decentralized network that requires cryptographic verification of registry objects by human maintainers, complete these steps to publish the registration:

1. **Sign Up on the DN42 Gitea instance**:
   - Visit [git.dn42.dev/user/sign_up](https://git.dn42.dev/user/sign_up) and create an account.
   - Confirm your email address.
   - Add your SSH public key (`~/.ssh/id_ed25519_gitlab.pub` or `~/.ssh/id_ed25519_signing.pub`) under your account settings.

2. **Fork the Registry Repository**:
   - Navigate to [git.dn42.dev/dn42/registry](https://git.dn42.dev/dn42/registry) and click **Fork**.

3. **Commit the Prepared Registry Objects**:
   - Clone your fork:
     ```bash
     git clone git@git.dn42.dev:<your-username>/registry.git /tmp/dn42-registry
     ```
   - Copy the pre-generated objects from this repo:
     ```bash
     cp -r ~/src/dn42/registry/data/* /tmp/dn42-registry/data/
     ```
   - Commit and sign:
     ```bash
     cd /tmp/dn42-registry
     git add data/
     git commit -S -m "Register SLOP-MNT, AS4242420125, 172.20.0.96/27, fdd4:af47:dcfa::/48"
     git push origin master
     ```

4. **Submit the Pull Request**:
   - Open a pull request against `master` of `dn42/registry`.
   - The CI checks will automatically validate schema, syntax, and signature.
   - Once merged by a DN42 maintainer, the objects become authoritative network-wide within ~30 minutes.

5. **Establish Peering**:
   - Use any automated peering portal:
     - **Kioubit**: [dn42.g-load.eu](https://dn42.g-load.eu)
     - **RoutedBits**: [dn42.routedbits.io](https://dn42.routedbits.io)
     - **AutoPeer**: [autopeer.su](https://autopeer.su)
   - Log in using `AS4242420125` and sign the challenge with `~/.ssh/id_ed25519_signing`.
   - Run `sudo dn42ctl add-peer ...` with the peer parameters provided by the portal!
