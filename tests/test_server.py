import json
import httpx
import pytest
import respx

from spike_mcp.server import create_server
from spike_mcp.templates import SYSTEM_PROMPT

BASE = "https://test.atlassian.net"


# ── helpers ────────────────────────────────────────────────────────────────────

def _get_tool(server, name: str):
    """Extract a registered tool's callable from a FastMCP server."""
    return server._tool_manager._tools[name].fn


def _get_prompt_fn(server, name: str):
    """Extract a registered prompt's callable from a FastMCP server."""
    return server._prompt_manager._prompts[name].fn


# ── basic registration ─────────────────────────────────────────────────────────

def test_create_server_returns_fastmcp(spike_config):
    from mcp.server.fastmcp import FastMCP
    assert isinstance(create_server(spike_config), FastMCP)


def test_all_tools_registered(spike_config):
    server = create_server(spike_config)
    tools = server._tool_manager._tools
    for name in [
        "search_confluence",
        "get_confluence_page",
        "search_jira",
        "write_spike_doc",
        "create_epic",
        "create_story",
        "create_task",
        "get_project_config",
    ]:
        assert name in tools, f"Tool not registered: {name}"


def test_spike_workflow_prompt_registered(spike_config):
    server = create_server(spike_config)
    assert "spike_workflow" in server._prompt_manager._prompts


def test_spike_workflow_prompt_returns_system_prompt(spike_config):
    server = create_server(spike_config)
    fn = _get_prompt_fn(server, "spike_workflow")
    assert fn() == SYSTEM_PROMPT


# ── get_project_config ─────────────────────────────────────────────────────────

async def test_get_project_config_redacts_token(spike_config):
    server = create_server(spike_config)
    result = await _get_tool(server, "get_project_config")()
    data = json.loads(result)
    assert data["atlassian"]["api_token"] == "***REDACTED***"
    assert "test-token-abc" not in result
    assert data["atlassian"]["base_url"] == BASE
    assert data["confluence"]["space_key"] == "ENG"
    assert data["jira"]["project_key"] == "PLAT"
    assert data["tickets"]["story_point_scale"] == [1, 2, 3, 5, 8, 13]


# ── search_confluence ──────────────────────────────────────────────────────────

@respx.mock
async def test_search_confluence_returns_results(spike_config):
    respx.get(f"{BASE}/wiki/rest/api/content/search").mock(
        return_value=httpx.Response(200, json={
            "results": [{
                "id": "1",
                "title": "Auth Docs",
                "excerpt": "Auth details",
                "_links": {"webui": "/spaces/ENG/pages/1"},
            }]
        })
    )
    server = create_server(spike_config)
    result = await _get_tool(server, "search_confluence")(query="auth")
    data = json.loads(result)
    assert data[0]["title"] == "Auth Docs"


@respx.mock
async def test_search_confluence_http_error_returns_string(spike_config):
    respx.get(f"{BASE}/wiki/rest/api/content/search").mock(
        return_value=httpx.Response(403, text="Forbidden")
    )
    server = create_server(spike_config)
    result = await _get_tool(server, "search_confluence")(query="auth")
    assert "403" in result
    assert "error" in result.lower()


# ── search_jira ────────────────────────────────────────────────────────────────

@respx.mock
async def test_search_jira_returns_results(spike_config):
    respx.get(f"{BASE}/rest/api/3/issue/search").mock(
        return_value=httpx.Response(200, json={
            "issues": [{
                "key": "PLAT-1",
                "fields": {
                    "summary": "Old queue impl",
                    "issuetype": {"name": "Story"},
                    "status": {"name": "Done"},
                },
            }]
        })
    )
    server = create_server(spike_config)
    result = await _get_tool(server, "search_jira")(query="queue")
    data = json.loads(result)
    assert data[0]["key"] == "PLAT-1"


# ── write_spike_doc ────────────────────────────────────────────────────────────

@respx.mock
async def test_write_spike_doc(spike_config):
    respx.post(f"{BASE}/wiki/rest/api/content").mock(
        return_value=httpx.Response(200, json={
            "id": "777",
            "_links": {"webui": "/spaces/ENG/pages/777"},
        })
    )
    server = create_server(spike_config)
    result = await _get_tool(server, "write_spike_doc")(
        title="My Spike",
        body_markdown="# Title\n\nContent",
    )
    data = json.loads(result)
    assert data["id"] == "777"
    assert "url" in data


# ── create_epic ────────────────────────────────────────────────────────────────

@respx.mock
async def test_create_epic_tool(spike_config):
    respx.post(f"{BASE}/rest/api/3/issue").mock(
        return_value=httpx.Response(201, json={"key": "PLAT-50"})
    )
    server = create_server(spike_config)
    result = await _get_tool(server, "create_epic")(
        summary="Big epic", description="Context here"
    )
    data = json.loads(result)
    assert data["key"] == "PLAT-50"
    assert data["url"] == f"{BASE}/browse/PLAT-50"


# ── create_story ───────────────────────────────────────────────────────────────

@respx.mock
async def test_create_story_tool(spike_config):
    respx.post(f"{BASE}/rest/api/3/issue").mock(
        return_value=httpx.Response(201, json={"key": "PLAT-51"})
    )
    server = create_server(spike_config)
    result = await _get_tool(server, "create_story")(
        epic_key="PLAT-50",
        summary="Add worker",
        description="Do the thing",
        acceptance_criteria="1. Works",
        story_points=3,
    )
    data = json.loads(result)
    assert data["key"] == "PLAT-51"
    assert data["url"] == f"{BASE}/browse/PLAT-51"


# ── create_task ────────────────────────────────────────────────────────────────

@respx.mock
async def test_create_task_tool(spike_config):
    respx.post(f"{BASE}/rest/api/3/issue").mock(
        return_value=httpx.Response(201, json={"key": "PLAT-52"})
    )
    server = create_server(spike_config)
    result = await _get_tool(server, "create_task")(
        epic_key="PLAT-50",
        summary="Set up namespace",
        description="Create it",
    )
    data = json.loads(result)
    assert data["key"] == "PLAT-52"
    assert data["url"] == f"{BASE}/browse/PLAT-52"
