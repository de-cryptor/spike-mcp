# spike-mcp

[![PyPI](https://img.shields.io/pypi/v/spike-mcp)](https://pypi.org/project/spike-mcp/)
[![Python](https://img.shields.io/pypi/pyversions/spike-mcp)](https://pypi.org/project/spike-mcp/)

MCP server that connects Claude Code to Jira and Confluence. Engineers can research spikes, generate technical solutions with Mermaid architecture diagrams, write Confluence docs, and create Jira epic + story breakdowns through natural conversation — no Anthropic API key required.

---

## Features

- **Research** — search Confluence and Jira before generating anything
- **Design** — produce Mermaid architecture/flow diagrams as part of every spike doc
- **Write** — create or update Confluence pages (markdown + Mermaid → Confluence storage format)
- **Ticket** — create Jira Epics, Stories with acceptance criteria, and Tasks; supports both next-gen and classic projects
- **Zero LLM cost** — Claude itself provides all intelligence; no separate AI API key needed

---

## Installation

```bash
pip install spike-mcp
# or
uv add spike-mcp
```

---

## Setup

### Step 1 — Create `.spike.toml`

Create a `.spike.toml` in your project root (or home directory) with your Atlassian details:

```toml
[atlassian]
base_url = "https://yourorg.atlassian.net"
email    = "you@yourorg.com"

[confluence]
space_key      = "ENG"
parent_page_id = "123456"

[jira]
project_key        = "PLAT"
epic_issue_type    = "Epic"
story_issue_type   = "Story"
task_issue_type    = "Task"
default_label      = "spike"
story_points_field = "customfield_10016"
epic_link_field    = "customfield_10014"

[tickets]
story_point_scale = [1, 2, 3, 5, 8, 13]
```

See `.spike.toml.example` for a full annotated example.

### Step 2 — Set your API token

Generate an Atlassian API token at https://id.atlassian.com/manage-profile/security/api-tokens and export it:

```bash
export ATLASSIAN_API_TOKEN="your-token-here"
```

Never put the token in `.spike.toml` — it is read exclusively from the environment.

---

## Connect to Claude Desktop

Add the MCP server to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

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

Restart Claude Desktop. A hammer icon in the toolbar confirms the tools are active.

---

## Example conversations

Start a spike session by invoking the workflow prompt at the top of your conversation:

```
/mcp__spike-mcp__spike_workflow
```

Then talk naturally:

- "I need to spike on replacing our job queue with Temporal. Research what we have, design a solution with a diagram, write a spike doc in Confluence under the Platform space, then create an epic and stories in the PLAT project."
- "Search Confluence for our auth service architecture and summarise what you find."
- "Break down the spike doc you just wrote into Jira tickets — 1 epic, stories with acceptance criteria, fibonacci points."
- "What Jira tickets are open in PLAT related to observability?"

---

## Tools

| Tool | Inputs | Description |
|---|---|---|
| `search_confluence` | `query`, `space_key?`, `limit?` | CQL full-text search across Confluence |
| `get_confluence_page` | `page_id` | Fetch full page content by ID |
| `search_jira` | `query`, `project_key?`, `limit?` | JQL full-text search across Jira |
| `write_spike_doc` | `title`, `body_markdown`, `space_key?`, `parent_page_id?` | Create a Confluence page (markdown + Mermaid → storage format) |
| `create_epic` | `summary`, `description`, `project_key?`, `label?` | Create a Jira Epic |
| `create_story` | `epic_key`, `summary`, `description`, `acceptance_criteria`, `story_points?`, `project_key?`, `label?` | Create a Jira Story linked to an Epic |
| `create_task` | `epic_key`, `summary`, `description`, `project_key?`, `label?` | Create a Jira Task linked to an Epic |
| `get_project_config` | — | Show current config targets (API token redacted) |

---

## Configuration reference

All fields in `.spike.toml`:

| Field | Required | Description |
|---|---|---|
| `atlassian.base_url` | Yes | Your Atlassian Cloud domain, e.g. `https://myorg.atlassian.net` |
| `atlassian.email` | Yes | Your Atlassian account email |
| `confluence.space_key` | Yes | Confluence space key for new spike docs, e.g. `ENG` |
| `confluence.parent_page_id` | No | Page ID to nest new docs under |
| `jira.project_key` | Yes | Jira project key, e.g. `PLAT` |
| `jira.epic_issue_type` | No | Issue type name for epics (default: `Epic`) |
| `jira.story_issue_type` | No | Issue type name for stories (default: `Story`) |
| `jira.task_issue_type` | No | Issue type name for tasks (default: `Task`) |
| `jira.default_label` | No | Label applied to all created tickets (default: `spike`) |
| `jira.story_points_field` | No | Custom field ID for story points; varies per instance |
| `jira.epic_link_field` | No | Custom field ID for epic link; classic projects only |
| `tickets.story_point_scale` | No | Fibonacci scale used when prompting for estimates |

Config search order: explicit path → current directory → git root walk-up → `~/.spike.toml`.

---

## Contributing

```bash
git clone https://github.com/de-cryptor/spike-mcp
cd spike-mcp
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

---

## License

MIT — see [LICENSE](LICENSE).
