// Which DynamoDB items the function writes WITHOUT a TTL (setup.yaml says "Every item has a TTL").
import { it, expect } from "vitest";
import { writeFileSync } from "node:fs";
import { harness, httpEvent, modelReply, requestBody } from "../../pr10b-wt/packages/explain/test/helpers.js";

it("lists items without ttl after an unknown-usage anomaly", async () => {
  const h = harness();
  h.aws.model = () => ({ status: 200, json: modelReply({ usage: null }) });
  const r = await h.call(httpEvent({ body: requestBody() }));
  expect(r.statusCode).toBe(503);
  const rows = [...h.aws.table.items.entries()].map(([pk, item]) => ({ pk: pk.replace(/[0-9a-f]{8}-[0-9a-f-]{27}/, "<uuid>").replace(/#[0-9a-f]{32}#/, "#<hash>#"), attrs: Object.keys(item).sort(), ttl: "ttl" in item }));
  writeFileSync(new URL("./ttl-items.json", import.meta.url), JSON.stringify(rows, null, 1));
  const noTtl = rows.filter((x) => !x.ttl).map((x) => x.pk);
  expect(noTtl.sort()).toEqual(["billing#pause", "billingdebt#<uuid>"]);
  // no request-derived text in the no-TTL items
  for (const [pk, item] of h.aws.table.items) if (!("ttl" in item)) expect(JSON.stringify(item)).not.toMatch(/economist|203\.0\.113/);
});
