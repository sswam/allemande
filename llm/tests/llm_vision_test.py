import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from PIL import Image
import base64

import llm_vision as subject

subject_name = subject.__name__

def test_is_url():
    assert subject.is_url("https://example.com/image.jpg") is True
    assert subject.is_url("http://example.com/image.jpg") is True
    assert subject.is_url("ftp://example.com/image.jpg") is True
    assert subject.is_url("not_a_url") is False
    assert subject.is_url("") is False
    assert subject.is_url("http://") is False

def test_encode_image_file():
    test_data = b"test image data"
    expected_encoding = base64.b64encode(test_data).decode("utf-8")

    with patch("builtins.open", mock_open(read_data=test_data)):
        assert subject.encode_image_file("test.jpg") == expected_encoding

    with pytest.raises(FileNotFoundError):
        subject.encode_image_file("nonexistent.jpg")

@pytest.mark.parametrize("width,height,max_pixels,max_short,max_long,expected", [
    (1000, 800, 500000, None, None, 0.7905694150420949),  # max pixels constraint
    (1000, 800, None, 400, None, 0.5),    # max short side constraint
    (1000, 800, None, None, 800, 0.8),    # max long side constraint
    (500, 400, 1000000, 800, 1000, 1.0),  # no constraints exceeded
    (0, 0, 1000, 1000, 1000, 1.0),        # degenerate case
])
def test_calculate_resize_factor(width, height, max_pixels, max_short, max_long, expected):
    result = subject.calculate_resize_factor(width, height, max_pixels, max_short, max_long)
    assert abs(result - expected) < 1e-10

def test_get_supported_image_mime_type():
    mock_img = MagicMock()

    # Test PNG
    mock_img.format = "PNG"
    assert subject.get_supported_image_mime_type(mock_img) == ("image/png", False)

    # Test JPEG
    mock_img.format = "JPEG"
    assert subject.get_supported_image_mime_type(mock_img) == ("image/jpeg", False)

    # Test invalid format
    mock_img.format = None
    with pytest.raises(ValueError):
        subject.get_supported_image_mime_type(mock_img)

@pytest.mark.parametrize("vendor,detail,expected_content", [
    ("openai", "auto", {"type": "image_url", "image_url": {"url": "https://example.com/img.jpg", "detail": "auto"}}),
    ("openai", "low", {"type": "image_url", "image_url": {"url": "https://example.com/img.jpg", "detail": "low"}}),
])
def test_format_image_url(vendor, detail, expected_content):
    result = subject.format_image("https://example.com/img.jpg", vendor, detail)
    assert result == expected_content

def test_format_message_for_vision_empty():
    message = {"role": "user", "content": "test"}
    assert subject.format_message_for_vision(message, "openai") == message

def test_format_message_for_vision_invalid_vendor():
    with pytest.raises(ValueError):
        subject.format_message_for_vision({"images": ["test.jpg"]}, "invalid_vendor")

@pytest.mark.parametrize("message,expected", [
    ({"content": "test"}, [{"type": "text", "text": "test"}]),
    ({"content": []}, []),
    ({}, []),
])
def test_handle_text_content(message, expected):
    content = []
    result = subject.handle_text_content(message, content)
    assert result == expected

@patch('PIL.Image.open')
def test_process_image_if_needed(mock_image_open):
    mock_img = MagicMock()
    mock_img.size = (100, 100)
    mock_img.mode = "RGB"
    mock_image_open.return_value = mock_img

    result = subject.process_image_if_needed(mock_img)
    assert result == mock_img  # No resize needed for small image

def test_format_message_for_vision_with_invalid_images():
    with pytest.raises(TypeError):
        subject.format_message_for_vision({"images": "not_a_list"}, "openai")


# Additional tests could be added for:
#
# 1. Performance testing of image processing
# 2. Testing with actual image files
# 3. Integration tests with different image formats
# 4. Memory usage tests for large images
# 5. Edge cases with corrupt or invalid images
