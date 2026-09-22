"""One agent; the SDK owns execution, tool calling, tracing, and memory."""

import os
from pathlib import Path

from agents import Agent, OpenAIResponsesModel, Runner, RunResult, SQLiteSession
from dotenv import load_dotenv
from openai import AsyncOpenAI

from tools.demo_tools import calculate, list_demo_items, save_note

ROOT = Path(__file__).resolve().parent
MAX_TURNS = 8
INSTRUCTIONS = """You are Phormeta, a general-purpose hackathon assistant.
Use tools when they provide factual or deterministic information. Never invent
database records. Prefer the calculation tool over mental arithmetic.
If a tool returns ok=false, explain the failure; never claim it succeeded.
Use tool results to give a clear, concise final answer to the user's goal.
"""


def get_settings() -> tuple[str, str]:
    load_dotenv(ROOT / ".env")
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "").strip()
    missing = [name for name, value in (
        ("OPENAI_API_KEY", api_key), ("OPENAI_MODEL", model)
    ) if not value]
    if missing:
        raise ValueError("Set " + " and ".join(missing) + " in .env, then restart Streamlit.")
    return api_key, model


async def run_agent(goal: str, session_id: str) -> RunResult:
    api_key, model = get_settings()
    session = SQLiteSession(session_id, ROOT / "agent_sessions.db")
    try:
        # Each Streamlit request uses asyncio.run; don't reuse a client from a closed loop.
        async with AsyncOpenAI(api_key=api_key, timeout=60, max_retries=1) as client:
            agent = Agent(
                name="Phormeta",
                instructions=INSTRUCTIONS,
                model=OpenAIResponsesModel(model=model, openai_client=client),
                tools=[list_demo_items, save_note, calculate],
            )
            return await Runner.run(agent, goal, session=session, max_turns=MAX_TURNS)
    finally:
        session.close()
