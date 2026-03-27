from spike_mcp.templates import SPIKE_DOC_TEMPLATE, STORY_TEMPLATE, SYSTEM_PROMPT


def test_spike_doc_has_required_sections():
    for section in [
        "Overview",
        "Problem Statement",
        "Goals",
        "Proposed Solution",
        "Architecture Diagram",
        "Implementation Options",
        "Recommendation",
        "Epic",
        "Story",
        "References",
    ]:
        assert section in SPIKE_DOC_TEMPLATE, f"Missing section: {section}"


def test_spike_doc_has_mermaid_placeholder():
    assert "```mermaid" in SPIKE_DOC_TEMPLATE


def test_story_template_is_formattable():
    result = STORY_TEMPLATE.format(
        context="Background info",
        what="Implement the thing",
        acceptance_criteria="1. It works",
        out_of_scope="Nothing else",
        notes="TBD",
    )
    assert "Background info" in result
    assert "Implement the thing" in result
    assert "1. It works" in result


def test_system_prompt_research_first():
    assert "search_confluence" in SYSTEM_PROMPT
    assert "search_jira" in SYSTEM_PROMPT


def test_system_prompt_requires_mermaid():
    assert "mermaid" in SYSTEM_PROMPT.lower()


def test_system_prompt_confirm_before_write():
    assert "get_project_config" in SYSTEM_PROMPT
    assert "confirm" in SYSTEM_PROMPT.lower() or "confirmation" in SYSTEM_PROMPT.lower()


def test_system_prompt_fibonacci_scale():
    assert "fibonacci" in SYSTEM_PROMPT.lower() or "Fibonacci" in SYSTEM_PROMPT


def test_system_prompt_imperative_verb():
    assert "imperative" in SYSTEM_PROMPT.lower()
