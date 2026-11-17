// Run: node --test tests/*.test.mjs
// Fixtures are cases from vectors/bundle/strict in agent-action-capsule (ts/v0.14.0 era).
import test from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import * as lib from "../docs/vendor/aac-bundle-verifier.js";
import { checkBundleText } from "../docs/vendor/bundle-check.js";

const read = (p) => readFileSync(new URL(p, import.meta.url), "utf8");
const valid = read("./fixtures/strict-valid-bundle.json");
const check = (text) => checkBundleText(text, lib);

async function withoutCrypto(replacement, fn) {
  const saved = Object.getOwnPropertyDescriptor(globalThis, "crypto");
  Object.defineProperty(globalThis, "crypto", { value: replacement, configurable: true, writable: true });
  try {
    return await fn();
  } finally {
    Object.defineProperty(globalThis, "crypto", saved);
  }
}

test("a strict-valid bundle is verified, signatures claim passing", async () => {
  const r = await check(valid);
  assert.equal(r.state, "verified");
  assert.equal(r.claims.find((c) => c.name === "signatures").status, "pass");
  assert.ok(r.records.length > 0 && r.records.every((x) => x.signature === "authored" && x.identityOk));
});

test("a one-byte change to any record signature fails", async () => {
  const bundle = JSON.parse(valid);
  for (let i = 0; i < bundle.records.length; i++) {
    const copy = JSON.parse(valid);
    const sig = copy.records[i].signature;
    const at = sig.length - 2;
    copy.records[i].signature = sig.slice(0, at) + (sig[at] === "0" ? "1" : "0") + sig.slice(at + 1);
    const r = await check(JSON.stringify(copy));
    assert.equal(r.state, "failed", `record ${i}`);
    assert.equal(r.records[i].signature, "invalid", `record ${i}`);
  }
});

test("an unsigned record is incomplete, not verified", async () => {
  const r = await check(read("./fixtures/strict-incomplete-unsigned-record.json"));
  assert.equal(r.state, "incomplete");
});

test("with crypto.subtle removed the valid bundle is cannot-check, not failed", async () => {
  const r = await withoutCrypto({}, () => check(valid));
  assert.deepEqual(r, { state: "cannot-check", detail: "ed25519" });
});

test("with no crypto object at all the valid bundle is cannot-check", async () => {
  const r = await withoutCrypto(undefined, () => check(valid));
  assert.equal(r.state, "cannot-check");
});

test("a subtle without Ed25519 is cannot-check, not failed", async () => {
  const real = globalThis.crypto.subtle;
  const noEd25519 = {
    subtle: new Proxy(real, {
      get(target, prop) {
        if (prop === "importKey") {
          return (fmt, key, algo, ...rest) => {
            if (algo?.name === "Ed25519") return Promise.reject(Object.assign(new Error("no"), { name: "NotSupportedError" }));
            return target.importKey(fmt, key, algo, ...rest);
          };
        }
        const v = target[prop];
        return typeof v === "function" ? v.bind(target) : v;
      },
    }),
  };
  const r = await withoutCrypto(noEd25519, () => check(valid));
  assert.equal(r.state, "cannot-check");
});

test("input that is not JSON is not-a-bundle", async () => {
  assert.equal((await check("{nope")).state, "not-a-bundle");
});

test("JSON that is not an evidence bundle is nothing to verify, not failed", async () => {
  assert.deepEqual(await check("[]"), { state: "not-a-bundle", detail: "not-an-evidence-bundle" });
  assert.equal((await check("{}")).detail, "not-an-evidence-bundle");
});

test("a changed number spelling is not normalised away (1 -> 1.0 must not verify)", async () => {
  const respelled = valid.replace('"seq": 1,', '"seq": 1.0,');
  assert.notEqual(respelled, valid);
  const r = await check(respelled);
  assert.notEqual(r.state, "verified");
});

test("a failure outside the seven claims is shown, so a failed verdict is never above an all-pass table", async () => {
  const b = JSON.parse(valid);
  b.checkpoint.witnesses = [{}];
  const r = await check(JSON.stringify(b));
  assert.equal(r.state, "failed");
  assert.ok(r.claims.every((c) => c.status === "pass"), "all seven claims pass");
  const w = r.beside.find((x) => x.name === "witnesses");
  assert.equal(w.status, "fail");
  assert.ok(w.findings.length > 0);
});

test("category coverage that was not checked is withheld, never a green pass", async () => {
  const props = lib.CATEGORY_COVERAGE_PROPERTIES;
  const coverage = Object.fromEntries(props.map((p, i) => [p, i === 0 ? "PASS" : i % 2 ? "NOT_CHECKED" : "INCONCLUSIVE"]));
  const stub = {
    ...lib,
    decodeFragment: () => ({}),
    verifyBundle: async () => ({
      categoryCoverage: coverage,
      strict: { verdict: "VALID", kindOk: true, claims: [{ name: "signatures", status: "pass", findings: [] }], witnesses: null, parentWitness: null, records: [] },
    }),
  };
  const r = await checkBundleText("{}", stub);
  const row = r.beside.find((x) => x.name === "category_coverage");
  assert.equal(row.status, "withheld");
  assert.ok(row.findings.length > 0 && row.findings.every((f) => /=(NOT_CHECKED|INCONCLUSIVE)$/.test(f)));
});

test("the vendored verifier matches its recorded SHA-256", () => {
  const rec = JSON.parse(read("../docs/vendor/aac-bundle-verifier.json"));
  const sha = createHash("sha256").update(readFileSync(new URL("../docs/vendor/aac-bundle-verifier.js", import.meta.url))).digest("hex");
  assert.equal(sha, rec.sha256);
  assert.match(rec.version, /^\d+\.\d+\.\d+$/);
});

test("nothing that reads the bundle can send it anywhere", () => {
  const page = read("../docs/verify-a-capsule.html");
  assert.match(page, /Content-Security-Policy" content="[^"]*connect-src 'none'/);
  for (const file of ["../docs/vendor/bundle-check.js", "../docs/vendor/aac-bundle-verifier.js"]) {
    assert.doesNotMatch(read(file), /\bfetch\s*\(|XMLHttpRequest|sendBeacon|WebSocket|EventSource/, file);
  }
  const inline = [...page.matchAll(/<script type="module" id="bundle-verify">([\s\S]*?)<\/script>/g)].map((m) => m[1]).join("\n");
  assert.ok(inline.length > 0, "page verify script present");
  assert.doesNotMatch(inline, /\bfetch\s*\(|XMLHttpRequest|sendBeacon|WebSocket|EventSource/);
});
