# Cursor Cloud Agents Hermes Skill

This Hermes skill lets an agent launch and manage Cursor Cloud Agents through the Cursor Cloud Agents API.

## Install

1. Push this repository to Git.
2. Install it in Hermes as a repo-based skill.
3. Configure the required secret:

```bash
CURSOR_API_KEY=your_cursor_api_key
```

The key must have access to Cursor Cloud Agents and the target GitHub repositories.

## Actions

- `me`: verify the configured Cursor API key.
- `models`: list available Cursor Cloud Agent models.
- `repositories`: list GitHub repositories visible to Cursor.
- `list_agents`: list Cursor Cloud Agents.
- `launch_agent`: start a new Cursor Cloud Agent.
- `get_agent`: fetch one agent by ID.
- `followup`: send a follow-up prompt to an agent.
- `stop_agent`: stop a running agent.
- `conversation`: retrieve an agent conversation.
- `list_artifacts`: list generated artifacts.
- `download_artifact`: get a temporary artifact download URL.

## Example Input

```json
{
  "action": "launch_agent",
  "prompt": "Add install docs to the README",
  "repository": "https://github.com/your-org/your-repo",
  "ref": "main",
  "model": "default",
  "branch_name": "cursor/add-install-docs",
  "auto_create_pr": true
}
```

## Notes

This first version targets Cursor Cloud Agents only. Cursor's Cloud Agents API does not expose the local SDK `run.stream()` event stream, so Hermes should poll `get_agent` or use Cursor webhooks outside this skill if it needs live status updates.

---

Created by Keith Vaughan @ Fair Developers [ Bullding Cutting Edge AI Systems In The Cloud ]