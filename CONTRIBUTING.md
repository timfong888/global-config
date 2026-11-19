# Contributing skills

## No model names in skills

A skill says **what** to do. Which model runs it is chosen outside the skill: Blocks profiles,
automation settings, the orchestrator's routing, or a workspace config table. (Tim, 2026-11-18.)

- Don't name LLM models or vendor models in a `SKILL.md`: no Kimi, Codex, GPT-*, Sol, Terra, Luna,
  Astra, Opus, Sonnet, Haiku, Fable, Gemini, Mistral, Llama, DeepSeek, GLM, Claude model ids
  (`claude-<family>-<n>`; "Claude" alone names the agent and is fine), and no `--profile <model>`
  or "use model X".
- If a skill needs a capability, say it neutrally: "needs deep reasoning", "high-volume and cheap",
  "a different model family from the author".
- Exceptions, listed here so reviewers can check them:
  - Router skills whose whole job is mapping a shorthand to an endpoint's model id (`do`,
    `aurora`).
  - Image-generation provider and model choices (`capability-image*`, `linear-image-pipeline`,
    `photo-compositing`): these pick an image tool, not the model that runs the skill.

Before opening a PR, run:

```bash
python3 scripts/validate_skills.py --models-only
```

It should report 0 model-name errors. CI runs the same check on every PR that touches a skill
(`.github/workflows/skills-no-model-names.yml`). To add an exception, add the skill's folder name to
`MODEL_NAME_EXCEPTIONS` in `scripts/validate_skills.py` and list it above.
