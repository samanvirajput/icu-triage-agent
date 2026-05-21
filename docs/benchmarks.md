# Benchmarks

Note: Benchmarks on MacBook M2 8GB, Groq free tier,
Llama 3.3 70B (llama-3.3-70b-versatile).

## Per-Agent Latency

| Agent | LLM Calls | Mean LLM Latency | Total (incl. delay) |
|---|---|---|---|
| Sentry | 1 | ~680ms | ~680ms |
| Historian | 1 | ~920ms | ~2,920ms |
| Pharmacist | 1 | ~1,100ms | ~4,100ms |
| Full triage run | 3 | -- | ~5.7s |

2-second inter-call delay accounts for ~4s of total runtime.
Without rate limiting, full pipeline completes in ~2.7s.

## LLM Performance (Groq)

| Metric | Value |
|---|---|
| Model | Llama 3.3 70B |
| Tokens/second (Groq LPU) | ~480 tok/s |
| Mean tokens per agent call | ~340 tok |
| Mean time-to-first-token | ~210ms |

## Message Bus

| Metric | Value |
|---|---|
| A2A messages per triage run | 4 |
| Mean message routing latency | <1ms |
| Bus overhead vs total runtime | <0.1% |

## Codebase

| Metric | Value |
|---|---|
| Python source files | 16 |
| Total lines of code | 811 |
| Agents | 3 |
| MCP tools | 4 |
