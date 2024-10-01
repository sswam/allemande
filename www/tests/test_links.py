import os

# disable DeprecationWarning https://github.com/jupyter/jupyter_core/issues/398
os.environ["JUPYTER_PLATFORM_DIRS"] = "1"

import io
import pytest
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup

import links as subject
subject_main = subject.links

@pytest.fixture
def sample_html():
    return """
    <html>
    <head>
        <link rel="stylesheet" href="style.css">
        <script src="script.js"></script>
    </head>
    <body>
        <a href="https://example.com">Example</a>
        <img src="image.jpg" alt="Sample Image">
        <video src="video.mp4"></video>
        <iframe src="https://youtube.com/embed/123"></iframe>
        <frame src="frame.html"></frame>
    </body>
    </html>
    """

@pytest.mark.parametrize("base_url, link, expected", [
    ("https://example.com", "https://example.com/page", True),
    ("https://example.com", "https://another.com", False),
])
def test_is_internal_link(base_url, link, expected):
    assert subject.is_internal_link(base_url, link) == expected

@pytest.mark.parametrize("base_url, link, expected", [
    ("https://example.com/parent/", "https://example.com/parent/child", True),
    ("https://example.com/parent/", "https://example.com/other", False),
])
def test_is_under_parent_directory(base_url, link, expected):
    assert subject.is_under_parent_directory(base_url, link) == expected

def test_extract_resources(sample_html):
    soup = BeautifulSoup(sample_html, 'html.parser')
    base_url = "https://example.com"
    resource_types = ['links', 'images', 'css', 'scripts', 'videos', 'iframes', 'frames']

    resources = subject.extract_resources(soup, base_url, resource_types)

    assert len(resources) == 7
    assert ('link', 'https://example.com', 'Example', 'body > a:nth-child(1)') in resources
    assert ('image', 'https://example.com/image.jpg', 'Sample Image', 'body > img:nth-child(2)') in resources
    assert ('css', 'https://example.com/style.css', '', 'head > link:nth-child(1)') in resources
    assert ('script', 'https://example.com/script.js', '', 'head > script:nth-child(2)') in resources
    assert ('video', 'https://example.com/video.mp4', '', 'body > video:nth-child(3)') in resources
    assert ('iframe', 'https://youtube.com/embed/123', '', 'body > iframe:nth-child(4)') in resources
    assert ('frame', 'https://example.com/frame.html', '', 'body > frame:nth-child(5)') in resources

@pytest.mark.parametrize("options, expected_count", [
    ({"no_links": True}, 6),
    ({"images": True}, 1),
    ({"css": True}, 1),
    ({"scripts": True}, 1),
    ({"videos": True}, 1),
    ({"iframes": True}, 1),
    ({"frames": True}, 1),
    ({"all": True}, 7),
])
def test_links_resource_types(sample_html, options, expected_count):
    input_stream = io.StringIO(sample_html)
    output_stream = io.StringIO()

    subject_main("https://example.com", istream=input_stream, ostream=output_stream, **options)

    output = output_stream.getvalue()
    assert len(output.strip().split('\n')) == expected_count

@pytest.mark.parametrize("option, expected_in_output", [
    ({"tag_type": True}, ["link\t", "image\t", "css\t", "script\t", "video\t", "iframe\t", "frame\t"]),
    ({"extract_text": True}, ["Example", "Sample Image"]),
    ({"css_path": True}, ["body > a:nth-child(1)", "body > img:nth-child(2)"]),
])
def test_links_output_options(sample_html, option, expected_in_output):
    input_stream = io.StringIO(sample_html)
    output_stream = io.StringIO()

    subject_main("https://example.com", istream=input_stream, ostream=output_stream, all=True, **option)

    output = output_stream.getvalue()
    for expected in expected_in_output:
        assert expected in output

def test_links_tsv_headers(sample_html):
    input_stream = io.StringIO(sample_html)
    output_stream = io.StringIO()

    subject_main("https://example.com", istream=input_stream, ostream=output_stream, all=True, tsv_headers=True, tag_type=True, extract_text=True, css_path=True)

    output = output_stream.getvalue().split('\n')
    assert output[0] == "Type\tURL\tText\tCSS Path"

@pytest.mark.parametrize("option, expected_count", [
    ({"same_site": True}, 6),
    ({"under_parent": True}, 6),
])
def test_links_filtering(sample_html, option, expected_count):
    input_stream = io.StringIO(sample_html)
    output_stream = io.StringIO()

    subject_main("https://example.com", istream=input_stream, ostream=output_stream, all=True, **option)

    output = output_stream.getvalue()
    assert len(output.strip().split('\n')) == expected_count

def test_links_css_selector(sample_html):
    input_stream = io.StringIO(sample_html)
    output_stream = io.StringIO()

    subject_main("https://example.com", istream=input_stream, ostream=output_stream, all=True, css_selector="body")

    output = output_stream.getvalue()
    assert len(output.strip().split('\n')) == 5  # Excludes resources in <head>

def test_links_markdown_input():
    markdown_input = """
    # Title
    [Link](https://example.com)
    ![Image](image.jpg)
    """
    input_stream = io.StringIO(markdown_input)
    output_stream = io.StringIO()

    subject_main("https://example.com", istream=input_stream, ostream=output_stream)

    output = output_stream.getvalue()
    assert "https://example.com" in output
    assert "https://example.com/image.jpg" in output

@patch('logging.Logger.warning')
def test_links_no_resources_found(mock_warning):
    empty_input = "<html></html>"
    input_stream = io.StringIO(empty_input)
    output_stream = io.StringIO()

    subject_main("https://example.com", istream=input_stream, ostream=output_stream)

    mock_warning.assert_called_with("No resources found matching the specified criteria.")

if __name__ == "__main__":
    pytest.main([__file__])

# Based on the provided `links.py` and the style of `test_hello_py.py`, I'll create a comprehensive `test_links.py` file that thoroughly tests all options and features of the `links.py` module. Here's the `test_links.py` file:

# This `test_links.py` file thoroughly tests the `links.py` module, covering all options and features. Here's a breakdown of the tests:
#
# 1. We test the helper functions `is_internal_link` and `is_under_parent_directory`.
# 2. We test the `extract_resources` function with all resource types.
# 3. We test the main `links` function with various combinations of options for resource types, output formatting, and filtering.
# 4. We test the CSS selector functionality.
# 5. We test Markdown input handling.
# 6. We test the warning message when no resources are found.
#
# The tests use parameterization to cover multiple scenarios efficiently. They also mock the logging functionality to test the warning message.
#
# This test suite should provide comprehensive coverage of the `links.py` module's functionality.

