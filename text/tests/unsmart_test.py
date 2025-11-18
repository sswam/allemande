#!/usr/bin/env python3

import io
import pytest

import unsmart as subject  # type: ignore

subject_name = subject.__name__


def test_version():
    """Test that version is defined."""
    assert hasattr(subject, '__version__')
    assert isinstance(subject.__version__, str)


def test_split_code_segments_no_code():
    """Test splitting text with no code blocks."""
    text = "Just plain text"
    result = list(subject._split_code_segments(text))
    assert len(result) == 1
    assert result[0] == (False, "Just plain text")


def test_split_code_segments_with_fenced_code():
    """Test splitting text with fenced code blocks."""
    text = "Before ```code here``` after"
    result = list(subject._split_code_segments(text))
    assert len(result) == 3
    assert result[0] == (False, "Before ")
    assert result[1] == (True, "```code here```")
    assert result[2] == (False, " after")


def test_split_code_segments_with_inline_code():
    """Test splitting text with inline backticks."""
    text = "Before `code` after"
    result = list(subject._split_code_segments(text))
    assert len(result) == 3
    assert result[0] == (False, "Before ")
    assert result[1] == (True, "`code`")
    assert result[2] == (False, " after")


def test_split_code_segments_empty():
    """Test splitting empty string."""
    text = ""
    result = list(subject._split_code_segments(text))
    assert len(result) == 1
    assert result[0] == (False, "")


def test_split_code_segments_multiple_blocks():
    """Test splitting text with multiple code blocks."""
    text = "`inline` and ```fenced``` code"
    result = list(subject._split_code_segments(text))
    assert len(result) == 5
    assert result[1] == (True, "`inline`")
    assert result[3] == (True, "```fenced```")


def test_is_likely_code_with_assignment():
    """Test code detection with assignment operators."""
    assert subject._is_likely_code("x = 5") is True
    assert subject._is_likely_code("a == b") is True
    assert subject._is_likely_code("x != y") is True


def test_is_likely_code_with_syntax():
    """Test code detection with syntax characters."""
    assert subject._is_likely_code("function() { }") is True
    assert subject._is_likely_code("array[0]") is True


def test_is_likely_code_with_keywords():
    """Test code detection with programming keywords."""
    assert subject._is_likely_code("if x > 5") is True
    assert subject._is_likely_code("def function()") is True
    assert subject._is_likely_code("import module") is True
    assert subject._is_likely_code("const x = 5") is True


def test_is_likely_code_plain_text():
    """Test code detection with plain text."""
    assert subject._is_likely_code("Just plain text") is False
    assert subject._is_likely_code("Hello, world!") is False
    assert subject._is_likely_code("") is False


def test_unsmart_emdash():
    """Test converting em/en dashes to hyphens."""
    assert subject.unsmart("Hello\u2014world") == "Hello-world"
    assert subject.unsmart("Hello\u2013world") == "Hello-world"
    assert subject.unsmart("Hello\u2015world") == "Hello-world"


def test_unsmart_quotes():
    """Test converting smart quotes to straight quotes."""
    assert subject.unsmart("\u201cHello\u201d") == '"Hello"'
    assert subject.unsmart("Say \u201chello\u201d") == 'Say "hello"'


def test_unsmart_apostrophes():
    """Test converting smart apostrophes to straight quotes."""
    assert subject.unsmart("It\u2019s") == "It's"
    assert subject.unsmart("\u2018Hello\u2019") == "'Hello'"


def test_unsmart_empty_string():
    """Test unsmart with empty string."""
    assert subject.unsmart("") == ""


def test_unsmart_preserves_code_blocks():
    """Test that code blocks are preserved."""
    text = "Text with \u2018quotes\u2019 and `code\u2019s here` more text"
    result = subject.unsmart(text)
    assert "`code\u2019s here`" in result
    assert "Text with 'quotes' and" in result


def test_unsmart_preserves_fenced_code():
    """Test that fenced code blocks are preserved."""
    text = "Before\n```\ncode\u2019s\u2014here\n```\nAfter\u2019s"
    result = subject.unsmart(text)
    assert "```\ncode\u2019s\u2014here\n```" in result
    assert "After's" in result


def test_unsmart_with_flags():
    """Test unsmart with selective conversion flags."""
    text = "It\u2019s \u201chello\u201d\u2014world"

    result = subject.unsmart(text, emdash=False, quotes=True, apostrophes=True)
    assert result == "It's \"hello\"\u2014world"

    result = subject.unsmart(text, emdash=True, quotes=False, apostrophes=True)
    assert result == "It's \u201chello\u201d-world"

    result = subject.unsmart(text, emdash=True, quotes=True, apostrophes=False)
    assert result == "It\u2019s \"hello\"-world"


def test_unsmart_quotes_only_affects_double_quotes():
    """Test that quotes=True only converts double quotes, not single quotes."""
    assert subject.unsmart("\u2018hello\u2019", quotes=True, apostrophes=False) == "\u2018hello\u2019"
    assert subject.unsmart("\u201chello\u201d", quotes=True, apostrophes=False) == '"hello"'


def test_smart_emdash():
    """Test converting hyphens to em dashes."""
    assert subject.smart("Hello -- world") == "Hello \u2014 world"
    assert subject.smart("Hello --- world") == "Hello \u2014 world"
    assert subject.smart("Hello - world") == "Hello \u2014 world"


def test_smart_quotes():
    """Test converting straight quotes to smart quotes."""
    assert subject.smart('"Hello"') == "\u201cHello\u201d"
    assert subject.smart('Say "hello"') == "Say \u201chello\u201d"
    assert subject.smart('"Hello" and "world"') == "\u201cHello\u201d and \u201cworld\u201d"


def test_smart_apostrophes():
    """Test converting straight apostrophes to smart apostrophes."""
    assert subject.smart("It's") == "It\u2019s"
    assert subject.smart("don't") == "don\u2019t"
    assert subject.smart("'90s") == "\u201990s"


def test_smart_empty_string():
    """Test smart with empty string."""
    assert subject.smart("") == ""


def test_smart_preserves_code_blocks():
    """Test that code blocks are preserved in smart mode."""
    text = "Text with 'quotes' and `code's here` more text"
    result = subject.smart(text)
    assert "`code's here`" in result
    assert "Text with \u2018quotes\u2019 and" in result


def test_smart_preserves_fenced_code():
    """Test that fenced code blocks are preserved in smart mode."""
    text = "Before\n```\ncode's--here\n```\nAfter's"
    result = subject.smart(text)
    assert "```\ncode's--here\n```" in result
    assert "After\u2019s" in result


def test_smart_with_flags():
    """Test smart with selective conversion flags."""
    text = "It's \"hello\" -- world"

    result = subject.smart(text, emdash=False, quotes=True, apostrophes=True)
    assert " -- " in result
    assert "\u201c" in result

    result = subject.smart(text, emdash=True, quotes=False, apostrophes=True)
    assert "\u2014" in result
    assert '"' in result

    result = subject.smart(text, emdash=True, quotes=True, apostrophes=False)
    assert "\u2014" in result
    assert "\u201c" in result


def test_smart_skips_likely_code():
    """Test that smart mode skips segments that look like code."""
    text = "Normal text x = 5 more text"
    result = subject.smart(text)
    assert "x = 5" in result


def test_unsmart_cli_unsmart_mode():
    """Test CLI in unsmart mode."""
    input_text = "It\u2019s \u201chello\u201d\u2014world"
    input_stream = io.StringIO(input_text)
    output_stream = io.StringIO()

    subject.unsmart_cli(input_stream, output_stream, smart_mode=False)

    result = output_stream.getvalue()
    assert result == "It's \"hello\"-world"


def test_unsmart_cli_smart_mode():
    """Test CLI in smart mode."""
    input_text = "It's \"hello\" -- world"
    input_stream = io.StringIO(input_text)
    output_stream = io.StringIO()

    subject.unsmart_cli(input_stream, output_stream, smart_mode=True)

    result = output_stream.getvalue()
    assert "It\u2019s" in result
    assert "\u201c" in result
    assert "\u2014" in result


def test_unsmart_cli_empty_input():
    """Test CLI with empty input."""
    input_stream = io.StringIO("")
    output_stream = io.StringIO()

    subject.unsmart_cli(input_stream, output_stream)

    assert output_stream.getvalue() == ""


def test_unsmart_cli_with_flags():
    """Test CLI with selective conversion flags."""
    input_text = "It\u2019s \u201chello\u201d\u2014world"
    input_stream = io.StringIO(input_text)
    output_stream = io.StringIO()

    subject.unsmart_cli(input_stream, output_stream,
                    smart_mode=False, emdash=False, quotes=True, apostrophes=True)

    result = output_stream.getvalue()
    assert result == "It's \"hello\"\u2014world"


def test_roundtrip_simple():
    """Test that unsmart -> smart -> unsmart preserves meaning."""
    original = "It's \"hello\" world"
    smart_text = subject.smart(original)
    unsmart_text = subject.unsmart(smart_text)
    assert unsmart_text == original


def test_roundtrip_with_code():
    """Test round-trip with code blocks."""
    original = "Text `code's here` more"
    smart_text = subject.smart(original)
    unsmart_text = subject.unsmart(smart_text)
    assert "`code's here`" in smart_text
    assert "`code's here`" in unsmart_text


@pytest.mark.parametrize("text", [
    "",     # empty string
    " ",    # single space
    "\n",   # single newline
    "abc",  # no special characters
    "---",  # only dashes
    '"""',  # only quotes
    "'''",  # only apostrophes
])
def test_unsmart_edge_cases(text):
    """Test unsmart with edge cases."""
    result = subject.unsmart(text)
    assert isinstance(result, str)


@pytest.mark.parametrize("text", [
    "",     # empty string
    " ",    # single space
    "\n",   # single newline
    "abc",  # no special characters
    "---",  # only dashes
    '"""',  # only quotes
    "'''",  # only apostrophes
])
def test_smart_edge_cases(text):
    """Test smart with edge cases."""
    result = subject.smart(text)
    assert isinstance(result, str)


def test_nested_quotes():
    """Test handling of nested quotes."""
    text = '"She said \'hello\' to me"'
    result = subject.smart(text)
    assert "\u201c" in result or "\u2018" in result


def test_multiline_text():
    """Test handling of multiline text."""
    text = "Line one\u2014with dash\nLine two\u2019s apostrophe"
    result = subject.unsmart(text)
    assert result == "Line one-with dash\nLine two's apostrophe"


def test_unicode_preservation():
    """Test that other Unicode characters are preserved."""
    text = "Hello \u00e9 café\u2019s"
    result = subject.unsmart(text)
    assert "\u00e9" in result
    assert "café's" in result
