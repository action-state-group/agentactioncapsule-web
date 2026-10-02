#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Check that docs/witnesses.html lists exactly the rows of capsule-emit's witnesses.json.

The directory's source of truth is the root witnesses.json in capsule-emit. This site keeps a
copy in data/witnesses.json, and tools/build_docs.py renders the page from that copy. The check
fails if any of these differ:

  1. the source witnesses.json and data/witnesses.json (byte for byte, after JSON parsing);
  2. the rows rendered in docs/witnesses.html and the source rows (name, endpoint, since),
     in alphabetical order by name, with nothing added, dropped or reordered.

Run:
  python3 tools/check_witness_directory.py --source path/to/witnesses.json
  python3 tools/check_witness_directory.py --capsule-emit ../capsule-emit --commit <sha>

Exit 0 when they match, 1 on a mismatch, 2 on a usage or read error.
"""
from __future__ import annotations

import argparse
import html
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ROW = re.compile(r'<tr><th>(?P<name>[^<]*)</th><td><a class="ln" href="(?P<endpoint>[^"]*)">'
                 r'.*?</td><td>(?P<since>[^<]*)</td></tr>')


def load_source(args: argparse.Namespace) -> dict:
    if args.source:
        return json.loads(pathlib.Path(args.source).read_text(encoding="utf-8"))
    out = subprocess.run(["git", "-C", args.capsule_emit, "show", f"{args.commit}:witnesses.json"],
                         check=True, capture_output=True, text=True)
    return json.loads(out.stdout)


def expected_rows(directory: dict) -> list[tuple[str, str, str]]:
    rows = sorted(directory["witnesses"], key=lambda r: (r["name"].casefold(), r["endpoint"]))
    return [(r["name"], r["endpoint"], r["since"]) for r in rows]


def page_rows(page: str) -> list[tuple[str, str, str]]:
    # The directory is the first table on the page; its rows are the only ones with an endpoint link.
    start = page.index("<th>Name</th><th>Endpoint</th>")
    body = page[start:page.index("</table>", start)]
    return [(html.unescape(m["name"]), html.unescape(m["endpoint"]), html.unescape(m["since"]))
            for m in ROW.finditer(body)]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--source", help="a witnesses.json file")
    src.add_argument("--capsule-emit", help="a capsule-emit checkout; use with --commit")
    ap.add_argument("--commit", default="origin/main", help="capsule-emit commit to read (default origin/main)")
    ap.add_argument("--page", default=str(ROOT / "docs" / "witnesses.html"))
    ap.add_argument("--data", default=str(ROOT / "data" / "witnesses.json"))
    args = ap.parse_args()
    try:
        source = load_source(args)
        copy = json.loads(pathlib.Path(args.data).read_text(encoding="utf-8"))
        page = pathlib.Path(args.page).read_text(encoding="utf-8")
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    problems = []
    if copy != source:
        problems.append(f"{args.data} differs from the source witnesses.json; copy it and rebuild")
    want, got = expected_rows(source), page_rows(page)
    if got != want:
        problems.append("page rows differ from the source witnesses.json")
        for row in want:
            if row not in got:
                problems.append(f"  missing from page: {row}")
        for row in got:
            if row not in want:
                problems.append(f"  not in source:     {row}")
        if sorted(got) == sorted(want):
            problems.append(f"  same rows, wrong order: {[r[0] for r in got]}")
    if problems:
        print("FAIL witness directory", *problems, sep="\n")
        return 1
    print(f"OK witness directory: {len(got)} rows match the source ({', '.join(r[0] for r in got)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
