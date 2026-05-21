# Roadmap

## Near-term
- [ ] Streaming Clinical Brief -- SSE token streaming to Streamlit
      so the brief appears in real-time rather than after full generation
- [ ] Multi-patient support -- orchestrator handles multiple patient
      IDs concurrently, not just Patient 4B
- [ ] Configurable agent roster -- add/remove agents without
      touching orchestrator code

## Medium-term
- [ ] FHIR integration -- replace mock_data with real HL7 FHIR R4
      endpoints for live EMR connectivity (requires hospital IT approval)
- [ ] Escalation routing -- Agent 3 can page on-call physician via
      webhook when Clinical Brief reaches severity threshold
- [ ] Audit log -- immutable record of every A2A message and
      Clinical Brief for clinical governance

## Long-term
- [ ] Local inference -- replace Groq with local Llama 3 via Ollama
      for air-gapped hospital deployments (no external API calls)
- [ ] SOFA/NEWS2 scoring layer -- add a dedicated scoring agent that
      computes standardized severity scores as structured data
      alongside the LLM-generated brief
- [ ] Multi-hospital federation -- shared anonymized deterioration
      patterns across hospital deployments
