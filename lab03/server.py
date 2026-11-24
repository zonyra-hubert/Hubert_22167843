"""Lab 3: Pharmacy stock MCP server.

Exposes the pharmacy's stock file as MCP tools (actions the agent can take)
and resources (read-only context the client can load).

Run it on its own and inspect it with the MCP Inspector:

    npx @modelcontextprotocol/inspector python lab03/server.py

The client agent (client_agent.py) starts this file itself over stdio.
"""
from __future__ import annotations

import csv
import json
from datetime import date, datetime, timedelta
from pathlib import Path

try:  # mcp 1.x (what the manual and requirements.txt use)
    from mcp.server.fastmcp import FastMCP
except ModuleNotFoundError:  # mcp 2.x renamed FastMCP to MCPServer
    from mcp.server.mcpserver import MCPServer as FastMCP

HERE = Path(__file__).resolve().parent
STOCK_FILE = HERE / "data" / "pharmacy_stock.csv"
SALES_FILE = HERE / "data" / "sales_log.csv"
FIELDS = ["item", "strength", "form", "quantity", "unit_price_ghs", "expiry_date"]

mcp = FastMCP("pharmacy-stock")


# ---------------------------------------------------------------- helpers
def _load() -> list[dict]:
    with open(STOCK_FILE, newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["quantity"] = int(r["quantity"])
        r["unit_price_ghs"] = float(r["unit_price_ghs"])
    return rows


def _save(rows: list[dict]) -> None:
    with open(STOCK_FILE, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({**r, "unit_price_ghs": f"{r['unit_price_ghs']:.2f}"})


def _norm(s: str | None) -> str:
    return (s or "").strip().lower().replace(" ", "")


def _match(rows: list[dict], item: str, strength: str | None = None) -> list[dict]:
    """Case-insensitive match on item name (substring) and, if given, strength."""
    name = item.strip().lower()
    hits = [r for r in rows if name in r["item"].lower()]
    if strength:
        hits = [r for r in hits if _norm(strength) == _norm(r["strength"])]
    return hits


def _days_left(r: dict) -> int:
    return (date.fromisoformat(r["expiry_date"]) - date.today()).days


def _public(r: dict) -> dict:
    return {**r, "days_to_expiry": _days_left(r)}


# ---------------------------------------------------------------- tools
@mcp.tool()
def check_stock(item: str, strength: str | None = None) -> str:
    """Look up how many packs of a medicine are in stock.

    Args:
        item: Medicine name, e.g. "Amoxicillin" (partial names are fine).
        strength: Optional strength to narrow the match, e.g. "500mg".
    Returns JSON with every matching stock line (quantity, price, expiry).
    """
    hits = _match(_load(), item, strength)
    if not hits:
        return json.dumps({"found": False, "message": f"No stock line matches '{item}'"
                           + (f" {strength}" if strength else "") + "."})
    return json.dumps({"found": True, "matches": [_public(r) for r in hits]})


@mcp.tool()
def get_price(item: str, strength: str, quantity: int = 1) -> str:
    """Quote the price in GHS for a quantity of one specific medicine and strength.

    Args:
        item: Medicine name.
        strength: Exact strength, e.g. "500mg".
        quantity: Number of packs (default 1).
    """
    if quantity < 1:
        return json.dumps({"ok": False, "error": "quantity must be at least 1"})
    hits = _match(_load(), item, strength)
    if len(hits) != 1:
        return json.dumps({"ok": False, "error": f"Expected exactly one line for {item} {strength}, "
                                                 f"found {len(hits)}. Use check_stock first."})
    r = hits[0]
    return json.dumps({"ok": True, "item": r["item"], "strength": r["strength"], "form": r["form"],
                       "unit_price_ghs": r["unit_price_ghs"], "quantity": quantity,
                       "total_ghs": round(r["unit_price_ghs"] * quantity, 2)})


@mcp.tool()
def list_expiring(days: int = 60) -> str:
    """List stock lines that expire within the next `days` days (default 60), soonest first.
    Lines that have already expired are included with a negative days_to_expiry."""
    if days < 0:
        return json.dumps({"ok": False, "error": "days must be 0 or more"})
    rows = [_public(r) for r in _load() if _days_left(r) <= days]
    rows.sort(key=lambda r: r["days_to_expiry"])
    return json.dumps({"ok": True, "within_days": days, "count": len(rows), "items": rows})


@mcp.tool()
def list_out_of_stock(threshold: int = 0) -> str:
    """List stock lines whose quantity is at or below `threshold` (default 0 = sold out).
    Use a threshold such as 15 to find items that need reordering."""
    rows = [_public(r) for r in _load() if r["quantity"] <= threshold]
    rows.sort(key=lambda r: r["quantity"])
    return json.dumps({"ok": True, "threshold": threshold, "count": len(rows), "items": rows})


@mcp.tool()
def record_sale(item: str, strength: str, quantity: int) -> str:
    """Record a sale and reduce stock. Refuses the sale if it would oversell,
    if the item has expired, or if the item/strength is ambiguous.

    Args:
        item: Medicine name.
        strength: Exact strength, e.g. "500mg".
        quantity: Number of packs sold (must be 1 or more).
    """
    # The tool enforces the business rules itself: the model's system prompt
    # is advice, this check is the guarantee.
    if not isinstance(quantity, int) or quantity < 1:
        return json.dumps({"ok": False, "error": "quantity must be a whole number of at least 1"})
    rows = _load()
    hits = _match(rows, item, strength)
    if len(hits) != 1:
        return json.dumps({"ok": False, "error": f"Expected exactly one line for {item} {strength}, "
                                                 f"found {len(hits)}. Use check_stock first."})
    r = hits[0]
    if _days_left(r) < 0:
        return json.dumps({"ok": False, "error": f"{r['item']} {r['strength']} expired on "
                                                 f"{r['expiry_date']} and must not be sold."})
    if quantity > r["quantity"]:
        return json.dumps({"ok": False, "error": f"Cannot sell {quantity}: only {r['quantity']} "
                                                 f"in stock for {r['item']} {r['strength']}."})
    r["quantity"] -= quantity
    _save(rows)
    total = round(r["unit_price_ghs"] * quantity, 2)
    new_file = not SALES_FILE.exists()
    with open(SALES_FILE, "a", newline="") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["timestamp", "item", "strength", "quantity", "total_ghs"])
        w.writerow([datetime.now().isoformat(timespec="seconds"), r["item"], r["strength"], quantity, total])
    return json.dumps({"ok": True, "item": r["item"], "strength": r["strength"], "sold": quantity,
                       "total_ghs": total, "remaining": r["quantity"]})


# ---------------------------------------------------------------- resources
@mcp.resource("pharmacy://stock")
def stock_resource() -> str:
    """The full current stock list as CSV (read-only)."""
    return STOCK_FILE.read_text()


@mcp.resource("pharmacy://policy")
def policy_resource() -> str:
    """Dispensing rules the agent should follow."""
    return (
        "1. Never sell more packs than are in stock.\n"
        "2. Never sell an expired item.\n"
        "3. Prescription-only items (antibiotics such as Amoxicillin and Ciprofloxacin) "
        "need a prescription: ask before recording the sale.\n"
        "4. Quote prices in GHS with two decimal places.\n"
        f"5. Flag items expiring within 60 days (before {date.today() + timedelta(days=60)}).\n"
    )


if __name__ == "__main__":
    mcp.run()  # stdio transport
