import pytest
from spike_mcp.config import (
    AtlassianConfig,
    ConfluenceConfig,
    JiraConfig,
    SpikeConfig,
    TicketsConfig,
)


@pytest.fixture
def spike_config() -> SpikeConfig:
    return SpikeConfig(
        atlassian=AtlassianConfig(
            base_url="https://test.atlassian.net",
            email="test@example.com",
        ),
        confluence=ConfluenceConfig(space_key="ENG", parent_page_id="999"),
        jira=JiraConfig(
            project_key="PLAT",
            epic_issue_type="Epic",
            story_issue_type="Story",
            task_issue_type="Task",
            default_label="spike",
            story_points_field="customfield_10016",
            epic_link_field="customfield_10014",
        ),
        tickets=TicketsConfig(),
        api_token="test-token-abc",
    )
