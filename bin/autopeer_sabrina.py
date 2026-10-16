#!/usr/bin/env python3
"""
Automated DN42 Peering with Sabrina's testnet (AS4242421810)
Authenticates via iEdon Auth42 (oauth.dn42 / auth.iedon.net) using SSH signature
and provisions WireGuard + MP-BGP sessions on Sabrina's edge nodes.
"""

import sys
import os
import re
import json
import time
import subprocess
import urllib.request
import urllib.parse
import http.cookiejar

sys.path.append("/home/slop/src/dn42/bin")
import autopeer_headscarf as ah

MY_ASN = "4242420125"
MY_PUBKEY = "sgYSxYeBQX9IMbcj7zv6UxYYq7QQPDfMdaxHFlTeckY="
MY_IP = "45.150.123.24"
MY_LL = "fe80::125"
MY_EMAIL = "slopmoder@tutamail.com"

def peer_with_sabrina(node="de", local_port=21810):
    cli = ah.Client()
    cli.login_iedon()
    
    print("[*] Logging in to Sabrina's portal via iEdon...")
    u, html = cli.get("https://dn42.sabrinaishere.party/peer/auth/login?provider=iedon", referer="https://dn42.sabrinaishere.party/peer")
    if "consent" in u:
        print("[*] Submitting OAuth consent...")
        token = re.search(r'name="gorilla\.csrf\.Token" value="([^"]+)"', html).group(1)
        u, html = cli.post("https://auth.iedon.net/consent", {
            "gorilla.csrf.Token": token,
            "decision": "approve"
        }, referer="https://auth.iedon.net/consent")
    
    print(f"[+] Logged in! Reached {u}")
    
    print(f"[*] Querying edge info for node: {node}...")
    edge_url = f"https://dn42.sabrinaishere.party/peer/api/edge?node={node}&asn={MY_ASN}&panel=peer"
    u, resp = cli.get(edge_url, referer="https://dn42.sabrinaishere.party/peer")
    edge_data = json.loads(resp)
    
    form_html = edge_data["html"]
    csrf = re.search(r'name="csrf" value="([^"]+)"', form_html).group(1)
    request_id = re.search(r'name="request_id" value="([^"]+)"', form_html).group(1)
    print(f"[*] CSRF: {csrf}, request_id: {request_id}")
    
    post_data = {
        "panel": "peer",
        "expected_revision": "",
        "csrf": csrf,
        "mode": "peer",
        "target_asn": MY_ASN,
        "request_id": request_id,
        "node": node,
        "channel": "IPv6 & IPv4",
        "mp_bgp": "IPv6",
        "enh": "1",
        "ipv6": MY_LL,
        "request_linklocal": "fe80::1810",
        "ipv4": "",
        "clearnet": f"[2a0f:be01:0:100::113]:{local_port}",
        "public_key": MY_PUBKEY,
        "mtu": "Auto",
        "psk_action": "unchanged",
        "contact": MY_EMAIL
    }
    
    print("[*] Submitting peering request...")
    u, submit_resp = cli.post("https://dn42.sabrinaishere.party/peer/submit", post_data, referer="https://dn42.sabrinaishere.party/peer")
    print(f"[+] Submit response URL: {u}")
    try:
        data = json.loads(submit_resp)
        print("Submit response JSON:\n", json.dumps(data, indent=2))
    except Exception:
        print("Submit response HTML/text:\n", submit_resp[:1500])

if __name__ == "__main__":
    node = sys.argv[1] if len(sys.argv) > 1 else "de"
    peer_with_sabrina(node)
