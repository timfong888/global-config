---
name: do
description: Route a prompt through the DigitalOcean Serverless Inference endpoint. Use when the user invokes `/do` followed by a model shorthand such as `/kimi`, `/deepseek`, or `/glm`. Calls do_chat_completion with the appropriate model and returns the response. Trigger on `/do` anywhere in the user message.
---

# DigitalOcean Inference Skill

Route the user's prompt through DigitalOcean's Serverless Inference endpoint using the `do_chat_completion` MCP tool.

## Model map

| Shorthand | DO model ID |
|---|---|
| `/kimi` | `kimi-k2-instruct` |
| `/deepseek` | `deepseek-chat` |
| `/glm` | `glm-4-plus` |

If no model shorthand is given, default to `kimi-k2-instruct`.

To see all currently available models, call `do_list_models` first.

> **Note:** The `do_chat_completion` tool requires `DO_MODEL_KEY` to be set as a workspace secret in blocks.team. If the tool is unavailable, inform the user that `DO_MODEL_KEY` must be added to **Workspace Settings → Secrets**.

## Steps

1. Parse the model shorthand from the user's message (e.g. `/do /kimi`).
2. Resolve it to the full DO model ID using the table above.
   - If the shorthand is unknown, call `do_list_models` and pick the closest match.
3. Extract the user's actual prompt (everything after the provider and model flags).
4. Call `do_chat_completion` with the resolved model and the prompt as a user message.
5. Return the response text directly to the user.

## Example invocations

```
@blocks /do /kimi Explain this error message
→ calls do_chat_completion(model="kimi-k2-instruct", messages=[{role:"user", content:"Explain this error message"}])

@blocks /do /deepseek Write a SQL query to find duplicate users
→ calls do_chat_completion(model="deepseek-chat", messages=[{role:"user", content:"Write a SQL query to find duplicate users"}])

@blocks /do /glm Translate this to Chinese
→ calls do_chat_completion(model="glm-4-plus", messages=[{role:"user", content:"Translate this to Chinese"}])
```
