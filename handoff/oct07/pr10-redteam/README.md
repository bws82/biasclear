# Probes from the PR #10 red-team (biasclear/biasclear, head 2299fe1)

These are throwaway probes. They import the PR's real `packages/explain/src` modules.

To run one:
1. Put the file in a folder that sits next to a checkout of PR #10.
2. Fix the import paths in `lib.ts` (it imports from the PR worktree) and in `money-rt.ts`.
3. Run:
   ```
   packages/explain/node_modules/.bin/esbuild X.ts --bundle --platform=node --format=esm --outfile=out/X.mjs
   node out/X.mjs
   ```

What each probe checks:
- `how*.ts` and `fix.ts`: verdict and injection bypasses (finding 1)
- `probe.ts`: URL bypasses (finding 2)
- `rw.ts`: rewrite reversals (gate D)
- `money-rt.ts`: overrun, settlement and the race behind the $25 cap

The full findings are in Drive: 298-claude-to-jarvis-explain-pr10-redteam.md
