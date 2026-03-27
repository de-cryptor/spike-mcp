from __future__ import annotations

import base64
import re
from typing import Optional

import httpx

from spike_mcp.config import SpikeConfig


def _inline_md(text: str) -> str:
    """Convert inline markdown to Confluence storage format HTML inline elements."""
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    return text


def _md_to_storage(md: str) -> str:
    """Convert markdown to Confluence storage format XML."""
    lines = md.split('\n')
    result: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Fenced code / mermaid blocks
        fence_match = re.match(r'^```(\w*)', line)
        if fence_match:
            lang = fence_match.group(1)
            body_lines: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                body_lines.append(lines[i])
                i += 1
            i += 1  # skip closing ```
            body = '\n'.join(body_lines)
            body_safe = body.replace(']]>', ']]]]><![CDATA[>')

            if lang == 'mermaid':
                result.append(
                    '<ac:structured-macro ac:name="mermaid">'
                    f'<ac:plain-text-body><![CDATA[{body_safe}]]></ac:plain-text-body>'
                    '</ac:structured-macro>'
                )
            else:
                result.append(
                    '<ac:structured-macro ac:name="code">'
                    f'<ac:parameter ac:name="language">{lang}</ac:parameter>'
                    f'<ac:plain-text-body><![CDATA[{body_safe}]]></ac:plain-text-body>'
                    '</ac:structured-macro>'
                )
            continue

        # Headings
        h_match = re.match(r'^(#{1,6})\s+(.*)', line)
        if h_match:
            level = len(h_match.group(1))
            result.append(f'<h{level}>{_inline_md(h_match.group(2))}</h{level}>')
            i += 1
            continue

        # Bullet list — collect consecutive items
        if re.match(r'^[*\-]\s+', line):
            items: list[str] = []
            while i < len(lines) and re.match(r'^[*\-]\s+', lines[i]):
                text = re.sub(r'^[*\-]\s+', '', lines[i])
                items.append(f'<li>{_inline_md(text)}</li>')
                i += 1
            result.append('<ul>' + ''.join(items) + '</ul>')
            continue

        # Numbered list — collect consecutive items
        if re.match(r'^\d+\.\s+', line):
            items = []
            while i < len(lines) and re.match(r'^\d+\.\s+', lines[i]):
                text = re.sub(r'^\d+\.\s+', '', lines[i])
                items.append(f'<li>{_inline_md(text)}</li>')
                i += 1
            result.append('<ol>' + ''.join(items) + '</ol>')
            continue

        # Blank line — skip
        if not line.strip():
            i += 1
            continue

        # Paragraph
        result.append(f'<p>{_inline_md(line)}</p>')
        i += 1

    return '\n'.join(result)


def _strip_html(html: str) -> str:
    """Strip HTML/XML tags and collapse whitespace to plain text."""
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


class ConfluenceClient:
    def __init__(self, config: SpikeConfig) -> None:
        self._base_url = config.atlassian.base_url.rstrip('/')
        credentials = base64.b64encode(
            f"{config.atlassian.email}:{config.api_token}".encode()
        ).decode()
        self._headers = {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self._default_space = config.confluence.space_key
        self._default_parent = config.confluence.parent_page_id

    async def get_page(self, page_id: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self._base_url}/wiki/rest/api/content/{page_id}",
                params={"expand": "body.storage"},
                headers=self._headers,
            )
            resp.raise_for_status()
            data = resp.json()
        body_html = data.get("body", {}).get("storage", {}).get("value", "")
        return {
            "id": data["id"],
            "title": data["title"],
            "body": _strip_html(body_html),
            "url": f"{self._base_url}/wiki{data['_links']['webui']}",
        }

    async def search(
        self, query: str, space_key: str = "", limit: int = 10
    ) -> list[dict]:
        cql = f'text~"{query}" AND type=page'
        if space_key:
            cql += f' AND space="{space_key}"'
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self._base_url}/wiki/rest/api/content/search",
                params={"cql": cql, "limit": limit, "expand": "excerpt"},
                headers=self._headers,
            )
            resp.raise_for_status()
            data = resp.json()
        return [
            {
                "id": item["id"],
                "title": item["title"],
                "excerpt": item.get("excerpt", "")[:400],
                "url": f"{self._base_url}/wiki{item['_links']['webui']}",
            }
            for item in data.get("results", [])
        ]

    async def get_page_children(self, page_id: str, limit: int = 25) -> list[dict]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self._base_url}/wiki/rest/api/content/{page_id}/child/page",
                params={"limit": limit},
                headers=self._headers,
            )
            resp.raise_for_status()
            data = resp.json()
        return [
            {"id": item["id"], "title": item["title"]}
            for item in data.get("results", [])
        ]

    async def create_page(
        self,
        title: str,
        body_markdown: str,
        space_key: str = "",
        parent_id: str = "",
    ) -> dict:
        space = space_key or self._default_space
        parent = parent_id or self._default_parent
        payload: dict = {
            "type": "page",
            "title": title,
            "space": {"key": space},
            "body": {
                "storage": {
                    "value": _md_to_storage(body_markdown),
                    "representation": "storage",
                }
            },
        }
        if parent:
            payload["ancestors"] = [{"id": parent}]
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self._base_url}/wiki/rest/api/content",
                json=payload,
                headers=self._headers,
            )
            resp.raise_for_status()
            data = resp.json()
        return {
            "id": data["id"],
            "url": f"{self._base_url}/wiki{data['_links']['webui']}",
        }

    async def update_page(
        self, page_id: str, title: str, body_markdown: str
    ) -> dict:
        async with httpx.AsyncClient() as client:
            get_resp = await client.get(
                f"{self._base_url}/wiki/rest/api/content/{page_id}",
                params={"expand": "version"},
                headers=self._headers,
            )
            get_resp.raise_for_status()
            current_version = get_resp.json()["version"]["number"]
            payload = {
                "type": "page",
                "title": title,
                "version": {"number": current_version + 1},
                "body": {
                    "storage": {
                        "value": _md_to_storage(body_markdown),
                        "representation": "storage",
                    }
                },
            }
            put_resp = await client.put(
                f"{self._base_url}/wiki/rest/api/content/{page_id}",
                json=payload,
                headers=self._headers,
            )
            put_resp.raise_for_status()
            data = put_resp.json()
        return {
            "id": data["id"],
            "url": f"{self._base_url}/wiki{data['_links']['webui']}",
        }
