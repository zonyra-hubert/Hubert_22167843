# Lab 11: Security and Guardrails

**Topic:** Prompt injection, tool permissions, data leakage, Ghana Data Protection Act, 2012 (Act 843)

**Style:** Fictional exercise, then another team's system. Code

Instructions are in the DCIT 403 Laboratory Manual (version 2), Lab 11.

## Deliverables

- Lab repository: `redteam.md` (before and after), guardrail code, `concept_check.md`
- Team repository: `security/` folder with findings given and received, fixes and the Act 843 mapping

Put outputs, traces, logs and screenshots in `evidence/`. Answer `concept_check.md` before the Wednesday session. Steps marked Independent in the manual are done on your own between the Thursday and Wednesday labs.

## The vulnerable agent

> This agent is insecure on purpose and uses fictional data only. Attack only your own copy.
> `send_email` sends nothing: it writes to `vulnerable_agent/outbox.jsonl` so you can see what the agent tried to do.

```bash
cd lab11
python -m vulnerable_agent.hall_agent --student 10900003   # log in as a fictional student
```

From Python:

```python
from vulnerable_agent.hall_agent import run
r = run("When is the water off in Volta Hall?", logged_in_student="10900003")
r["answer"], r["tool_calls"]
```
