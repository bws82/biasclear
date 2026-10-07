// Q2: partially read / oddly shaped logging and retention bodies, runtime vs
// the deploy-time jq in infra/aws/ops.sh (cmd_settings).
import { execFileSync } from "node:child_process";
import { describe, expect, it } from "vitest";
import { readAccountSettings } from "../../pr10b-wt/packages/explain/src/aws/bedrock.js";
import type { Transport } from "../../pr10b-wt/packages/explain/src/aws/transport.js";

const JQ_LOGGING = 'if .loggingConfig == null then "off" elif (.loggingConfig | type) != "object" then "on" elif (.loggingConfig | length) > 0 then "on" else "off" end';

function jqLogging(body: string): string {
  try {
    return execFileSync("jq", ["-r", JQ_LOGGING], { input: `${body}\n` }).toString().trim();
  } catch { return "jq-error(exit!=0)"; }
}

async function runtimeLogging(body: string): Promise<string> {
  const t: Transport = async (call) => ({ status: 200, headers: {}, body: call.path === "/data-retention" ? '{"mode":"none"}' : body });
  try {
    return (await readAccountSettings(t, "us-east-1", ["us-east-1", "us-east-2", "us-west-2"])).loggingOn ? "on" : "off";
  } catch { return "read-error"; }
}

describe("logging body interpretation", () => {
  const bodies = [
    "{}",
    '{"loggingConfig":null}',
    '{"loggingConfig":{}}',
    '{"loggingConfig":{"cloudWatchConfig":{"logGroupName":"g"}}}',
    '{"loggingConfig":[]}',
    '{"loggingConfig":[{"s3Config":{}}]}',
    '{"loggingConfig":false}',
    '{"loggingConfig":""}',
    '{"LoggingConfig":{"s3Config":{"bucketName":"b"}}}',
    '{"message":"Rate exceeded"}',
    '{"loggingConfig":{"s3Config":{"bucketName":"b"}},"loggingConfig":null}',
    "",
  ];
  it("table", async () => {
    const rows: string[] = [];
    for (const b of bodies) rows.push(`${JSON.stringify(b)} runtime=${await runtimeLogging(b)} ops.sh=${jqLogging(b)}`);
    console.log(rows.join("\n"));
    // Divergence: an array loggingConfig is "off" at runtime but "on" at deploy time.
    expect(await runtimeLogging('{"loggingConfig":[{"s3Config":{}}]}')).toBe("on");
    expect(await runtimeLogging('{"loggingConfig":[]}')).toBe("off");
    expect(jqLogging('{"loggingConfig":[]}')).toBe("on");
    // Any 200 JSON object without the exact key reads as "logging off" in both.
    expect(await runtimeLogging('{"LoggingConfig":{"s3Config":{"bucketName":"b"}}}')).toBe("off");
    expect(jqLogging('{"LoggingConfig":{"s3Config":{"bucketName":"b"}}}')).toBe("off");
    // An empty CLI stdout is "off" at deploy time (jq exits 0 with no output).
    expect(jqLogging("")).toBe("");
  });
});
