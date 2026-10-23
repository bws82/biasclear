// Independent reproduction of findings 1 and 2: concurrent pausedUntil overwrites.
import { describe, expect, it } from "vitest";
import { harness, httpEvent, modelReply } from "../../pr10b-wt/packages/explain/test/helpers.js";
import { SETTINGS_INTERVAL_MS } from "../../pr10b-wt/packages/explain/src/state.js";

const codes = (h: ReturnType<typeof harness>) => h.logs.map((l) => (JSON.parse(l) as { code?: string }).code ?? "ok");
const tick = (ms = 10) => new Promise((r) => setTimeout(r, ms));
const LOGGING_ON = { logging: { cloudWatchConfig: { logGroupName: "g" } }, retention: "none" };

describe("F1: failed verdict lost when pausedUntil is lowered", () => {
  it("variant: 403 pauseInstance from an earlier in-flight request", async () => {
    const h = harness();
    const t0 = h.clock.ms;
    expect((await h.call(httpEvent({ ip: "198.51.100.1" }))).statusCode).toBe(200);
    // B: cached pass, inside the model call
    h.clock.ms = t0 + SETTINGS_INTERVAL_MS - 30_000;
    let rel!: () => void; const g = new Promise<void>((r) => (rel = r));
    h.aws.model = async () => { await g; return { status: 403, errorType: "AccessDeniedException", json: { message: "x" } }; };
    const b = h.call(httpEvent({ ip: "198.51.100.2" }));
    await tick();
    // A: check due, logging ON
    h.clock.ms = t0 + SETTINGS_INTERVAL_MS + 1_000;
    h.aws.settings = LOGGING_ON;
    const a = await h.call(httpEvent({ ip: "198.51.100.3" }));
    const afterA = { p: h.deps.state.pausedUntil, n: h.deps.state.nextSettingsCheck };
    rel();
    const br = await b;
    const afterB = { p: h.deps.state.pausedUntil, n: h.deps.state.nextSettingsCheck };
    // C after B's lowered pause but before nextSettingsCheck
    h.aws.model = () => ({ status: 200, json: modelReply() });
    h.clock.ms = afterB.p;
    const reads = h.aws.settingsReads, calls = h.aws.modelCalls.length;
    const c = await h.call(httpEvent({ ip: "198.51.100.4" }));
    console.log("F1-403", JSON.stringify({ a: a.statusCode, b: br.statusCode, c: c.statusCode, afterA, afterB, windowMs: afterB.n - afterB.p,
      newReads: h.aws.settingsReads - reads, newModelCalls: h.aws.modelCalls.length - calls, codes: codes(h), loggingStillOn: h.aws.settings === LOGGING_ON }));
    expect(c.statusCode).toBe(200);
    expect(h.aws.modelCalls.length - calls).toBe(1);
    expect(h.aws.settingsReads - reads).toBe(0);
  });

  it("variant: E_HEADROOM near midnight (B started 23:50 on cached pass, A fails 23:52)", async () => {
    const h = harness();
    const D = Date.UTC(2026, 9, 7);
    h.clock.ms = D + 23 * 3600_000 + 37 * 60_000; // 23:37, check passes, next due 23:52
    expect((await h.call(httpEvent({ ip: "198.51.100.1" }))).statusCode).toBe(200);
    // fill today's spend so B gets E_HEADROOM
    const dk = `spendday#${new Date(D).toISOString().slice(0, 10)}`;
    const it0 = h.aws.table.items.get(dk)!;
    h.aws.table.items.set(dk, { ...it0, m: { N: String(h.deps.config!.dailyMicros) } });
    h.clock.ms = D + 23 * 3600_000 + 51 * 60_000 + 59_000; // B at 23:51:59, cached pass
    h.aws.table.delayMs = 40;
    const b = h.call(httpEvent({ ip: "198.51.100.2" }));
    await tick(5);
    h.clock.ms = D + 23 * 3600_000 + 52 * 60_000; // A at 23:52 check fails
    h.aws.settings = LOGGING_ON;
    const a = await h.call(httpEvent({ ip: "198.51.100.3" }));
    const afterA = { p: h.deps.state.pausedUntil, n: h.deps.state.nextSettingsCheck };
    const br = await b;
    h.aws.table.delayMs = 0;
    const afterB = { p: h.deps.state.pausedUntil, n: h.deps.state.nextSettingsCheck };
    h.clock.ms = D + 24 * 3600_000 + 3 * 60_000; // C at 00:03 next day
    const reads = h.aws.settingsReads, calls = h.aws.modelCalls.length;
    const c = await h.call(httpEvent({ ip: "198.51.100.4" }));
    console.log("F1-midnight", JSON.stringify({ a: a.statusCode, b: br.statusCode, c: c.statusCode,
      afterA: new Date(afterA.p).toISOString(), afterBpause: new Date(afterB.p).toISOString(), next: new Date(afterB.n).toISOString(),
      newReads: h.aws.settingsReads - reads, newModelCalls: h.aws.modelCalls.length - calls, codes: codes(h) }));
    expect(c.statusCode).toBe(200);
  });

  it("control: sequential requests cannot trigger it", async () => {
    const h = harness();
    const t0 = h.clock.ms;
    await h.call(httpEvent({ ip: "198.51.100.1" }));
    h.clock.ms = t0 + SETTINGS_INTERVAL_MS;
    h.aws.settings = LOGGING_ON;
    expect((await h.call(httpEvent({ ip: "198.51.100.2" }))).statusCode).toBe(503);
    const s = h.deps.state;
    console.log("control", s.pausedUntil >= s.nextSettingsCheck);
    h.clock.ms = s.pausedUntil;
    const calls = h.aws.modelCalls.length;
    const r = await h.call(httpEvent({ ip: "198.51.100.3" }));
    expect(r.statusCode).toBe(503);
    expect(h.aws.modelCalls.length).toBe(calls);
  });
});

describe("F2: Infinity in-memory billing stop lowered by a concurrent timed pause", () => {
  it("timeout + failed persist, concurrent settings-read failure overwrites Infinity", async () => {
    const h = harness();
    const t0 = h.clock.ms;
    expect((await h.call(httpEvent({ ip: "198.51.100.1" }))).statusCode).toBe(200);
    // Y: cached pass, model call blocks then times out
    h.clock.ms = t0 + SETTINGS_INTERVAL_MS - 5_000;
    let relModel!: () => void; const gm = new Promise<void>((r) => (relModel = r));
    h.aws.model = async () => { await gm; return "timeout"; };
    const y = h.call(httpEvent({ ip: "198.51.100.2" }));
    await tick();
    // X: settings check due; block the settings read
    h.clock.ms = t0 + SETTINGS_INTERVAL_MS + 1_000;
    let relSet!: () => void; const gs = new Promise<void>((r) => (relSet = r));
    const inner = h.aws.transport;
    let blockSettings = true;
    h.deps.transport = async (call) => {
      if (blockSettings && call.host.startsWith("bedrock.")) { await gs; return { status: 500, headers: {}, body: "{}" }; }
      return inner(call);
    };
    const x = h.call(httpEvent({ ip: "198.51.100.3" }));
    await tick();
    // Y resolves: timeout -> pause(); make persistBillingPause fail
    h.aws.table.fault = (op) => (op === "TransactWriteItems" || op === "PutItem" || op === "UpdateItem" ? "network" : undefined);
    relModel();
    const yr = await y;
    const afterY = h.deps.state.pausedUntil;
    h.aws.table.fault = undefined;
    relSet();
    const xr = await x;
    blockSettings = false;
    const afterX = h.deps.state.pausedUntil;
    // Z after the finite pause; settings OK again
    h.clock.ms = afterX;
    const calls = h.aws.modelCalls.length;
    h.aws.model = () => ({ status: 200, json: modelReply() });
    const z = await h.call(httpEvent({ ip: "198.51.100.4" }));
    const logs = h.logs.map((l) => JSON.parse(l) as Record<string, unknown>).map((l) => [l.code ?? "ok", l.pausePersisted]);
    console.log("F2", JSON.stringify({ y: yr.statusCode, x: xr.statusCode, z: z.statusCode, afterY, afterX, newModelCalls: h.aws.modelCalls.length - calls, logs,
      pauseRow: [...h.aws.table.items.keys()].filter((k) => /pause|event/.test(k)) }));
    expect(afterY).toBe(Number.POSITIVE_INFINITY);
    expect(Number.isFinite(afterX)).toBe(true);
    expect(z.statusCode).toBe(200);
  });
});
