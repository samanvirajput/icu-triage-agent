# Design Decisions

## Why A2A messaging over a single monolithic prompt
A single LLM prompt combining vitals + EMR + medications would exceed
context limits for complex patients and obscure which agent is
responsible for which clinical domain. A2A messaging gives each agent
a focused role, a dedicated system prompt, and a narrow tool set.
This mirrors real ICU workflows -- the bedside nurse, the pharmacist,
and the attending physician each have domain expertise and communicate
through structured handoffs.

## Why the LLM decides clinical significance (not hardcoded rules)
Hardcoded rules (SpO2 < 92% -> alert) fail on edge cases: a COPD
patient with chronic hypoxemia has a different baseline than a
post-surgical patient. The LLM interprets vitals in the context of
the patient's history, current medications, and lab trends -- exactly
what a clinician does. The tradeoff is non-determinism; mitigated
by the Pharmacist agent's explicit medication validation step before
any Clinical Brief is broadcast.

## Why Groq + Llama 3.3 70B
Groq's LPU hardware delivers ~500 tokens/second on Llama 3.3 70B --
roughly 10x faster than equivalent GPU inference. For a triage system
where latency directly affects patient outcomes, this matters.
Llama 3.3 70B provides strong clinical reasoning without requiring
a proprietary model. The tradeoff is the free-tier rate limit
(30 req/min), handled by inter-call delays.

## Why in-process async message bus over external broker
An external broker (Redis pub/sub, RabbitMQ) adds operational
complexity -- another service to run, monitor, and secure. For a
single-hospital deployment with 3 agents and low message volume,
an in-process asyncio bus is sufficient, faster, and simpler to
debug. The bus interface is abstracted so an external broker can
be swapped in without changing agent code.

## Why Streamlit for the UI
ICU triage is a demo/prototype context. Streamlit delivers a
functional 3-column clinical dashboard in minimal code, letting
the architecture and agent logic be the focus. A production
deployment would replace Streamlit with a proper React frontend
with websocket streaming for real-time vitals.

## Why mock data over a live EMR connection
Real EMR integration (Epic FHIR, Cerner) requires hospital IT
approval, OAuth flows, and HIPAA compliance infrastructure -- none
of which are appropriate for a research prototype. The mock_data
layer uses a realistic Patient 4B scenario (CHF, SpO2 decline,
missed diuretic) that exercises all agent capabilities without
touching real patient data.
