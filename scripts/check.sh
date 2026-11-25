#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Local check run before every push: the commands the pull_request and main CI jobs run.
# Not run here: dco (commit sign-off) and the neutrality term scan, which needs the
# NEUTRALITY_TERMS secret; the scanner's self-test runs.
set -euo pipefail
cd "$(dirname "$0")/.."

# neutrality.yml
python3 .github/neutrality_scan.py --self-test
# schemas.yml
python3 tools/check_schemas.py --upstream
# verify-bundle.yml
node --test tests/*.test.mjs
tools/vendor_verifier.sh --check
