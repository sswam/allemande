## Claude Vision: Quick Reference for Image Integration

### Basics and Limits

*   Up to 20 images via claude.ai, 100 via API.
*   Max image size:
    *   8000x8000 px, or rejected
    *   If more than 20 images in one API request, this limit is 2000x2000 px.

### Image Resizing

*   Resize images to no more than 1.15 megapixels and within 1568 pixels in both dimensions.
*   Very small images under 200 pixels on any given edge may degrade performance.

### Supported Image Formats

*   JPEG, PNG, GIF, WebP

### API Examples

**Base64-encoded image:**

```python
import anthropic
import base64
import httpx

# For base64-encoded images
image1_url = "https://upload.wikimedia.org/wikipedia/commons/a/a7/Camponotus_flavomarginatus_ant.jpg"
image1_media_type = "image/jpeg"
image1_data = base64.standard_b64encode(httpx.get(image1_url).content).decode("utf-8")

client = anthropic.Anthropic()
message = client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": image1_media_type,
                        "data": image1_data,
                    },
                },
                {
                    "type": "text",
                    "text": "Describe this image."
                }
            ],
        }
    ],
)
print(message)
```

**URL-based image:**

```python
import anthropic

client = anthropic.Anthropic()
message = client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "url",
                        "url": "https://upload.wikimedia.org/wikipedia/commons/a/a7/Camponotus_flavomarginatus_ant.jpg",
                    },
                },
                {
                    "type": "text",
                    "text": "Describe this image."
                }
            ],
        }
    ],
)
print(message)
```
