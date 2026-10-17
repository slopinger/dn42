#!/usr/bin/env python3
"""
DN42 Automated Peering Daemon for slop (AS4242420125)
Monitors PR #7531 on git.dn42.dev and automatically establishes peerings
across multiple DN42 backbone nodes as soon as the registry registration is merged.
"""

import os
import sys
import time
import json
import re
import base64
import subprocess
import urllib.request
import urllib.error

PR_URL = "https://git.dn42.dev/api/v1/repos/dn42/registry/pulls/7531"
GITEA_USER_FILE = "/home/slop/.secrets/dn42/username"
GITEA_PASS_FILE = "/home/slop/.secrets/dn42/password"

FLIPFLAP_NODES = [
    {"name": "flipflap-fra", "host": "de-fra1.flap42.eu", "port": 4242},
    {"name": "flipflap-ams", "host": "nl-ams2.flap42.eu", "port": 4242},
    {"name": "flipflap-par", "host": "fr-par1.flap42.eu", "port": 4242},
]

MY_ASN = "4242420125"
MY_WG_PUBKEY = "sgYSxYeBQX9IMbcj7zv6UxYYq7QQPDfMdaxHFlTeckY="
MY_ENDPOINT_ADDR = "45.150.123.24"
MY_ENDPOINT_PORT = "20125"
KEY_PATH = "/home/slop/.ssh/id_ed25519_signing"

def log(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)

def get_auth_header():
    try:
        with open(GITEA_USER_FILE, "r") as f:
            u = f.read().strip()
        with open(GITEA_PASS_FILE, "r") as f:
            p = f.read().strip()
        auth = base64.b64encode(f"{u}:{p}".encode()).decode()
        return f"Basic {auth}"
    except Exception as e:
        log(f"Error reading credentials: {e}")
        return None

def check_pr_status():
    req = urllib.request.Request(PR_URL)
    auth_hdr = get_auth_header()
    if auth_hdr:
        req.add_header("Authorization", auth_hdr)
    req.add_header("User-Agent", "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0")

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return {
                "state": data.get("state"),
                "merged": data.get("merged", False),
                "merged_at": data.get("merged_at"),
                "title": data.get("title")
            }
    except Exception as e:
        log(f"Error checking PR: {e}")
        return None

def run_cmd(cmd, timeout=180):
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return res.returncode, res.stdout.strip(), res.stderr.strip()
    except Exception as e:
        return -1, "", str(e)

def setup_flipflap():
    log("Attempting FlipFlap peering...")
    cmd = f"{sys.executable} {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'autopeer_flipflap.py')}"
    code, stdout, stderr = run_cmd(cmd, timeout=120)
    log(f"FlipFlap script output:\n{stdout}")
    if stderr:
        log(f"FlipFlap stderr:\n{stderr}")
    return "Successful peerings: 0" not in stdout

def setup_kioubit():
    log("Attempting Kioubit peering...")
    cmd = f"{sys.executable} {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'autopeer_kioubit.py')}"
    code, stdout, stderr = run_cmd(cmd, timeout=120)
    log(f"Kioubit script output:\n{stdout}")
    if stderr:
        log(f"Kioubit stderr:\n{stderr}")
    return code == 0

def setup_all_peers():
    ff_ok = setup_flipflap()
    kb_ok = setup_kioubit()
    return ff_ok or kb_ok

def update_roa_tables():
    log("Checking/updating DN42 ROA tables...")
    code, out, err = run_cmd("sudo /usr/local/bin/dn42-update-roa.sh")
    if code == 0:
        log("ROA tables updated successfully.")
    else:
        log(f"ROA update error: {err}")

def verify_bgp_and_connectivity():
    code, out, _ = run_cmd("sudo birdc show protocols")
    log(f"BIRD Protocols:\n{out}")
    
    established = []
    for line in out.splitlines():
        if "BGP" in line and "Established" in line:
            established.append(line.split()[0])
            
    log(f"Established BGP sessions ({len(established)}): {established}")
    
    # Test ping Anycast DNS IPv4 and IPv6
    code4, ping4, _ = run_cmd("ping -c 3 -W 2 172.20.0.53")
    log(f"Ping 172.20.0.53 (DN42 Anycast DNS IPv4):\n{ping4}")
    
    code6, ping6, _ = run_cmd("ping -c 3 -W 2 fd42:d42:d42:54::1")
    log(f"Ping fd42:d42:d42:54::1 (DN42 Anycast DNS IPv6):\n{ping6}")
    
    ping_ok = (code4 == 0 or code6 == 0)
    return len(established), established, ping_ok

PEERS_DOC = "/home/slop/src/dn42/PEERS.md"

def update_docs_and_git(peer_count, peers):
    log("Updating documentation and pushing ~/src/dn42 to origin (GitHub)...")
    try:
        with open(PEERS_DOC, "r") as f:
            content = f.read()
        
        peer_summary = f"\n- **DN42 Active Peers**: {peer_count} peers established ({', '.join(peers) if peers else 'none'}).\n"
        if "DN42 Active Peers" in content:
            content = re.sub(r"- \*\*DN42 Active Peers\*\*:[^\n]+", f"- **DN42 Active Peers**: {peer_count} peers established ({', '.join(peers) if peers else 'none'}).", content)
        else:
            content += peer_summary
            
        with open(PEERS_DOC, "w") as f:
            f.write(content)

        # Commit only the peer summary; other changes in the checkout are not ours to commit.
        run_cmd(f"git -C /home/slop/src/dn42 add -- {PEERS_DOC}")
        run_cmd(f'git -C /home/slop/src/dn42 commit -m "Auto-established DN42 peering sessions ({peer_count} peers)" -- {PEERS_DOC} || true')
        run_cmd("git -C /home/slop/src/dn42 push origin main || true")
        log("dn42 repo updated on GitHub (origin).")
    except Exception as e:
        log(f"Error updating docs: {e}")

def main():
    log("Starting DN42 Auto-Peer Daemon for AS4242420125...")
    
    # Check if already merged
    merged = False
    while not merged:
        status = check_pr_status()
        if status:
            log(f"PR #7531 status: state={status['state']}, merged={status['merged']}")
            if status["merged"]:
                log(f"PR #7531 IS MERGED! Merged at: {status['merged_at']}")
                merged = True
                break
        time.sleep(30)

    log("PR is merged! Entering active peering loop...")
    
    # Loop until we have multiple peers and ping connectivity
    iteration = 0
    while True:
        iteration += 1
        log(f"=== Peering loop iteration #{iteration} ===")
        
        # 1. Update ROA
        update_roa_tables()
        
        # 2. Attempt FlipFlap peering on remaining nodes
        setup_flipflap()
        
        # 3. Attempt Kioubit peering
        setup_kioubit()
        
        # 4. Verify BGP and ping
        count, peers, ping_ok = verify_bgp_and_connectivity()
        update_docs_and_git(count, peers)
        
        log(f"Iteration #{iteration} complete: {count} peers active ({peers}), ping_ok={ping_ok}")
        
        # If we have 3 or more peers and ping works, we can relax polling
        if count >= 3 and ping_ok:
            log(f"Target peering state reached! {count} peers established and ping working. Polling every 5m...")
            time.sleep(300)
        else:
            log("Continuing peering discovery in 60s...")
            time.sleep(60)

if __name__ == "__main__":
    main()
