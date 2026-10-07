export default { test: { root: new URL(".", import.meta.url).pathname, include: ["fixed-*.check.ts"], testTimeout: 30_000 } };
