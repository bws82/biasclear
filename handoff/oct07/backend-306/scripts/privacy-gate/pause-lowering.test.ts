// Same root cause as the privacy-cache window: state.pausedUntil is assigned,
// never max-merged. A settings failure that lands while a concurrent request
// sets the in-memory billing stop (Infinity) lowers it to now+15 min.
import { describe, expect, it } from "vitest";
import { harness, httpEvent, modelReply } from "../../pr10b-wt/packages/explain/test/helpers.js";
import { SETTINGS_INTERVAL_MS } from "../../pr10b-wt/packages/explain/src/state.js";

describe("in-memory billing stop is lowered by a concurrent settings failure", () => {
  it("unpersisted pause (disclosed: 'stops only the confirmed instance') is lifted after 15 min on that same instance", async () => {
    const h = harness();
    expect((await h.call(httpEvent({ ip: "198.51.100.1" }))).statusCode).toBe(200);
    const t0 = h.clock.ms;

    // The durable pause write fails (disclosed limit), so only the in-memory stop remains.
    h.aws.table.fault = (op, payload) => {
      const s = JSON.stringify(payload);
      return op === "TransactWriteItems" && s.includes('"billingdebt#') ? "network" : undefined;
    };

    // Y: passes step 2 on the cached pass, then its model call times out (maybe billed).
    h.clock.ms = t0 + SETTINGS_INTERVAL_MS - 5000;
    let releaseModel!: () => void;
    const mg = new Promise<void>((r) => { releaseModel = r; });
    h.aws.model = async () => { await mg; return "timeout"; };
    const y = h.call(httpEvent({ ip: "198.51.100.2" }));
    await new Promise((r) => setTimeout(r, 20));

    // X: settings check due; its reads are held in flight.
    h.clock.ms = t0 + SETTINGS_INTERVAL_MS + 1000;
    const inner = h.aws.transport;
    let releaseSettings!: () => void;
    const sg = new Promise<void>((r) => { releaseSettings = r; });
    (h.deps as { transport: typeof inner }).transport = async (call) => {
      if (call.host.startsWith("bedrock.")) { await sg; return { status: 500, headers: {}, body: "{}" }; }
      return inner(call);
    };
    const x = h.call(httpEvent({ ip: "198.51.100.3" }));
    await new Promise((r) => setTimeout(r, 5));

    releaseModel();
    const yr = await y;
    expect(yr.statusCode).toBe(503);
    const yLog = JSON.parse(h.logs.at(-1)!);
    expect(yLog.code).toBe("E_MODEL_TIMEOUT");
    expect(yLog.pausePersisted).toBe(0);
    expect(h.deps.state.pausedUntil).toBe(Number.POSITIVE_INFINITY);

    releaseSettings();
    expect((await x).statusCode).toBe(503);
    expect(JSON.parse(h.logs.at(-1)!).code).toBe("E_SETTINGS_READ");
    expect(h.deps.state.pausedUntil).toBeLessThan(Number.POSITIVE_INFINITY); // Infinity lowered

    // Z, 15 min later on the same instance: settings readable again, model called.
    (h.deps as { transport: typeof inner }).transport = inner;
    h.aws.table.fault = undefined;
    h.aws.model = () => ({ status: 200, json: modelReply() });
    h.clock.ms = h.deps.state.pausedUntil + 1;
    const before = h.aws.modelCalls.length;
    const z = await h.call(httpEvent({ ip: "198.51.100.4" }));
    expect(h.aws.modelCalls.length).toBe(before + 1);
    expect(z.statusCode).toBe(200);
    console.log(JSON.stringify(h.logs.map((l) => JSON.parse(l)).map((l) => [l.code ?? "ok", l.pausePersisted])));
  });
});
