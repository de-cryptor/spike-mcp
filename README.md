# spike-mcp

MCP server connecting Claude Code to Jira and Confluence — research spikes, generate diagrams, write docs, create tickets through natural conversation.

## Installation

```bash
pip install spike-mcp
# or
uv add spike-mcp
```

## Setup

### Step 1 — Create `.spike.toml`

Copy the example configuration and edit it with your Atlassian details:

```bash
cp .spike.toml.example .spike.toml
# Edit with your Atlassian base URL, email, space key, and project key
```

### Step 2 — Set API token

Set your Atlassian API token as an environment variable (do not commit it to `.spike.toml`):

```bash
export ATLASSIAN_API_TOKEN="your-token-here"
# Generate at: https://id.atlassian.com/manage-profile/security/api-tokens
```

## Connect to Claude

Add the MCP server to Claude's desktop configuration at `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "spike-mcp": {
      "command": "spike-mcp",
      "env": {
        "ATLASSIAN_API_TOKEN": "your-token-here"
      }
    }
  }
}
```

Restart Claude. A hammer icon confirms the tools are active.

## Start a spike session

Load the workflow instructions in Claude:

```
/mcp__spike-mcp__spike_workflow
```

Example prompt: "I need to spike on replacing our job queue with Temporal. Research what we have, design a solution with a diagram, write a spike doc in Confluence under the Platform space, then create an epic and stories in the PLAT project"

## Example conversations

- "Search Confluence for our auth service architecture and summarise what you find"
- "Break down the spike doc you just wrote into Jira tickets — 1 epic, stories with acceptance criteria, fibonacci points"

## Tools

| Tool | Description |
|---|---|
| `search_confluence` | CQL full-text search across Confluence |
| `get_confluence_page` | Fetch full page content by ID |
| `search_jira` | JQL full-text search across Jira |
| `write_spike_doc` | Create a Confluence page (markdown + Mermaid → storage format) |
| `create_epic` | Create a Jira Epic |
| `create_story` | Create a Jira Story linked to an Epic |
| `create_task` | Create a Jira Task linked to an Epic |
| `get_project_config` | Show current config targets (token redacted) |

## Configuration reference

See `.spike.toml.example` for a complete example. Key fields:

- `atlassian.base_url` — Your Jira/Confluence domain (e.g. `https://myorg.atlassian.net`)
- `confluence.space_key` — Confluence space where spikes are documented (e.g. `ENG`)
- `jira.project_key` — Jira project key for spike work (e.g. `PLAT`)
- `jira.story_points_field` — Custom field ID for story points; check your Jira instance to confirm (e.g. `customfield_10016`)
- `jira.epic_link_field` — Custom field ID linking stories to epics; only used in classic projects (e.g. `customfield_10014`)
