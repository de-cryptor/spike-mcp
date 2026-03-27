import json
import httpx
import pytest
import respx

from spike_mcp.jira import JiraClient

BASE = "https://test.atlassian.net"


@pytest.fixture
def client(spike_config):
    return JiraClient(spike_config)


@respx.mock
async def test_search_issues(client):
    respx.get(f"{BASE}/rest/api/3/issue/search").mock(
        return_value=httpx.Response(200, json={
            "issues": [{
                "key": "PLAT-10",
                "fields": {
                    "summary": "Migrate job queue",
                    "issuetype": {"name": "Story"},
                    "status": {"name": "In Progress"},
                },
            }]
        })
    )
    results = await client.search_issues("job queue")
    assert len(results) == 1
    assert results[0]["key"] == "PLAT-10"
    assert results[0]["summary"] == "Migrate job queue"
    assert results[0]["type"] == "Story"
    assert results[0]["status"] == "In Progress"
    assert results[0]["url"] == f"{BASE}/browse/PLAT-10"


@respx.mock
async def test_search_issues_empty(client):
    respx.get(f"{BASE}/rest/api/3/issue/search").mock(
        return_value=httpx.Response(200, json={"issues": []})
    )
    assert await client.search_issues("nothing") == []


@respx.mock
async def test_get_issue(client):
    respx.get(f"{BASE}/rest/api/3/issue/PLAT-42").mock(
        return_value=httpx.Response(200, json={"key": "PLAT-42", "fields": {"summary": "Test"}})
    )
    issue = await client.get_issue("PLAT-42")
    assert issue["key"] == "PLAT-42"


@respx.mock
async def test_create_epic(client):
    respx.post(f"{BASE}/rest/api/3/issue").mock(
        return_value=httpx.Response(201, json={"key": "PLAT-100"})
    )
    key = await client.create_epic(
        summary="Implement Temporal job queue",
        description="We need to replace Bull with Temporal.",
    )
    assert key == "PLAT-100"
    body = json.loads(respx.calls[0].request.content)
    assert body["fields"]["project"]["key"] == "PLAT"
    assert body["fields"]["issuetype"]["name"] == "Epic"
    assert body["fields"]["summary"] == "Implement Temporal job queue"
    assert body["fields"]["description"]["type"] == "doc"
    assert body["fields"]["labels"] == ["spike"]


@respx.mock
async def test_create_epic_custom_project_key(client):
    respx.post(f"{BASE}/rest/api/3/issue").mock(
        return_value=httpx.Response(201, json={"key": "OPS-5"})
    )
    key = await client.create_epic("Epic", "desc", project_key="OPS")
    assert key == "OPS-5"
    body = json.loads(respx.calls[0].request.content)
    assert body["fields"]["project"]["key"] == "OPS"


@respx.mock
async def test_create_story_next_gen(client):
    """Story created with parent field on first attempt (next-gen Jira project)."""
    respx.post(f"{BASE}/rest/api/3/issue").mock(
        return_value=httpx.Response(201, json={"key": "PLAT-101"})
    )
    key = await client.create_story(
        epic_key="PLAT-100",
        summary="Add Temporal worker",
        description="Worker implementation.",
        acceptance_criteria="1. Worker starts\n2. Worker processes jobs",
        story_points=5,
    )
    assert key == "PLAT-101"
    assert len(respx.calls) == 1  # no fallback
    body = json.loads(respx.calls[0].request.content)
    assert body["fields"]["parent"]["key"] == "PLAT-100"
    assert body["fields"]["customfield_10016"] == 5
    assert body["fields"]["issuetype"]["name"] == "Story"


@respx.mock
async def test_create_story_classic_fallback(client):
    """400 on parent field triggers fallback to epic_link_field (classic projects)."""
    route = respx.post(f"{BASE}/rest/api/3/issue")
    route.side_effect = [
        httpx.Response(400, json={"errors": {"parent": "Field 'parent' cannot be set"}}),
        httpx.Response(201, json={"key": "PLAT-102"}),
    ]
    key = await client.create_story(
        epic_key="PLAT-100",
        summary="Add Temporal worker",
        description="Worker implementation.",
        acceptance_criteria="1. Worker starts",
    )
    assert key == "PLAT-102"
    assert len(respx.calls) == 2
    fallback_body = json.loads(respx.calls[1].request.content)
    assert "parent" not in fallback_body["fields"]
    assert fallback_body["fields"]["customfield_10014"] == "PLAT-100"


@respx.mock
async def test_create_task(client):
    respx.post(f"{BASE}/rest/api/3/issue").mock(
        return_value=httpx.Response(201, json={"key": "PLAT-200"})
    )
    key = await client.create_task(
        epic_key="PLAT-100",
        summary="Set up Temporal namespace",
        description="Create the namespace in staging.",
    )
    assert key == "PLAT-200"
    body = json.loads(respx.calls[0].request.content)
    assert body["fields"]["issuetype"]["name"] == "Task"
    assert body["fields"]["parent"]["key"] == "PLAT-100"


@respx.mock
async def test_create_task_classic_fallback(client):
    route = respx.post(f"{BASE}/rest/api/3/issue")
    route.side_effect = [
        httpx.Response(400, json={"errors": {"parent": "not supported"}}),
        httpx.Response(201, json={"key": "PLAT-201"}),
    ]
    key = await client.create_task("PLAT-100", "Task summary", "desc")
    assert key == "PLAT-201"
    fallback_body = json.loads(respx.calls[1].request.content)
    assert fallback_body["fields"]["customfield_10014"] == "PLAT-100"
