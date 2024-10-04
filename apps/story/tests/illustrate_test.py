import pytest
from illustrate import check_markdown_image, check_html_image

def test_check_markdown_image():
    line = '![Alt text](image.jpg){width=100 height=200}'
    result = check_markdown_image(line, 300, 400)
    assert result == ('Alt text', 'image.jpg', 100, 200)

def test_check_markdown_image_default_size():
    line = '![Alt text](image.jpg)'
    result = check_markdown_image(line, 300, 400)
    assert result == ('Alt text', 'image.jpg', 300, 400)

def test_check_html_image():
    line = '<img alt="alt text" src="image.jpg" width="100" height="200">'
    result = check_html_image(line, 300, 400)
    assert result == ('alt text', 'image.jpg', 100, 200)

def test_check_html_image_default_size():
    line = '<img alt="alt text" src="image.jpg">'
    result = check_html_image(line, 300, 400)
    assert result == ('alt text', 'image.jpg', 300, 400)
