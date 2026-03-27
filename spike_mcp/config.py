from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Optional

from pydantic import BaseModel


class AtlassianConfig(BaseModel):
    base_url: str
    email: str


class ConfluenceConfig(BaseModel):
    space_key: str = ""
    parent_page_id: str = ""


class JiraConfig(BaseModel):
    project_key: str = ""
    epic_issue_type: str = "Epic"
    story_issue_type: str = "Story"
    task_issue_type: str = "Task"
    default_label: str = "spike"
    story_points_field: str = "customfield_10016"
    epic_link_field: str = "customfield_10014"


class TicketsConfig(BaseModel):
    story_point_scale: list[int] = [1, 2, 3, 5, 8, 13]


class SpikeConfig(BaseModel):
    atlassian: AtlassianConfig
    confluence: ConfluenceConfig = ConfluenceConfig()
    jira: JiraConfig = JiraConfig()
    tickets: TicketsConfig = TicketsConfig()
    api_token: str


def _find_toml(explicit_path: Optional[str] = None) -> Path:
    if explicit_path:
        p = Path(explicit_path)
        if not p.exists():
            raise FileNotFoundError(f"Config file not found: {explicit_path}")
        return p

    current = Path.cwd()
    while True:
        candidate = current / ".spike.toml"
        if candidate.exists():
            return candidate
        if (current / ".git").exists() or current.parent == current:
            break
        current = current.parent

    home_config = Path.home() / ".spike.toml"
    if home_config.exists():
        return home_config

    raise FileNotFoundError(
        "No .spike.toml found. Create one in your project root or at ~/.spike.toml.\n"
        "Run: cp .spike.toml.example .spike.toml  (then edit with your values)"
    )


def load_config(explicit_path: Optional[str] = None) -> SpikeConfig:
    api_token = os.environ.get("ATLASSIAN_API_TOKEN", "")
    if not api_token:
        raise SystemExit(
            "ATLASSIAN_API_TOKEN environment variable is not set.\n"
            "Generate at: https://id.atlassian.com/manage-profile/security/api-tokens\n"
            "Then: export ATLASSIAN_API_TOKEN='your-token-here'"
        )

    toml_path = _find_toml(explicit_path)
    with open(toml_path, "rb") as f:
        data = tomllib.load(f)

    if "api_token" in data.get("atlassian", {}):
        raise SystemExit(
            "Do not put api_token in .spike.toml — use the ATLASSIAN_API_TOKEN "
            "environment variable instead."
        )

    return SpikeConfig(
        atlassian=AtlassianConfig(**data["atlassian"]),
        confluence=ConfluenceConfig(**data.get("confluence", {})),
        jira=JiraConfig(**data.get("jira", {})),
        tickets=TicketsConfig(**data.get("tickets", {})),
        api_token=api_token,
    )
