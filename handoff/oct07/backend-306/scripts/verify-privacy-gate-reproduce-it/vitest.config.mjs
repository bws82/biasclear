export default { test: { root: new URL(".", import.meta.url).pathname, include: ["*.test.ts"], testTimeout: 30_000 } };
