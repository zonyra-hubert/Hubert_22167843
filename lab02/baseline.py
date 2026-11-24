"""Lab 2, Step 1: baseline. The model on its own, with no tools.

Run from inside lab02/:  python baseline.py
Writes evidence/baseline.md. Fill in the Correct? column yourself.
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from litellm import completion

load_dotenv()
MODEL = os.getenv("LLM_MODEL")
EVIDENCE = Path(__file__).parent / "evidence"

BUDGET_Q = (
    "I have GHS 1,200. I want 4 bags of rice at GHS 185 each and 3 gallons of "
    "oil at GHS 95 each. How much will I have left?"
)
FACT_QS = [
    "What is the capital of the Bono East Region of Ghana?",
    "In what year was Makola Market in Accra established?",
]


def ask(question):
    resp = completion(
        model=MODEL,
        messages=[{"role": "user", "content": question}],
        temperature=0,
    )
    return (resp.choices[0].message.content or "").strip()


def cell(text):
    """Make a reply safe for one Markdown table cell."""
    return text.replace("|", "\\|").replace("\n", " ")


def main():
    if not MODEL:
        print("LLM_MODEL is not set. Check your .env file.")
        return
    rows = []
    for run in range(1, 4):
        answer = ask(BUDGET_Q)
        print(f"Budget run {run}: {answer}\n")
        rows.append((f"Budget, run {run}", answer))
    for q in FACT_QS:
        answer = ask(q)
        print(f"{q}\n-> {answer}\n")
        rows.append((q, answer))

    lines = [
        "# Lab 2 baseline: the model without tools",
        "",
        f"Model: {MODEL}, temperature 0. Correct budget answer: GHS 175.",
        "",
        "| Question | Model answer | Correct? | Confident-sounding? |",
        "|---|---|---|---|",
    ]
    lines += [f"| {cell(q)} | {cell(a)} |  |  |" for q, a in rows]
    EVIDENCE.mkdir(exist_ok=True)
    (EVIDENCE / "baseline.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Saved evidence/baseline.md. Now mark each row correct or incorrect.")


if __name__ == "__main__":
    main()
