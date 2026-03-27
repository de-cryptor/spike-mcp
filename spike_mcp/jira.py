from __future__ import annotations

import base64
import re
from typing import Optional

import httpx

from spike_mcp.config import SpikeConfig


def _inline_adf(text: str) -> list[dict]:
    """Convert inline markdown to a list of ADF text nodes."""
    nodes: list[dict] = []
    pattern = re.compile(
        r'\*\*\*(?P<bold_italic>.+?)\*\*\*'
        r'|\*\*(?P<bold>.+?)\*\*'
        r'|\*(?P<italic>.+?)\*'
        r'|`(?P<code>.+?)`'
    )
    last_end = 0
    for match in pattern.finditer(text):
        if match.start() > last_end:
            nodes.append({"type": "text", "text": text[last_end:match.start()]})
        if match.group('bold_italic'):
            nodes.append({
                "type": "text",
                "text": match.group('bold_italic'),
                "marks": [{"type": "strong"}, {"type": "em"}],
            })
        elif match.group('bold'):
            nodes.append({
                "type": "text",
                "text": match.group('bold'),
                "marks": [{"type": "strong"}],
            })
        elif match.group('italic'):
            nodes.append({
                "type": "text",
                "text": match.group('italic'),
                "marks": [{"type": "em"}],
            })
        elif match.group('code'):
            nodes.append({
                "type": "text",
                "text": match.group('code'),
                "marks": [{"type": "code"}],
            })
        last_end = match.end()
    if last_end < len(text):
        nodes.append({"type": "text", "text": text[last_end:]})
    return nodes or [{"type": "text", "text": text}]


def _md_to_adf(md: str) -> dict:
    """Convert markdown string to Atlassian Document Format JSON."""
    content: list[dict] = []
    lines = md.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i]

        # Fenced code block
        fence_match = re.match(r'^```(\w*)', line)
        if fence_match:
            lang = fence_match.group(1)
            code_lines: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            i += 1  # skip closing ```
            attrs = {"language": lang} if lang else {}
            content.append({
                "type": "codeBlock",
                "attrs": attrs,
                "content": [{"type": "text", "text": '\n'.join(code_lines)}],
            })
            continue

        # Heading
        h_match = re.match(r'^(#{1,6})\s+(.*)', line)
        if h_match:
            content.append({
                "type": "heading",
                "attrs": {"level": len(h_match.group(1))},
                "content": _inline_adf(h_match.group(2)),
            })
            i += 1
            continue

        # Bullet list
        if re.match(r'^[*\-]\s+', line):
            items: list[dict] = []
            while i < len(lines) and re.match(r'^[*\-]\s+', lines[i]):
                text = re.sub(r'^[*\-]\s+', '', lines[i])
                items.append({
                    "type": "listItem",
                    "content": [{"type": "paragraph", "content": _inline_adf(text)}],
                })
                i += 1
            content.append({"type": "bulletList", "content": items})
            continue

        # Numbered list
        if re.match(r'^\d+\.\s+', line):
            items = []
            while i < len(lines) and re.match(r'^\d+\.\s+', lines[i]):
                text = re.sub(r'^\d+\.\s+', '', lines[i])
                items.append({
                    "type": "listItem",
                    "content": [{"type": "paragraph", "content": _inline_adf(text)}],
                })
                i += 1
            content.append({"type": "orderedList", "content": items})
            continue

        # Blank line — skip
        if not line.strip():
            i += 1
            continue

        # Paragraph
        content.append({
            "type": "paragraph",
            "content": _inline_adf(line),
        })
        i += 1

    return {"version": 1, "type": "doc", "content": content}


class JiraClient:
    pass  # implemented in Task 7
