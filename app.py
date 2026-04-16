import asyncio
import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

from a2a.message import A2AMessage
from mcp_tools.vitals import get_live_vitals
from orchestrator import Orchestrator

PATIENT_ID = "4B"

AGENT_ICONS = {
    "sentry": "●",
    "historian": "●",
    "pharmacist": "●",
}

INTENT_BADGES = {
    "alert": "alert",
    "query": "query",
    "response": "response",
    "clinical_brief": "brief",
}


def _load_css():
    css = (Path(__file__).parent / "static" / "style.css").read_text()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def build_vitals_dataframe() -> pd.DataFrame:
    vitals = get_live_vitals(PATIENT_ID)
    df = pd.DataFrame(vitals)
    df = df.set_index("time")
    return df


def render_message_card(msg: dict):
    sender   = msg.get("sender", "unknown")
    receiver = msg.get("receiver", "")
    intent   = msg.get("intent", "")
    ts       = msg.get("timestamp", "")
    payload  = msg.get("payload", {})

    icon  = AGENT_ICONS.get(sender, "●")
    badge = INTENT_BADGES.get(intent, intent)

    st.markdown(
        f"""
        <div class="msg-card agent-{sender}">
          <div class="msg-header">
            <span>
              <span class="msg-sender">{icon} {sender.upper()}</span>
              <span class="msg-arrow">→</span>
              <span class="msg-receiver">{receiver}</span>
            </span>
            <span class="msg-meta">{ts} · {badge}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Payload", expanded=(intent == "clinical_brief")):
        for k, v in payload.items():
            if isinstance(v, str) and len(v) > 80:
                st.text(f"{k}:\n{v}")
            elif isinstance(v, list):
                st.markdown(f"**{k}:**")
                for item in v:
                    st.markdown(f"- {item}" if isinstance(item, str) else f"- `{item}`")
            else:
                st.markdown(f"**{k}:** {v}")


def render_clinical_brief(brief: dict):
    text         = brief.get("clinical_brief", "")
    missed       = brief.get("missed_medications", [])
    interactions = brief.get("interactions", [])

    if "Priority: HIGH" in text:
        priority = "HIGH"
    elif "Priority: MEDIUM" in text:
        priority = "MEDIUM"
    else:
        priority = "LOW"

    priority_cls = f"priority-{priority.lower()}"

    st.markdown(
        f"""
        <div class="brief-card {priority_cls}">
          <div class="brief-label">Clinical Brief — Patient {PATIENT_ID} · {priority}</div>
          <pre>{text}</pre>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if missed:
        st.error("**Missed medications:** " + " · ".join(missed))
    if interactions:
        st.warning("**Drug interactions:** " + " · ".join(interactions))
    else:
        st.success("No drug interactions flagged.")


def main():
    st.set_page_config(
        page_title="ICU Triage Agent",
        page_icon="🏥",
        layout="centered",
    )
    _load_css()

    # ── Header ──────────────────────────────────────────────────────────
    st.title("ICU Triage Agent")
    st.caption(f"Patient **{PATIENT_ID}** · ICU Bed 4B · 67M · Admitted: CHF")

    # ── Vitals chart ─────────────────────────────────────────────────────
    df = build_vitals_dataframe()
    st.line_chart(df[["spo2", "hr"]], color=["#4FC3F7", "#f85149"])

    latest = df.iloc[-1]
    c1, c2, c3 = st.columns(3)
    c1.metric("SpO₂", f"{int(latest['spo2'])}%",
              delta=f"{int(latest['spo2']) - int(df.iloc[0]['spo2'])}%")
    c2.metric("HR", f"{int(latest['hr'])} bpm",
              delta=f"{int(latest['hr']) - int(df.iloc[0]['hr'])} bpm")
    c3.metric("BP", latest["bp"])

    st.divider()

    # ── Trigger ──────────────────────────────────────────────────────────
    run_btn = st.button("Run Triage", use_container_width=True, type="primary")

    # ── Output areas ─────────────────────────────────────────────────────
    log_container   = st.container()
    brief_container = st.container()

    if not run_btn:
        return

    if not os.getenv("GROQ_API_KEY"):
        st.error("GROQ_API_KEY not found. Add it to your .env file.")
        return

    messages_so_far: list[dict] = []

    def on_message(msg: A2AMessage):
        messages_so_far.append(msg.to_dict())
        with log_container:
            render_message_card(messages_so_far[-1])
        if msg.intent == "clinical_brief":
            with brief_container:
                st.markdown('<p class="section-label">Clinical Brief</p>',
                            unsafe_allow_html=True)
                render_clinical_brief(msg.payload)

    with st.spinner("Running triage..."):
        orchestrator = Orchestrator(on_message=on_message)
        result = asyncio.run(orchestrator.run_triage(PATIENT_ID))

    if not result.get("clinical_brief"):
        brief_container.warning("No clinical brief generated — check agent logs.")

    st.caption(f"Triage complete · {len(result['messages'])} messages")


if __name__ == "__main__":
    main()
