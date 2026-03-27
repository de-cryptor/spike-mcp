from spike_mcp.confluence import _inline_md, _md_to_storage, _strip_html


def test_inline_md_bold():
    assert _inline_md("**hello**") == "<strong>hello</strong>"


def test_inline_md_italic():
    assert _inline_md("*world*") == "<em>world</em>"


def test_inline_md_bold_italic():
    assert _inline_md("***hi***") == "<strong><em>hi</em></strong>"


def test_inline_md_code():
    assert _inline_md("`foo`") == "<code>foo</code>"


def test_inline_md_plain():
    assert _inline_md("plain text") == "plain text"


def test_md_to_storage_h1():
    assert _md_to_storage("# Title") == "<h1>Title</h1>"


def test_md_to_storage_h3():
    assert _md_to_storage("### Sub") == "<h3>Sub</h3>"


def test_md_to_storage_paragraph():
    assert _md_to_storage("Hello world") == "<p>Hello world</p>"


def test_md_to_storage_bullet_list():
    result = _md_to_storage("- item one\n- item two")
    assert result == "<ul><li>item one</li><li>item two</li></ul>"


def test_md_to_storage_numbered_list():
    result = _md_to_storage("1. first\n2. second")
    assert result == "<ol><li>first</li><li>second</li></ol>"


def test_md_to_storage_code_block():
    md = "```python\nprint('hi')\n```"
    result = _md_to_storage(md)
    assert 'ac:name="code"' in result
    assert 'ac:name="language">python' in result
    assert "print('hi')" in result
    assert "<![CDATA[" in result


def test_md_to_storage_mermaid_block():
    md = "```mermaid\ngraph TD\n    A --> B\n```"
    result = _md_to_storage(md)
    assert 'ac:name="mermaid"' in result
    assert "graph TD" in result
    assert "<![CDATA[" in result
    assert 'ac:name="code"' not in result


def test_md_to_storage_cdata_injection_escaped():
    """]]> inside a code block must be escaped so the CDATA section stays valid."""
    md = "```python\nx = a[0]]]>evil\n```"
    result = _md_to_storage(md)
    # The ]]> in the body must be split into ]]]]><![CDATA[> to prevent early CDATA termination
    assert "]]]]><![CDATA[>" in result


def test_md_to_storage_blank_lines_skipped():
    result = _md_to_storage("line one\n\nline two")
    assert "<p>line one</p>" in result
    assert "<p>line two</p>" in result


def test_strip_html_removes_tags():
    html = "<h1>Title</h1><p>Some <strong>text</strong> here</p>"
    assert _strip_html(html) == "Title Some text here"


def test_strip_html_collapses_whitespace():
    assert _strip_html("<p>  lots   of   space  </p>") == "lots of space"
