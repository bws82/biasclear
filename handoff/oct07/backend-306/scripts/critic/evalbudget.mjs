// Can one live evaluate run of the planned corpus fit in one UTC day's cap?
// Uses the dry run's real per-row promptBytes and the reviewed prices.
import { readFileSync } from "node:fs";
const r = JSON.parse(readFileSync(process.argv[2], "utf8"));
const DAILY = 2_500_000; // micros, $25 x 10%
for (const m of r.models) {
  const rows = m.raw.filter((x) => x.evaluation.modelCalled);
  const bytes = rows.map((x) => x.evaluation.promptBytes);
  const sumBytes = bytes.reduce((a, b) => a + b, 0);
  const id = m.id;
  const [pin, pout] = id.includes("grok") ? [2200, 6600] : [2200, 11000]; // nanos per token
  const out = { id, calls: rows.length, avgPromptBytes: Math.round(sumBytes / rows.length),
    stubReservationTotalUsd: m.stubReservationTotalUsd };
  // Scenarios: input tokens = bytes/k + framing F; output tokens O (visible + any billed reasoning).
  for (const [label, k, F, O] of [["optimistic", 4, 20, 80], ["mid", 3.5, 50, 150], ["reasoning", 3.5, 50, 300]]) {
    let micros = 0, fitted = 0;
    const worstLast = Math.ceil(((Math.max(...bytes) + 50) * pin + 400 * pout) / 1000);
    for (const b of bytes) {
      const a = Math.ceil(((b / k + F) * pin + O * pout) / 1000);
      if (micros + worstLast > DAILY) break; // the next reservation would be refused
      micros += a; fitted++;
    }
    const total = bytes.reduce((s, b) => s + Math.ceil(((b / k + F) * pin + O * pout) / 1000), 0);
    out[label] = { estTotalUsd: +(total / 1e6).toFixed(3), callsBeforeDayCap: fitted };
  }
  console.log(JSON.stringify(out));
}
