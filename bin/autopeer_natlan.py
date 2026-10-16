#!/usr/bin/env python3
"""
Automated DN42 Peering with NATLAN (AS4242420028)
Authenticates via NATLAN OpenID Provider (https://auth.natlan.io) using SSH signature
(ssh-keygen -Y sign -f ~/.ssh/id_ed25519_signing -n dn42-autopeer)
and provisions WireGuard + MP-BGP sessions on NATLAN edge nodes.
"""

import sys
import os
import re
import json
import time
import subprocess
import urllib.request
import urllib.parse

MY_ASN = 4242420125
KEY_PATH = "/home/slop/.ssh/id_ed25519_signing"
MY_PUBKEY = "sgYSxYeBQX9IMbcj7zv6UxYYq7QQPDfMdaxHFlTeckY="
MY_IP = "45.150.123.24"
DEFAULT_PORT = 20028
MY_LL = "fe80::125"

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0"

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def api_get(url, token=None):
    headers = {"User-Agent": USER_AGENT}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

def api_post(url, data=None, token=None):
    headers = {"User-Agent": USER_AGENT, "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data is not None else b"{}"
    req = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

def authenticate():
    log("Step 1: Fetching login URL from Natlan autopeering API...")
    login_info = api_get("https://api.natlan.io/control/v1/autopeering/auth/login-url")
    auth_url = login_info["authorize_url"]
    qs = urllib.parse.urlparse(auth_url).query

    log("Step 2: Fetching OAuth authorize context from auth.natlan.io...")
    ctx = api_get(f"https://auth.natlan.io/api/v1/oauth/authorize-context?{qs}")

    log("Step 3: Querying verification options for AS4242420125...")
    opts = api_post("https://auth.natlan.io/api/v1/verification-options", {"asn": MY_ASN})
    ssh_opt = None
    for opt in opts.get("options", []):
        if opt.get("kind") == "ssh":
            ssh_opt = opt
            break

    if not ssh_opt:
        raise RuntimeError("No SSH verification option found for AS4242420125 on Natlan!")

    log(f"Found SSH option {ssh_opt['id']} ({ssh_opt['comment']})")

    log("Step 4: Requesting challenge nonce...")
    chal = api_post("https://auth.natlan.io/api/v1/challenge", {
        "asn": MY_ASN,
        "option_id": ssh_opt["id"],
        "captcha_token": "",
        "captcha_pass": ""
    })
    challenge_id = chal["challenge_id"]
    nonce = chal["nonce"]
    log(f"Received nonce: {nonce}")

    log("Step 5: Signing nonce with ssh-keygen...")
    cmd = f'printf %s "{nonce}" | ssh-keygen -Y sign -f {KEY_PATH} -n dn42-autopeer'
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
    sig = proc.stdout.strip()
    if not sig or "BEGIN SSH SIGNATURE" not in sig:
        sig = proc.stderr.strip()
    log("Signature created successfully.")

    log("Step 6: Submitting signature...")
    sub_res = api_post("https://auth.natlan.io/api/v1/challenge/submit", {
        "challenge_id": challenge_id,
        "answer": sig
    })
    auth_token = sub_res["token"]
    log("Authentication token obtained.")

    log("Step 7: Approving OAuth consent...")
    approve_data = {**ctx["params"], "deny": False}
    app_res = api_post("https://auth.natlan.io/api/v1/oauth/approve", approve_data, token=auth_token)
    redirect_to = app_res["redirect_to"]

    log("Step 8: Following callback redirect for handoff token...")
    opener = urllib.request.build_opener(NoRedirect)
    curr_url = redirect_to
    handoff = None
    while curr_url:
        try:
            req = urllib.request.Request(curr_url, headers={"User-Agent": USER_AGENT})
            opener.open(req)
            curr_url = None
        except urllib.error.HTTPError as e:
            loc = e.headers.get("Location", "")
            m = re.search(r"handoff=([^&]+)", loc)
            if m:
                handoff = m.group(1)
                break
            curr_url = loc

    if not handoff:
        raise RuntimeError(f"Could not extract handoff token from {redirect_to}")

    log(f"Step 9: Exchanging handoff token for session token...")
    ex_res = api_post("https://api.natlan.io/control/v1/autopeering/auth/exchange", {"handoff": handoff})
    session_token = ex_res["session_token"]
    log("Successfully logged in to Natlan autopeering system!")
    return session_token

def peer_with_node(session_token, node_id, local_port=DEFAULT_PORT):
    log(f"Querying node info for {node_id}...")
    nodes_info = api_get("https://api.natlan.io/control/v1/autopeering/nodes", token=session_token)
    target_node = None
    for n in nodes_info.get("nodes", []):
        if n.get("node_id") == node_id:
            target_node = n
            break

    if not target_node:
        raise RuntimeError(f"Node {node_id} not found in node list!")

    log(f"Submitting peering request for node {node_id}...")
    req_body = {
        "node_id": node_id,
        "public_key": MY_PUBKEY,
        "endpoint": f"{MY_IP}:{local_port}",
        "link_local": MY_LL
    }
    
    res = api_post("https://api.natlan.io/control/v1/autopeering/requests", req_body, token=session_token)
    log(f"Peering request response:\n{json.dumps(res, indent=2)}")
    return res

def main():
    token = authenticate()
    
    # List active requests
    existing = api_get("https://api.natlan.io/control/v1/autopeering/requests", token=token)
    log(f"Existing requests: {json.dumps(existing, indent=2)}")
    
    # Check if fra1 is already requested
    node_id = "fra1"
    res = peer_with_node(token, node_id, local_port=20028)
    print("\nResult:", json.dumps(res, indent=2))

if __name__ == "__main__":
    main()
