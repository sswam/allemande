import re
import pytest
from unittest.mock import MagicMock

from ally import soma as subject

subject_name = subject.__name__


def test_normalize_replacement():
    assert subject.normalize_replacement("$1") == r"\1"
    assert subject.normalize_replacement("$1 and $2") == r"\1 and \2"
    assert subject.normalize_replacement("no captures here") == "no captures here"
    assert subject.normalize_replacement("$10") == r"\10"
    assert subject.normalize_replacement("") == ""


def test_parse_macro_call_no_macros():
    """Test that macro calls are left unchanged when macro not in dict."""
    match = re.match(r"(.*)", "test")
    result = subject.parse_macro_call(r"\unknown(arg)", match, {})
    assert result == r"\unknown(arg)"


def test_parse_macro_call_with_macro():
    """Test that macro calls are executed correctly."""
    def mock_macro(match, arg):
        return f"PROCESSED_{arg}"

    macros = {"test": mock_macro}
    match = re.match(r"(.*)", "test")
    result = subject.parse_macro_call(r"\test(hello)", match, macros)
    assert result == "PROCESSED_hello"


def test_parse_macro_call_multiple_args():
    """Test macro with multiple arguments."""
    def mock_macro(match, arg1, arg2):
        return f"{arg1}_{arg2}"

    macros = {"join": mock_macro}
    match = re.match(r"(.*)", "test")
    result = subject.parse_macro_call(r"\join(foo, bar)", match, macros)
    assert result == "foo_bar"


def test_parse_macro_call_with_capture_groups():
    """Test that $N is replaced with capture groups."""
    def mock_macro(match, arg):
        return f"[{arg}]"

    macros = {"wrap": mock_macro}
    match = re.match(r"(\w+) (\w+)", "hello world")
    result = subject.parse_macro_call(r"\wrap($1)", match, macros)
    assert result == "[hello]"

    result = subject.parse_macro_call(r"\wrap($2)", match, macros)
    assert result == "[world]"


def test_parse_macro_call_with_quotes():
    """Test that quotes are stripped from arguments."""
    def mock_macro(match, arg):
        return arg

    macros = {"echo": mock_macro}
    match = re.match(r"(.*)", "test")

    result = subject.parse_macro_call(r'\echo("quoted")', match, macros)
    assert result == "quoted"

    result = subject.parse_macro_call(r"\echo('single')", match, macros)
    assert result == "single"


def test_parse_macro_call_escape_backslash():
    """Test that regular backslashes are preserved."""
    match = re.match(r"(.*)", "test")
    result = subject.parse_macro_call(r"\\test", match, {})
    assert result == r"\\test"


def test_parse_macro_call_empty_args():
    """Test macro call with no arguments."""
    def mock_macro(match):
        return "NO_ARGS"

    macros = {"noargs": mock_macro}
    match = re.match(r"(.*)", "test")
    result = subject.parse_macro_call(r"\noargs()", match, macros)
    assert result == "NO_ARGS"


def test_apply_mappings_empty():
    """Test with empty mapping."""
    assert subject.apply_mappings("text", {}) == "text"
    assert subject.apply_mappings("", {}) == ""


def test_apply_mappings_no_match():
    """Test when no patterns match."""
    mapping = {r"foo": "bar"}
    assert subject.apply_mappings("hello world", mapping) == "hello world"


def test_apply_mappings_simple_replacement():
    """Test simple pattern replacement."""
    mapping = {r"hello": "goodbye"}
    assert subject.apply_mappings("hello world", mapping) == "goodbye world"


def test_apply_mappings_with_capture_groups():
    """Test replacement with capture groups."""
    mapping = {r"(\w+) (\w+)": r"$2 $1"}
    assert subject.apply_mappings("hello world", mapping) == "world hello"


def test_apply_mappings_multiple_patterns():
    """Test multiple patterns applied in parallel."""
    mapping = {
        r"foo": "FOO",
        r"bar": "BAR",
    }
    assert subject.apply_mappings("foo and bar", mapping) == "FOO and BAR"


def test_apply_mappings_with_macro():
    """Test replacement with macro call."""
    def upper_macro(match, arg):
        return arg.upper()

    macros = {"upper": upper_macro}
    mapping = {r"(\w+)": r"\upper($1)"}

    result = subject.apply_mappings("hello", mapping, macros)
    assert result == "HELLO"


def test_apply_mappings_overlapping_patterns():
    """Test that first matching pattern wins in parallel application."""
    mapping = {
        r"hello world": "BOTH",
        r"hello": "HELLO",
    }
    result = subject.apply_mappings("hello world", mapping)
    assert result == "BOTH"


def test_sub_empty():
    """Test with empty text and configs."""
    assert subject.sub("", []) == ""
    assert subject.sub("text", []) == "text"
    assert subject.sub("", [{}]) == ""


def test_sub_single_pass():
    """Test simple single-pass transformation."""
    configs = [{r"hello": "goodbye"}]
    result = subject.sub("hello world", configs)
    assert result == "goodbye world"


def test_sub_recursive():
    """Test recursive application."""
    configs = [
        {r"A": "B"},
        {r"B": "C"},
    ]
    result = subject.sub("A", configs)
    assert result == "C"


def test_sub_multiple_configs():
    """Test with multiple config dictionaries."""
    configs = [
        {r"foo": "bar"},
        {r"bar": "baz"},
    ]
    result = subject.sub("foo", configs)
    assert result == "baz"


def test_sub_no_change():
    """Test that it stops when text stops changing."""
    configs = [{r"hello": "hello"}]
    result = subject.sub("hello", configs)
    assert result == "hello"


def test_sub_max_depth():
    """Test that max_depth prevents infinite loops."""
    configs = [{r"(.+)": r"$1x"}]

    result = subject.sub("start", configs, max_depth=3)
    assert result == "startxxx"


def test_sub_with_macros():
    """Test sub with macro dictionary."""
    def mock_macro(match, arg):
        return arg.upper()

    macros = {"up": mock_macro}
    configs = [{r"(\w+)": r"\up($1)"}]

    result = subject.sub("hello", configs, macros)
    assert result == "HELLO"


def test_sub_complex_case():
    """Test a more complex transformation with nested macro expansion."""
    def col_macro(match, person1, person2):
        return f"collaborated({person1}, {person2})"

    def person_macro(match, name):
        return f"Person[{name}]"

    macros = {"col": col_macro, "person": person_macro}

    configs = [{
        r"(.*?) COL (.*)": r"\col(\person($1), \person($2))",
    }]

    result = subject.sub("Alice COL Bob", configs, macros)
    assert result == "collaborated(Person[Alice], Person[Bob])"


@pytest.mark.parametrize("text, config, expected", [
    ("", {}, ""),
    ("x", {}, "x"),
    ("hello", {r"hello": "hi"}, "hi"),
    ("foo bar", {r"foo": "FOO", r"bar": "BAR"}, "FOO BAR"),
    ("123", {r"\d+": "NUM"}, "NUM"),
])
def test_sub_parametrized(text, config, expected):
    """Parametrized tests for various inputs."""
    result = subject.sub(text, [config] if config else [])
    assert result == expected


def test_sub_case_insensitive():
    """Test case-insensitive pattern matching."""
    configs = [{r"(?i)hello": "HI"}]
    assert subject.sub("Hello", configs) == "HI"
    assert subject.sub("HELLO", configs) == "HI"
    assert subject.sub("hello", configs) == "HI"


def test_sub_multiline():
    """Test with multiline text."""
    configs = [{r"^line": "LINE"}]
    text = "line1\nline2\nline3"
    result = subject.sub(text, configs)
    assert result == "LINE1\nLINE2\nLINE3"


def test_apply_mappings_none_macros():
    """Test that None macros_dict is handled correctly."""
    mapping = {r"hello": "hi"}
    result = subject.apply_mappings("hello", mapping, None)
    assert result == "hi"


def test_sub_filter_empty_configs():
    """Test that empty/None configs are filtered out."""
    configs = [{r"a": "A"}, None, {}, {r"b": "B"}]
    result = subject.sub("a b", configs)
    assert result == "A B"


def test_parse_macro_call_nested():
    """Test nested macro calls are now expanded recursively."""
    def inner(match, arg):
        return f"[{arg}]"

    def outer(match, arg):
        return f"<{arg}>"

    macros = {"inner": inner, "outer": outer}
    match = re.match(r"(.*)", "test")

    result = subject.parse_macro_call(r"\outer(\inner(x))", match, macros)
    assert result == "<[x]>"


def test_apply_mappings_special_chars():
    """Test with special regex characters."""
    mapping = {r"\$\d+": "MONEY"}
    result = subject.apply_mappings("$100", mapping)
    assert result == "MONEY"


def test_sub_zero_max_depth():
    """Test with max_depth=0."""
    configs = [{r"a": "b"}]
    result = subject.sub("a", configs, max_depth=0)
    assert result == "a"


def test_sub_one_max_depth():
    """Test with max_depth=1 - applies all configs once then stops."""
    configs = [{r"a": "b"}, {r"b": "c"}]
    result = subject.sub("a", configs, max_depth=1)
    assert result == "c"
