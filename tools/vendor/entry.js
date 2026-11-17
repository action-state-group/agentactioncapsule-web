// The only exports the page uses: strict verifyBundle, the "no Ed25519 here" error, the package's
// reader the package's own bundle viewer uses (keeps number spelling), and the category-coverage gate the verdict depends on.
export {
  verifyBundle,
  Ed25519UnavailableError,
  decodeFragment,
  categoryCoverageFails,
  CATEGORY_COVERAGE_PROPERTIES,
} from "@action-state-group/agent-action-capsule";
