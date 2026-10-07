// Reimplements the RIC formatJsonMessage single-param branch, then checks top-level selectors.
const app = JSON.stringify({outcome:"paused",status:503,ms:5,code:"E_SETTLE",pausePersisted:0,overrun:1,billedBoundViolated:1});
const stored = JSON.stringify({timestamp:"t",level:"INFO",requestId:"r",message:app});
const ev = JSON.parse(stored);
for (const k of ["overrun","billedBoundViolated","pausePersisted","code"]) console.log(k, "top-level:", k in ev, " message type:", typeof ev.message);
const asObj = JSON.parse(JSON.stringify({timestamp:"t",level:"INFO",requestId:"r",message:JSON.parse(app)}));
console.log("if object logged -> $.message.code =", asObj.message.code);
