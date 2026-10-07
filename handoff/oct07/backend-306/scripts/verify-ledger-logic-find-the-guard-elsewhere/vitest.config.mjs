const here = "/tmp/claude-0/-home-user-biasclear/bb187462-b843-5453-a36d-b91a5ff093cc/scratchpad/backend-rt/verify-ledger-logic-find-the-guard-elsewhere";
export default {
  cacheDir: here + "/.vite-cache",
  test: {
    root: here,
    include: ["*.test.ts"],
    testTimeout: 60_000,
  },
  server: { fs: { allow: ["/tmp/claude-0/-home-user-biasclear/bb187462-b843-5453-a36d-b91a5ff093cc/scratchpad"] } },
};
