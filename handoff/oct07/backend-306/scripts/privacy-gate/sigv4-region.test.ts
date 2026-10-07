// Q2: per-region SigV4. Every privacy read and the model call must be signed
// for the same region and service as the host it is sent to.
import { createHash, createHmac } from "node:crypto";
import { describe, expect, it } from "vitest";
import { converseModel, modelRequest, readAccountSettings } from "../../pr10b-wt/packages/explain/src/aws/bedrock.js";
import { fetchTransport } from "../../pr10b-wt/packages/explain/src/aws/transport.js";
import { Ddb } from "../../pr10b-wt/packages/explain/src/aws/dynamodb.js";
import { STUB_MODELS } from "../../pr10b-wt/packages/explain/test/helpers.js";

const ENV = { AWS_ACCESS_KEY_ID: "AKIDEXAMPLE", AWS_SECRET_ACCESS_KEY: "wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY", AWS_SESSION_TOKEN: "tok" };
const NOW = Date.UTC(2026, 9, 7, 12, 0, 0);

interface Seen { url: string; headers: Record<string, string>; method: string; body: string }

function recorder(reply: (url: string) => { status: number; body: string }) {
  const seen: Seen[] = [];
  const fetchImpl = (async (url: string, init: RequestInit) => {
    seen.push({ url, headers: init.headers as Record<string, string>, method: String(init.method), body: String(init.body ?? "") });
    const r = reply(url);
    return new Response(r.body, { status: r.status, headers: { "content-type": "application/json" } });
  }) as unknown as typeof fetch;
  return { seen, fetchImpl };
}

function scopeOf(auth: string): { region: string; service: string; day: string } {
  const m = /Credential=[^/]+\/(\d{8})\/([^/]+)\/([^/]+)\/aws4_request/.exec(auth);
  if (!m) throw new Error(`no scope in ${auth}`);
  return { day: m[1]!, region: m[2]!, service: m[3]! };
}

/** Independent recomputation of the SigV4 signature from the request as sent. */
function independentSignature(s: Seen, region: string, service: string): string {
  const u = new URL(s.url);
  const headers: Record<string, string> = { ...s.headers, host: u.host };
  delete headers.authorization;
  const names = Object.keys(headers).map((n) => n.toLowerCase()).sort();
  const lower: Record<string, string> = {};
  for (const [k, v] of Object.entries(headers)) lower[k.toLowerCase()] = v;
  const canonical = [s.method, u.pathname /* simple ASCII paths: canonical form is identical */, "",
    names.map((n) => `${n}:${lower[n]!.trim()}\n`).join(""), names.join(";"), createHash("sha256").update(s.body).digest("hex")].join("\n");
  const stamp = lower["x-amz-date"]!;
  const scope = `${stamp.slice(0, 8)}/${region}/${service}/aws4_request`;
  const sts = ["AWS4-HMAC-SHA256", stamp, scope, createHash("sha256").update(canonical).digest("hex")].join("\n");
  let k: Buffer = createHmac("sha256", `AWS4${ENV.AWS_SECRET_ACCESS_KEY}`).update(stamp.slice(0, 8)).digest();
  for (const part of [region, service, "aws4_request"]) k = createHmac("sha256", k).update(part).digest();
  return createHmac("sha256", k).update(sts).digest("hex");
}

describe("per-region SigV4 for privacy reads", () => {
  it("signs each regional read with its own host region and service bedrock", async () => {
    const { seen, fetchImpl } = recorder((url) => ({ status: 200, body: url.endsWith("/data-retention") ? '{"mode":"none"}' : "{}" }));
    // Transport's default region deliberately differs from every read region.
    const transport = fetchTransport({ region: "eu-west-1", env: ENV, now: () => NOW, fetchImpl });
    const s = await readAccountSettings(transport, "us-east-1", ["us-east-1", "us-east-2", "us-west-2"]);
    expect(s.loggingOn).toBe(false);
    expect(Object.keys(s.retentionByRegion).sort()).toEqual(["us-east-1", "us-east-2", "us-west-2"]);
    expect(seen.length).toBe(4);
    for (const r of seen) {
      const hostRegion = new URL(r.url).host.split(".")[1]!;
      const sc = scopeOf(r.headers.authorization!);
      expect(sc.region, r.url).toBe(hostRegion);
      expect(sc.service, r.url).toBe("bedrock");
      const sig = /Signature=([0-9a-f]{64})/.exec(r.headers.authorization!)![1];
      expect(sig, r.url).toBe(independentSignature(r, hostRegion, "bedrock"));
      // Region is load-bearing in the key: signing for another region would differ.
      expect(sig).not.toBe(independentSignature(r, hostRegion === "us-east-1" ? "us-west-2" : "us-east-1", "bedrock"));
    }
    // Logging is read only at the source; retention at source + both destinations.
    expect(seen.filter((r) => r.url.endsWith("/logging/modelinvocations")).map((r) => new URL(r.url).host)).toEqual(["bedrock.us-east-1.amazonaws.com"]);
  });

  it("Converse and DynamoDB are signed with the transport's region (index.ts sets it from config.region)", async () => {
    const { seen, fetchImpl } = recorder(() => ({ status: 500, body: "{}" }));
    const model = STUB_MODELS["us.xai.grok-4.7"]!;
    const good = fetchTransport({ region: "us-east-1", env: ENV, now: () => NOW, fetchImpl });
    await converseModel(good, "us-east-1", "us.xai.grok-4.7", modelRequest("s", "u", model), model);
    await new Ddb(good, "us-east-1", "biasclear-explain").get("x", 1).catch(() => undefined);
    for (const r of seen) {
      const hostRegion = new URL(r.url).host.split(".")[1]!;
      expect(scopeOf(r.headers.authorization!).region).toBe(hostRegion);
    }
    expect(scopeOf(seen[0]!.headers.authorization!).service).toBe("bedrock");
    expect(scopeOf(seen[1]!.headers.authorization!).service).toBe("dynamodb");

    // Not a live path (index.ts derives both from config.region), but the
    // Converse call carries no explicit region: a mis-built transport signs
    // for its own region while sending to the model's host.
    const mis = recorder(() => ({ status: 500, body: "{}" }));
    const wrong = fetchTransport({ region: "us-west-2", env: ENV, now: () => NOW, fetchImpl: mis.fetchImpl });
    await converseModel(wrong, "us-east-1", "us.xai.grok-4.7", modelRequest("s", "u", model), model);
    expect(new URL(mis.seen[0]!.url).host).toBe("bedrock-runtime.us-east-1.amazonaws.com");
    expect(scopeOf(mis.seen[0]!.headers.authorization!).region).toBe("us-west-2");
  });
});
