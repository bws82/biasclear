// Fault-injecting wrapper around the package's FakeAws (read-only import).
// Adds what the package fake does not model:
//  - DynamoDB transaction conflicts: an in-flight TransactWriteItems holds every
//    item it touches for `txMs`; another transaction touching one of those items
//    is cancelled (TransactionCanceledException / reason TransactionConflict),
//    and a single-item write to a held item gets TransactionConflictException.
//  - late commit: the client sees a network error now, the write lands later.
//  - hang: a call never answers (models the Lambda being killed mid-call).
//  - latency: every call waits a scaled delay (to measure the 28 s budget).
import type { AwsCall, AwsReply, Transport } from "../../pr10b-wt/packages/explain/src/aws/transport.js";
import { TransportError } from "../../pr10b-wt/packages/explain/src/aws/transport.js";
import { FakeAws } from "../../pr10b-wt/packages/explain/test/helpers.js";

export const sleep = (ms: number) => new Promise<void>((r) => setTimeout(r, ms));

export type Fault = "late-commit" | "hang" | "conflict" | undefined;

export function opOf(call: AwsCall): string {
  return (call.headers["x-amz-target"] ?? "").replace("DynamoDB_20120810.", "");
}

export function txKeys(body: Record<string, unknown>): string[] {
  return (body.TransactItems as Record<string, Record<string, unknown>>[]).map((item) => {
    const [component, b] = Object.entries(item)[0]!;
    return component === "Put" ? ((b.Item as Record<string, { S: string }>).pk.S) : ((b.Key as { pk: { S: string } }).pk.S);
  });
}

export class FaultAws {
  readonly aws = new FakeAws();
  readonly locks = new Set<string>();
  txMs = 0;
  conflicts = 0;
  readonly conflictLog: string[] = [];
  /** Per-call fault hook (DynamoDB calls only). */
  fault: ((op: string, body: Record<string, unknown>) => Fault) | undefined;
  /** Latency for each call kind, in real ms (scaled). */
  latency: { ddb: number; settings: number; model: number } = { ddb: 0, settings: 0, model: 0 };
  readonly lateCommits: Promise<unknown>[] = [];

  readonly transport: Transport = async (call) => {
    if (call.service !== "dynamodb") {
      if (call.host.startsWith("bedrock-runtime.")) { if (this.latency.model) await sleep(this.latency.model); }
      else if (this.latency.settings) await sleep(this.latency.settings);
      return this.aws.transport(call);
    }
    if (this.latency.ddb) await sleep(this.latency.ddb);
    const op = opOf(call);
    const body = JSON.parse(call.body) as Record<string, unknown>;
    const f = this.fault?.(op, body);
    if (f === "hang") return new Promise<AwsReply>(() => undefined);
    if (f === "late-commit") {
      // The client gives up now; the write is applied 30 ms later.
      this.lateCommits.push(sleep(30).then(() => this.aws.transport(call)).catch(() => undefined));
      throw new TransportError("timeout");
    }
    if (op === "TransactWriteItems") {
      const keys = txKeys(body);
      const idx = f === "conflict" ? 0 : keys.findIndex((k) => this.locks.has(k));
      if (idx >= 0) {
        this.conflicts++;
        this.conflictLog.push(`${keys.join("|")} @${keys[idx]}`);
        return {
          status: 400, headers: {},
          body: JSON.stringify({
            __type: "com.amazonaws.dynamodb.v20120810#TransactionCanceledException",
            CancellationReasons: keys.map((_, i) => ({ Code: i === idx ? "TransactionConflict" : "None" })),
          }),
        };
      }
      for (const k of keys) this.locks.add(k);
      try {
        if (this.txMs) await sleep(this.txMs);
        return await this.aws.transport(call);
      } finally {
        for (const k of keys) this.locks.delete(k);
      }
    }
    if (op === "PutItem" || op === "UpdateItem" || op === "DeleteItem") {
      const key = op === "PutItem" ? (body.Item as Record<string, { S: string }>).pk.S : (body.Key as { pk: { S: string } }).pk.S;
      if (this.locks.has(key)) {
        this.conflicts++;
        return { status: 400, headers: {}, body: JSON.stringify({ __type: "com.amazonaws.dynamodb.v20120810#TransactionConflictException" }) };
      }
    }
    return this.aws.transport(call);
  };

  items(prefix: string) {
    return [...this.aws.table.items.entries()].filter(([k]) => k.startsWith(prefix));
  }
}

/** Deterministic PRNG (mulberry32). */
export function rng(seed: number) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
