# Changelog

All notable changes to this project will be documented in this file.
Bump `version` in `pyproject.toml`, add an entry here, then `git tag vX.Y.Z` to trigger a release.

## [Unreleased]

## [0.1.0] — 2025-03-27

### Added
- Initial release
- MCP tools: `search_confluence`, `get_confluence_page`, `search_jira`, `write_spike_doc`, `create_epic`, `create_story`, `create_task`, `get_project_config`
- `spike_workflow` MCP prompt — invoke with `/mcp__spike-mcp__spike_workflow` to load workflow instructions
- `.spike.toml` project config with search order: explicit path → cwd → git root walk-up → `~/.spike.toml`
- Confluence markdown → storage format conversion (headings, lists, bold/italic, fenced code, Mermaid diagrams)
- Jira markdown → Atlassian Document Format (ADF) JSON conversion
- Next-gen and classic Jira project support (auto-detects via `parent` field fallback)
- CDATA injection protection for Mermaid/code blocks in Confluence pages
