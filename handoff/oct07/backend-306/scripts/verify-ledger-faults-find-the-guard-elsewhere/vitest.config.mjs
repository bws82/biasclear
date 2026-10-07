export default {
  root: import.meta.dirname,
  cacheDir: import.meta.dirname + "/.vite-cache",
  test: { include: ["*.test.ts"], testTimeout: 120_000 },
};
