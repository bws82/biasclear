export default {
  test: {
    root: new URL(".", import.meta.url).pathname,
    include: ["*.test.ts"],
    testTimeout: 60_000,
    server: { deps: { inline: true } },
  },
  server: { fs: { allow: ["/tmp/claude-0"] } },
};
