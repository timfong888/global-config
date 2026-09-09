---
name: aurora
description: Route a prompt through the Aurora inference endpoint. Use when the user invokes `/aurora` followed by a model shorthand such as `/deepseek`. Calls aurora_chat_completion with the appropriate model and returns the response. Trigger on `/aurora` anywhere in the user message.
---

# Aurora Inference Skill

Route the user's prompt through Aurora's inference endpoint using the `aurora_chat_completion` MCP tool.

## Model map

| Shorthand | Aurora model ID |
|---|---|
| `/deepseek` | `deepseek/deepseek-v4-flash` |

If no model shorthand is given, default to `deepseek/deepseek-v4-flash`.

To see all currently available models, call `aurora_list_models` first.

## Steps

1. Parse the model shorthand from the user's message (e.g. `/aurora /deepseek`).
2. Resolve it to the full Aurora model ID using the table above.
   - If the shorthand is unknown, call `aurora_list_models` and pick the closest match.
3. Extract the user's actual prompt (everything after the provider and model flags).
4. Call `aurora_chat_completion` with the resolved model and the prompt as a user message.
5. Return the response text directly to the user.

## Example invocations

```
@blocks /aurora /deepseek Summarise the quarterly results doc
→ calls aurora_chat_completion(model="deepseek/deepseek-v4-flash", messages=[{role:"user", content:"Summarise the quarterly results doc"}])
```
