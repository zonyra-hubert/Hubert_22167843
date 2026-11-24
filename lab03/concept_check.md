# Lab 3: Percepts and Actions as Tools: Function Calling and MCP: Concept Check

Answer in your own words before the Wednesday session (independent work). Your answers feed Section 2 of your lab report (Concept and classical root).

## Q1. List one advantage and one disadvantage of native function calling compared with the Lab 2 text protocol.

_Your answer:_

**Advantage:** The model returns tool calls as structured JSON (tool name plus arguments that match a schema), so I don't need regular expressions to pull `Action:` and `Action Input:` out of free text. Parsing errors, made-up formats and badly formed JSON are far less common, and the model can request several tool calls in one turn.

**Disadvantage:** The reasoning becomes less visible and less portable. With the text protocol every Thought is written out in the trace, and any model that can follow a prompt can run the loop. With native function calling I depend on the provider supporting tools (and on its particular message format, such as `tool_call_id`). The model often calls tools without explaining why, which makes traces harder to debug and to mark.

## Q2. In MCP, what is the difference between a tool and a resource? Give a pharmacy example of each.

_Your answer:_

A **tool** is an action the model can choose to invoke. It takes arguments, runs code on the server and can change the world (it is model-controlled). A **resource** is read-only data, identified by a URI, that the client application loads as context. It has no side effects (it is application-controlled).

- Tool example: `record_sale(item, strength, quantity)` reduces stock and writes to the sales log. `check_stock` and `list_expiring` are tools too, because the model decides when to call them and with what arguments.
- Resource example: `pharmacy://stock` (the full stock list as CSV) or `pharmacy://policy` (the dispensing rules). The client can attach these to the conversation, but reading them changes nothing.

## Q3. Why should `record_sale` check the quantity even though the system prompt already says "never oversell"?

_Your answer:_

A system prompt is only a request to the model, not a guarantee. The model can ignore it, misread the stock figure, count wrongly, be talked into it by the user ("just record 50, I'll restock later") or be manipulated by prompt injection. Stock may also have changed between the model's `check_stock` call and its `record_sale` call. The tool is the last point before the environment actually changes, so the business rule has to be enforced there in code (defence in depth). In my server, `record_sale` refuses quantity < 1, quantities above stock, expired items and ambiguous matches. It returns an error message the agent can perceive and explain to the user.

## Q4. Which messages in the worked example are percepts?

_Your answer:_

Percepts are what the agent receives from its environment: the **user's message** (the request, as perceived from the customer or pharmacist) and every **tool result** (the `role: "tool"` messages in function calling, or the `Observation:` lines in the ReAct version). For example, the JSON returned by `list_expiring`, or the refusal "Cannot sell 50: only 12 in stock". The system prompt is not a percept, because it is the agent's built-in design. The assistant's tool calls and final answer are not percepts either, because they are the agent's actions.
