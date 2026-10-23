// Q2: the concurrent single-flight privacy check, error propagation, partial
// reads, TTL, and whether a failed verdict can be "cached" as a pass.
import { describe, expect, it } from "vitest";
import { harness, httpEvent, evalEvent, lastLog, modelReply, type Harness } from "./fixcopy/packages/explain/test/helpers.js";
import { SETTINGS_INTERVAL_MS } from "./fixcopy/packages/explain/src/state.js";

const MIN = 60_000;
const codes = (h: Harness) => h.logs.map((l) => (JSON.parse(l) as { code?: string }).code ?? "ok");

/** Wrap the fake transport so settings reads block until released. */
function gateSettings(h: Harness) {
  let release!: () => void;
  const gate = new Promise<void>((r) => { release = r; });
  const inner = h.aws.transport;
  let blocked = true;
  h.deps.transport = async (call) => {
    if (blocked && call.host.startsWith("bedrock.")) await gate;
    return inner(call);
  };
  return { release: () => { blocked = false; release(); } };
}

describe("single-flight privacy check", () => {
  it("N concurrent callers share one read and none reaches Bedrock before it finishes", async () => {
    const h = harness();
    // harness() captured transport at construction; rebuild deps transport via a proxy.
    const inner = h.aws.transport;
    let release!: () => void;
    const gate = new Promise<void>((r) => { release = r; });
    (h.deps as { transport: typeof inner }).transport = async (call) => {
      if (call.host.startsWith("bedrock.")) await gate;
      return inner(call);
    };
    const p = Array.from({ length: 5 }, (_, i) => h.call(httpEvent({ ip: `198.51.100.${i + 1}` })));
    await new Promise((r) => setTimeout(r, 20));
    expect(h.aws.modelCalls.length).toBe(0);
    expect(h.aws.table.ops).toEqual([]);
    release();
    const rs = await Promise.all(p);
    expect(rs.map((r) => r.statusCode)).toEqual([200, 200, 200, 200, 200]);
    expect(h.aws.settingsReads).toBe(4);
  });

  it("a failed or partial read propagates to every waiter (no model call, no DynamoDB)", async () => {
    for (const fault of ["all", "us-west-2-only", "logging-non-json", "retention-missing-mode", "retention-number"] as const) {
      const h = harness();
      const inner = h.aws.transport;
      (h.deps as { transport: typeof inner }).transport = async (call) => {
        if (call.host.startsWith("bedrock.")) {
          if (fault === "all") return { status: 500, headers: {}, body: "{}" };
          if (fault === "us-west-2-only" && call.host.includes("us-west-2")) return { status: 403, headers: {}, body: "{}" };
          if (fault === "logging-non-json" && call.path.startsWith("/logging")) return { status: 200, headers: {}, body: "<html>" };
          if (fault === "retention-missing-mode" && call.host.includes("us-east-2") && call.path === "/data-retention") return { status: 200, headers: {}, body: "{}" };
          if (fault === "retention-number" && call.path === "/data-retention") return { status: 200, headers: {}, body: '{"mode":0}' };
        }
        return inner(call);
      };
      const rs = await Promise.all([1, 2, 3].map((i) => h.call(httpEvent({ ip: `198.51.100.${i}` }))));
      expect(rs.map((r) => r.statusCode), fault).toEqual([503, 503, 503]);
      expect(new Set(codes(h)), fault).toEqual(new Set(["E_SETTINGS_READ"]));
      expect(h.aws.modelCalls.length, fault).toBe(0);
      expect(h.aws.table.ops, fault).toEqual([]);
    }
  });

  it("a thrown transport error (timeout) inside the check is contained and pauses", async () => {
    const h = harness();
    const inner = h.aws.transport;
    (h.deps as { transport: typeof inner }).transport = async (call) => {
      if (call.host.startsWith("bedrock.us-east-2")) throw new Error("boom");
      return inner(call);
    };
    const r = (await h.handler(evalEvent())) as { status: number; evaluation: { modelCalled?: boolean } };
    expect(r.status).toBe(503);
    expect(r.evaluation.modelCalled).toBe(false);
    expect(lastLog(h).code).toBe("E_SETTINGS_READ");
    expect(h.aws.modelCalls.length).toBe(0);
    expect(h.deps.state.settingsCheck).toBeUndefined();
  });

  it("TTL: logging switched ON after a passing check is not seen for up to 15 minutes (disclosed design)", async () => {
    const h = harness();
    await h.call(httpEvent({ ip: "198.51.100.1" }));
    h.aws.settings = { logging: { cloudWatchConfig: { logGroupName: "x" } }, retention: "none" };
    h.clock.advance(SETTINGS_INTERVAL_MS - 1);
    const r = await h.call(httpEvent({ ip: "198.51.100.2" }));
    expect(r.statusCode).toBe(200);
    expect(h.aws.modelCalls.length).toBe(2); // second call reached Bedrock with logging ON
    h.clock.advance(1);
    expect((await h.call(httpEvent({ ip: "198.51.100.3" }))).statusCode).toBe(503);
    expect(lastLog(h).code).toBe("E_SETTINGS_LOGGING_ON");
  });
});

describe("a failed verdict is stored only in pausedUntil, which other paths overwrite", () => {
  it("in-flight request's not-billed pauseInstance lowers pausedUntil below nextSettingsCheck: Bedrock reached with logging known ON", async () => {
    const h = harness();
    expect((await h.call(httpEvent({ ip: "198.51.100.1" }))).statusCode).toBe(200); // check #1 passes at T0
    const t0 = h.clock.ms;

    // B starts 10 s before the cache expires, passes step 2 on the cached pass,
    // and is inside the 20 s model call when the next check fails.
    h.clock.ms = t0 + SETTINGS_INTERVAL_MS - 10_000;
    let releaseModel!: () => void;
    const modelGate = new Promise<void>((r) => { releaseModel = r; });
    h.aws.model = async () => { await modelGate; return { status: 403, errorType: "AccessDeniedException", json: { message: "denied" } }; };
    const b = h.call(httpEvent({ ip: "198.51.100.2" }));
    await new Promise((r) => setTimeout(r, 20));
    expect(h.aws.modelCalls.length).toBe(2);

    // A: cache expired; logging is now ON; the check fails and pauses 15 min.
    h.clock.ms = t0 + SETTINGS_INTERVAL_MS + 5_000;
    h.aws.settings = { logging: { cloudWatchConfig: { logGroupName: "x" } }, retention: "none" };
    expect((await h.call(httpEvent({ ip: "198.51.100.3" }))).statusCode).toBe(503);
    expect(lastLog(h).code).toBe("E_SETTINGS_LOGGING_ON");
    const failedPause = h.deps.state.pausedUntil;
    const nextCheck = h.deps.state.nextSettingsCheck;

    // B's model call returns 403 (not billed, pauseInstance): pausedUntil = B.start + 15 min.
    releaseModel();
    expect((await b).statusCode).toBe(503);
    void failedPause; void nextCheck;

    // C, inside [B.start+15m, A.check+15m): passes step 1, skips step 2, reaches Bedrock.
    h.aws.model = () => ({ status: 200, json: modelReply() });
    for (const t of [t0 + 2 * SETTINGS_INTERVAL_MS - 10_000 + 1, t0 + 2 * SETTINGS_INTERVAL_MS + 5_000 + 1]) {
      h.clock.ms = t;
      const modelsBefore = h.aws.modelCalls.length;
      const c = await h.call(httpEvent({ ip: "198.51.100.4" }));
      expect(h.aws.modelCalls.length).toBe(modelsBefore);
      expect(c.statusCode).toBe(503);
    }
    console.log(JSON.stringify({ windowMs: nextCheck - h.deps.state.pausedUntil, codes: codes(h) }));
  });

  it("near UTC midnight an in-flight E_HEADROOM lowers pausedUntil to 00:00: ~15 min window with logging known ON", async () => {
    const h = harness();
    const D = Date.UTC(2026, 9, 7);
    h.clock.ms = D + 23 * 60 * MIN + 45 * MIN; // 23:45 day D
    expect((await h.call(httpEvent({ ip: "198.51.100.1" }))).statusCode).toBe(200); // check passes; next due 00:00
    // Day D's counter is full, so a request on day D gets E_HEADROOM.
    const dayKey = `spendday#${new Date(D).toISOString().slice(0, 10)}`;
    const item = h.aws.table.items.get(dayKey)!;
    h.aws.table.items.set(dayKey, { ...item, m: { N: String(h.deps.config!.dailyMicros) } });

    // B at 23:59:59 passes step 2 on the cached pass and waits on DynamoDB.
    h.clock.ms = D + 24 * 60 * MIN - 1000;
    h.aws.table.delayMs = 50;
    const b = h.call(httpEvent({ ip: "198.51.100.2" }));
    await new Promise((r) => setTimeout(r, 5));

    // A at 00:00:00: check due; logging is ON -> E_SETTINGS_LOGGING_ON, pause until 00:15.
    h.clock.ms = D + 24 * 60 * MIN;
    h.aws.settings = { logging: { s3Config: { bucketName: "x" } }, retention: "none" };
    expect((await h.call(httpEvent({ ip: "198.51.100.3" }))).statusCode).toBe(503);
    expect(lastLog(h).code).toBe("E_SETTINGS_LOGGING_ON");
    const nextCheck = h.deps.state.nextSettingsCheck;

    expect((await b).statusCode).toBe(503); // B: E_HEADROOM, pausedUntil := 00:00:00
    h.aws.table.delayMs = 0;

    // C at 00:05: passes the pause flag, skips the privacy read, reaches Bedrock.
    h.clock.ms = D + 24 * 60 * MIN + 5 * MIN;
    const readsBefore = h.aws.settingsReads;
    const modelsBefore = h.aws.modelCalls.length;
    const c = await h.call(httpEvent({ ip: "198.51.100.4" }));
    void readsBefore;
    expect(h.aws.modelCalls.length).toBe(modelsBefore);
    expect(c.statusCode).toBe(503);
    console.log(JSON.stringify({ windowMs: nextCheck - (D + 24 * 60 * MIN), codes: codes(h) }));
  });
});
