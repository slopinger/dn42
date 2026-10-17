# dn42 development notes

Source tooling/config and prepared registry objects for AS4242420125. `AGENTS.md` points here.
Keep this file and README current whenever allocation, peer tooling or operational procedures change.

- Current configured IPv4: `172.22.64.128/27`, router `172.22.64.129`; IPv6 `fdd4:af47:dcfa::/48`,
  router `fdd4:af47:dcfa::1`. The earlier `172.20.0.96/27` candidate is obsolete.
- Keep registry objects, README, BIRD/dummy source config, CLI displays and landing-page details in sync.
  Runtime and registry acceptance are separate facts: a configured peer is not an established session.
- Inspect `dn42ctl peers`, `birdc show protocols`, `ip -brief address show dn42-dummy`; compare live
  `/etc/bird/bird.conf` and `/etc/systemd/network/20-dn42-dummy.network` before changing source.
- Syntax-check scripts with `bash -n`. Validate BIRD with `sudo bird -p -c <source-config>` before
  deploying. `./deploy.sh` modifies live forwarding/networkd/BIRD; do not run it for documentation-only work.
- Do not touch WAN/SSH routing for routine project changes. Preserve unrelated peer configuration.
  Never print/commit WireGuard private keys or account/API credentials. Public keys are not private keys.
- Check git status/history before committing; use an isolated worktree if another session is active.
  Sign/push changes regularly. Registry submission is a distinct external action, not a syntax check.
- Use small commits: one logical change per commit (with its tests/docs), each passing the checks above.
  Don't bundle unrelated changes or a whole session's work into one commit.

- Every software change must maintain project-owned Nix flake packaging, a committed lockfile,
  development tools and checks. Export a reusable NixOS module where host/service integration
  applies. Verify package builds and relevant flake checks; document supported commands in README.

- Nix: `nix build`, `nix flake check`, `nix develop`; commit `flake.lock`.
  `nixosModules.default` exports the reusable host module; see README for options and limits.
- Never add Co-Authored-By trailers or session links to public GitHub content.

## Live host (AS4242420125)
- Registry: PR https://git.dn42.dev/dn42/registry/pulls/7531 merged on 2026-10-15 (`4513a83f3`).
  Account `slop_freifick` on git.dn42.dev (`~/.secrets/dn42/{username,password}`; SSH via
  `~/.ssh/id_ed25519_signing`). Registry checkout: `~/src/dn42-registry` (upstream data, not ours).
- BIRD: `/etc/bird/bird.conf` (`/etc/bird.conf` symlink), peer snippets `/etc/bird/peers/`.
  `dn42-dummy` is managed by networkd. Enabled: `bird`, `dn42-update-roa.timer` (hourly),
  `dn42-auto-peer.service`. WireGuard private key `/etc/wireguard/dn42.key`; never print or commit it.
- `dn42-auto-peer.service` runs `bin/dn42-auto-peer-daemon.py` straight from this checkout (as
  `slop`, with the Python venv under `~/.gemini/antigravity-cli/brain/.../scratch/venv`; see
  `systemctl cat dn42-auto-peer`). It provisions WireGuard tunnels and BIRD sessions, verifies
  convergence, and every few minutes rewrites the summary line in `PEERS.md`, commits only that
  file and pushes. Restart it after changing the script; never restart bird for doc changes.
- Peer inventory, pending requests and verified anycast DNS: `PEERS.md`. Peering PR forks live in
  `~/src/{baragoon,highdef,maiyun}-peering` (each with an `upstream` remote).
