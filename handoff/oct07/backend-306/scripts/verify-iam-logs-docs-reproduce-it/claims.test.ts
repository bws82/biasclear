// Executable checks of doc claims (lens iam-logs-docs).
import { it, expect } from "vitest";
import { harness, httpEvent, requestBody } from "../../pr10b-wt/packages/explain/test/helpers.js";

it("consent says 'Explain pauses if that setting changes': a sentence is still sent to Bedrock 14 min after retention changed", async () => {
  const h = harness();
  const r1 = await h.call(httpEvent({ body: requestBody() }));
  expect(r1.statusCode).toBe(200);
  const reads = h.aws.settingsReads;
  h.aws.regionalRetention["us-east-2"] = "default"; // owner/attacker flips one destination region
  h.clock.advance(14 * 60 * 1000);
  const before = h.aws.modelCalls.length;
  const r2 = await h.call(httpEvent({ body: requestBody(), ip: "198.51.100.9" }));
  console.info("after change: status", r2.statusCode, "model calls +", h.aws.modelCalls.length - before, "settings reads +", h.aws.settingsReads - reads);
  expect(r2.statusCode).toBe(200);
  expect(h.aws.modelCalls.length - before).toBe(1);
  h.clock.advance(60 * 1000 + 1);
  const r3 = await h.call(httpEvent({ body: requestBody(), ip: "198.51.100.10" }));
  expect(r3.statusCode).toBe(503);
});

it("one transient DynamoDB throttle on settlement durably pauses Explain for every caller (owner-only clear)", async () => {
  const h = harness();
  let tx = 0;
  h.aws.table.fault = (op) => (op === "TransactWriteItems" && ++tx === 2 ? "throttle" : undefined); // only the settle transaction
  const r1 = await h.call(httpEvent({ body: requestBody() }));
  const l1 = JSON.parse(h.logs.at(-1)!);
  console.info("settle-throttled request:", r1.statusCode, l1.code, "pausePersisted", l1.pausePersisted, "billing#pause exists", h.aws.table.items.has("billing#pause"));
  expect(l1).toMatchObject({ code: "E_SETTLE", pausePersisted: 1 });
  // a fresh instance (new state) and a different visitor
  const fresh = harness();
  for (const [k, v] of h.aws.table.items) fresh.aws.table.items.set(k, v);
  fresh.clock.advance(40 * 24 * 3600 * 1000); // next month too
  const r2 = await fresh.call(httpEvent({ body: requestBody(), ip: "192.0.2.44" }));
  console.info("fresh instance, other IP, 40 days later:", r2.statusCode, JSON.parse(fresh.logs.at(-1)!).code);
  expect(JSON.parse(fresh.logs.at(-1)!).code).toBe("E_BILLING_PAUSE");
});
