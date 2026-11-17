// Turns the strict verifyBundle result into the four outcomes the "Verify a bundle" section shows.
// Pure logic with no DOM and no network, so Node tests and the page run the same code.
//
//   verified      strict verdict VALID and the signatures claim passed
//   failed        strict verdict INVALID
//   incomplete    strict verdict INCOMPLETE (nothing failed, something could not be shown)
//   cannot-check  this browser cannot do Ed25519 (or SHA-256), so no strict verdict exists;
//                 never a failure
//   not-a-bundle  the input is not JSON, so there is nothing to verify (not a verdict)

export async function checkBundleText(text, { verifyBundle, Ed25519UnavailableError }) {
  let bundle;
  try {
    bundle = JSON.parse(text);
  } catch (error) {
    return { state: "not-a-bundle", detail: "The input is not valid JSON." };
  }
  let result;
  try {
    result = await verifyBundle(bundle, { strict: true });
  } catch (error) {
    if (error instanceof Ed25519UnavailableError || error?.name === "Ed25519UnavailableError") {
      return { state: "cannot-check", detail: "ed25519" };
    }
    if (error?.name === "Sha256UnavailableError") {
      return { state: "cannot-check", detail: "sha256" };
    }
    throw error;
  }
  const strict = result.strict;
  const claims = strict.claims.map((c) => ({ name: c.name, status: c.status, findings: [...c.findings] }));
  const signatures = claims.find((c) => c.name === "signatures");
  let state;
  if (strict.verdict === "INVALID") state = "failed";
  else if (strict.verdict === "VALID" && signatures?.status === "pass") state = "verified";
  else state = "incomplete";
  return {
    state,
    claims,
    records: strict.records.map((r) => ({
      capsuleId: r.capsuleId,
      identityOk: r.identityOk,
      signature: r.signature,
      messages: [...r.messages],
    })),
    witnesses: strict.witnesses
      ? { status: strict.witnesses.status, findings: [...strict.witnesses.findings] }
      : null,
  };
}
