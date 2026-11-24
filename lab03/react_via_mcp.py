"""Lab 3 (Wednesday): the Lab 2 ReAct text protocol, with actions served by MCP.

Same Thought / Action / Action Input / Observation loop as Lab 2, but instead of
calling local Python functions, every Action is sent to the pharmacy MCP server.
The model never sees native tool schemas: it reads the tool list as plain text and
writes its actions as text, which this script parses.

    python lab03/react_via_mcp.py "Can I sell 10 packs of Amoxicillin 250mg?"

The full trace is printed and appended to evidence/react_via_mcp.txt.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from litellm import completion
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

HERE = Path(__file__).resolve().parent
load_dotenv(HERE.parent / ".env")
MODEL = os.getenv("LLM_MODEL", "groq/openai/gpt-oss-20b")
TRACE_FILE = HERE / "evidence" / "react_via_mcp.txt"
MAX_STEPS = 8


def _schema(tool) -> dict:
    """Tool input schema (named inputSchema in mcp 1.x, input_schema in 2.x)."""
    return getattr(tool, "inputSchema", None) or getattr(tool, "input_schema", None) or {}

PROMPT_TEMPLATE = """You are the stock assistant for a small community pharmacy in Accra.
You answer by reasoning step by step and using tools. Never guess stock, prices or dates.

Available tools (arguments are JSON):
{tool_text}

Use EXACTLY this format, one step at a time:
Thought: what you need to do next
Action: one tool name from the list above
Action Input: a JSON object with the arguments

Then STOP and wait. You will receive:
Observation: the tool result

Repeat Thought/Action/Action Input as needed. When you can answer:
Thought: I can answer now
Final Answer: your answer to the user
"""

ACTION_RE = re.compile(r"Action:\s*([\w\-]+)\s*\nAction Input:\s*(\{.*?\})\s*$", re.S | re.M)
FINAL_RE = re.compile(r"Final Answer:\s*(.*)", re.S)


def describe_tools(tools) -> str:
    lines = []
    for t in tools:
        params = ", ".join(f"{k}: {v.get('type', 'any')}"
                           for k, v in (_schema(t) or {}).get("properties", {}).items())
        first_line = (t.description or "").strip().splitlines()[0] if t.description else ""
        lines.append(f"- {t.name}({params}): {first_line}")
    return "\n".join(lines)


async def run(question: str) -> str:
    server = StdioServerParameters(command=sys.executable, args=[str(HERE / "server.py")])
    trace: list[str] = [f"=== {datetime.now().isoformat(timespec='seconds')} | model={MODEL}",
                        f"Question: {question}"]

    def emit(text: str) -> None:
        print(text)
        trace.append(text)

    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = (await session.list_tools()).tools
            names = {t.name for t in tools}
            messages = [
                {"role": "system", "content": PROMPT_TEMPLATE.format(tool_text=describe_tools(tools))},
                {"role": "user", "content": question},
            ]
            answer = "Stopped: step limit reached."
            for _ in range(MAX_STEPS):
                reply = completion(model=MODEL, messages=messages, temperature=0,
                                   stop=["Observation:"]).choices[0].message.content or ""
                reply = reply.strip()
                emit(reply)
                messages.append({"role": "assistant", "content": reply})

                final = FINAL_RE.search(reply)
                if final:
                    answer = final.group(1).strip()
                    break

                m = ACTION_RE.search(reply)
                if not m:
                    obs = ("Observation: I could not parse an Action. Reply with 'Action:' and "
                           "'Action Input:' (JSON), or a 'Final Answer:'.")
                elif m.group(1) not in names:
                    obs = f"Observation: Unknown tool '{m.group(1)}'. Choose from: {', '.join(sorted(names))}."
                else:
                    try:
                        args = json.loads(m.group(2))
                        result = await session.call_tool(m.group(1), args)
                        obs = "Observation: " + "\n".join(
                            c.text for c in result.content if getattr(c, "text", None))
                    except json.JSONDecodeError as e:
                        obs = f"Observation: Action Input was not valid JSON ({e})."
                    except Exception as e:  # noqa: BLE001
                        obs = f"Observation: Tool error: {e}"
                emit(obs)
                messages.append({"role": "user", "content": obs})

    trace.append(f"ANSWER: {answer}\n")
    TRACE_FILE.parent.mkdir(exist_ok=True)
    with open(TRACE_FILE, "a") as f:
        f.write("\n".join(trace) + "\n")
    return answer


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "Which items expire within 60 days, and what is their total stock value?"
    print("\nFinal:", asyncio.run(run(q)))
