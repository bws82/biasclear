import { refusalLike } from "../../pr10b-wt/packages/explain/ops/ops.ts";
for (const t of ["```json\n{\"how\":\"I'm sorry, I can't help.\"}\n```", "\"I'm sorry, but I can't help with that.\"", "{\"how\":null,\"note\":\"I cannot help with that.\"}",
  "I’M SORRY", "Je suis désolé, je ne peux pas aider.", "No.", "I will not answer this.", "I can’t."])
  console.log(JSON.stringify(t).padEnd(60), refusalLike({ status: 502, modelCalled: true, providerStopReason: "end_turn", providerText: t }));
