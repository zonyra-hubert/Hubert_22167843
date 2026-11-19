"""Check that the Codespace is ready for DCIT 403 labs.

    python scripts/check_setup.py           # checks libraries, keys and data
    python scripts/check_setup.py --call    # also makes one small model call
"""
import importlib
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ok = True


def report(passed: bool, label: str, hint: str = ""):
    global ok
    ok &= passed
    print(("  OK   " if passed else "  FAIL ") + label + ("" if passed or not hint else f"\n         -> {hint}"))


print("Python")
report(sys.version_info >= (3, 11), f"Python {sys.version.split()[0]} (3.11+ needed)",
       "Rebuild the Codespace from the template.")

print("Libraries")
for mod in ["litellm", "langgraph", "mcp", "chromadb", "dotenv", "requests", "pydantic"]:
    try:
        importlib.import_module(mod)
        report(True, mod)
    except Exception as e:  # noqa: BLE001
        report(False, mod, f"pip install -r requirements.txt  ({e.__class__.__name__})")
try:
    from mcp.server.fastmcp import FastMCP  # noqa: F401
    report(True, "mcp 1.x (FastMCP available)")
except Exception:
    report(False, "mcp 1.x (FastMCP available)", 'pip install "mcp>=1.9,<2"')

print("Keys and settings")
from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")
report((ROOT / ".env").exists(), ".env file exists", "cp .env.example .env")
report(bool(os.getenv("LLM_MODEL")), f"LLM_MODEL = {os.getenv('LLM_MODEL')}", "Set LLM_MODEL in .env")
model = os.getenv("LLM_MODEL", "")
groq = os.getenv("GROQ_API_KEY", "")
gemini = os.getenv("GEMINI_API_KEY", "")
report(bool(groq), f"GROQ_API_KEY visible ({groq[:6]}...)" if groq else "GROQ_API_KEY visible",
       "Create a free Groq key (Free Model Access Guide), add the Codespaces secret, restart the Codespace.")
if gemini:
    report(True, "GEMINI_API_KEY visible (n8n labs and backup model)")
else:
    print("  WARN GEMINI_API_KEY not set (needed from Lab 4 and as the backup; see the Free Model Access Guide)")
needed = "GROQ_API_KEY" if model.startswith("groq/") else "GEMINI_API_KEY" if model.startswith("gemini/") else None
if needed:
    report(bool(os.getenv(needed)), f"key for LLM_MODEL ({needed}) is set", f"Set the {needed} secret or change LLM_MODEL in .env")
key = os.getenv(needed, "") if needed else (groq or gemini)

print("Sample data")
for rel in ["lab03/data/pharmacy_stock.csv", "lab05/docs", "lab07/data/venues.json",
            "lab09/data/orders.csv", "lab10/agent/faq_agent.py",
            "lab11/vulnerable_agent/hall_agent.py", "lab12/data/shuttle_schedule.csv"]:
    report((ROOT / rel).exists(), rel, "Run: python scripts/refresh_dates.py, or re-sync from the template.")

if "--call" in sys.argv and key:
    print("Model call")
    try:
        from litellm import completion
        r = completion(model=os.getenv("LLM_MODEL"), temperature=0,
                       messages=[{"role": "user", "content": "Reply with the single word: ready"}])
        report(True, f"model replied: {r.choices[0].message.content.strip()[:40]}")
    except Exception as e:  # noqa: BLE001
        report(False, "model call", str(e)[:200])

print("\nAll checks passed." if ok else "\nSome checks failed. Fix the items marked FAIL, or ask the TA.")
sys.exit(0 if ok else 1)
