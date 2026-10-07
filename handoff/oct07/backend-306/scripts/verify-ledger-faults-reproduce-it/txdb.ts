// Independent conflict-model wrapper (verify pass). Wraps the package FakeAws (imported read-only).
// DynamoDB semantics modelled (per AWS "Transaction conflict handling"): while a TransactWriteItems is
// in flight it holds every item it names (Put/Update/ConditionCheck); a second TransactWriteItems that
// names a held item is cancelled with CancellationReasons TransactionConflict; a single-item write on a
// held item gets TransactionConflictException. The newcomer is the one cancelled.
import type { AwsReply, Transport } from "../../pr10b-wt/packages/explain/src/aws/transport.js";
import { TransportError } from "../../pr10b-wt/packages/explain/src/aws/transport.js";
import { FakeAws } from "../../pr10b-wt/packages/explain/test/helpers.js";

export const sleep = (ms: number) => new Promise<void>((r) => setTimeout(r, ms));

function keysOf(body: Record<string, unknown>): string[] {
  return (body.TransactItems as Record<string, Record<string, unknown>>[]).map((it) => {
    const [c, b] = Object.entries(it)[0]!;
    return c === "Put" ? (b.Item as Record<string, { S: string }>).pk.S : (b.Key as { pk: { S: string } }).pk.S;
  });
}

export type Hook = (op: string, body: Record<string, unknown>, keys: string[]) =>
  undefined | "lost-ack" | "network" | "hang" | { late: number } | Promise<undefined>;

export class TxDb {
  readonly aws = new FakeAws();
  readonly held = new Map<string, string>();
  holdMs = 0;
  log: string[] = [];
  hook: Hook | undefined;
  lat = { ddb: 0, model: 0, settings: 0 };
  starts: Array<{ t: number; what: string }> = [];
  t0 = 0;
  readonly transport: Transport = async (call) => {
    const what = call.service === "dynamodb" ? (call.headers["x-amz-target"] ?? "").replace("DynamoDB_20120810.", "") : call.host.split(".")[0]!;
    if (call.service !== "dynamodb") {
      this.starts.push({ t: performance.now() - this.t0, what: what + (call.host.startsWith("bedrock-runtime") ? ":model" : ":settings") });
      if (call.host.startsWith("bedrock-runtime.")) { if (this.lat.model) await sleep(this.lat.model); }
      else if (this.lat.settings) await sleep(this.lat.settings);
      return this.aws.transport(call);
    }
    const body = JSON.parse(call.body) as Record<string, unknown>;
    const op = what;
    const keys = op === "TransactWriteItems" ? keysOf(body)
      : [op === "PutItem" ? (body.Item as Record<string, { S: string }>).pk.S : (body.Key as { pk: { S: string } }).pk.S];
    this.starts.push({ t: performance.now() - this.t0, what: `${op}:${keys.join("|")}` });
    if (this.lat.ddb) await sleep(this.lat.ddb);
    const h = await this.hook?.(op, body, keys);
    if (h === "hang") return new Promise<AwsReply>(() => undefined);
    if (h === "network") throw new TransportError("network");
    if (h !== undefined && typeof h === "object") {
      void sleep(h.late).then(() => this.aws.transport(call)).catch(() => undefined);
      throw new TransportError("timeout");
    }
    if (op === "TransactWriteItems") {
      const idx = keys.findIndex((k) => this.held.has(k));
      if (idx >= 0) {
        this.log.push(`CONFLICT ${keys.join("|")} on ${keys[idx]} held by ${this.held.get(keys[idx]!)}`);
        return { status: 400, headers: {}, body: JSON.stringify({
          __type: "com.amazonaws.dynamodb.v20120810#TransactionCanceledException",
          CancellationReasons: keys.map((_, i) => ({ Code: i === idx ? "TransactionConflict" : "None" })) }) };
      }
      const tag = keys.join("|");
      for (const k of keys) this.held.set(k, tag);
      try {
        if (this.holdMs) await sleep(this.holdMs);
        const r = await this.aws.transport(call);
        if (h === "lost-ack" && r.status === 200) throw new TransportError("network");
        return r;
      } finally { for (const k of keys) this.held.delete(k); }
    }
    if ((op === "PutItem" || op === "UpdateItem" || op === "DeleteItem") && this.held.has(keys[0]!)) {
      this.log.push(`CONFLICT single ${op} ${keys[0]}`);
      return { status: 400, headers: {}, body: JSON.stringify({ __type: "com.amazonaws.dynamodb.v20120810#TransactionConflictException" }) };
    }
    const r = await this.aws.transport(call);
    if (h === "lost-ack" && r.status === 200) throw new TransportError("network");
    return r;
  };
  keys(prefix: string) { return [...this.aws.table.items.entries()].filter(([k]) => k.startsWith(prefix)); }
  item(pk: string) { return this.aws.table.items.get(pk); }
}
