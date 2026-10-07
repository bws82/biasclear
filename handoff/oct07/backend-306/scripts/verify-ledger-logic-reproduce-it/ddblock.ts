// Independent re-derivation of DynamoDB's documented transaction-conflict rule,
// layered over the package FakeAws (which never conflicts):
//  - while a TransactWriteItems is in progress, every item it names (Put/Update/
//    Delete/ConditionCheck) is locked;
//  - another TransactWriteItems naming a locked item is cancelled with
//    TransactionCanceledException, CancellationReasons[i].Code = "TransactionConflict"
//    for the locked item and "None" elsewhere; nothing of it is applied;
//  - a single-item write to a locked item gets TransactionConflictException;
//  - GetItem is never blocked (read-committed).
// The "in progress" window is controlled by the test via gate().
import type { AwsCall, AwsReply, Transport } from "../../pr10b-wt/packages/explain/src/aws/transport.js";

type P = Record<string, unknown>;

export function keysOf(p: P): { op: string; pk: string }[] {
  return (p.TransactItems as Record<string, Record<string, unknown>>[]).map((it) => {
    const [op, body] = Object.entries(it)[0]!;
    const b = body as { Key?: { pk: { S: string } }; Item?: { pk: { S: string } } };
    return { op, pk: (b.Key ?? b.Item)!.pk.S };
  });
}

export function kind(p: P): string {
  const s = JSON.stringify(p);
  if (s.includes("ConditionCheck")) return "reserve";
  if (s.includes(":settled")) return "settle";
  return "persist";
}

export class Locks {
  readonly held = new Map<string, number>();
  readonly log: string[] = [];
  /** Return a promise to keep this transaction's locks held until it resolves. */
  gate: ((p: P, k: string) => Promise<void> | undefined) | undefined;
  onConflict: ((k: string) => void) | undefined;
  constructor(private readonly inner: Transport) {}
  readonly transport: Transport = async (call: AwsCall): Promise<AwsReply> => {
    if (call.service !== "dynamodb") return this.inner(call);
    const op = (call.headers["x-amz-target"] ?? "").replace("DynamoDB_20120810.", "");
    const p = JSON.parse(call.body) as P;
    if (op === "TransactWriteItems") {
      const ks = keysOf(p);
      const k = kind(p);
      const blocked = ks.filter((x) => (this.held.get(x.pk) ?? 0) > 0);
      if (blocked.length > 0) {
        this.log.push(`CONFLICT ${k} on ${blocked.map((b) => b.pk).join(",")}`);
        this.onConflict?.(k);
        return {
          status: 400, headers: {},
          body: JSON.stringify({
            __type: "com.amazonaws.dynamodb.v20120810#TransactionCanceledException",
            Message: "Transaction cancelled",
            CancellationReasons: ks.map((x) => ({ Code: (this.held.get(x.pk) ?? 0) > 0 ? "TransactionConflict" : "None" })),
          }),
        };
      }
      for (const x of ks) this.held.set(x.pk, (this.held.get(x.pk) ?? 0) + 1);
      try {
        const g = this.gate?.(p, k);
        if (g) await g;
        const r = await this.inner(call);
        this.log.push(`OK ${k} status ${r.status}`);
        return r;
      } finally {
        for (const x of ks) this.held.set(x.pk, (this.held.get(x.pk) ?? 1) - 1);
      }
    }
    if (op === "PutItem" || op === "UpdateItem" || op === "DeleteItem") {
      const pk = ((p.Key ?? p.Item) as { pk: { S: string } }).pk.S;
      if ((this.held.get(pk) ?? 0) > 0) {
        this.log.push(`CONFLICT single ${op} ${pk}`);
        return { status: 400, headers: {}, body: JSON.stringify({ __type: "com.amazonaws.dynamodb.v20120810#TransactionConflictException" }) };
      }
    }
    return this.inner(call);
  };
}

export function later(): { p: Promise<void>; go: () => void } {
  let go!: () => void;
  const p = new Promise<void>((r) => { go = r; });
  return { p, go };
}

export async function waitFor(f: () => boolean): Promise<void> {
  for (let i = 0; i < 20000; i++) { if (f()) return; await new Promise((r) => setImmediate(r)); }
  throw new Error("timeout waiting");
}
