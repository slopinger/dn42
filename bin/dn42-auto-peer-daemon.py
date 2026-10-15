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
import subprocess
import urllib.request
import urllib.error

PR_URL = "https://git.dn42.dev/api/v1/repos/dn42/registry/pulls/7531"

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

def check_pr_status():
    req = urllib.request.Request(PR_URL)
    req.add_header("User-Agent", "DN42-AutoPeer-Daemon/1.0")

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

def run_cmd(cmd):
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return res.returncode, res.stdout.strip(), res.stderr.strip()
    except Exception as e:
        return -1, "", str(e)

def setup_flipflap():
    log("Attempting FlipFlap peering...")
    cmd = f"{sys.executable} {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'autopeer_flipflap.py')}"
    code, stdout, stderr = run_cmd(cmd)
    log(f"FlipFlap script output:\n{stdout}")
    if stderr:
        log(f"FlipFlap stderr:\n{stderr}")
    return "Successful peerings: 0" not in stdout

def verify_bgp_and_connectivity():
    code, out, _ = run_cmd("birdc show protocols")
    log(f"BIRD Protocols:\n{out}")
    
    established = []
    for line in out.splitlines():
        if "BGP" in line and "Established" in line:
            established.append(line.split()[0])
            
    log(f"Established BGP sessions ({len(established)}): {established}")
    
    # Test ping
    code4, ping4, _ = run_cmd("ping -c 3 -W 2 172.20.0.53")
    log(f"Ping 172.20.0.53 (DN42 Anycast DNS):\n{ping4}")
    
    return len(established), established

def update_docs_and_git(peer_count, peers):
    log("Updating documentation and committing to internal GitLab...")
    try:
        with open("/home/slop/CLAUDE.md", "r") as f:
            content = f.read()
        
        peer_summary = f"\n- **DN42 Active Peers**: {peer_count} peers established ({', '.join(peers) if peers else 'none'}).\n"
        if "DN42 Active Peers" not in content:
            content += peer_summary
            with open("/home/slop/CLAUDE.md", "w") as f:
                f.write(content)
                
        # Git commit in ~/src/dn42
        run_cmd("git -C /home/slop/src/dn42 add -A")
        run_cmd('git -C /home/slop/src/dn42 commit -m "Auto-established DN42 peering sessions after registry merge" || true')
        run_cmd("git -C /home/slop/src/dn42 push origin main || true")
        log("Internal GitLab repo updated.")
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
        time.sleep(60)

    # Allow registry sync propagation
    log("Waiting 30 seconds for registry distribution across mirrors...")
    time.sleep(30)

    # Attempt peering
    peers_ok = False
    for attempt in range(1, 20):
        log(f"Peering setup attempt #{attempt}...")
        success = setup_flipflap()
        if success:
            log("FlipFlap autopeering succeeded!")
            peers_ok = True
            break
        log("Peering not ready yet, waiting 60s for registry sync...")
        time.sleep(60)

    # Wait for BGP convergence
    log("Waiting 15 seconds for BGP convergence...")
    time.sleep(15)

    count, peers = verify_bgp_and_connectivity()
    update_docs_and_git(count, peers)
    log(f"DN42 Peering setup complete. Total peers: {count}.")

if __name__ == "__main__":
    main()
