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
