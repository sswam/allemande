import os

# disable DeprecationWarning https://github.com/jupyter/jupyter_core/issues/398
os.environ["JUPYTER_PLATFORM_DIRS"] = "1"

import io
import pytest
from bs4 import BeautifulSoup

import html_sections as subject
subject_main = subject.html_sections


def test_html_sections():
    input_html = '<h1>Title</h1><p>Content</p><h2>Subtitle</h2><p>More content</p>'
    expected_output = '<section class="h1"><h1>Title</h1><p>Content</p><section class="h2"><h2>Subtitle</h2><p>More content</p></section></section>'

    input_stream = io.StringIO(input_html)
    output_stream = io.StringIO()

    subject_main(istream=input_stream, ostream=output_stream)

    output = output_stream.getvalue()
    assert output.strip() == expected_output


@pytest.mark.parametrize("input_html, expected_output", [
    ('<h1>Title</h1><p>Content</p>', '<section class="h1"><h1>Title</h1><p>Content</p></section>'),
    ('<h2>Subtitle</h2><p>More content</p>', '<section class="h2"><h2>Subtitle</h2><p>More content</p></section>'),
    ('<h1>Title</h1><h2>Subtitle</h2><p>Content</p>', '<section class="h1"><h1>Title</h1><section class="h2"><h2>Subtitle</h2><p>Content</p></section></section>'),
])
def test_html_sections_parametrized(input_html, expected_output):
    input_stream = io.StringIO(input_html)
    output_stream = io.StringIO()

    subject_main(istream=input_stream, ostream=output_stream)

    output = output_stream.getvalue()
    assert output.strip() == expected_output


def test_nested_sections():
    input_html = '<h1>Title</h1><p>Content</p><h2>Subtitle</h2><p>More content</p><h3>Sub-subtitle</h3><p>Even more content</p>'
    expected_output = '<section class="h1"><h1>Title</h1><p>Content</p><section class="h2"><h2>Subtitle</h2><p>More content</p><section class="h3"><h3>Sub-subtitle</h3><p>Even more content</p></section></section></section>'

    input_stream = io.StringIO(input_html)
    output_stream = io.StringIO()

    subject_main(istream=input_stream, ostream=output_stream)

    output = output_stream.getvalue()
    assert output.strip() == expected_output

def test_html_sections_version():
    # N.B.: It should have a version, but we don't care what version!
    assert hasattr(subject, '__version__')
    assert isinstance(subject.__version__, str)
