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

async def run():
    display = ":99"
    os.environ["DISPLAY"] = display
    xvfb = subprocess.Popen(["Xvfb", display, "-screen", "0", "1280x1024x24"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    openbox = subprocess.Popen(["openbox"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    await asyncio.sleep(1)

    try:
        browser = await uc.start(headless=False, browser_args=["--no-sandbox", "--disable-dev-shm-usage", "--window-size=1280,1024"])
        page = await browser.get("about:blank")
        success = await authenticate_kioubit(page)
        browser.stop()
        return success
    finally:
        openbox.terminate()
        xvfb.terminate()

def main():
    success = uc.loop().run_until_complete(run())
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
