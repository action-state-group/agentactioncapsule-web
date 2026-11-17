// Turns the strict verifyBundle result into the outcomes the "Verify a bundle" section shows.
// Pure logic with no DOM and no network, so Node tests and the page run the same code.
//
//   verified      strict verdict VALID and the signatures claim passed
//   failed        strict verdict INVALID for an Evidence Bundle
//   incomplete    strict verdict INCOMPLETE (nothing failed, something could not be shown)
//   cannot-check  this browser cannot do Ed25519 (or SHA-256), so no strict verdict exists;
//                 never a failure
//   not-a-bundle  the input is not JSON, or is JSON but not an Evidence Bundle: nothing to
//                 verify, not a verdict (`detail` says which)
//
// `lib` is the vendored module: { verifyBundle, Ed25519UnavailableError, decodeFragment,
// categoryCoverageFails, CATEGORY_COVERAGE_PROPERTIES }.

export async function checkBundleText(text, lib) {
  let bundle;
  try {
    // The package's own reader (the one behind its bundle URL fragments): it keeps number spelling,
    // so 1.0 stays distinct from 1, which JSON.parse would silently normalise before the verifier
    // sees it. It takes unpadded base64url over the UTF-8 text.
    const bytes = new TextEncoder().encode(text);
    let binary = "";
    for (let i = 0; i < bytes.length; i += 0x8000) binary += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
    bundle = lib.decodeFragment(btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, ""));
  } catch (error) {
    return { state: "not-a-bundle", detail: "not-json" };
  }
  let result;
  try {
    result = await lib.verifyBundle(bundle, { strict: true });
  } catch (error) {
    if (error instanceof lib.Ed25519UnavailableError || error?.name === "Ed25519UnavailableError") {
      return { state: "cannot-check", detail: "ed25519" };
    }
    if (error?.name === "Sha256UnavailableError") {
      return { state: "cannot-check", detail: "sha256" };
    }
    throw error;
  }
  const strict = result.strict;
  if (!strict.kindOk) return { state: "not-a-bundle", detail: "not-an-evidence-bundle" };
  const claims = strict.claims.map((c) => ({ name: c.name, status: c.status, findings: [...c.findings] }));
  // Results that change the verdict without being one of the claims: a failing one must be shown,
  // or a "failed" verdict would sit above an all-pass table.
  const beside = [];
  if (strict.witnesses) {
    beside.push({ name: "witnesses", status: strict.witnesses.status, findings: [...strict.witnesses.findings] });
  }
  if (strict.parentWitness) {
    beside.push({ name: "parent_witness", status: strict.parentWitness.status, findings: [...(strict.parentWitness.findings ?? [])] });
  }
  const coverage = result.categoryCoverage ?? null;
  if (coverage) {
    const failing = lib.CATEGORY_COVERAGE_PROPERTIES.filter((p) => coverage[p] === "FAIL");
    beside.push({
      name: "category_coverage",
      status: lib.categoryCoverageFails(coverage) ? "fail" : "pass",
      findings: failing,
    });
  }
  const signatures = claims.find((c) => c.name === "signatures");
  let state;
  if (strict.verdict === "INVALID") state = "failed";
  else if (strict.verdict === "VALID" && signatures?.status === "pass") state = "verified";
  else state = "incomplete";
  return {
    state,
    claims,
    beside,
    records: strict.records.map((r) => ({
      capsuleId: r.capsuleId,
      identityOk: r.identityOk,
      signature: r.signature,
      messages: [...r.messages],
    })),
  };
}
