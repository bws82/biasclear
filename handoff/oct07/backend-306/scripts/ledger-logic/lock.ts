// A thin model of DynamoDB's documented transaction-conflict behaviour, layered
// over the package's FakeAws (which applies transactions instantly and so never
// conflicts). While a TransactWriteItems is "in progress" its item keys are
// locked; another TransactWriteItems touching a locked key is cancelled with
// CancellationReasons Code "TransactionConflict", and a single-item write to a
// locked key gets TransactionConflictException. Reads are not blocked.
// Source of the semantics: DynamoDB developer guide, "Transaction conflict
// handling" (cited by the SPEC itself at handoff/explain/SPEC.md:612).
import type { AwsCall, AwsReply, Transport } from "../../pr10b-wt/packages/explain/src/aws/transport.js";

type Payload = Record<string, unknown>;

export function txKeys(payload: Payload): string[] {
  const items = payload.TransactItems as Record<string, Record<string, unknown>>[];
  return items.map((it) => {
    const body = Object.values(it)[0] as { Key?: { pk: { S: string } }; Item?: { pk: { S: string } } };
    return (body.Key ?? body.Item)!.pk.S;
  });
}

export class LockingTransport {
  readonly locks = new Set<string>();
  readonly conflicts: Array<{ keys: string[]; locked: string[] }> = [];
  /** Optional: called with each admitted transaction; a returned promise keeps its locks held. */
  hold: ((payload: Payload, keys: string[]) => Promise<void> | undefined) | undefined;
  /** Simulated in-progress time for every admitted transaction (ms, real timers). */
  txMs = 0;
  onConflict: ((keys: string[]) => void) | undefined;

  constructor(private readonly inner: Transport) {}

  readonly transport: Transport = async (call: AwsCall): Promise<AwsReply> => {
    if (call.service !== "dynamodb") return this.inner(call);
    const op = (call.headers["x-amz-target"] ?? "").replace("DynamoDB_20120810.", "");
    const payload = JSON.parse(call.body) as Payload;
    if (op === "TransactWriteItems") {
      const keys = txKeys(payload);
      const locked = keys.filter((k) => this.locks.has(k));
      if (locked.length > 0) {
        this.conflicts.push({ keys, locked });
        this.onConflict?.(keys);
        return {
          status: 400,
          headers: {},
          body: JSON.stringify({
            __type: "com.amazonaws.dynamodb.v20120810#TransactionCanceledException",
            CancellationReasons: keys.map((k) => ({ Code: this.locks.has(k) ? "TransactionConflict" : "None" })),
            Message: "Transaction cancelled, please refer cancellation reasons for specific reasons",
          }),
        };
      }
      for (const k of keys) this.locks.add(k);
      try {
        const h = this.hold?.(payload, keys);
        if (h) await h;
        if (this.txMs > 0) await new Promise((r) => setTimeout(r, this.txMs));
        return await this.inner(call);
      } finally {
        for (const k of keys) this.locks.delete(k);
      }
    }
    if (op === "UpdateItem" || op === "PutItem" || op === "DeleteItem") {
      const k = ((payload.Key ?? payload.Item) as { pk: { S: string } }).pk.S;
      if (this.locks.has(k)) {
        this.conflicts.push({ keys: [k], locked: [k] });
        return { status: 400, headers: {}, body: JSON.stringify({ __type: "com.amazonaws.dynamodb.v20120810#TransactionConflictException" }) };
      }
    }
    return this.inner(call);
  };
}

export async function until(cond: () => boolean, limit = 10_000): Promise<void> {
  for (let i = 0; i < limit; i++) {
    if (cond()) return;
    await new Promise((r) => setImmediate(r));
  }
  throw new Error("condition never became true");
}

export function deferred(): { promise: Promise<void>; resolve: () => void } {
  let resolve!: () => void;
  const promise = new Promise<void>((r) => { resolve = r; });
  return { promise, resolve };
}
