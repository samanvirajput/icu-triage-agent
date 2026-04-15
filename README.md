# ICU Autonomous Triage & Handoff Agent

A multi-agent AI system for ICU patient monitoring that detects clinical deterioration trends, 
queries historical records, validates medication orders, and generates an actionable Clinical Brief — 
all autonomously via agent-to-agent (A2A) messaging.

## Stack

| Component | Technology |
|-----------|-----------|
| LLM | Groq — Llama 3.3 70B (`llama-3.3-70b-versatile`) |
| UI | Streamlit |
| Async | Python asyncio |
| Client | OpenAI SDK → Groq endpoint |

## Quick Start

```bash
pip install -r requirements.txt
# Add your GROQ_API_KEY to .env
streamlit run app.py
```

## Demo Scenario

**Patient 4B** — 67-year-old male, CHF. SpO₂ drops 97→91 over 20 minutes.

| Agent | Role | MCP Tools Used |
|-------|------|---------------|
| **Sentry** | Vitals trend monitor | `get_live_vitals` |
| **Historian** | EMR context retrieval | `query_lab_results`, `fetch_clinical_notes` |
| **Pharmacist** | Medication safety + brief | `get_active_infusions` |

The LLM — not hardcoded rules — decides what's clinically concerning.

## A2A Message Flow

```
Sentry → Historian  [query: SpO₂ trend concern]
Historian → Sentry  [response: BNP elevated, furosemide ordered]
Historian → Pharmacist  [query: was diuretic administered?]
Pharmacist → broadcast  [clinical_brief: furosemide NOT given → act now]
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
├── mock_data/              # Hardcoded patient 4B scenario data
├── a2a/
│   ├── message.py          # A2AMessage dataclass
│   └── bus.py              # In-process async message bus
└── scripts/
    └── update_readme.py    # Auto-README updater (hook-triggered)
```

**Python source:** 16 files · 811 lines

## Rate Limiting

Groq free tier: 30 req/min. A 2-second delay is inserted between each LLM call.
Three agents = 3 calls minimum per triage run.

## Environment

```
GROQ_API_KEY=gsk_...
```
