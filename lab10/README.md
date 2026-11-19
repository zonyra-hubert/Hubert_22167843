# Lab 10: Evaluation: Test Sets, Model-Graded Checks, Trajectories, Cost and Latency

**Topic:** Test sets, model-graded checks, step-by-step trajectory review, cost and latency

**Style:** Fictional exercise, then your team system. Code

Instructions are in the DCIT 403 Laboratory Manual (version 2), Lab 10.

## Deliverables

- Lab repository: `evals/cases.jsonl`, `evals/run.py`, `evidence/eval_results.md`, `concept_check.md`
- Team repository: `evals/` with at least 20 cases, results table and cost per run; feedback session notes

Put outputs, traces, logs and screenshots in `evidence/`. Answer `concept_check.md` before the Wednesday session. Steps marked Independent in the manual are done on your own between the Thursday and Wednesday labs.

## The agent you evaluate

```bash
cd lab10
python -m agent.faq_agent          # chat with it
```

From your evaluation runner (`evals/run.py`, run from inside `lab10/`):

```python
from agent.faq_agent import run
r = run("When does add/drop end?")
r["answer"], r["tool_calls"], r["tokens"], r["latency_s"]
```

`evals/cases_example.jsonl` shows the test-case format. Do not change the agent until Step 4.
