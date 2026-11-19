"""Turn a JSON-lines message log into a Mermaid sequence diagram (Lab 8, Step 3).

Each line of the log must be a JSON object with at least:
    sender, receiver, performative, content
(conversation_id is optional; use --conversation to keep only one conversation).

Usage:
    python log_to_mermaid.py evidence/messages.jsonl > evidence/generated_sequence.md
    python log_to_mermaid.py evidence/messages.jsonl --conversation order-001
"""
import argparse
import json
import re
import sys


def safe_id(name: str) -> str:
    """Mermaid participant ids must be simple words."""
    return re.sub(r"\W+", "_", str(name)).strip("_") or "unknown"


def short(text, limit: int) -> str:
    if not isinstance(text, str):
        text = json.dumps(text, ensure_ascii=False)
    text = " ".join(text.split())
    text = text.replace(";", ",").replace("#", "no.")  # characters Mermaid treats specially
    return text if len(text) <= limit else text[: limit - 3] + "..."


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("log", help="path to messages.jsonl")
    ap.add_argument("--conversation", help="only include this conversation_id")
    ap.add_argument("--max-label", type=int, default=60, help="maximum characters of content per arrow")
    args = ap.parse_args()

    messages = []
    with open(args.log, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"skipping line {n}: not valid JSON ({e})", file=sys.stderr)
                continue
            if args.conversation and msg.get("conversation_id") != args.conversation:
                continue
            messages.append(msg)

    if not messages:
        sys.exit("No messages found. Check the log path and the --conversation value.")

    participants = []
    for m in messages:
        for who in (m.get("sender"), m.get("receiver")):
            if who not in participants:
                participants.append(who)

    out = ["```mermaid", "sequenceDiagram"]
    for p in participants:
        out.append(f"    participant {safe_id(p)} as {p}")
    for m in messages:
        perf = m.get("performative", "?")
        arrow = "-->>" if perf in ("inform", "refuse", "failure", "accept", "reject") else "->>"
        label = f"{perf}: {short(m.get('content', ''), args.max_label)}"
        out.append(f"    {safe_id(m.get('sender'))}{arrow}{safe_id(m.get('receiver'))}: {label}")
    out.append("```")
    print("\n".join(out))


if __name__ == "__main__":
    main()
