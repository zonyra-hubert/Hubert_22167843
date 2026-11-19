# DCIT 403: Designing Intelligent Agents — Lab Repository

Your personal repository for the DCIT 403 labs (2026/27). Instructions for every lab are in the
**DCIT 403 Laboratory Manual (version 2)**. This repository gives you the Codespace setup,
the sample data and the starter code the labs need.

## First time (Lab Manual Section 2)

1. Create your own free keys by following the **Free Model Access Guide**: a Groq key and a Google AI Studio key.
   Add them as Codespaces secrets `GROQ_API_KEY` and `GEMINI_API_KEY`, with access to this repository.
2. Open the repository in a Codespace (**Code → Codespaces → Create codespace on main**).
   The first start installs everything; wait until the terminal says `Done`.
3. Check your setup:

   ```bash
   python scripts/check_setup.py          # libraries, keys, sample data
   python scripts/check_setup.py --call   # also one small model call
   ```

4. Stop the Codespace when you finish (Codespaces page → **Stop codespace**) to save your free hours.

## What is in here

| Path | What it is |
|---|---|
| `.devcontainer/` | Codespace setup (Python 3.11, Node.js, libraries). Do not edit |
| `requirements.txt` | Python libraries. `mcp` is kept below version 2 on purpose (the manual uses mcp 1.x) |
| `.env.example` | Copied to `.env` automatically. Sets `LLM_MODEL` (Groq by default; Gemini backup commented out). Keys come from Codespaces secrets, never from files |
| `AI_USE_LOG.md` | Your AI-use log (Lab Manual Section 4) |
| `scripts/check_setup.py` | Checks that everything is ready |
| `scripts/refresh_dates.py` | Rewrites date-sensitive sample data relative to today (runs automatically) |
| `labNN/` | One folder per lab, each with `README.md`, `concept_check.md` and `evidence/` |

### Starter material by lab

| Lab | Provided |
|---|---|
| 3 | `lab03/data/pharmacy_stock.csv` (20 items; several expire within 60 days) |
| 4 | `lab04/skills/_template/SKILL.md`, `lab04/tests/sample_complaints.md` |
| 5 | `lab05/docs/` — five fictional clinic documents |
| 7 | `lab07/data/venues.json`, `lab07/data/caterers.json` |
| 8 | `lab08/log_to_mermaid.py` — turns your message log into a sequence diagram |
| 9 | `lab09/data/orders.csv` (orders inside and outside the 14-day window; some above GHS 300; one already refunded) |
| 10 | `lab10/agent/` — the registration FAQ agent you evaluate; `lab10/evals/cases_example.jsonl` |
| 11 | `lab11/vulnerable_agent/` — a deliberately insecure agent to red-team (fictional data) |
| 12 | `lab12/data/shuttle_schedule.csv`, `lab12/logs/` |

## Rules (Lab Manual Section 1.5)

- Never commit keys or `.env`. Check every exported n8n workflow for keys before committing.
- Use only fictional or anonymised data.
- Attack only your own copy of the Lab 11 agent (and, in Part C, another team's system with permission).
- Record every AI-tool use in `AI_USE_LOG.md`.

## Troubleshooting

See Lab Manual Appendix B. The most common fix: restart the Codespace after adding a secret.
