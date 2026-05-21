# Challenges

## Groq rate limiting with 3 sequential LLM calls
The Groq free tier allows 30 requests/minute. A single triage run
makes 3 LLM calls minimum -- at high frequency this hits the limit
quickly. Solution: a 2-second delay inserted between calls in the
orchestrator. This adds latency but prevents 429 errors mid-triage,
which would leave a Clinical Brief incomplete. A production deployment
would use the paid tier with higher rate limits or implement
exponential backoff with retry.

## LLM non-determinism in clinical context
The same vitals input can produce slightly different Clinical Brief
wording across runs. For a research prototype this is acceptable,
but in a clinical setting non-determinism in safety-critical outputs
is a concern. Partial mitigation: the Pharmacist agent's system
prompt includes explicit output format constraints and a mandatory
medication verification step before broadcasting.

## A2A message ordering under async execution
With asyncio, message delivery order is not guaranteed if agents
process concurrently. Early versions had the Pharmacist generating
a Clinical Brief before the Historian had finished EMR retrieval --
producing incomplete context. Solution: the orchestrator enforces
a sequential pipeline (Sentry -> Historian -> Pharmacist) rather than
fully parallel execution, trading some throughput for correctness.

## Mock data realism
The Patient 4B scenario needed to be realistic enough to exercise
all agent capabilities -- SpO2 trend, BNP elevation, missed diuretic
-- without being so complex it obscured the A2A flow. Several
iterations were needed to find the right balance of clinical
detail and narrative clarity for demo purposes.

## Context accumulation across agent turns
Each agent maintains its own conversation context. In long triage
sessions, this context grows unbounded -- eventually exceeding the
model's context window. Solution: context is pruned to the last
N turns per agent after each triage run, keeping each agent's
working memory bounded.
