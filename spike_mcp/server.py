from __future__ import annotations

import json

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.types import PromptMessage, TextContent

from spike_mcp.config import SpikeConfig, load_config
from spike_mcp.confluence import ConfluenceClient
from spike_mcp.jira import JiraClient
from spike_mcp.templates import SYSTEM_PROMPT


def create_server(config: SpikeConfig) -> FastMCP:
    mcp_server = FastMCP("spike-mcp")
    confluence = ConfluenceClient(config)
    jira = JiraClient(config)

    @mcp_server.tool()
    async def search_confluence(
        query: str, space_key: str = "", limit: int = 5
    ) -> str:
        """Search Confluence pages using CQL full-text search."""
        try:
            results = await confluence.search(query, space_key=space_key, limit=limit)
            return json.dumps(results, indent=2)
        except httpx.HTTPStatusError as e:
            return f"Confluence API error {e.response.status_code}: {e.response.text[:300]}"

    @mcp_server.tool()
    async def get_confluence_page(page_id: str) -> str:
        """Get the full title and plain-text body of a Confluence page by ID."""
        try:
            page = await confluence.get_page(page_id)
            return json.dumps(page, indent=2)
        except httpx.HTTPStatusError as e:
            return f"Confluence API error {e.response.status_code}: {e.response.text[:300]}"

    @mcp_server.tool()
    async def search_jira(
        query: str, project_key: str = "", limit: int = 10
    ) -> str:
        """Search Jira issues using JQL full-text search."""
        try:
            results = await jira.search_issues(query, project_key=project_key, limit=limit)
            return json.dumps(results, indent=2)
        except httpx.HTTPStatusError as e:
            return f"Jira API error {e.response.status_code}: {e.response.text[:300]}"

    @mcp_server.tool()
    async def write_spike_doc(
        title: str,
        body_markdown: str,
        space_key: str = "",
        parent_page_id: str = "",
    ) -> str:
        """Create a Confluence page for a spike doc. Converts markdown (including Mermaid diagrams) to Confluence storage format."""
        try:
            result = await confluence.create_page(
                title, body_markdown, space_key=space_key, parent_id=parent_page_id
            )
            return json.dumps(result, indent=2)
        except httpx.HTTPStatusError as e:
            return f"Confluence API error {e.response.status_code}: {e.response.text[:300]}"

    @mcp_server.tool()
    async def create_epic(
        summary: str,
        description: str,
        project_key: str = "",
        label: str = "",
    ) -> str:
        """Create a Jira Epic. Returns the epic key and URL."""
        try:
            key = await jira.create_epic(
                summary, description, label=label, project_key=project_key
            )
            url = f"{config.atlassian.base_url}/browse/{key}"
            return json.dumps({"key": key, "url": url}, indent=2)
        except httpx.HTTPStatusError as e:
            return f"Jira API error {e.response.status_code}: {e.response.text[:300]}"

    @mcp_server.tool()
    async def create_story(
        epic_key: str,
        summary: str,
        description: str,
        acceptance_criteria: str,
        story_points: int | None = None,
        project_key: str = "",
        label: str = "",
    ) -> str:
        """Create a Jira Story linked to an Epic. Tries next-gen parent field first, falls back to classic epic link field."""
        try:
            key = await jira.create_story(
                epic_key,
                summary,
                description,
                acceptance_criteria,
                story_points=story_points,
                label=label,
                project_key=project_key,
            )
            url = f"{config.atlassian.base_url}/browse/{key}"
            return json.dumps({"key": key, "url": url}, indent=2)
        except httpx.HTTPStatusError as e:
            return f"Jira API error {e.response.status_code}: {e.response.text[:300]}"

    @mcp_server.tool()
    async def create_task(
        epic_key: str,
        summary: str,
        description: str,
        project_key: str = "",
        label: str = "",
    ) -> str:
        """Create a Jira Task linked to an Epic."""
        try:
            key = await jira.create_task(
                epic_key, summary, description, label=label, project_key=project_key
            )
            url = f"{config.atlassian.base_url}/browse/{key}"
            return json.dumps({"key": key, "url": url}, indent=2)
        except httpx.HTTPStatusError as e:
            return f"Jira API error {e.response.status_code}: {e.response.text[:300]}"

    @mcp_server.tool()
    async def get_project_config() -> str:
        """Return current config values (API token redacted) so Claude can confirm targets before acting."""
        return json.dumps(
            {
                "atlassian": {
                    "base_url": config.atlassian.base_url,
                    "email": config.atlassian.email,
                    "api_token": "***REDACTED***",
                },
                "confluence": {
                    "space_key": config.confluence.space_key,
                    "parent_page_id": config.confluence.parent_page_id,
                },
                "jira": {
                    "project_key": config.jira.project_key,
                    "epic_issue_type": config.jira.epic_issue_type,
                    "story_issue_type": config.jira.story_issue_type,
                    "task_issue_type": config.jira.task_issue_type,
                    "default_label": config.jira.default_label,
                },
                "tickets": {
                    "story_point_scale": config.tickets.story_point_scale,
                },
            },
            indent=2,
        )

    @mcp_server.prompt()
    def spike_workflow() -> list[PromptMessage]:
        """Workflow instructions for running a spike with Claude. Invoke at the start of a spike session."""
        return [PromptMessage(role="user", content=TextContent(type="text", text=SYSTEM_PROMPT))]

    return mcp_server


def main() -> None:
    config = load_config()
    server = create_server(config)
    server.run(transport="stdio")
