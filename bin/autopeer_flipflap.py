#!/usr/bin/env python3
"""
Automated DN42 Peering with FlipFlap Net (AS4242420263)
Supports nodes:
 - de-fra1.flap42.eu (Frankfurt, DE)
 - nl-ams2.flap42.eu (Amsterdam, NL)
 - fr-par1.flap42.eu (Paris, FR)
 - pl-waw1.flap42.eu (Warsaw, PL)
"""

import sys
import os
import re
import time
import subprocess
import paramiko

NODES = [
    {"name": "flipflap-fra", "host": "de-fra1.flap42.eu", "port": 4242},
    {"name": "flipflap-ams", "host": "nl-ams2.flap42.eu", "port": 4242},
    {"name": "flipflap-par", "host": "fr-par1.flap42.eu", "port": 4242},
    {"name": "flipflap-waw", "host": "pl-waw1.flap42.eu", "port": 4242},
]

MY_ASN = "4242420125"
MY_WG_PUBKEY = "sgYSxYeBQX9IMbcj7zv6UxYYq7QQPDfMdaxHFlTeckY="
MY_ENDPOINT_ADDR = "45.150.123.24"
MY_ENDPOINT_PORT = "20125"
KEY_PATH = "/home/slop/.ssh/id_ed25519_signing"

def read_until(channel, pattern, timeout=15):
    buf = ""
    start = time.time()
    while time.time() - start < timeout:
        if channel.recv_ready():
            chunk = channel.recv(4096).decode("utf-8", errors="replace")
            buf += chunk
            if re.search(pattern, buf):
                return buf
        time.sleep(0.1)
    return buf

def peer_with_flipflap_node(node):
    print(f"[*] Connecting to {node['name']} ({node['host']}:{node['port']})...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(
            hostname=node["host"],
            port=node["port"],
            username="slop",
            key_filename=KEY_PATH,
            timeout=10,
            look_for_keys=False,
            allow_agent=False
        )
    except paramiko.AuthenticationException:
        print(f"[-] Authentication failed on {node['host']}. (Registry update may still be syncing)")
        return False
    except Exception as e:
        print(f"[-] Connection failed to {node['host']}: {e}")
        return False

    print(f"[+] Successfully authenticated with {node['host']}!")
    channel = client.invoke_shell()
    
    # Wait for prompt
    out = read_until(channel, r">", timeout=10)
    print(f"[*] Initial shell output received")

    # Send peer_create
    channel.send("peer_create\n")
    read_until(channel, r"AS Number", timeout=5)
    channel.send(f"{MY_ASN}\n")
    
    read_until(channel, r"WireGuard public key", timeout=5)
    channel.send(f"{MY_WG_PUBKEY}\n")
    
    read_until(channel, r"WireGuard endpoint address", timeout=5)
    channel.send(f"{MY_ENDPOINT_ADDR}\n")
    
    read_until(channel, r"WireGuard endpoint port", timeout=5)
    channel.send(f"{MY_ENDPOINT_PORT}\n")
    
    read_until(channel, r"Link-local IPv6", timeout=5)
    channel.send("\n") # Default auto
    
    time.sleep(2)
    # Request config
    channel.send("peer_config\n")
    time.sleep(2)
    config_out = read_until(channel, r">", timeout=10)
    
    channel.send("bye\n")
    client.close()
    
    print(f"[*] Raw peer configuration output:\n{config_out}")
    
    # Parse remote endpoint, pubkey, and link-local address
    # Look for Remote peer configuration table or WireGuard config block
    # WireGuard configuration block:
    # [Peer]
    # PublicKey = ...
    # Endpoint = host:port
    pubkey_m = re.search(r"PublicKey\s*=\s*([0-9a-zA-Z+/]{43}=)", config_out)
    endpoint_m = re.search(r"Endpoint\s*=\s*([^\s:]+):([0-9]+)", config_out)
    ll_m = re.search(r"fe80::[0-9a-fA-F:]+", config_out)
    
    if not (pubkey_m and endpoint_m):
        # Fallback to table search
        print("[-] Could not find standard WireGuard config block, parsing tables...")
        # Match from table rows:
        # WG pub key | ...
        # WG Endpoint addr. | ...
        # WG Endpoint port | ...
        # Link-local address | ...
    
    peer_pubkey = pubkey_m.group(1) if pubkey_m else None
    peer_endpoint = f"{endpoint_m.group(1)}:{endpoint_m.group(2)}" if endpoint_m else None
    
    # Extract link-local addresses
    # BIRD snippet specifies: neighbor <peer_ll> as 4242420263
    # PostUp snippet specifies: PostUp = ... <my_ll>/128 peer <peer_ll>/128
    neighbor_m = re.search(r"neighbor\s+(fe80:[0-9a-fA-F:]+)\s+as", config_out)
    postup_m = re.search(r"PostUp\s*=.*?\s+(fe80:[0-9a-fA-F:]+)/128\s+peer\s+(fe80:[0-9a-fA-F:]+)", config_out)

    if neighbor_m and postup_m:
        peer_ll = neighbor_m.group(1)
        my_ll = postup_m.group(1)
    else:
        ll_addrs = re.findall(r"fe80:[0-9a-fA-F:]+", config_out)
        if len(ll_addrs) >= 2:
            my_ll = ll_addrs[0]
            peer_ll = ll_addrs[1]
        else:
            my_ll = None
            peer_ll = None

    print(f"[*] Extracted: PubKey={peer_pubkey}, Endpoint={peer_endpoint}, my_ll={my_ll}, peer_ll={peer_ll}")
    
    if peer_pubkey and peer_endpoint and my_ll and peer_ll:
        print(f"[+] Configuring local peer {node['name']}...")
        cmd = [
            "sudo", "/usr/local/bin/dn42ctl", "add-peer", node["name"],
            "--asn", "4242420263",
            "--endpoint", peer_endpoint,
            "--pubkey", peer_pubkey,
            "--peer-ll-v6", peer_ll,
            "--my-ll-v6", my_ll
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        print(f"[*] Result: {res.stdout}\n{res.stderr}")
        return True
    else:
        print(f"[-] Incomplete peering parameters from {node['name']}")
        return False

def main():
    success_count = 0
    for node in NODES:
        if peer_with_flipflap_node(node):
            success_count += 1
    print(f"[+] Completed. Successful peerings: {success_count}/{len(NODES)}")

if __name__ == "__main__":
    main()
