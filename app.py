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

AGENT_COLORS = {
    "sentry": "#4FC3F7",
    "historian": "#81C784",
    "pharmacist": "#FFB74D",
}

AGENT_ICONS = {
    "sentry": "🔵",
    "historian": "🟢",
    "pharmacist": "🟠",
}

INTENT_BADGES = {
    "alert": "🚨",
    "query": "❓",
    "response": "📋",
    "clinical_brief": "📄",
}


def build_vitals_dataframe() -> pd.DataFrame:
    vitals = get_live_vitals(PATIENT_ID)
    df = pd.DataFrame(vitals)
    df = df.set_index("time")
    return df


def render_clinical_brief(brief: dict):
    text = brief.get("clinical_brief", "")
    missed = brief.get("missed_medications", [])
    interactions = brief.get("interactions", [])

    priority = "HIGH"
    if "Priority: HIGH" in text:
        priority = "HIGH"
    elif "Priority: MEDIUM" in text:
        priority = "MEDIUM"
    else:
        priority = "LOW"

    color = {"HIGH": "#FF4444", "MEDIUM": "#FFA500", "LOW": "#44BB44"}.get(priority, "#888")

    st.markdown(
        f"""
        <div style="
            border: 2px solid {color};
            border-radius: 10px;
            padding: 16px;
            background: #1a1a2e;
            font-family: monospace;
        ">
        <h3 style="color:{color}; margin-top:0;">
            CLINICAL BRIEF — Patient {PATIENT_ID}
        </h3>
        <pre style="color:#eee; white-space:pre-wrap; font-size:13px;">{text}</pre>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if missed:
        st.error("**Missed Medications:**\n" + "\n".join(f"- {m}" for m in missed))

    if interactions:
        st.warning("**Drug Interactions:**\n" + "\n".join(f"- {i}" for i in interactions))
    else:
        st.success("No drug interactions flagged.")


def render_message_card(msg: dict):
    sender = msg.get("sender", "unknown")
    receiver = msg.get("receiver", "")
    intent = msg.get("intent", "")
    ts = msg.get("timestamp", "")
    payload = msg.get("payload", {})

    icon = AGENT_ICONS.get(sender, "⚪")
    badge = INTENT_BADGES.get(intent, "💬")
    color = AGENT_COLORS.get(sender, "#aaa")

    st.markdown(
        f"""
        <div style="
            border-left: 4px solid {color};
            padding: 8px 12px;
            margin: 6px 0;
            background: #111827;
            border-radius: 4px;
        ">
        <span style="color:{color}; font-weight:bold;">{icon} {sender.upper()}</span>
        <span style="color:#888;"> → </span>
        <span style="color:#ccc;">{receiver}</span>
        <span style="float:right; color:#555; font-size:11px;">{ts} {badge} {intent}</span>
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


def main():
    st.set_page_config(
        page_title="ICU Triage Agent",
        page_icon="🏥",
        layout="wide",
    )

    st.title("ICU Autonomous Triage & Handoff Agent")
    st.caption(f"Patient **{PATIENT_ID}** · ICU Bed 4B · 67M · Admitted: CHF")

    col_vitals, col_log, col_brief = st.columns([1, 1.2, 1])

    with col_vitals:
        st.subheader("Live Vitals — Patient 4B")
        df = build_vitals_dataframe()
        st.line_chart(df[["spo2", "hr"]], color=["#4FC3F7", "#FF6B6B"])

        st.markdown("**Latest readings:**")
        latest = df.iloc[-1]
        c1, c2, c3 = st.columns(3)
        c1.metric("SpO₂", f"{int(latest['spo2'])}%", delta=f"{int(latest['spo2']) - int(df.iloc[0]['spo2'])}%")
        c2.metric("HR", f"{int(latest['hr'])} bpm", delta=f"{int(latest['hr']) - int(df.iloc[0]['hr'])} bpm")
        c3.metric("BP", latest["bp"])

        st.markdown("---")
        run_btn = st.button("Run Triage", use_container_width=True, type="primary")

    with col_log:
        st.subheader("Agent Conversation Log")
        log_placeholder = st.empty()

    with col_brief:
        st.subheader("Clinical Brief")
        brief_placeholder = st.empty()

    if run_btn:
        if not os.getenv("GROQ_API_KEY"):
            st.error("GROQ_API_KEY not found. Add it to your .env file.")
            return

        messages_so_far = []
        brief_result = None

        def on_message(msg: A2AMessage):
            messages_so_far.append(msg.to_dict())

            with log_placeholder.container():
                for m in messages_so_far:
                    render_message_card(m)

            if msg.intent == "clinical_brief":
                with brief_placeholder.container():
                    render_clinical_brief(msg.payload)

        status_map = {
            "sentry": "Sentry analyzing vitals...",
            "historian": "Historian querying EMR records...",
            "pharmacist": "Pharmacist reviewing medications...",
        }

        orchestrator = Orchestrator(on_message=on_message)

        with col_vitals:
            with st.spinner("Running multi-agent triage..."):
                with col_log:
                    for agent_name, status_msg in status_map.items():
                        col_log.info(f"⏳ {status_msg}")

                result = asyncio.run(orchestrator.run_triage(PATIENT_ID))

        with log_placeholder.container():
            for m in result["messages"]:
                render_message_card(m)

        if result.get("clinical_brief"):
            with brief_placeholder.container():
                render_clinical_brief(result["clinical_brief"])
        else:
            brief_placeholder.warning("No clinical brief generated — check agent logs.")

        with col_vitals:
            st.success(f"Triage complete. {len(result['messages'])} messages exchanged.")


if __name__ == "__main__":
    main()
