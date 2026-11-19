"""Course Registration FAQ Agent (DCIT 403, Lab 10).

A small function-calling agent with two tools:
    search_faq(query)    -> the most relevant FAQ sections (keyword search)
    get_deadline(event)  -> a date from the deadlines table

This is the agent you EVALUATE in Lab 10. Do not change it until Step 4,
when you make one fix and re-run your suite.

Use it from Python (this is what evals/run.py should call):

    from agent.faq_agent import run
    result = run("When does add/drop end?")
    result["answer"], result["tool_calls"], result["tokens"], result["latency_s"]

Or chat with it in the terminal (run from inside lab10/):

    python -m agent.faq_agent
"""
import json
import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv
from litellm import completion

load_dotenv()
MODEL = os.getenv("LLM_MODEL", "groq/openai/gpt-oss-20b")
DATA = Path(__file__).resolve().parent / "data"
MAX_STEPS = 5

SYSTEM_PROMPT = """You are the Department of Computer Science registration assistant.
Answer students' questions about course registration using ONLY the tools provided.
- Use search_faq for rules and procedures, and get_deadline for dates.
- If the tools do not contain the answer, say you do not know and refer the student
  to the Departmental Registration Desk.
- Keep answers short (at most 4 sentences) and do not invent dates, fees or rules."""

# ---------------------------------------------------------------- tools


def _load_sections() -> list[dict]:
    text = (DATA / "faq.md").read_text(encoding="utf-8")
    sections = []
    for block in re.split(r"\n## ", text)[1:]:
        title, _, body = block.partition("\n")
        sections.append({"title": title.strip(), "text": body.strip()})
    return sections


def search_faq(query: str) -> list[dict]:
    """Search the registration FAQ. Returns up to 2 sections whose words best match the query."""
    words = set(re.findall(r"[a-z0-9/]+", query.lower()))
    scored = []
    for s in _load_sections():
        hay = (s["title"] + " " + s["text"]).lower()
        score = sum(1 for w in words if len(w) > 2 and w in hay)
        if score:
            scored.append((score, s))
    scored.sort(key=lambda x: -x[0])
    return [s for _, s in scored[:2]] or [{"title": "No match", "text": "No FAQ section matched the query."}]


def get_deadline(event: str) -> str:
    """Return the date of a registration event, e.g. 'add/drop ends' or 'registration deadline'."""
    table = json.loads((DATA / "deadlines.json").read_text(encoding="utf-8"))
    key = event.lower().strip()
    for name, value in table.items():
        if name.startswith("_"):
            continue
        if key == name or key in name or name in key:
            return f"{name}: {value}"
    known = ", ".join(k for k in table if not k.startswith("_"))
    return f"No deadline found for '{event}'. Known events: {known}."


TOOLS = {"search_faq": search_faq, "get_deadline": get_deadline}

TOOL_SCHEMAS = [
    {"type": "function", "function": {
        "name": "search_faq",
        "description": "Search the course registration FAQ for rules and procedures.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "description": "Keywords, e.g. 'credit limit probation'"}},
            "required": ["query"]}}},
    {"type": "function", "function": {
        "name": "get_deadline",
        "description": "Get the date of a registration event such as 'add/drop ends', "
                       "'registration deadline' or 'examinations begin'.",
        "parameters": {"type": "object", "properties": {
            "event": {"type": "string", "description": "Name of the event"}},
            "required": ["event"]}}},
]

# ---------------------------------------------------------------- agent loop


def run(question: str, history: list | None = None) -> dict:
    """Answer one question. Returns answer, tool_calls (in order), tokens and latency."""
    start = time.perf_counter()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + (history or [])
    messages.append({"role": "user", "content": question})
    tool_calls, tokens = [], {"prompt": 0, "completion": 0}
    answer = None

    for _ in range(MAX_STEPS):
        resp = completion(model=MODEL, messages=messages, tools=TOOL_SCHEMAS, temperature=0)
        if getattr(resp, "usage", None):
            tokens["prompt"] += resp.usage.prompt_tokens or 0
            tokens["completion"] += resp.usage.completion_tokens or 0
        msg = resp.choices[0].message
        if not msg.tool_calls:
            answer = msg.content
            break
        messages.append(msg.model_dump())
        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
                result = TOOLS[name](**args) if name in TOOLS else f"Unknown tool: {name}"
            except Exception as e:  # noqa: BLE001
                args, result = {}, f"Tool error: {e}"
            tool_calls.append({"name": name, "args": args})
            messages.append({"role": "tool", "tool_call_id": tc.id,
                             "content": json.dumps(result, ensure_ascii=False)})
    if answer is None:
        answer = "Sorry, I could not complete that request. Please contact the Departmental Registration Desk."

    return {"question": question, "answer": answer, "tool_calls": tool_calls, "tokens": tokens,
            "latency_s": round(time.perf_counter() - start, 3), "model": MODEL}


if __name__ == "__main__":
    print("Registration FAQ agent. Type 'quit' to exit.")
    while True:
        q = input("\nYou: ").strip()
        if q.lower() in {"quit", "exit"}:
            break
        r = run(q)
        print(f"Agent: {r['answer']}")
        print(f"  [tools: {[c['name'] for c in r['tool_calls']]}, tokens: {r['tokens']}, {r['latency_s']}s]")
