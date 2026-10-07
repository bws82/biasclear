# 306: backend review evidence (Explain PR #10 at 19eebb3)

The report itself is in Drive, file 306-claude-to-jarvis-explain-backend-review.md.

- `findings.json` holds every finding, both verifier votes, the holds per lens and the critic's gaps.
- `scripts/<lens>/` holds the probe and fault-injection scripts. They import the PR's `packages/explain/src` from a sibling checkout named `pr10b-wt`; adjust that path to rerun them.

No credentials appear anywhere. One fake placeholder key, used to test that the scripts refuse operator keys, is written as `<fake-operator-key>`.
