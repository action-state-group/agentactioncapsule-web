#!/usr/bin/env bash
# Build docs/vendor/aac-bundle-verifier.js from the pinned AAC release (tools/vendor/package.json +
# package-lock.json), or with --check rebuild it and fail if the committed file or its record differs.
# Authoring/CI time only: the deployed site loads the vendored file from itself, never from a CDN.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
mode="${1:-build}"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
cp "$root/tools/vendor/package.json" "$root/tools/vendor/package-lock.json" "$root/tools/vendor/entry.js" "$work/"
(cd "$work" && npm ci --silent --ignore-scripts=false >/dev/null)
(cd "$work" && ./node_modules/.bin/esbuild entry.js --bundle --format=esm --platform=browser \
  --conditions=browser --minify --legal-comments=eof --log-level=warning --outfile=out.js)
sha="$(shasum -a 256 "$work/out.js" | cut -d' ' -f1)"
ver() { node -p "require('$work/node_modules/$1/package.json').version"; }
record="$(printf '{\n  "package": "@action-state-group/agent-action-capsule",\n  "version": "%s",\n  "cll": "%s",\n  "esbuild": "%s",\n  "sha256": "%s",\n  "source": "https://github.com/action-state-group/agent-action-capsule/tree/ts/v%s/ts",\n  "build": "tools/vendor_verifier.sh"\n}\n' \
  "$(ver @action-state-group/agent-action-capsule)" "$(ver @action-state-group/cll)" "$(ver esbuild)" "$sha" "$(ver @action-state-group/agent-action-capsule)")"
if [ "$mode" = "--check" ]; then
  cmp -s "$work/out.js" "$root/docs/vendor/aac-bundle-verifier.js" || { echo "FAIL: docs/vendor/aac-bundle-verifier.js differs from the pinned release build (rebuilt sha256 $sha)"; exit 1; }
  [ "$record" = "$(cat "$root/docs/vendor/aac-bundle-verifier.json")" ] || { echo "FAIL: docs/vendor/aac-bundle-verifier.json differs from the rebuild"; exit 1; }
  echo "OK: vendored verifier matches the pinned release build (sha256 $sha)"
else
  cp "$work/out.js" "$root/docs/vendor/aac-bundle-verifier.js"
  printf '%s\n' "$record" > "$root/docs/vendor/aac-bundle-verifier.json"
  echo "built docs/vendor/aac-bundle-verifier.js sha256 $sha"
fi
