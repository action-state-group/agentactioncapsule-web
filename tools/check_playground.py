#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Checks for /playground.html and the verifier code it runs.

1. js/aac-crypto.js is the verify surface's own browser bundle, copied byte for byte, never
   edited: scitt-cose viewer/dist/aac-crypto.js at the commit below (the verify service at
   verify.agentactioncapsule.org serves the same file as /static/aac-crypto.js). The page
   hashes and canonicalises with it so there is one implementation, not two. To refresh, copy
   the new build and update both constants; ``--against <scitt-cose checkout>`` compares the
   copy with that checkout's build.
2. The registration endpoint in the page's config stays empty until live registration is
   approved: an empty endpoint means the page registers nothing.
3. The page loads no script but that copy.

Usage: python3 tools/check_playground.py [--against PATH]
Exit 0 = all checks pass; 1 = a check failed.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENDORED = ROOT / "js" / "aac-crypto.js"
VENDORED_SHA256 = "fb26a65546afefe71f27d2d4ee660771a4f89903ac8a164db1060bb59d232e81"
VENDORED_FROM = "action-state-group/scitt-cose@3d32059474b468f9cd851199a319d022aa38aef0:viewer/dist/aac-crypto.js"
VERIFY_URL = "https://verify.agentactioncapsule.org"
PAGE = ROOT / "playground.html"


def main(argv: list[str]) -> int:
    failures: list[str] = []

    digest = hashlib.sha256(VENDORED.read_bytes()).hexdigest()
    if digest != VENDORED_SHA256:
        failures.append(f"{VENDORED.relative_to(ROOT)} sha256 {digest} != pinned {VENDORED_SHA256} ({VENDORED_FROM})")
    if "--against" in argv:
        upstream = Path(argv[argv.index("--against") + 1]) / "viewer" / "dist" / "aac-crypto.js"
        if upstream.read_bytes() != VENDORED.read_bytes():
            failures.append(f"{VENDORED.relative_to(ROOT)} differs from {upstream}")

    html = PAGE.read_text(encoding="utf-8")
    m = re.search(r'<script id="playground-config" type="application/json">(.*?)</script>', html, re.S)
    if not m:
        failures.append("playground.html: no playground-config block")
    else:
        cfg = json.loads(m.group(1))
        if cfg.get("anchor") != "":
            failures.append(f"playground.html: registration endpoint is set ({cfg.get('anchor')!r}); "
                            "it stays empty until live registration is approved")
        if cfg.get("verify") != VERIFY_URL:
            failures.append(f"playground.html: verify is {cfg.get('verify')!r}, expected {VERIFY_URL!r}")

    srcs = re.findall(r'<script[^>]*\bsrc="([^"]*)"', html)
    if srcs != ["/js/aac-crypto.js"]:
        failures.append(f"playground.html: scripts loaded {srcs}, expected only ['/js/aac-crypto.js']")
    if "COPY js/" not in (ROOT / "Dockerfile").read_text(encoding="utf-8"):
        failures.append("Dockerfile does not copy js/, so /js/aac-crypto.js would 404")

    for f in failures:
        print(f"FAIL {f}")
    if not failures:
        print(f"ok: aac-crypto.js = {VENDORED_FROM}; registration endpoint empty; one script")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
