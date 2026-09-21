import pytest
from ally import macro as subject

subject_name = subject.__name__


def test_empty_string():
    assert subject.process_macros("", {}) == ""


def test_no_macros():
    text = "Hello, world!\nThis is a test."
    assert subject.process_macros(text, {}) == text


def test_simple_true_condition():
    text = "<if show>\nvisible\n</if>"
    assert subject.process_macros(text, {"show": True}) == "visible"


def test_simple_false_condition():
    text = "<if show>\nvisible\n</if>"
    assert subject.process_macros(text, {"show": False}) == ""


def test_missing_var_is_falsy():
    text = "<if missing>\nshould not appear\n</if>"
    assert subject.process_macros(text, {}) == ""


def test_truthy_string_value():
    text = "<if name>\nhello\n</if>"
    assert subject.process_macros(text, {"name": "Alice"}) == "hello"


def test_falsy_empty_string():
    text = "<if name>\nhello\n</if>"
    assert subject.process_macros(text, {"name": ""}) == ""


def test_falsy_zero():
    text = "<if count>\nhas count\n</if>"
    assert subject.process_macros(text, {"count": 0}) == ""


def test_truthy_nonzero():
    text = "<if count>\nhas count\n</if>"
    assert subject.process_macros(text, {"count": 1}) == "has count"


def test_truthy_negative_number():
    text = "<if val>\nhas val\n</if>"
    assert subject.process_macros(text, {"val": -1}) == "has val"


def test_content_before_if_block():
    text = "before\n<if show>\nvisible\n</if>"
    assert subject.process_macros(text, {"show": True}) == "before\nvisible"


def test_content_after_if_block():
    text = "<if show>\nvisible\n</if>\nafter"
    assert subject.process_macros(text, {"show": True}) == "visible\nafter"


def test_content_around_false_if_block():
    text = "before\n<if show>\nvisible\n</if>\nafter"
    assert subject.process_macros(text, {"show": False}) == "before\nafter"


def test_multiple_lines_in_block():
    text = "<if show>\nline1\nline2\nline3\n</if>"
    assert subject.process_macros(text, {"show": True}) == "line1\nline2\nline3"


def test_multiple_lines_false():
    text = "<if show>\nline1\nline2\nline3\n</if>"
    assert subject.process_macros(text, {"show": False}) == ""


def test_nested_both_true():
    text = "<if outer>\n<if inner>\nnested\n</if>\n</if>"
    assert subject.process_macros(text, {"outer": True, "inner": True}) == "nested"


def test_nested_outer_false():
    text = "<if outer>\n<if inner>\nnested\n</if>\n</if>"
    assert subject.process_macros(text, {"outer": False, "inner": True}) == ""


def test_nested_inner_false():
    text = "<if outer>\n<if inner>\nnested\n</if>\n</if>"
    assert subject.process_macros(text, {"outer": True, "inner": False}) == ""


def test_nested_both_false():
    text = "<if outer>\n<if inner>\nnested\n</if>\n</if>"
    assert subject.process_macros(text, {"outer": False, "inner": False}) == ""


def test_nested_with_content_at_each_level():
    text = "<if outer>\nouter content\n<if inner>\ninner content\n</if>\n</if>"
    result = subject.process_macros(text, {"outer": True, "inner": True})
    assert result == "outer content\ninner content"


def test_nested_inner_false_outer_content_visible():
    text = "<if outer>\nouter content\n<if inner>\ninner content\n</if>\n</if>"
    result = subject.process_macros(text, {"outer": True, "inner": False})
    assert result == "outer content"


def test_sequential_blocks_both_true():
    text = "<if a>\nblock a\n</if>\n<if b>\nblock b\n</if>"
    result = subject.process_macros(text, {"a": True, "b": True})
    assert result == "block a\nblock b"


def test_sequential_blocks_first_true():
    text = "<if a>\nblock a\n</if>\n<if b>\nblock b\n</if>"
    result = subject.process_macros(text, {"a": True, "b": False})
    assert result == "block a"


def test_sequential_blocks_second_true():
    text = "<if a>\nblock a\n</if>\n<if b>\nblock b\n</if>"
    result = subject.process_macros(text, {"a": False, "b": True})
    assert result == "block b"


def test_sequential_blocks_both_false():
    text = "<if a>\nblock a\n</if>\n<if b>\nblock b\n</if>"
    result = subject.process_macros(text, {"a": False, "b": False})
    assert result == ""


def test_indented_tag_is_matched():
    text = "  <if show>\n  visible\n  </if>"
    result = subject.process_macros(text, {"show": True})
    assert result == "  visible"


def test_indented_content_preserved():
    text = "<if show>\n    indented content\n</if>"
    result = subject.process_macros(text, {"show": True})
    assert result == "    indented content"


def test_if_tag_not_in_output():
    text = "<if show>\nvisible\n</if>"
    result = subject.process_macros(text, {"show": True})
    assert "<if show>" not in result
    assert "</if>" not in result


def test_if_tag_not_in_output_false():
    text = "<if show>\nvisible\n</if>"
    result = subject.process_macros(text, {"show": False})
    assert "<if show>" not in result
    assert "</if>" not in result


def test_unmatched_if_no_crash():
    # Unclosed <if> — should not crash; content inside is included if truthy
    text = "<if show>\nvisible"
    result = subject.process_macros(text, {"show": True})
    assert result == "visible"


def test_unmatched_endif_no_crash():
    # Extra </if> without opening — should not crash (pop on empty stack is guarded)
    text = "before\n</if>\nafter"
    result = subject.process_macros(text, {})
    assert result == "before\nafter"


def test_single_line_no_newline():
    # A single line with no newline at all
    result = subject.process_macros("hello", {})
    assert result == "hello"


def test_var_name_single_char():
    text = "<if x>\nyes\n</if>"
    assert subject.process_macros(text, {"x": True}) == "yes"
    assert subject.process_macros(text, {"x": False}) == ""


def test_deeply_nested():
    text = (
        "<if a>\n"
        "<if b>\n"
        "<if c>\n"
        "deep\n"
        "</if>\n"
        "</if>\n"
        "</if>"
    )
    assert subject.process_macros(text, {"a": True, "b": True, "c": True}) == "deep"
    assert subject.process_macros(text, {"a": True, "b": True, "c": False}) == ""
    assert subject.process_macros(text, {"a": True, "b": False, "c": True}) == ""
    assert subject.process_macros(text, {"a": False, "b": True, "c": True}) == ""


@pytest.mark.parametrize("varname,value,expected", [
    ("flag", True, "yes"),
    ("flag", False, ""),
    ("flag", 1, "yes"),
    ("flag", 0, ""),
    ("flag", "hello", "yes"),
    ("flag", "", ""),
    ("flag", [], ""),
    ("flag", [1], "yes"),
    ("flag", None, ""),
])
def test_truthy_falsy_values(varname, value, expected):
    text = f"<if {varname}>\nyes\n</if>"
    assert subject.process_macros(text, {varname: value}) == expected


def test_returns_string():
    result = subject.process_macros("", {})
    assert isinstance(result, str)


def test_preserves_blank_lines_in_block():
    text = "<if show>\nline1\n\nline3\n</if>"
    result = subject.process_macros(text, {"show": True})
    assert result == "line1\n\nline3"


def test_multiple_vars_only_relevant_checked():
    text = "<if a>\nblock a\n</if>"
    # b is irrelevant here
    result = subject.process_macros(text, {"a": True, "b": False})
    assert result == "block a"
