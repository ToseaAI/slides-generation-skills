# `slides-generation-skills`

Official ToseaAI skill package for agentic document-to-presentation workflows.

This repository is intentionally separate from the MCP server and the main ToseaAI application:

- the MCP server is an execution connector;
- the skill is the workflow policy and operator guide;
- the product backend remains the system of record for auth, billing, quota, and exports.

## What this repo contains

- `SKILL.md`: the operational instructions for the agent
- `agents/openai.yaml`: lightweight metadata for OpenAI-compatible skill packaging
- `references/`: compact reference docs
- `examples/`: one-shot and staged workflow examples

## Required runtime

This skill assumes an MCP server named `tosea` is already configured and healthy.

Recommended pairing:

- MCP repo: `git@github.com:ToseaAI/mcp-ToseaAI.git`
- Skill repo: `git@github.com:ToseaAI/slides-generation-skills.git`

## Install

For Codex-style local skills, place this repository under your local skills directory and keep the repository name stable, for example:

```bash
git clone git@github.com:ToseaAI/slides-generation-skills.git ~/.codex/skills/tosea-slides
```

For Claude Code style workflows, keep this repo next to your MCP config and load `SKILL.md` through your team's skill or project-instructions mechanism.

For Cursor, pair the MCP server with the guidance in `SKILL.md` by adapting the workflow rules into project rules or shared instructions.

## Validate and package

This repo includes a zero-dependency validator and zip packager:

```bash
python scripts/validate_skill.py
python scripts/package_skill.py --version 0.1.0
```

## Design goals

- Prefer one-shot generation for speed when the user only wants a finished deck.
- Prefer staged workflows for iterative work, high-value decks, or when the user asks for edits.
- Keep cost-sensitive actions explicit.
- Preserve `presentation_id`, `job`, `filename`, and `download_url` in final summaries.
- Reuse idempotency keys only for safe retries of the same mutation.
