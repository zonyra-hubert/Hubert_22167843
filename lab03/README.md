# Lab 3: Percepts and Actions as Tools: Function Calling and MCP

**Topic:** Function calling and the Model Context Protocol (MCP)

**Style:** Standalone, code

Instructions are in the DCIT 403 Laboratory Manual (version 2), Lab 3.

## Deliverables

- `server.py` with at least four tools, `client_agent.py`, `concept_check.md`
- `evidence/tool_calls.jsonl` and a screenshot of the MCP Inspector
- `evidence/react_via_mcp.txt` (Wednesday)

Put outputs, traces, logs and screenshots in `evidence/`. Answer `concept_check.md` before the Wednesday session. Steps marked Independent in the manual are done on your own between the Thursday and Wednesday labs.

## Data

`data/pharmacy_stock.csv` is regenerated relative to today by `python scripts/refresh_dates.py` (run from the repository root), so "items expiring within 60 days" always returns results.

**Note on MCP versions.** The manual's code uses `from mcp.server.fastmcp import FastMCP` (mcp 1.x). `requirements.txt` keeps `mcp` below version 2, where this was renamed. If you see `No module named 'mcp.server.fastmcp'`, run `pip install "mcp>=1.9,<2"`.
