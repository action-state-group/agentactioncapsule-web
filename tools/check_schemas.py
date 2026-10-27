#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Check that the schemas this site serves are byte-identical to their pinned upstream files.

Each JSON Schema whose $id is https://agentactioncapsule.org/<path> is copied unchanged into
this repo at <path>, and data/schemas-pin.json records, per file, the upstream repo, commit,
source path and sha256. The check fails if any of these hold:

  1. a served file's sha256 differs from its pin;
  2. a served file's $id is not https://agentactioncapsule.org/ followed by its own path;
  3. a file under schemas/ has no pin, or a pin has no file;
  4. with --upstream: the file at the pinned repo and commit differs from the pin.

Run:
  python3 tools/check_schemas.py
  python3 tools/check_schemas.py --upstream                       # fetch each pinned file
  python3 tools/check_schemas.py --upstream --git agent-action-capsule=../agent-action-capsule

--git NAME=DIR reads the pinned commit from a local clone instead of fetching it; NAME is the
repo's last path segment. To re-pin, copy the new bytes from the upstream commit and update the
file's commit and sha256 in data/schemas-pin.json in the same change.

Exit 0 when everything matches, 1 on a mismatch, 2 on a usage or read error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
PIN = ROOT / "data" / "schemas-pin.json"
SERVED_DIR = ROOT / "schemas"
ORIGIN = "https://agentactioncapsule.org/"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch_upstream(pin: dict, clones: dict[str, str]) -> bytes:
    name = pin["repo"].rsplit("/", 1)[-1]
    if name in clones:
        return subprocess.run(["git", "-C", clones[name], "show", f"{pin['commit']}:{pin['source']}"],
                              check=True, capture_output=True).stdout
    url = f"https://raw.githubusercontent.com/{pin['repo']}/{pin['commit']}/{pin['source']}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        return resp.read()


def check(upstream: bool, clones: dict[str, str]) -> list[str]:
    pins = json.loads(PIN.read_text(encoding="utf-8"))["files"]
    problems = []
    pinned_paths = {p["path"] for p in pins}
    served_paths = {f.relative_to(ROOT).as_posix() for f in SERVED_DIR.rglob("*") if f.is_file()}
    for path in sorted(served_paths - pinned_paths):
        problems.append(f"UNPINNED  {path}: served but not in {PIN.relative_to(ROOT)}")
    for path in sorted(pinned_paths - served_paths):
        problems.append(f"MISSING   {path}: pinned but not in the repo")

    for pin in pins:
        path = ROOT / pin["path"]
        if not path.is_file():
            continue
        data = path.read_bytes()
        if sha256(data) != pin["sha256"]:
            problems.append(f"DRIFT     {pin['path']}: sha256 {sha256(data)} != pinned {pin['sha256']}")
        want_id = ORIGIN + pin["path"]
        try:
            got_id = json.loads(data).get("$id")
        except json.JSONDecodeError as exc:
            got_id = f"<not JSON: {exc}>"
        if got_id != want_id or pin["id"] != want_id:
            problems.append(f"ID        {pin['path']}: $id {got_id!r}, pin {pin['id']!r}, served at {want_id!r}")
        if upstream:
            src = fetch_upstream(pin, clones)
            if sha256(src) != pin["sha256"]:
                problems.append(f"UPSTREAM  {pin['path']}: {pin['repo']}@{pin['commit']}:{pin['source']} "
                                f"sha256 {sha256(src)} != pinned {pin['sha256']}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--upstream", action="store_true", help="also compare each pin to the file at its pinned commit")
    ap.add_argument("--git", action="append", default=[], metavar="NAME=DIR",
                    help="read repo NAME from a local clone at DIR instead of fetching it")
    args = ap.parse_args()
    clones = {}
    for item in args.git:
        name, sep, directory = item.partition("=")
        if not sep:
            print(f"error: --git expects NAME=DIR, got {item!r}", file=sys.stderr)
            return 2
        clones[name] = directory
    try:
        problems = check(args.upstream, clones)
    except (OSError, KeyError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    for line in problems:
        print(line)
    if problems:
        return 1
    count = len(json.loads(PIN.read_text(encoding="utf-8"))["files"])
    print(f"OK  {count} served schemas match their pins" + (" and their upstream commits" if args.upstream else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
