#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Deploying DN42 configuration..."

# 1. Sysctl forwarding
echo "--> Installing sysctl forwarding..."
sudo cp "$SCRIPT_DIR/systemd/99-dn42.conf" /etc/sysctl.d/99-dn42.conf
sudo sysctl -p /etc/sysctl.d/99-dn42.conf > /dev/null

# 2. Dummy loopback interface in systemd-networkd
echo "--> Configuring dn42-dummy interface..."
sudo cp "$SCRIPT_DIR/systemd/20-dn42-dummy.netdev" /etc/systemd/network/20-dn42-dummy.netdev
sudo cp "$SCRIPT_DIR/systemd/20-dn42-dummy.network" /etc/systemd/network/20-dn42-dummy.network
sudo networkctl reload
sudo networkctl reconfigure dn42-dummy || true

# 3. WireGuard directory & permissions
echo "--> Ensuring WireGuard permissions..."
sudo mkdir -p /etc/wireguard
sudo chmod 755 /etc/wireguard
if [ ! -f /etc/wireguard/dn42.key ]; then
    sudo wg genkey | sudo tee /etc/wireguard/dn42.key | sudo wg pubkey | sudo tee /etc/wireguard/dn42.pub > /dev/null
    sudo chmod 600 /etc/wireguard/dn42.key
    sudo chmod 644 /etc/wireguard/dn42.pub
fi

# 4. BIRD 3 configuration & ROA
echo "--> Configuring BIRD..."
sudo mkdir -p /etc/bird/peers
sudo cp "$SCRIPT_DIR/bird/bird.conf" /etc/bird/bird.conf
sudo ln -sf /etc/bird/bird.conf /etc/bird.conf

# Initial ROA download if missing
if [ ! -f /etc/bird/roa_dn42.conf ] || [ ! -f /etc/bird/roa_dn42_v6.conf ]; then
    echo "--> Downloading initial ROA tables..."
    sudo curl -sSLf -o /etc/bird/roa_dn42.conf https://dn42.burble.com/roa/dn42_roa_bird2_4.conf
    sudo curl -sSLf -o /etc/bird/roa_dn42_v6.conf https://dn42.burble.com/roa/dn42_roa_bird2_6.conf
    sudo chmod 644 /etc/bird/roa_dn42*.conf
fi

# 5. ROA updater script & timer
echo "--> Installing ROA updater service & timer..."
sudo cp "$SCRIPT_DIR/bird/dn42-update-roa.sh" /usr/local/bin/dn42-update-roa.sh
sudo chmod +x /usr/local/bin/dn42-update-roa.sh
sudo cp "$SCRIPT_DIR/systemd/dn42-update-roa.service" /etc/systemd/system/
sudo cp "$SCRIPT_DIR/systemd/dn42-update-roa.timer" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now dn42-update-roa.timer

# 6. dn42ctl utility
echo "--> Installing dn42ctl CLI..."
sudo cp "$SCRIPT_DIR/bin/dn42ctl" /usr/local/bin/dn42ctl
sudo chmod +x /usr/local/bin/dn42ctl

# 7. Start/reload BIRD
echo "--> Starting / reloading BIRD..."
sudo systemctl enable --now bird
sudo birdc configure || sudo systemctl restart bird

echo "==> Deployment complete!"
dn42ctl status
