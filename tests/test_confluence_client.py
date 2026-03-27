import json
import httpx
import pytest
import respx

from spike_mcp.confluence import ConfluenceClient

BASE = "https://test.atlassian.net"


@pytest.fixture
def client(spike_config):
    return ConfluenceClient(spike_config)


@respx.mock
async def test_search_returns_results(client):
    respx.get(f"{BASE}/wiki/rest/api/content/search").mock(
        return_value=httpx.Response(200, json={
            "results": [{
                "id": "42",
                "title": "Auth Architecture",
                "excerpt": "How auth works...",
                "_links": {"webui": "/spaces/ENG/pages/42"},
            }]
        })
    )
    results = await client.search("auth")
    assert len(results) == 1
    assert results[0]["id"] == "42"
    assert results[0]["title"] == "Auth Architecture"
    assert results[0]["excerpt"] == "How auth works..."
    assert results[0]["url"] == f"{BASE}/wiki/spaces/ENG/pages/42"


@respx.mock
async def test_search_empty(client):
    respx.get(f"{BASE}/wiki/rest/api/content/search").mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    assert await client.search("nothing") == []


@respx.mock
async def test_search_truncates_excerpt_to_400(client):
    respx.get(f"{BASE}/wiki/rest/api/content/search").mock(
        return_value=httpx.Response(200, json={
            "results": [{
                "id": "1",
                "title": "Page",
                "excerpt": "x" * 500,
                "_links": {"webui": "/spaces/ENG/pages/1"},
            }]
        })
    )
    results = await client.search("x")
    assert len(results[0]["excerpt"]) == 400


@respx.mock
async def test_get_page_returns_plain_text(client):
    respx.get(f"{BASE}/wiki/rest/api/content/123").mock(
        return_value=httpx.Response(200, json={
            "id": "123",
            "title": "My Page",
            "body": {"storage": {"value": "<h1>Hello</h1><p>World</p>"}},
            "_links": {"webui": "/spaces/ENG/pages/123"},
        })
    )
    page = await client.get_page("123")
    assert page["id"] == "123"
    assert page["title"] == "My Page"
    assert "Hello" in page["body"]
    assert "World" in page["body"]
    assert "<h1>" not in page["body"]
    assert page["url"] == f"{BASE}/wiki/spaces/ENG/pages/123"


@respx.mock
async def test_get_page_children(client):
    respx.get(f"{BASE}/wiki/rest/api/content/99/child/page").mock(
        return_value=httpx.Response(200, json={
            "results": [
                {"id": "100", "title": "Child One"},
                {"id": "101", "title": "Child Two"},
            ]
        })
    )
    children = await client.get_page_children("99")
    assert len(children) == 2
    assert children[0] == {"id": "100", "title": "Child One"}


@respx.mock
async def test_create_page_posts_storage_format(client):
    respx.post(f"{BASE}/wiki/rest/api/content").mock(
        return_value=httpx.Response(200, json={
            "id": "500",
            "_links": {"webui": "/spaces/ENG/pages/500"},
        })
    )
    result = await client.create_page("My Spike", "# Overview\n\nContent here")
    assert result == {
        "id": "500",
        "url": f"{BASE}/wiki/spaces/ENG/pages/500",
    }
    body = json.loads(respx.calls[0].request.content)
    assert body["title"] == "My Spike"
    assert body["space"]["key"] == "ENG"
    assert body["body"]["storage"]["representation"] == "storage"
    assert "<h1>Overview</h1>" in body["body"]["storage"]["value"]


@respx.mock
async def test_create_page_uses_parent_from_config(client):
    respx.post(f"{BASE}/wiki/rest/api/content").mock(
        return_value=httpx.Response(200, json={
            "id": "501",
            "_links": {"webui": "/spaces/ENG/pages/501"},
        })
    )
    await client.create_page("Test", "body")
    body = json.loads(respx.calls[0].request.content)
    assert body["ancestors"] == [{"id": "999"}]


@respx.mock
async def test_create_page_explicit_space_and_parent(client):
    respx.post(f"{BASE}/wiki/rest/api/content").mock(
        return_value=httpx.Response(200, json={
            "id": "502",
            "_links": {"webui": "/spaces/OPS/pages/502"},
        })
    )
    await client.create_page("Test", "body", space_key="OPS", parent_id="888")
    body = json.loads(respx.calls[0].request.content)
    assert body["space"]["key"] == "OPS"
    assert body["ancestors"] == [{"id": "888"}]


@respx.mock
async def test_update_page_bumps_version(client):
    respx.get(f"{BASE}/wiki/rest/api/content/200").mock(
        return_value=httpx.Response(200, json={
            "id": "200",
            "version": {"number": 3},
        })
    )
    respx.put(f"{BASE}/wiki/rest/api/content/200").mock(
        return_value=httpx.Response(200, json={
            "id": "200",
            "_links": {"webui": "/spaces/ENG/pages/200"},
        })
    )
    result = await client.update_page("200", "Updated Title", "## New content")
    assert result["id"] == "200"
    body = json.loads(respx.calls[1].request.content)
    assert body["version"]["number"] == 4
    assert body["title"] == "Updated Title"


@respx.mock
async def test_search_raises_http_status_error(client):
    respx.get(f"{BASE}/wiki/rest/api/content/search").mock(
        return_value=httpx.Response(401, json={"message": "Unauthorized"})
    )
    with pytest.raises(httpx.HTTPStatusError):
        await client.search("query")
