from spike_mcp.jira import _inline_adf, _md_to_adf


def test_inline_adf_plain_text():
    assert _inline_adf("hello world") == [{"type": "text", "text": "hello world"}]


def test_inline_adf_bold():
    nodes = _inline_adf("**bold**")
    assert nodes[0]["text"] == "bold"
    assert {"type": "strong"} in nodes[0]["marks"]


def test_inline_adf_italic():
    nodes = _inline_adf("*italic*")
    assert nodes[0]["text"] == "italic"
    assert {"type": "em"} in nodes[0]["marks"]


def test_inline_adf_bold_italic():
    nodes = _inline_adf("***both***")
    assert nodes[0]["text"] == "both"
    assert {"type": "strong"} in nodes[0]["marks"]
    assert {"type": "em"} in nodes[0]["marks"]


def test_inline_adf_code():
    nodes = _inline_adf("`code`")
    assert nodes[0]["text"] == "code"
    assert {"type": "code"} in nodes[0]["marks"]


def test_inline_adf_mixed():
    nodes = _inline_adf("Hello **world** and *you*")
    texts = [n["text"] for n in nodes]
    assert "Hello " in texts
    assert "world" in texts
    assert " and " in texts
    assert "you" in texts


def test_md_to_adf_paragraph():
    adf = _md_to_adf("Hello world")
    assert adf["type"] == "doc"
    assert adf["version"] == 1
    assert adf["content"][0]["type"] == "paragraph"
    assert adf["content"][0]["content"][0]["text"] == "Hello world"


def test_md_to_adf_heading():
    adf = _md_to_adf("## Section")
    node = adf["content"][0]
    assert node["type"] == "heading"
    assert node["attrs"]["level"] == 2
    assert node["content"][0]["text"] == "Section"


def test_md_to_adf_bullet_list():
    adf = _md_to_adf("- item one\n- item two")
    node = adf["content"][0]
    assert node["type"] == "bulletList"
    assert len(node["content"]) == 2
    assert node["content"][0]["type"] == "listItem"
    assert node["content"][0]["content"][0]["type"] == "paragraph"


def test_md_to_adf_ordered_list():
    adf = _md_to_adf("1. first\n2. second")
    node = adf["content"][0]
    assert node["type"] == "orderedList"
    assert len(node["content"]) == 2


def test_md_to_adf_code_block_with_language():
    adf = _md_to_adf("```python\nprint('hi')\n```")
    node = adf["content"][0]
    assert node["type"] == "codeBlock"
    assert node["attrs"]["language"] == "python"
    assert node["content"][0]["text"] == "print('hi')"


def test_md_to_adf_code_block_no_language():
    adf = _md_to_adf("```\nsome code\n```")
    node = adf["content"][0]
    assert node["type"] == "codeBlock"
    assert node["attrs"] == {}


def test_md_to_adf_skips_blank_lines():
    adf = _md_to_adf("line one\n\nline two")
    assert len(adf["content"]) == 2
    assert adf["content"][0]["content"][0]["text"] == "line one"
    assert adf["content"][1]["content"][0]["text"] == "line two"
