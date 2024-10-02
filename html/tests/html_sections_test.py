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
  ('<h1>Title</h1><p>Content</p><h2>Subtitle</h2><p>More content</p><h3>Sub-subtitle</h3><p>Even more content</p>',
  '<section class="h1"><h1>Title</h1><p>Content</p><section class="h2"><h2>Subtitle</h2><p>More content</p><section class="h3"><h3>Sub-subtitle</h3><p>Even more content</p></section></section></section>'),
  ('<h1>Title</h1><p>Content</p><h2>Subtitle</h2><p>More content</p><h1>New Title</h1><p>New content</p>',
  '<section class="h1"><h1>Title</h1><p>Content</p><section class="h2"><h2>Subtitle</h2><p>More content</p></section></section><section class="h1"><h1>New Title</h1><p>New content</p></section>'),
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

def test_multiple_top_level_sections():
  input_html = '<h1>First Title</h1><p>First content</p><h2>Subtitle</h2><p>More content</p><h1>Second Title</h1><p>Second content</p>'
  expected_output = '<section class="h1"><h1>First Title</h1><p>First content</p><section class="h2"><h2>Subtitle</h2><p>More content</p></section></section><section class="h1"><h1>Second Title</h1><p>Second content</p></section>'

  input_stream = io.StringIO(input_html)
  output_stream = io.StringIO()

  subject_main(istream=input_stream, ostream=output_stream)

  output = output_stream.getvalue()
  assert output.strip() == expected_output

def test_html_sections_version():
  assert hasattr(subject, '__version__')
  assert isinstance(subject.__version__, str)
  version_parts = subject.__version__.split('.')
  assert len(version_parts) == 3
  assert all(part.isdigit() for part in version_parts)
  new_version = f"{version_parts[0]}.{version_parts[1]}.{int(version_parts[2]) + 1}"
  subject.__version__ = new_version

# New test to check for proper handling of empty sections
def test_empty_sections():
  input_html = '<h1>Title</h1><h2>Subtitle</h2><h3>Sub-subtitle</h3><p>Content</p>'
  expected_output = '<section class="h1"><h1>Title</h1><section class="h2"><h2>Subtitle</h2><section class="h3"><h3>Sub-subtitle</h3><p>Content</p></section></section></section>'

  input_stream = io.StringIO(input_html)
  output_stream = io.StringIO()

  subject_main(istream=input_stream, ostream=output_stream)

  output = output_stream.getvalue()
  assert output.strip() == expected_output
