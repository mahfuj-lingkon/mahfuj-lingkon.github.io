#!/usr/bin/env python3
"""Mobile layout regression test (no external Python deps).

Loads the built site in headless Chromium at several phone widths and
asserts that nothing forces horizontal overflow — the bug that clipped
the footer on mobile.

Uses the Chromium shipped with Hermes/agent-browser over the DevTools
Protocol, so no `pip install playwright` is required.

Requires the site to be built first (`hugo`).

Usage:  python3 scripts/test_mobile_layout.py
Exit 0 = pass, 1 = failure, 0 = skipped (no chromium found).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

WIDTHS = [320, 360, 375, 390, 414, 430]
PAGES = ["/", "/about/", "/skills/", "/contact/", "/experience/", "/404.html"]
PORT = 8899


def find_chromium():
    """Locate a Chromium/Chrome binary (Hermes bundle first, then system)."""
    home = Path.home()
    candidates = []
    for pat in ("**/chromium-*/chrome-mac/Chromium.app/Contents/MacOS/Chromium",
                "**/chromium-*/chrome-linux/chrome",
                "**/chromium-*/chrome-linux64/chrome"):
        candidates += list(home.glob(f".hermes/tools/{pat}"))
    candidates += [
        Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
    ]
    for c in candidates:
        if c.exists() and os.access(c, os.X_OK):
            return str(c)
    for name in ("chromium", "chromium-browser", "google-chrome", "chrome"):
        p = shutil.which(name)
        if p:
            return p
    return None


def http_json(url, timeout=10):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode())


class CDP:
    """Tiny synchronous CDP client over a raw websocket (stdlib only)."""

    def __init__(self, ws_url):
        import base64
        import socket
        from urllib.parse import urlparse

        u = urlparse(ws_url)
        self.sock = socket.create_connection((u.hostname, u.port), timeout=20)
        key = base64.b64encode(os.urandom(16)).decode()
        path = u.path + (f"?{u.query}" if u.query else "")
        req = (
            f"GET {path} HTTP/1.1\r\nHost: {u.hostname}:{u.port}\r\n"
            f"Upgrade: websocket\r\nConnection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(req.encode())
        # drain handshake headers
        buf = b""
        while b"\r\n\r\n" not in buf:
            buf += self.sock.recv(4096)
        self._id = 0
        self._buf = b""

    def _send_frame(self, payload: bytes):
        import struct
        mask = os.urandom(4)
        n = len(payload)
        header = bytearray([0x81])
        if n < 126:
            header.append(0x80 | n)
        elif n < (1 << 16):
            header.append(0x80 | 126)
            header += struct.pack(">H", n)
        else:
            header.append(0x80 | 127)
            header += struct.pack(">Q", n)
        header += mask
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        self.sock.sendall(bytes(header) + masked)

    def _recv_exact(self, n):
        while len(self._buf) < n:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise ConnectionError("socket closed")
            self._buf += chunk
        out, self._buf = self._buf[:n], self._buf[n:]
        return out

    def _recv_frame(self):
        b0, b1 = self._recv_exact(2)
        length = b1 & 0x7F
        if length == 126:
            length = int.from_bytes(self._recv_exact(2), "big")
        elif length == 127:
            length = int.from_bytes(self._recv_exact(8), "big")
        return self._recv_exact(length)

    def call(self, method, params=None):
        self._id += 1
        mid = self._id
        self._send_frame(json.dumps({"id": mid, "method": method,
                                     "params": params or {}}).encode())
        while True:
            msg = json.loads(self._recv_frame())
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg.get("result", {})

    def evaluate(self, expr):
        r = self.call("Runtime.evaluate", {
            "expression": expr, "returnByValue": True, "awaitPromise": True})
        return r.get("result", {}).get("value")

    def close(self):
        try:
            self.sock.close()
        except Exception:
            pass


MEASURE_JS = """(() => {
  const docW = document.documentElement.clientWidth;
  const clipped = el => {
    if (!el) return false;
    const b = el.getBoundingClientRect();
    return b.right > docW + 1 || b.left < -1;
  };
  return {
    docW,
    scrollW: document.documentElement.scrollWidth,
    brand: clipped(document.querySelector('.footer-brand')),
    copy: clipped(document.querySelector('.footer-copy')),
    links: clipped(document.querySelector('.footer-links')),
  };
})()"""


def wait_for_server(url, timeout=15):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=2)
            return True
        except Exception:
            time.sleep(0.4)
    return False


def main():
    root = Path(__file__).resolve().parent.parent
    chromium = find_chromium()
    if not chromium:
        print("SKIP: no Chromium binary found")
        return 0

    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT), "--directory", str(root / "public")],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f"http://localhost:{PORT}"
    if not wait_for_server(base):
        print("ERROR: local server did not start")
        server.kill()
        return 1

    profile = tempfile.mkdtemp(prefix="mobile-test-")
    browser = subprocess.Popen(
        [chromium, "--headless=new", "--remote-debugging-port=0",
         f"--user-data-dir={profile}", "--no-first-run", "--no-default-browser-check",
         "--disable-gpu", "--hide-scrollbars", "about:blank"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    failures, checks = [], 0
    try:
        # discover the debugging port from stderr
        ws = None
        deadline = time.time() + 25
        while time.time() < deadline and not ws:
            line = browser.stderr.readline()
            if not line:
                time.sleep(0.1)
                continue
            if "DevTools listening on" in line:
                ws = line.split("DevTools listening on", 1)[1].strip()
        if not ws:
            print("ERROR: could not get DevTools endpoint")
            return 1

        port = ws.split(":")[2].split("/")[0]
        targets = http_json(f"http://127.0.0.1:{port}/json/list")
        page = next((t for t in targets if t.get("type") == "page"), None)
        if not page:
            print("ERROR: no page target")
            return 1

        cdp = CDP(page["webSocketDebuggerUrl"])
        cdp.call("Page.enable")
        cdp.call("Runtime.enable")

        for path in PAGES:
            for w in WIDTHS:
                cdp.call("Emulation.setDeviceMetricsOverride",
                         {"width": w, "height": 844, "deviceScaleFactor": 3, "mobile": True})
                cdp.call("Page.navigate", {"url": base + path})
                time.sleep(0.6)
                res = cdp.evaluate(MEASURE_JS)
                checks += 1
                if not isinstance(res, dict):
                    failures.append(f"{path} @ {w}px: could not measure")
                    continue
                if res["scrollW"] > res["docW"] + 1:
                    failures.append(
                        f"{path} @ {w}px: horizontal overflow "
                        f"(scrollWidth {res['scrollW']} > viewport {res['docW']})")
                for part in ("brand", "copy", "links"):
                    if res[part]:
                        failures.append(f"{path} @ {w}px: footer .{part} is clipped")
        cdp.close()
    finally:
        browser.kill()
        server.kill()
        shutil.rmtree(profile, ignore_errors=True)

    print(f"Mobile layout checks: {checks}")
    if failures:
        print(f"\n{len(failures)} FAILURE(S):")
        for f in failures:
            print(f"  ✗ {f}")
        return 1
    print("\n✓ No horizontal overflow or footer clipping at any tested width.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
