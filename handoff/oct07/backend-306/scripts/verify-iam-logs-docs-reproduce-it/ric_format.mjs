// Extracts formatJsonMessage + jsonErrorReplacer verbatim from aws-lambda-ric 4.0.2 and applies it to an app line.
import { readFileSync } from "node:fs";
import { format } from "node:util";
const src = readFileSync(process.argv[2], "utf8");
const fn = src.slice(src.indexOf("function formatJsonMessage("), src.indexOf("// dist/logging/socket-logger.js"));
const JSON_LOG_FIELDS = { TIMESTAMP: "timestamp", LEVEL: "level", REQUEST_ID: "requestId", TENANT_ID: "tenantId", MESSAGE: "message", ERROR_TYPE: "errorType", ERROR_MESSAGE: "errorMessage", STACK_TRACE: "stackTrace" };
const formatJsonMessage = new Function("format", "JSON_LOG_FIELDS", fn + "; return formatJsonMessage;")(format, JSON_LOG_FIELDS);
const app = '{"outcome":"paused","status":503,"ms":0,"code":"E_SETTLE","pausePersisted":0}';
const stored = formatJsonMessage("2026-10-07T00:00:00.000Z", "req-1", "", { name: "INFO" }, app);
console.log("STORED:", stored);
const ev = JSON.parse(stored);
// CloudWatch JSON selector $.x = top-level property lookup on the parsed event
const sel = (k) => ev[k];
console.log("typeof message:", typeof ev.message);
console.log("$.pausePersisted:", sel("pausePersisted"), " $.code:", sel("code"), " $.overrun:", sel("overrun"), " $.billedBoundViolated:", sel("billedBoundViolated"));
const asObj = formatJsonMessage("2026-10-07T00:00:00.000Z", "req-1", "", { name: "INFO" }, JSON.parse(app));
console.log("IF LOGGED AS OBJECT:", asObj);
