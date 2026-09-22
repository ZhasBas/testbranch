"""Minimal Streamlit UI. Conversation history lives in SDK SQLiteSession."""

import asyncio
import json
import sqlite3
from uuid import uuid4

import streamlit as st
from agents.exceptions import AgentsException, MaxTurnsExceeded, ModelBehaviorError
from agents.items import ToolCallItem, ToolCallOutputItem
from openai import APIError, AuthenticationError, RateLimitError

from agent import get_settings, run_agent
from db import init_db


def activity_rows(items: list) -> list[dict]:
    """Read SDK items only; matching IDs also handles parallel tool calls."""
    calls = {}
    for item in items:
        if isinstance(item, ToolCallItem):
            raw = item.raw_item
            arguments = raw.get("arguments", "") if isinstance(raw, dict) else getattr(raw, "arguments", "")
            calls[item.call_id] = {
                "tool": item.tool_name,
                "arguments": arguments,
                "status": "No result recorded",
                "result": "",
            }
        elif isinstance(item, ToolCallOutputItem) and item.call_id in calls:
            output = item.output
            if isinstance(output, str):
                try:
                    output = json.loads(output)
                except json.JSONDecodeError:
                    pass
            ok = output.get("ok") if isinstance(output, dict) else None
            calls[item.call_id]["status"] = {True: "Success", False: "Failed"}.get(ok, "Completed")
            calls[item.call_id]["result"] = str(output)[:1500]
    return list(calls.values())


def readable_error(error: Exception) -> str:
    # Do not display raw API/SDK exception bodies: they can contain request secrets.
    if isinstance(error, MaxTurnsExceeded):
        return "The agent reached its turn limit. Try a smaller goal."
    if isinstance(error, AuthenticationError):
        return "OpenAI authentication failed. Check OPENAI_API_KEY locally."
    if isinstance(error, RateLimitError):
        return "OpenAI quota or rate limit reached. Check billing, or wait and retry."
    if isinstance(error, APIError):
        return "OpenAI request failed. Check network access, model access, and service availability."
    if isinstance(error, (sqlite3.Error, OSError)):
        return "Local database access failed. Check folder permissions and database file locks."
    if isinstance(error, ModelBehaviorError):
        return "The model returned invalid output or tool arguments. Try a clearer goal."
    if isinstance(error, AgentsException):
        return "The agent could not complete this run. Check its tool configuration and SDK trace."
    return "Unexpected application error (" + type(error).__name__ + "). Check the implementation and SDK trace."


st.set_page_config(page_title="Phormeta")
st.title("Phormeta")
st.caption("A minimal agentic AI starter for your next hackathon case.")

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = uuid4().hex
    st.session_state.messages = []  # Display only; never sent as agent memory.
    st.session_state.activity = []

if st.button("Reset conversation"):
    st.session_state.conversation_id = uuid4().hex
    st.session_state.messages = []
    st.session_state.activity = []
    st.session_state.pop("goal", None)
    st.rerun()

ready = True
try:
    get_settings()
except ValueError as error:
    st.error(str(error))  # Only our fixed configuration validation message.
    ready = False
try:
    init_db()
except (sqlite3.Error, OSError) as error:
    st.error(readable_error(error))
    ready = False

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message.get("error"):
            st.error(message["content"])
        else:
            st.markdown(message["content"])

with st.form("agent_goal", clear_on_submit=True):
    goal = st.text_area("Your goal", key="goal")
    submitted = st.form_submit_button("Run agent", disabled=not ready)

if submitted:
    if not goal.strip():
        st.warning("Enter a goal first.")
    else:
        st.session_state.messages.append({"role": "user", "content": goal.strip()})
        st.session_state.activity = []
        with st.spinner("Agent is working..."):
            try:
                result = asyncio.run(run_agent(goal.strip(), st.session_state.conversation_id))
                st.session_state.activity = activity_rows(result.new_items)
                st.session_state.messages.append({"role": "assistant", "content": str(result.final_output)})
            except Exception as error:
                details = getattr(error, "run_data", None)
                st.session_state.activity = activity_rows(getattr(details, "new_items", []))
                st.session_state.messages.append({
                    "role": "assistant", "error": True,
                    "content": readable_error(error) + " Earlier tool writes may have completed; check activity before retrying.",
                })
        st.rerun()

with st.expander("Agent Activity"):
    st.caption("Most recent run; tool arguments and result previews from the SDK.")
    if not st.session_state.activity:
        st.write("No tool activity recorded.")
    for activity in st.session_state.activity:
        st.write(f"**{activity['tool']}** — {activity['status']}")
        st.code(activity["arguments"], language="json")
        st.text(activity["result"])
