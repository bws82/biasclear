# Approved plan · Oct 7–11 (saved Oct 7)

Brad approved the daily plan ("approved lets go"), relayed by Jarvis.

## Roles
- Claude is BiasClear coordinator and sole writer through Sunday, Oct 11.
- Codex is reserved for Soldiers' Angels.
- Claude's changes wait for Jarvis's independent review. No self-clearing.

## Usage ceilings
Manual planning ceilings, not automated enforcement. They are measured in percentage points of the whole weekly bucket, from a 47% used baseline.

| Day | Ceiling |
|---|---|
| Wednesday | +8 (stop by 55% used) |
| Thursday | +12 |
| Friday | +12 |
| Saturday before refill | +6 |
| Saturday after refill | +5 (confirm the refill in the UI at 7 p.m. local) |
| Sunday | +10 |

- Total-week stop: 85% used, keeping 15% for personal use.
- Other personal use shares the bucket, so stop sooner if needed.
- Check at the start and end of each work block, save checkpoints, and pause at the ceiling.

**Meter check (Jarvis):** this cloud session can't read the weekly meter.
- At each saved checkpoint, pause before another substantial block and ask Brad for the current weekly percentage from his Claude app.
- Allowance consumed stays "unverified" until that reading.
- The 55% and 85% stops apply to verified readings.

## Days
- **Wed:** finish checker 304 and backend review 306, the bounded one-file PR #12 read (311), then rank confirmed findings. Keep the exact-source-or-refuse correction.
- **Thu:** reproduce and fix the priority injection, spending-control and privacy findings, with regressions.
- **Fri:** integrate checker and backend, fixtures, relevant tests and the offline stub evaluation.
- **Sat:** remaining fixes, privacy draft, decisions and the review packet.
- **Sun:** freeze exact patches, tests and findings. Only if Explain is stable, prepare the separate Model Check harness with neutral unit inputs. Its questions remain unapproved and unrun.
- Unfinished work carries forward or pauses. Sunday is a candidate target, not a launch promise.

## Rules
- Pinned patches go on this save branch. No new access or child session for PR #10.
- None of the following:
  - broad fan-out, an automatic Codex wake, a watcher or a scheduled resume;
  - AWS or paid model calls;
  - merge, deployment or a model switch;
  - settings, access or site changes;
  - extra capacity purchases.
- New AWS/Bedrock spend is $0. The $25 later-live cap stays.
- Each checkpoint includes the SHA, files, tests, open findings and decisions, reviews owed and usage consumed.
