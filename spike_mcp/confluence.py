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

            if lang == 'mermaid':
                result.append(
                    '<ac:structured-macro ac:name="mermaid">'
                    f'<ac:plain-text-body><![CDATA[{body}]]></ac:plain-text-body>'
                    '</ac:structured-macro>'
                )
            else:
                result.append(
                    '<ac:structured-macro ac:name="code">'
                    f'<ac:parameter ac:name="language">{lang}</ac:parameter>'
                    f'<ac:plain-text-body><![CDATA[{body}]]></ac:plain-text-body>'
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
    pass  # implemented in Task 5
