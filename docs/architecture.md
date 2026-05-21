# Architecture

## System Overview

ICU Triage Agent is a 3-agent A2A system for autonomous ICU patient
monitoring. The LLM -- not hardcoded rules -- decides what is clinically
concerning. Agents communicate via an in-process async message bus.

```
Patient Vitals Stream
        |
        v
[ Sentry Agent ]             <- detects deterioration trends
  MCP: get_live_vitals          SpO2, HR, MAP, RR over time
        |
        | A2A: "SpO2 trend concern"
        v
[ Historian Agent ]          <- retrieves EMR context
  MCP: query_lab_results,       BNP, clinical notes,
       fetch_clinical_notes      prior orders
        |
        | A2A: "BNP elevated, furosemide ordered"
        v
[ Pharmacist Agent ]         <- validates medication safety
  MCP: get_active_infusions     checks active infusions
                                generates Clinical Brief
        |
        | A2A broadcast
        v
[ Clinical Brief ]           <- actionable output to clinician
  (Streamlit UI)                "furosemide NOT given -> act now"
```

## A2A Message Flow (Demo Scenario)

Patient 4B -- 67-year-old male, CHF. SpO2 drops 97->91 over 20 minutes.

```
Sentry    -> Historian   [query: SpO2 trend concern]
Historian -> Sentry      [response: BNP elevated, furosemide ordered]
Historian -> Pharmacist  [query: was diuretic administered?]
Pharmacist -> broadcast  [clinical_brief: furosemide NOT given -> act now]
```

## Project Structure

```
icu-triage-agent/
├── app.py                  # Streamlit UI (3-column layout)
├── orchestrator.py         # Message bus + agent lifecycle
├── agents/
│   ├── base_agent.py       # Abstract base + Groq client
│   ├── sentry.py           # Vitals trend analysis
│   ├── historian.py        # EMR context retrieval
│   └── pharmacist.py       # Medication safety + clinical brief
├── mcp_tools/
│   ├── vitals.py           # get_live_vitals(patient_id)
│   ├── labs.py             # query_lab_results(patient_id)
│   ├── notes.py            # fetch_clinical_notes(patient_id)
│   └── infusions.py        # get_active_infusions(patient_id)
├── mock_data/              # Patient 4B scenario data
├── a2a/
│   ├── message.py          # A2AMessage dataclass
│   └── bus.py              # In-process async message bus
└── scripts/
    └── update_readme.py    # Auto-README updater
```

16 source files -- 811 lines of Python

## Component Details

### Orchestrator (orchestrator.py)
- Manages agent lifecycle: spawn, message routing, shutdown
- Owns the async message bus
- Coordinates 3-agent pipeline per triage run
- Inserts 2-second delay between LLM calls (Groq rate limit: 30 req/min)

### Message Bus (a2a/bus.py)
- In-process async pub/sub
- A2AMessage dataclass: sender, recipient, message_type, payload, timestamp
- Supports both directed messages and broadcast
- No external broker dependency -- fully in-process

### MCP Tools (mcp_tools/)
- get_live_vitals(patient_id) -> SpO2, HR, MAP, RR time series
- query_lab_results(patient_id) -> BNP, CBC, metabolic panel
- fetch_clinical_notes(patient_id) -> structured clinical history
- get_active_infusions(patient_id) -> current medication orders

### LLM Layer
- Model: Groq -- Llama 3.3 70B (llama-3.3-70b-versatile)
- Client: OpenAI SDK pointed at Groq endpoint
- Each agent maintains its own system prompt + conversation context
- LLM decides clinical significance -- no hardcoded threshold rules
