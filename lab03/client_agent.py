"""Lab 3: Pharmacy assistant that uses the MCP server's tools through native function calling.

The client starts server.py over stdio, asks it for its tool list, hands those
tool schemas to the model (LiteLLM, model from LLM_MODEL in .env), and runs
every tool call the model asks for through MCP. Each call is appended to
evidence/tool_calls.jsonl.

    python lab03/client_agent.py "Which items expire within 60 days?"
    python lab03/client_agent.py            # interactive; type 'quit' to stop
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from litellm import completion
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
load_dotenv(ROOT / ".env")

MODEL = os.getenv("LLM_MODEL", "groq/openai/gpt-oss-20b")
LOG_FILE = HERE / "evidence" / "tool_calls.jsonl"
MAX_STEPS = 8


def _schema(tool) -> dict:
    """Tool input schema (named inputSchema in mcp 1.x, input_schema in 2.x)."""
    return getattr(tool, "inputSchema", None) or getattr(tool, "input_schema", None) or {}

SYSTEM_PROMPT = """You are the stock assistant for a small community pharmacy in Accra.
Use the tools to answer; never guess quantities, prices or expiry dates.
Rules: never oversell, never sell expired stock, quote prices in GHS with two decimals,
and point out any item that expires within 60 days. Before recording a sale of a
prescription-only antibiotic, confirm the customer has a prescription.
Keep answers short and clear."""


def mcp_tool_to_openai(tool) -> dict:
    """Convert an MCP tool description into the function-calling format LiteLLM expects."""
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": _schema(tool) or {"type": "object", "properties": {}},
        },
    }


def log_call(question: str, step: int, name: str, args: dict, result: str, is_error: bool) -> None:
    LOG_FILE.parent.mkdir(exist_ok=True)
    entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "model": MODEL,
        "question": question,
        "step": step,
        "tool": name,
        "arguments": args,
        "is_error": is_error,
        "result": result,
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


async def ask(session: ClientSession, tools: list[dict], history: list[dict], question: str) -> str:
    history.append({"role": "user", "content": question})
    for step in range(1, MAX_STEPS + 1):
        response = completion(model=MODEL, messages=history, tools=tools, tool_choice="auto", temperature=0)
        msg = response.choices[0].message
        calls = msg.tool_calls or []
        history.append({
            "role": "assistant",
            "content": msg.content,
            **({"tool_calls": [c.model_dump() for c in calls]} if calls else {}),
        })
        if not calls:
            return msg.content or ""

        for call in calls:
            name = call.function.name
            try:
                args = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            print(f"  [tool] {name}({json.dumps(args)})")
            try:
                result = await session.call_tool(name, args)
                text = "\n".join(c.text for c in result.content if getattr(c, "text", None))
                is_error = bool(getattr(result, "isError", getattr(result, "is_error", False)))
            except Exception as e:  # noqa: BLE001  - report failures back to the model
                text, is_error = f"Tool error: {e}", True
            log_call(question, step, name, args, text, is_error)
            print(f"  [result] {text[:200]}{'...' if len(text) > 200 else ''}")
            history.append({"role": "tool", "tool_call_id": call.id, "name": name, "content": text})
    return "Stopped: too many tool steps without a final answer."


async def main() -> None:
    server = StdioServerParameters(command=sys.executable, args=[str(HERE / "server.py")])
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            listed = await session.list_tools()
            tools = [mcp_tool_to_openai(t) for t in listed.tools]
            print(f"Connected to pharmacy server. Tools: {', '.join(t.name for t in listed.tools)}")
            print(f"Model: {MODEL}\n")

            history = [{"role": "system", "content": SYSTEM_PROMPT}]
            if len(sys.argv) > 1:
                question = " ".join(sys.argv[1:])
                print(f"You: {question}")
                print(f"Agent: {await ask(session, tools, history, question)}")
                return
            while True:
                try:
                    question = input("You: ").strip()
                except EOFError:
                    break
                if question.lower() in {"quit", "exit", "q"}:
                    break
                if question:
                    print(f"Agent: {await ask(session, tools, history, question)}\n")


if __name__ == "__main__":
    asyncio.run(main())
