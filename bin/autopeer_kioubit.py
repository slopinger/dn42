#!/usr/bin/env python3
"""
Automated DN42 Peering with Kioubit Network (AS4242423914) & Federated Portals
Authenticates via Kioubit's SSH challenge-response mechanism using ~/.ssh/id_ed25519_signing.
"""

import asyncio
import os
import sys
import re
import time
import json
import subprocess
import nodriver as uc

MY_ASN = "4242420125"
MY_WG_PUBKEY = "sgYSxYeBQX9IMbcj7zv6UxYYq7QQPDfMdaxHFlTeckY="
MY_ENDPOINT_ADDR = "45.150.123.24"
MY_ENDPOINT_PORT = "20125"
KEY_PATH = "/home/slop/.ssh/id_ed25519_signing"

def log(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)

async def authenticate_kioubit(page):
    log("Navigating to https://dn42.g-load.eu/auth/ ...")
    await page.get("https://dn42.g-load.eu/auth/")
    await asyncio.sleep(3)

    # 1. Fill ASN
    log(f"Entering ASN {MY_ASN}...")
    asn_input = await page.find("input[name=username], input[name=asn], input[placeholder*='424242']")
    if not asn_input:
        log("Could not find ASN input field")
        return False
    await asn_input.send_keys(MY_ASN)
    await asyncio.sleep(1)

    btn = await page.find("button[type=submit]")
    if btn:
        await btn.click()
    await asyncio.sleep(3)

    # Check for errors
    body = await page.evaluate("document.body.innerText")
    if "ASN Not Found" in body:
        log("Kioubit returned 'ASN Not Found' - registry update not propagated yet.")
        return False

    # 2. Method selection: select SSH
    log("Selecting SSH authentication method...")
    ssh_selected = await page.evaluate("""
        (() => {
            const labels = Array.from(document.querySelectorAll('label'));
            for (const l of labels) {
                if (l.innerText.includes('SSH')) {
                    const r = l.querySelector('input[type="radio"]') || l;
                    r.click();
                    return true;
                }
            }
            return false;
        })()
    """)
    if not ssh_selected:
        log("Could not select SSH method")
        return False

    await asyncio.sleep(1)
    btn_cont = await page.find("button[type=submit]")
    if btn_cont:
        await btn_cont.click()
    await asyncio.sleep(3)

    # 3. Read SSH verification target
    log("Checking for SSH connection instructions...")
    ssh_info = await page.evaluate("""
        (() => {
            const codeEl = document.querySelector('code[data-tmpl-text="{info}"], .alert-info code');
            return codeEl ? codeEl.innerText.trim() : null;
        })()
    """)
    log(f"SSH Target info: {ssh_info}")
    if not ssh_info:
        log("Could not find SSH verification target info")
        return False

    # Connect via SSH and get the code
    log(f"Executing SSH connection to {ssh_info} with {KEY_PATH}...")
    ssh_cmd = f"ssh -i {KEY_PATH} -o StrictHostKeyChecking=no -o ConnectTimeout=10 {ssh_info}"
    res = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True, timeout=20)
    ssh_out = (res.stdout + "\n" + res.stderr).strip()
    log(f"SSH Output:\n{ssh_out}")

    code_match = re.search(r'\b([0-9]{4,8})\b', ssh_out)
    if not code_match:
        log("Could not find numeric verification code in SSH output")
        return False
    v_code = code_match.group(1)
    log(f"Found verification code: {v_code}")

    # 4. Enter verification code
    code_input = await page.find("input[name=response]")
    if not code_input:
        log("Could not find response code input field")
        return False
    await code_input.send_keys(v_code)
    await asyncio.sleep(1)

    btn_submit = await page.find("button[type=submit]")
    if btn_submit:
        await btn_submit.click()
    await asyncio.sleep(4)

    body_after = await page.evaluate("document.body.innerText")
    log(f"Body text after verification:\n{body_after[:500]}")
    return "dashboard" in page.url or "success" in body_after.lower()

async def setup_kioubit_peerings(page):
    log("Navigating to Kioubit dashboard...")
    await page.get("https://dn42.g-load.eu/dashboard/")
    await asyncio.sleep(4)
    
    setup_js = """
    (async () => {
        try {
            const rNode = await fetch('/dashboard/api/nodeList');
            const nodes = JSON.parse(await rNode.text());
            
            const rPeer = await fetch('/dashboard/api/myPeerings');
            const peerings = JSON.parse(await rPeer.text());
            const existing = new Set(peerings.map(p => p.node));
            
            const candidates = [];
            for (const n of nodes) {
                if (n.acceptsNewPeerings === 1 && !existing.has(n.hostname)) {
                    candidates.push(n);
                }
            }
            
            candidates.sort((a, b) => {
                const aPri = (a.hostname.includes('de-') || a.hostname.includes('fra')) ? 0 : 1;
                const bPri = (b.hostname.includes('de-') || b.hostname.includes('fra')) ? 0 : 1;
                return aPri - bPri;
            });
            
            const toAdd = candidates.slice(0, 3);
            for (const target of toAdd) {
                const changes = {
                    Endpoint: "45.150.123.24:20125",
                    Wgkey: "sgYSxYeBQX9IMbcj7zv6UxYYq7QQPDfMdaxHFlTeckY=",
                    WGpsk: "",
                    V4: "",
                    V6: "",
                    Multiprotocol: 1,
                    Enexthop: 1,
                    LinkMTU: 1420
                };
                await fetch('/dashboard/api/setPeeringValues?node=' + encodeURIComponent(target.hostname) + '&changes=' + encodeURIComponent(JSON.stringify(changes)));
            }
            
            await new Promise(r => setTimeout(r, 2000));
            const rUpdated = await fetch('/dashboard/api/myPeerings');
            const updatedPeerings = JSON.parse(await rUpdated.text());
            
            const configs = [];
            for (const p of updatedPeerings) {
                const nodeObj = nodes.find(n => n.hostname === p.node);
                if (nodeObj) {
                    configs.push({
                        hostname: nodeObj.hostname,
                        port: p.port,
                        pubkey: nodeObj.wgkey,
                        peer_ll: nodeObj.v6,
                        my_ll: p.v6
                    });
                }
            }
            return {success: true, configs: configs};
        } catch(e) {
            return {success: false, error: String(e)};
        }
    })()
    """
    res = await page.evaluate(setup_js)
    log(f"Kioubit setup result: {res}")
    if not res or not res.get("success"):
        return False
        
    configs = res.get("configs", [])
    if not configs:
        log("No Kioubit peer configurations returned.")
        return False
        
    success_count = 0
    for cfg in configs:
        name = f"kioubit-{cfg['hostname']}"
        endpoint = f"{cfg['hostname']}.g-load.eu:{cfg['port']}"
        pubkey = cfg["pubkey"]
        peer_ll = cfg["peer_ll"]
        my_ll = cfg["my_ll"]
        
        log(f"Adding local peer {name} ({endpoint}, pubkey {pubkey}, peer_ll {peer_ll}, my_ll {my_ll})...")
        cmd = [
            "sudo", "/usr/local/bin/dn42ctl", "add-peer", name,
            "--asn", "4242423914",
            "--endpoint", endpoint,
            "--pubkey", pubkey,
            "--peer-ll-v6", peer_ll,
            "--my-ll-v6", my_ll
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        log(f"dn42ctl output:\n{proc.stdout}\n{proc.stderr}")
        if proc.returncode == 0:
            success_count += 1
            
    return success_count > 0

async def run():
    display = ":99"
    os.environ["DISPLAY"] = display
    xvfb = subprocess.Popen(["Xvfb", display, "-screen", "0", "1280x1024x24"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    openbox = subprocess.Popen(["openbox"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    await asyncio.sleep(1)

    try:
        browser = await uc.start(headless=False, browser_args=["--no-sandbox", "--disable-dev-shm-usage", "--window-size=1280,1024"])
        page = await browser.get("about:blank")
        auth_ok = await authenticate_kioubit(page)
        if not auth_ok:
            log("Kioubit authentication failed or not ready.")
            browser.stop()
            return False
            
        peering_ok = await setup_kioubit_peerings(page)
        browser.stop()
        return peering_ok
    finally:
        openbox.terminate()
        xvfb.terminate()

def main():
    success = uc.loop().run_until_complete(run())
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
