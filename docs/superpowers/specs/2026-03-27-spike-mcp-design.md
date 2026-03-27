# spike-mcp Design Spec
**Date:** 2026-03-27
**Status:** Approved

---

## Overview

A Python MCP (Model Context Protocol) server package that connects Claude Code to Jira and Confluence. Engineers can research spikes, generate technical solutions with diagrams, write Confluence docs, and create Jira epic + story breakdowns through natural conversation with Claude — no Anthropic API key required.

---

## Architecture

A single Python package with five internal modules wired together by `server.py`. No external services beyond Atlassian APIs — Claude itself provides all intelligence. The server speaks stdio MCP to Claude Code and HTTP/HTTPS to Atlassian Cloud.

```
Claude Code  <—stdio MCP—>  server.py
                                ├── config.py    (.spike.toml + env token)
                                ├── confluence.py (httpx async client)
                                ├── jira.py       (httpx async client)
                                └── templates.py  (prompt, doc, story templates)
```

All Atlassian auth uses HTTP Basic (`email:api_token`, base64-encoded) — the standard for Atlassian Cloud REST APIs.

---

## File Structure

```
spike-mcp/
├── spike_mcp/
│   ├── __init__.py
│   ├── server.py        # MCP server — all tool registrations
│   ├── config.py        # .spike.toml loader with env token injection
│   ├── confluence.py    # Confluence REST API v2 client
│   ├── jira.py          # Jira REST API v3 client
│   └── templates.py     # Jira ticket + Confluence page templates
├── pyproject.toml
├── .spike.toml.example
└── README.md
```

---

## Module Designs

### config.py

- Pydantic models: `AtlassianConfig`, `ConfluenceConfig`, `JiraConfig`, `TicketsConfig`, `SpikeConfig`
- Config search order: explicit path → cwd → git root walk-up → `~/.spike.toml`
- Uses `tomllib` (stdlib in Python 3.11+) to parse
- `ATLASSIAN_API_TOKEN` injected from environment only — never read from the toml file
- Missing config or token raises `SystemExit` with clear human-readable instructions

`.spike.toml` schema:
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

### confluence.py

Async `ConfluenceClient` using `httpx.AsyncClient`. Atlassian Cloud Confluence REST API v2.

Methods:
- `get_page(page_id) -> dict` — returns `{id, title, body (plain text), url}`
- `search(query, space_key="", limit=10) -> list[dict]` — CQL search, returns `{id, title, excerpt (400 chars), url}`
- `get_page_children(page_id, limit=25) -> list[dict]` — child page titles + IDs
- `create_page(title, body_markdown, space_key="", parent_id="") -> dict` — creates page, converts markdown to storage format, returns `{id, url}`
- `update_page(page_id, title, body_markdown) -> dict` — bumps version and updates

Format conversion (markdown → Confluence storage format):
- Line-by-line regex; no full HTML parser needed
- Headings `#`–`######` → `<h1>`–`<h6>`
- Bold/italic
- Bullet and numbered lists
- Fenced code blocks → `<ac:structured-macro ac:name="code">` with language parameter
- Mermaid fenced blocks (` ```mermaid `) → `<ac:structured-macro ac:name="mermaid">` with `<ac:plain-text-body><![CDATA[...]]></ac:plain-text-body>`

Helper `_strip_html(html) -> str` converts storage format to plain text for reading.

### jira.py

Async `JiraClient` using `httpx.AsyncClient`. Atlassian Cloud Jira REST API v3.

Methods:
- `search_issues(query, project_key="", limit=10) -> list[dict]` — JQL text search, returns `{key, summary, type, status, url}`
- `get_issue(issue_key) -> dict` — full issue detail
- `create_epic(summary, description, label) -> str` — returns epic key e.g. `PLAT-42`
- `create_story(epic_key, summary, description, acceptance_criteria, story_points, label) -> str` — returns story key. Epic linking: try `parent` field first (next-gen projects), fall back to `epic_link_field` custom field from config (classic projects).
- `create_task(epic_key, summary, description, label) -> str` — returns task key

Format conversion (markdown → ADF JSON):
- Walk lines, emit typed ADF nodes
- Supported nodes: `heading`, `paragraph`, `bulletList`/`orderedList`, `codeBlock`
- Supported inline marks: `strong`, `em`

ADF root structure:
```json
{
  "version": 1,
  "type": "doc",
  "content": [ ... ]
}
```

### templates.py

Three exports:

1. **`SPIKE_DOC_TEMPLATE`** — Confluence page markdown template with sections:
   - Overview, Problem Statement, Goals & Non-goals, Proposed Solution, Architecture Diagram (Mermaid placeholder), Implementation Options, Recommendation, Epic + Story Breakdown, References

2. **`STORY_TEMPLATE`** — Jira story description template with fields:
   - Context, What needs to be done, Acceptance criteria, Out of scope, Notes / open questions

3. **`SYSTEM_PROMPT`** — Multi-line string exposed as an MCP prompt resource. Instructs Claude to:
   - Call `search_confluence` and `search_jira` before generating anything
   - Always produce a Mermaid architecture or flow diagram as part of the spike doc
   - Break down work into: 1 Epic → multiple Stories (3–8 story points each) → Tasks for very small items
   - Write Jira tickets with: imperative-verb one-line summary, context paragraph, numbered acceptance criteria, explicit out-of-scope line
   - Ask for confirmation before creating anything in Jira or Confluence

### server.py

Uses the `mcp` SDK. Startup sequence in `main()`:
1. Load config via `load_config()` — print clear error and exit if missing
2. Instantiate `ConfluenceClient` and `JiraClient`
3. Register all tools and the `spike_workflow` prompt
4. Run with `mcp.run(transport="stdio")`

---

## MCP Surface

### Tools (8 total)

| Tool | Inputs | Output |
|---|---|---|
| `search_confluence` | `query`, `space_key?`, `limit=5` | list of `{title, excerpt, url}` |
| `get_confluence_page` | `page_id` | `{title, body}` |
| `search_jira` | `query`, `project_key?`, `limit=10` | list of `{key, summary, type, status, url}` |
| `write_spike_doc` | `title`, `body_markdown`, `space_key?`, `parent_page_id?` | `{id, url}` |
| `create_epic` | `summary`, `description`, `project_key?`, `label?` | `{key, url}` |
| `create_story` | `epic_key`, `summary`, `description`, `acceptance_criteria`, `story_points?`, `project_key?`, `label?` | `{key, url}` |
| `create_task` | `epic_key`, `summary`, `description`, `project_key?`, `label?` | `{key, url}` |
| `get_project_config` | none | redacted config values |

### Prompt (1 total)

| Prompt | Description |
|---|---|
| `spike_workflow` | Returns `SYSTEM_PROMPT` as a `user`-role message. Invoke with `/mcp__spike-mcp__spike_workflow` at the start of a spike session. |

---

## Error Handling

- All tool handlers catch `httpx.HTTPStatusError` and return a human-readable error string — Claude surfaces it conversationally rather than crashing the MCP server
- Config/token errors cause `SystemExit` at startup with actionable instructions

---

## Packaging

- `pyproject.toml` with `hatchling` build backend
- Entry point: `spike-mcp` CLI → `spike_mcp.server:main`
- Python 3.11+ required (for `tomllib` stdlib)
- Dependencies: `mcp>=1.0.0`, `httpx>=0.27.0`, `pydantic>=2.0.0`
- Installable via `pip install spike-mcp` or `uv add spike-mcp`
