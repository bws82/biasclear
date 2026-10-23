# Explain offline evaluation rehearsal

Actual spend: $0. All operations used in-memory AWS/model stubs. Times, tokens, costs and answers are synthetic.
Fixed synthetic usage per attempted call: 100 input / 40 output tokens. It is not a model measurement.
Model quality is unmeasured. Nothing is approved to ship. The real matched-pair, injection and rewrite review remains a separate owner-approved sitting under the cap.

Fixture SHA-256: 0a3a4be14b244e7e7ec6de9692f50e0e311570710ce0e30ae1c8a5d699a6565f

## Grok 4.7

Route: us.xai.grok-4.7. Live configuration blocked: yes.

| Part | Planned | Ran | Answered | Refusal-like | Preflight rejected | Output rejected | Simulated cost USD | Simulated time ms |
|---|---|---|---|---|---|---|---|---|
| a | 490 | 490 | 490 | 0 | 0 | 0 | 0.23716 | 490 |
| b | 490 | 490 | 490 | 0 | 0 | 0 | 0.23716 | 490 |
| i | 63 | 63 | 42 | 0 | 3 | 18 | 0.02904 | 60 |
| r | 18 | 18 | 18 | 0 | 0 | 0 | 0.008712 | 18 |
| c | 24 | 24 | 24 | 0 | 0 | 0 | 0.011616 | 24 |

Stub verdict probes rejected: 9/9. Unsafe stub rewrites dropped: 6/6. Safe stub rewrites kept: 12/12.
Synthetic wiring checks: pass. This is not a model pass.

## Claude Sonnet 5.5

Route: us.anthropic.claude-sonnet-5-5. Live configuration blocked: yes.

| Part | Planned | Ran | Answered | Refusal-like | Preflight rejected | Output rejected | Simulated cost USD | Simulated time ms |
|---|---|---|---|---|---|---|---|---|
| a | 490 | 490 | 490 | 0 | 0 | 0 | 0.3234 | 490 |
| b | 490 | 490 | 490 | 0 | 0 | 0 | 0.3234 | 490 |
| i | 63 | 63 | 42 | 0 | 3 | 18 | 0.0396 | 60 |
| r | 18 | 18 | 18 | 0 | 0 | 0 | 0.01188 | 18 |
| c | 24 | 24 | 24 | 0 | 0 | 0 | 0.01584 | 24 |

Stub verdict probes rejected: 9/9. Unsafe stub rewrites dropped: 6/6. Safe stub rewrites kept: 12/12.
Synthetic wiring checks: pass. This is not a model pass.

## GPT-6.1 Sol

Route: us.openai.gpt-6.1-sol. Live configuration blocked: yes.

| Part | Planned | Ran | Answered | Refusal-like | Preflight rejected | Output rejected | Simulated cost USD | Simulated time ms |
|---|---|---|---|---|---|---|---|---|
| a | 490 | 490 | 490 | 0 | 0 | 0 | 0.3234 | 490 |
| b | 490 | 490 | 490 | 0 | 0 | 0 | 0.3234 | 490 |
| i | 63 | 63 | 42 | 0 | 3 | 18 | 0.0396 | 60 |
| r | 18 | 18 | 18 | 0 | 0 | 0 | 0.01188 | 18 |
| c | 24 | 24 | 24 | 0 | 0 | 0 | 0.01584 | 24 |

Stub verdict probes rejected: 9/9. Unsafe stub rewrites dropped: 6/6. Safe stub rewrites kept: 12/12.
Synthetic wiring checks: pass. This is not a model pass.

