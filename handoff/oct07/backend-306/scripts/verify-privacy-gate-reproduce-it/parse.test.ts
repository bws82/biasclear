import { it } from "vitest";
import { readAccountSettings } from "../../pr10b-wt/packages/explain/src/aws/bedrock.js";
import { execFileSync } from "node:child_process";
const JQ = 'if .loggingConfig == null then "off" elif (.loggingConfig | type) != "object" then "on" elif (.loggingConfig | length) > 0 then "on" else "off" end';
it("table", async () => {
  const bodies = ["{}", '{"loggingConfig":null}', '{"loggingConfig":{}}', '{"loggingConfig":[]}', '{"LoggingConfig":{"s3Config":{"bucketName":"b"}}}',
    '{"message":"Rate exceeded"}', '{"loggingConfig":{"s3Config":{"bucketName":"b"}}}', '{"loggingConfig":{"textDataDeliveryEnabled":false}}'];
  const rows = [];
  for (const b of bodies) {
    let rt: string;
    try {
      const s = await readAccountSettings(async (c) => ({ status: 200, headers: {}, body: c.path.startsWith("/logging") ? b : '{"mode":"none"}' }), "us-east-1", ["us-east-1"]);
      rt = s.loggingOn ? "on" : "off";
    } catch { rt = "throw(pause)"; }
    const ops = execFileSync("jq", ["-r", JQ], { input: b }).toString().trim();
    rows.push({ body: b, runtime: rt, opsSh: ops });
  }
  console.table(rows);
});
