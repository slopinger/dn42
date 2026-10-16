#!/usr/bin/env python3
"""
Automated DN42 Peering with HEADSCARF175 (AS4242420842)
Authenticates via iEdon Auth42 (oauth.dn42 / auth.iedon.net) using SSH signature
and provisions WireGuard + MP-BGP sessions on HEADSCARF175 nodes.
"""

import os
import re
import sys
import json
import time
import subprocess
import urllib.request
import urllib.parse
import http.cookiejar

MY_ASN = "4242420125"
KEY_PATH = "/home/slop/.ssh/id_ed25519_signing"
MY_PUBKEY = "sgYSxYeBQX9IMbcj7zv6UxYYq7QQPDfMdaxHFlTeckY="
MY_IP = "45.150.123.24"
MY_LL = "fe80::125"

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0"

class Client:
    def __init__(self):
        self.cj = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))
        self.headers = {"User-Agent": USER_AGENT}

    def get(self, url, referer=None):
        headers = dict(self.headers)
        if referer:
            headers["Referer"] = referer
        req = urllib.request.Request(url, headers=headers)
        with self.opener.open(req) as resp:
            return resp.geturl(), resp.read().decode()

    def post(self, url, data, referer=None):
        headers = dict(self.headers)
        if referer:
            headers["Referer"] = referer
        body = urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(url, data=body, headers=headers)
        with self.opener.open(req) as resp:
            return resp.geturl(), resp.read().decode()

    def login_iedon(self):
        print("[*] Fetching auth.iedon.net/login...")
        u, html = self.get("https://auth.iedon.net/login")
        token = re.search(r'name="gorilla\.csrf\.Token" value="([^"]+)"', html).group(1)

        print("[*] Querying ASN...")
        u, html2 = self.post("https://auth.iedon.net/login/query", {
            "gorilla.csrf.Token": token,
            "asn": MY_ASN
        }, referer="https://auth.iedon.net/login")
        token2 = re.search(r'name="gorilla\.csrf\.Token" value="([^"]+)"', html2).group(1)

        print("[*] Requesting SSH challenge...")
        u, html3 = self.post("https://auth.iedon.net/login/request", {
            "gorilla.csrf.Token": token2,
            "method_id": "1"
        }, referer="https://auth.iedon.net/login/query")
        token3 = re.search(r'name="gorilla\.csrf\.Token" value="([^"]+)"', html3).group(1)
        payload = re.search(r'data-copy="(DN42_VERIFY_[^"]+)"', html3).group(1)
        print(f"[*] Challenge payload: {payload}")

        print("[*] Signing challenge with ssh-keygen...")
        proc = subprocess.run(
            ["ssh-keygen", "-Y", "sign", "-f", KEY_PATH, "-n", "file"],
            input=payload.encode(), capture_output=True, check=True
        )
        sig = proc.stdout.decode().strip()

        print("[*] Submitting challenge response...")
        u, html4 = self.post("https://auth.iedon.net/login/challenge", {
            "gorilla.csrf.Token": token3,
            "response": sig
        }, referer="https://auth.iedon.net/login/request")
        print("[+] Logged in to auth.iedon.net successfully!")

    def login_headscarf(self):
        self.login_iedon()
        print("[*] Logging in to peer.headscarf175.net...")
        u, html = self.get("https://peer.headscarf175.net/auth/login", referer="https://peer.headscarf175.net/")
        if "consent" in u:
            print("[*] Submitting OAuth consent...")
            token = re.search(r'name="gorilla\.csrf\.Token" value="([^"]+)"', html).group(1)
            u, html = self.post("https://auth.iedon.net/consent", {
                "gorilla.csrf.Token": token,
                "decision": "approve"
            }, referer="https://auth.iedon.net/consent")
        print(f"[+] Reached {u}")
        return html

    def create_session(self, node="de-fra03", local_port=20842):
        print(f"[*] Loading session creation form for {node}...")
        u, html = self.get("https://peer.headscarf175.net/sessions/create", referer="https://peer.headscarf175.net/")
        csrf_token = re.search(r'name="_token" value="([^"]+)"', html).group(1)
        
        post_data = {
            "_token": csrf_token,
            "node": node,
            "transport": "wireguard",
            "wg_pubkey": MY_PUBKEY,
            "endpoint_host": MY_IP,
            "endpoint_port": str(local_port),
            "link_local": MY_LL,
            "local_link_local": "fe80::842",
            "ipv4_enh": "1",
            "ipv6_only": "0",
            "policy": "full",
            "strict_local_role": "0"
        }
        print(f"[*] Submitting session to {node} with data:\n{json.dumps(post_data, indent=2)}")
        u, resp_html = self.post("https://peer.headscarf175.net/sessions", post_data, referer="https://peer.headscarf175.net/sessions/create")
        print(f"[+] Post-submit URL: {u}")
        return u, resp_html

def main():
    cli = Client()
    cli.login_headscarf()
    u, html = cli.create_session("de-fra03", local_port=20842)
    print("Result HTML snippet:")
    for line in html.splitlines():
        if any(x in line for x in ("flash", "error", "notice", "alert", "de-fra03", "wireguard", "Endpoint", "20125")):
            print("  ", line.strip())

if __name__ == "__main__":
    main()

