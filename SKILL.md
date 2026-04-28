---
name: cursor-cloud-agents
description: Use when the user asks to launch, run, inspect, follow up, stop, or retrieve results from Cursor Cloud Agents for a GitHub repository.
version: 0.1.0
author: Keith Vaughan @ Fair Developers DA NANG
license: MIT
metadata:
  hermes:
    tags:
      - cursor
      - cloud-agents
      - coding-agent
      - github
      - automation
    related_skills:
      - claude-code
      - codex
      - hermes-agent
---

# Cursor Cloud Agents Skill for Hermes Agents

## Overview

Use this skill to launch and manage Cursor Cloud Agents through the Cursor Cloud Agents API at `https://api.cursor.com/v0`.

Cursor Cloud Agents run coding tasks against GitHub repositories connected to the user's Cursor account. The agent can create branches, optionally open pull requests, accept follow-up prompts, expose status, return conversation history, and provide generated artifacts.

This skill is a knowledge document. It does not execute code by itself. Follow the API instructions below using the available HTTP, web, shell, or integration tools in the Hermes runtime.

Authentication requires the environment variable `CURSOR_API_KEY`.

Use Basic authentication with the base64 encoding of `{CURSOR_API_KEY}:`:

```http
Authorization: Basic <base64-of-CURSOR_API_KEY-colon>
```

With `curl`, this is equivalent to:

```bash
curl -u "$CURSOR_API_KEY:" https://api.cursor.com/v0/me
```

If `CURSOR_API_KEY` is missing, tell the user to add it to `~/.hermes/.env`:

```bash
echo 'CURSOR_API_KEY=your_cursor_api_key_here' >> ~/.hermes/.env
```

## When to Use

Use this skill when the user says or implies any of these trigger phrases:

- "launch a cursor agent"
- "run cursor cloud agent"
- "use cursor to code"
- "cursor agent for [repo]"
- "build this with cursor"
- "cursor cloud agents"

Use this skill for tasks such as:

- Launching a Cursor Cloud Agent on a GitHub repository.
- Checking whether a Cursor Cloud Agent is still running.
- Getting the pull request URL after Cursor completes work.
- Sending a follow-up instruction to an existing Cursor Cloud Agent.
- Listing available Cursor models or repositories.
- Fetching conversation history or generated artifacts.

Do not use this skill for local Cursor IDE automation, local SDK streaming, or direct filesystem edits. Cursor Cloud Agents API does not expose a live event stream. Poll status instead.

## CLI / API Reference

Base URL:

```text
https://api.cursor.com/v0
```

Required environment variable:

```text
CURSOR_API_KEY
```

Authentication:

```text
Basic base64("{CURSOR_API_KEY}:")
```

Common headers:

```http
Authorization: Basic <base64-of-CURSOR_API_KEY-colon>
Content-Type: application/json
```

Action reference:

| Action | Purpose | Method and endpoint | Required inputs |
|---|---|---|---|
| `me` | Verify the API key | `GET /me` | None |
| `models` | List available models | `GET /models` | None |
| `repositories` | List visible GitHub repos | `GET /repositories` | None |
| `list_agents` | List agents | `GET /agents?limit=&cursor=` | Optional `limit`, `cursor`, `pr_url` |
| `launch_agent` | Start an agent | `POST /agents` | `repository`, `prompt`, `ref` defaulting to `main` |
| `get_agent` | Fetch agent status | `GET /agents/{agent_id}` | `agent_id` |
| `followup` | Send follow-up prompt | `POST /agents/{agent_id}/followup` | `agent_id`, `prompt` |
| `stop_agent` | Stop a running agent | `POST /agents/{agent_id}/stop` | `agent_id` |
| `conversation` | Get conversation history | `GET /agents/{agent_id}/conversation` | `agent_id` |
| `list_artifacts` | List artifacts | `GET /agents/{agent_id}/artifacts` | `agent_id` |
| `download_artifact` | Get download URL | `GET /agents/{agent_id}/artifacts/download?path={artifact_path}` | `agent_id`, `artifact_path` |

Use `curl -u "$CURSOR_API_KEY:"` when a shell is available. This avoids manually constructing the Basic auth header.

Verify the API key:

```bash
curl -sS -u "$CURSOR_API_KEY:" \
  https://api.cursor.com/v0/me
```

List models:

```bash
curl -sS -u "$CURSOR_API_KEY:" \
  https://api.cursor.com/v0/models
```

List repositories:

```bash
curl -sS -u "$CURSOR_API_KEY:" \
  https://api.cursor.com/v0/repositories
```

List agents:

```bash
curl -sS -u "$CURSOR_API_KEY:" \
  "https://api.cursor.com/v0/agents?limit=20"
```

Launch agent request format:

```json
{
  "prompt": {
    "text": "Add a README.md file with install and usage instructions."
  },
  "model": "default",
  "source": {
    "repository": "https://github.com/your-org/your-repo",
    "ref": "main"
  },
  "target": {
    "branchName": "cursor/add-readme",
    "autoCreatePr": true
  }
}
```

Launch agent with `curl`:

```bash
curl -sS -u "$CURSOR_API_KEY:" \
  -H "Content-Type: application/json" \
  -X POST https://api.cursor.com/v0/agents \
  -d '{
    "prompt": {
      "text": "Add a README.md file with install and usage instructions."
    },
    "model": "default",
    "source": {
      "repository": "https://github.com/your-org/your-repo",
      "ref": "main"
    },
    "target": {
      "branchName": "cursor/add-readme",
      "autoCreatePr": true
    }
  }'
```

Input mapping for user-friendly fields:

| User-facing field | Cursor API field |
|---|---|
| `repository` | `source.repository` |
| `ref` | `source.ref` |
| `prompt` | `prompt.text` |
| `model` | `model` |
| `branch_name` | `target.branchName` |
| `auto_create_pr` | `target.autoCreatePr` |
| `auto_branch` | `target.autoBranch`, mainly for PR-based sources |

Status values may include `CREATING`, `RUNNING`, `FINISHED`, `ERROR`, and `EXPIRED`. If the API returns another terminal status such as `STOPPED`, treat it as terminal.

## Workflow

1. Verify `CURSOR_API_KEY` is set before any Cursor call.

   If missing, tell the user to add it to `~/.hermes/.env`:

   ```bash
   echo 'CURSOR_API_KEY=your_cursor_api_key_here' >> ~/.hermes/.env
   ```

2. For `launch_agent`, collect the required inputs:

   - `repository`: full GitHub repository URL.
   - `prompt`: clear task for Cursor to perform.
   - `ref`: base branch or commit. Default to `main` when the user does not specify it.

   Optional inputs:

   - `branch_name`: target branch for Cursor's work.
   - `model`: use `default` unless the user requests a specific Cursor model.
   - `auto_create_pr`: set to `true` when the user wants Cursor to open a PR automatically.
   - `auto_branch`: use when working from an existing PR source.

3. Call `POST /agents` to launch the agent.

4. Capture and present:

   - Agent ID.
   - Initial status.
   - Cursor agent URL, if present.
   - PR URL, if present.
   - Branch name, if present.

5. Poll `GET /agents/{agent_id}` every 30 to 60 seconds until the status is terminal.

   Treat `FINISHED` as successful. Treat `ERROR`, `EXPIRED`, and `STOPPED` as unsuccessful or interrupted unless the user intentionally stopped the agent.

6. Always present the latest agent status and any PR URL to the user.

7. For `followup`, require both:

   - `agent_id`
   - `prompt`

   Then call `POST /agents/{agent_id}/followup`.

8. For artifacts, call `GET /agents/{agent_id}/artifacts` first. Use the returned absolute artifact path as the `path` query parameter for the download URL endpoint.

## One-Shot Recipes

### Launch an agent to add a README

Use when the user says: "Launch a Cursor agent to add a README."

Request:

```bash
curl -sS -u "$CURSOR_API_KEY:" \
  -H "Content-Type: application/json" \
  -X POST https://api.cursor.com/v0/agents \
  -d '{
    "prompt": {
      "text": "Add a README.md file with project overview, installation steps, usage examples, configuration notes, and troubleshooting."
    },
    "model": "default",
    "source": {
      "repository": "https://github.com/your-org/your-repo",
      "ref": "main"
    },
    "target": {
      "branchName": "cursor/add-readme",
      "autoCreatePr": true
    }
  }'
```

Report the returned `id`, `status`, `target.url`, `target.branchName`, and `target.prUrl` if present.

### Check agent status and get PR link

Use the returned `agent_id` from launch.

Single status check:

```bash
curl -sS -u "$CURSOR_API_KEY:" \
  https://api.cursor.com/v0/agents/bc_abc123
```

Poll loop:

```bash
while true; do
  curl -sS -u "$CURSOR_API_KEY:" \
    https://api.cursor.com/v0/agents/bc_abc123
  sleep 45
done
```

Stop polling when status is `FINISHED`, `ERROR`, `EXPIRED`, or `STOPPED`. Present the final `summary`, `target.url`, and `target.prUrl` when available.

### Send follow-up prompt to running agent

Use when the user says: "Tell the Cursor agent to also update the changelog."

Request:

```bash
curl -sS -u "$CURSOR_API_KEY:" \
  -H "Content-Type: application/json" \
  -X POST https://api.cursor.com/v0/agents/bc_abc123/followup \
  -d '{
    "prompt": {
      "text": "Also update the changelog with a concise entry for this change."
    }
  }'
```

After the follow-up is accepted, poll `GET /agents/{agent_id}` again until terminal status.

## Common Pitfalls

- The Cursor Cloud Agents API does not expose a live event stream. Poll `GET /agents/{agent_id}` for status every 30 to 60 seconds.
- `launch_agent` without `branchName` may fail or behave unexpectedly if the agent cannot write to the default branch. Prefer a dedicated branch name for public repositories and production work.
- Set `autoCreatePr` to `true` when the user wants a pull request created automatically.
- Large repositories may take several minutes to clone before the agent starts working. Keep polling unless the status becomes terminal.
- `GET /repositories` has strict rate limits and can take a long time for accounts with many repositories. Use a known repository URL when possible.
- Artifact download uses an absolute artifact path returned by `list_artifacts`. Pass that path as the `path` query parameter to `/artifacts/download`.
- Inline MCP server streaming and local SDK `run.stream()` are separate from Cursor Cloud Agents API. Do not promise live stream events from this API.
- Cursor API keys are secrets. Do not print the key, commit it to a repository, or place it in prompts.

## Verification Checklist

- [ ] `CURSOR_API_KEY` is set in `~/.hermes/.env`
- [ ] Repository URL is accessible to Cursor
- [ ] Agent launched successfully with a successful `POST /agents` response
- [ ] Agent ID was saved for polling and follow-up
- [ ] Agent status was polled until completion
- [ ] PR URL or artifact was returned to the user

Created by Keith Vaughan @ Fair Developers DA NANG.
