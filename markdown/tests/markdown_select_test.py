import io
import pytest
from typing import Any
from unittest.mock import patch

import markdown_select as subject  # type: ignore

subject_name = subject.__name__

def test_extract_links_empty():
    """Test extracting links from empty text."""
    assert list(subject.extract_links("")) == []

def test_extract_links_no_matches():
    """Test text with no links or images."""
    text = "Plain text without any links or images"
    assert list(subject.extract_links(text)) == []

@pytest.mark.parametrize("markdown, expected", [
    ("[link](url)", [('link', 'url', 'link')]),
    ("![image](url)", [('image', 'url', 'image')]),
    ("[](url)", [('link', 'url', '')]),
    ("![](url)", [('image', 'url', '')]),
])
def test_extract_links_basic(markdown, expected):
    """Test basic link and image extraction."""
    assert list(subject.extract_links(markdown)) == expected

def test_extract_links_multiple():
    """Test extracting multiple links and images."""
    text = """
    Here's a [link](http://example.com) and an ![image](img.jpg).
    Another [link with spaces](http://test.com/path) here.
    """
    expected = [
        ('image', 'img.jpg', 'image'),
        ('link', 'http://example.com', 'link'),
        ('link', 'http://test.com/path', 'link with spaces'),
    ]
    assert sorted(list(subject.extract_links(text))) == sorted(expected)

def test_process_markdown_empty():
    """Test processing empty markdown."""
    input_stream = io.StringIO("")
    output_stream = io.StringIO()

    subject.process_markdown(input_stream, output_stream)
    assert output_stream.getvalue() == ""

@pytest.mark.parametrize("markdown, images, links, expected", [
    ("[link](url) ![img](pic)", True, False, "pic\timg\n"),
    ("[link](url) ![img](pic)", False, True, "url\tlink\n"),
    ("[link](url) ![img](pic)", False, False, "link\turl\tlink\nimage\tpic\timg\n"),
])
def test_process_markdown_filters(markdown, images, links, expected):
    """Test different output filters."""
    input_stream = io.StringIO(markdown)
    output_stream = io.StringIO()

    subject.process_markdown(input_stream, output_stream, images=images, links=links)
    assert output_stream.getvalue() == expected

def test_process_markdown_empty_urls():
    """Test handling of empty URLs."""
    markdown = "[empty]() ![also empty]()"
    input_stream = io.StringIO(markdown)
    output_stream = io.StringIO()

    subject.process_markdown(input_stream, output_stream)
    assert output_stream.getvalue() == ""

def test_process_markdown_complex():
    """Test processing complex markdown with mixed content."""
    markdown = """
    # Header
    [Link 1](http://example.com)
    Some text with an ![inline image](img.jpg) and
    another [link](http://test.com) here.
    """
    input_stream = io.StringIO(markdown)
    output_stream = io.StringIO()

    subject.process_markdown(input_stream, output_stream)
    expected = (
        "link\thttp://example.com\tLink 1\n"
        "image\timg.jpg\tinline image\n"
        "link\thttp://test.com\tlink\n"
    )
    assert sorted(output_stream.getvalue().split('\n')) == sorted(expected.split('\n'))

def test_setup_args():
    """Test argument setup."""
    mock_arg = lambda *args, **kwargs: None
    subject.setup_args(mock_arg)  # Should not raise any exceptions
