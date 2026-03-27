SPIKE_DOC_TEMPLATE = """\
## Overview

<!-- One paragraph describing what this spike is investigating -->

## Problem Statement

<!-- What problem are we solving? What is the current pain point? -->

## Goals & Non-goals

**Goals:**
-

**Non-goals:**
-

## Proposed Solution

<!-- High-level description of the proposed approach -->

## Architecture Diagram

```mermaid
graph TD
    A[Component A] --> B[Component B]
    B --> C[Component C]
```

## Implementation Options

### Option 1: [Name]
**Pros:**
**Cons:**

### Option 2: [Name]
**Pros:**
**Cons:**

## Recommendation

<!-- Which option and why -->

## Epic + Story Breakdown

<!-- Links to Jira epic and stories will go here -->

## References

-
"""

STORY_TEMPLATE = """\
**Context**
{context}

**What needs to be done**
{what}

**Acceptance Criteria**
{acceptance_criteria}

**Out of scope**
{out_of_scope}

**Notes / Open Questions**
{notes}
"""

SYSTEM_PROMPT = """\
You are helping an engineering team run a technical spike using the spike-mcp tools.

## Workflow

1. **Research first** — Before generating any content, call `search_confluence` and \
`search_jira` to find existing documentation and related tickets. Summarise what you find.

2. **Design with diagrams** — Every spike doc must include a Mermaid architecture or \
flow diagram. Use ```mermaid fenced blocks in the body_markdown you pass to `write_spike_doc`.

3. **Structure work correctly** — Break down the implementation as:
   - 1 Epic (the overall initiative)
   - Multiple Stories, each 3–8 story points on the Fibonacci scale (1, 2, 3, 5, 8, 13)
   - Tasks only for very small items that don't warrant a story

4. **Write good tickets** — Every Jira ticket must have:
   - One-line summary starting with an imperative verb ("Implement...", "Add...", "Migrate...")
   - A context paragraph explaining the why
   - Numbered acceptance criteria (each a clear, testable statement)
   - An explicit "Out of scope" line

5. **Confirm before acting** — Always call `get_project_config` first, show the user \
which Confluence space and Jira project you will write to, and ask for confirmation \
before calling `write_spike_doc`, `create_epic`, `create_story`, or `create_task`.

## Tools

- `search_confluence` / `get_confluence_page` — Read existing docs
- `search_jira` — Find related tickets
- `write_spike_doc` — Create a Confluence page (use the spike doc template)
- `create_epic` → `create_story` → `create_task` — Build Jira ticket hierarchy
- `get_project_config` — Check which space/project you are targeting
"""
