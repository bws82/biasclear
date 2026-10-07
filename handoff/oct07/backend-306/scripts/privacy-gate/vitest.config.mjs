// Red-team tests for the privacy gate. Root is this folder; the package under
// review is imported read-only by relative path.
export default {
  test: {
    root: new URL(".", import.meta.url).pathname,
    include: ["*.test.ts"],
    testTimeout: 30_000,
  },
};
