# Lab 9: Dynamic Workflows: Failure Handling and Human Approval

**Topic:** Planning, re-planning, plan failure (BDI) leading to retries and fallbacks; human-in-the-loop approval

**Style:** Fictional exercise, then your team system. Code (LangGraph). An optional n8n version is in Appendix A

Instructions are in the DCIT 403 Laboratory Manual (version 2), Lab 9.

## Deliverables

- Lab repository: `refund_graph.py`, five traces, `manual_refunds.csv`, `concept_check.md`
- Team repository: `design/failure_handling.md`, failure-case trace, approval-flow trace

Put outputs, traces, logs and screenshots in `evidence/`. Answer `concept_check.md` before the Wednesday session. Steps marked Independent in the manual are done on your own between the Thursday and Wednesday labs.

## Data

`data/orders.csv` is regenerated relative to today by `python scripts/refresh_dates.py` (run from the repository root), so the 14-day refund window always has orders inside and outside it.
