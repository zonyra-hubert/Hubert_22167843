"""Lab 2 tools: the agent's actuators.

The model never runs these. It only writes the tool name and input as text;
react_agent.py parses that text and calls the matching function here.
"""
import ast
import operator as op

import requests

# Only these operators are allowed. Anything else (names, function calls,
# attribute access such as __import__) is rejected, so the calculator is safe.
OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.USub: op.neg,
}


def _eval(node):
    """Walk the parsed expression tree and compute it, allowing only numbers and OPS."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in OPS:
        return OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in OPS:
        return OPS[type(node.op)](_eval(node.operand))
    raise ValueError("Unsupported expression")


def calculator(expression: str) -> str:
    """Evaluate an arithmetic expression such as '4*185 + 3*95'. Never uses eval()."""
    try:
        expr = expression.replace(",", "").strip()  # allow "1,200"
        result = _eval(ast.parse(expr, mode="eval").body)
        # Show 175.0 as 175 so answers look natural
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        return str(result)
    except Exception as e:
        return f"Error: {e}"


def wiki_lookup(title: str) -> str:
    """Return the first part of the Wikipedia summary for an exact page title."""
    url = (
        "https://en.wikipedia.org/api/rest_v1/page/summary/"
        + title.strip().replace(" ", "_")
    )
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": "DCIT403-lab"})
    except requests.RequestException as e:
        return f"Error: could not reach Wikipedia ({e})."
    if r.status_code != 200:
        return f"No Wikipedia page found for '{title}'."
    return r.json().get("extract", "")[:800]


# Name -> function. The agent loop looks tools up here by the name the model wrote.
TOOLS = {
    "calculator": calculator,
    "wiki_lookup": wiki_lookup,
}


if __name__ == "__main__":
    # Step 2 checkpoint: test the tools directly, without the model.
    print("4*185 + 3*95       ->", calculator("4*185 + 3*95"))      # 1025
    print("1,200 - 1025       ->", calculator("1,200 - 1025"))      # 175
    print("10 / 4             ->", calculator("10 / 4"))            # 2.5
    print("__import__('os')   ->", calculator("__import__('os')"))  # Error
    print("Bono East Region   ->", wiki_lookup("Bono East Region")[:150], "...")
    print("Not a real page    ->", wiki_lookup("Xyzzy Nonexistent Page 403"))
