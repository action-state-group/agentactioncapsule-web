# Agent notes

## Before every push

Run `scripts/check.sh` (about 16 s on an Apple-silicon Mac). It runs what CI runs on pull requests and main, except the DCO sign-off check and the neutrality term scan, which needs the `NEUTRALITY_TERMS` secret (the scanner's self-test runs).
