"""Lab 2: a ReAct agent from scratch (no framework).

Loop: the model writes a Thought and an Action (deliberative), our code runs the
tool and appends an Observation (a new percept), and the model reacts to it.
The loop ends on the finish action or when max_steps is reached.

Usage (from inside lab02/):
    python react_agent.py "I have GHS 1,200 ..."     # one question
    python react_agent.py --all                       # all test questions, one trace each
"""
import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from litellm import completion

from tools import TOOLS

load_dotenv()
MODEL = os.getenv("LLM_MODEL")
EVIDENCE = Path(__file__).parent / "evidence"

SYSTEM_PROMPT = """You are a helpful assistant for a trader at Makola Market.
You answer questions about costs and quick facts by using tools.

Tools:
- calculator: evaluates an arithmetic expression using + - * / and brackets.
  Input: only the expression, for example 4*185 + 3*95. No words or currency signs.
- wiki_lookup: returns the summary of one Wikipedia page.
  Input: the exact page title only, for example Bono East Region (not a question).
- finish: ends the task. Input: your final answer for the user.

Do not use function calling or JSON. Write your reply as plain text.
On EVERY step, reply in exactly this format and nothing else:
Thought: <your reasoning about what to do next>
Action: <one of: calculator, wiki_lookup, finish>
Action Input: <the input for the tool, or the final answer if Action is finish>

Rules:
- Do one action per reply, then stop. Never write an Observation yourself;
  it will be given to you.
- Always use the calculator for arithmetic. Do not compute in your head.
- Use wiki_lookup for facts you are not sure about. If a page is not found,
  try a different title once, then say you could not find it.
- If the question needs no tool, use finish straight away.
- Amounts are in Ghana cedis (GHS)."""

# Finds the action name and everything after "Action Input:".
ACTION_RE = re.compile(r"Action:\s*(\w+)\s*\nAction Input:\s*(.*)", re.DOTALL)


def parse(text):
    """Return (action, action_input) from a model reply, or (None, None) if unparseable."""
    m = ACTION_RE.search(text)
    if not m:
        return None, None
    action = m.group(1).strip()
    action_input = m.group(2).strip()
    # Tool inputs must be one line, so drop any extra text the model added.
    # The final answer (finish) may be several lines, so keep it whole.
    if action != "finish":
        action_input = action_input.splitlines()[0].strip() if action_input else ""
    return action, action_input


def tool_call_to_text(error):
    """Turn a rejected native tool call back into our text protocol.

    gpt-oss models are trained on native function calling, so they sometimes
    answer "Action: calculator" by making a real tool call instead of writing
    text. We gave no tools= argument, so Groq rejects it with code
    tool_use_failed, but the error still contains what the model generated,
    e.g. {"name": "calculator", "arguments": {"expression": "4*185 + 3*95"}}.
    Returns the equivalent Thought/Action/Action Input text, or None.
    """
    text = str(error)
    if "tool_use_failed" not in text or "{" not in text:
        return None
    try:
        body, _ = json.JSONDecoder().raw_decode(text, text.index("{"))
        call = json.loads(body["error"]["failed_generation"])
        args = call.get("arguments", {})
        if isinstance(args, str):
            args = json.loads(args)
        value = next(iter(args.values()), "") if isinstance(args, dict) else args
        return (
            "Thought: (the model sent a native tool call; converted by the code)\n"
            f"Action: {call['name']}\n"
            f"Action Input: {value}"
        )
    except (ValueError, KeyError, TypeError):
        return None


def call_model(messages):
    """One model call. stop= prevents the model from inventing its own Observation."""
    try:
        resp = completion(
            model=MODEL,
            messages=messages,
            temperature=0,
            stop=["Observation:"],
        )
    except Exception as e:
        converted = tool_call_to_text(e)
        if converted is None:
            raise  # a real failure (rate limit, network): run_agent handles it
        return converted, 0
    text = resp.choices[0].message.content or ""
    # Safety net: if the provider ignored stop, cut the reply there ourselves.
    text = text.split("Observation:")[0].strip()
    tokens = resp.usage.total_tokens if resp.usage else 0
    return text, tokens


def run_agent(question, max_steps=6, trace_path=None):
    """Run the ReAct loop on one question. Returns the final answer as a string."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Question: {question}"},
    ]
    trace = [f"Question: {question}", ""]
    total_tokens = 0
    answer = None

    def log(line):
        print(line)
        trace.append(line)

    for step in range(1, max_steps + 1):
        log(f"--- Step {step} ---")
        try:
            reply, tokens = call_model(messages)
        except Exception as e:  # e.g. rate limit (429) or network error
            log(f"Model call failed: {type(e).__name__}: {e}")
            answer = "Sorry, I could not reach the model. Please try again shortly."
            break
        total_tokens += tokens
        log(reply if reply else "(empty reply)")
        messages.append({"role": "assistant", "content": reply})

        action, action_input = parse(reply)

        # Failure 1: the reply does not follow the format -> corrective observation.
        if action is None:
            observation = (
                "Error: I could not read your reply. Reply in exactly this format:\n"
                "Thought: ...\nAction: calculator | wiki_lookup | finish\nAction Input: ..."
            )
        # Normal end: the model chose finish.
        elif action == "finish":
            answer = action_input
            break
        # Failure 2: the model named a tool that does not exist.
        elif action not in TOOLS:
            observation = (
                f"Error: unknown action '{action}'. "
                f"Use one of: {', '.join(TOOLS)}, finish."
            )
        # Normal step: run the tool. The code computes, not the model.
        else:
            observation = TOOLS[action](action_input)

        log(f"Observation: {observation}")
        messages.append({"role": "user", "content": f"Observation: {observation}"})

    # Failure 3: max_steps reached without finish (prevents runaway loops).
    if answer is None:
        answer = f"Stopped after {max_steps} steps without a final answer."
        log(answer)

    log("")
    log(f"Final answer: {answer}")
    log(f"Total tokens: {total_tokens}")

    if trace_path:
        EVIDENCE.mkdir(exist_ok=True)
        Path(trace_path).write_text("\n".join(trace) + "\n", encoding="utf-8")
        print(f"(trace saved to {trace_path})")
    return answer


# Step 4 and Step 5 questions. Edit the last five to your own if you like.
TEST_QUESTIONS = [
    # 1. Budget question (Step 4 checkpoint: expect GHS 175 and calculator calls)
    "I have GHS 1,200. I want 4 bags of rice at GHS 185 each and 3 gallons of "
    "oil at GHS 95 each. How much will I have left?",
    # 2-3. Need both tools
    "What is the capital of the Bono East Region, and if I send 12 boxes there "
    "at GHS 45 each, what is the total cost?",
    "How many regions does Ghana have? If I open one shop in each region at "
    "GHS 2,500 per shop, what is the total?",
    # 4. Wikipedia page that does not exist
    "What does Wikipedia say about the Makola Golden Yam Festival of 1823?",
    # 5. Needs no tool
    "Hello! What can you help me with?",
    # 6. Deliberately badly worded
    "rice 185 x4 oil 95 x3 i got 1200 how much remain??",
]


def main():
    if not MODEL:
        print("LLM_MODEL is not set. Check your .env file (see Lab Manual 2.5).")
        sys.exit(1)
    args = sys.argv[1:]
    if args == ["--all"]:
        for n, q in enumerate(TEST_QUESTIONS, start=1):
            print(f"\n===== Question {n} =====")
            run_agent(q, trace_path=EVIDENCE / f"trace_{n}.txt")
    elif args:
        run_agent(" ".join(args), trace_path=EVIDENCE / "trace_custom.txt")
    else:
        run_agent(TEST_QUESTIONS[0], trace_path=EVIDENCE / "trace_1.txt")


if __name__ == "__main__":
    main()
