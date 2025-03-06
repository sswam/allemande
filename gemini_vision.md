```markdown
# Explore Vision Capabilities with the Gemini API

[Try a Colab notebook](link-to-colab-notebook) | [View notebook on GitHub](link-to-github-notebook)

Gemini models process images and videos, enabling many advanced developer use cases previously requiring domain-specific models.  Gemini's vision capabilities include:

* Captioning and answering questions about images
* Transcribing and reasoning over PDFs (up to 2 million tokens)
* Describing, segmenting, and extracting information from videos (up to 90 minutes long)
* Detecting objects in images and returning bounding box coordinates

Gemini was built to be multimodal, and we continue to expand its capabilities.


## Image Input

For images under 20MB, upload base64 encoded images or directly upload local files.


### Working with Local Images

Using the Python Imaging Library (Pillow):

```python
from google import genai
from google.genai import types
import PIL.Image

image = PIL.Image.open('/path/to/image.png')

client = genai.Client(api_key="GEMINI_API_KEY")
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=["What is this image?", image])

print(response.text)
```

### Base64 Encoded Images

Upload public image URLs as Base64 payloads:

```python
from google import genai
from google.genai import types
import requests

image_path = "https://goo.gle/instrument-img"
image = requests.get(image_path)

client = genai.Client(api_key="GEMINI_API_KEY")
response = client.models.generate_content(
    model="gemini-2.0-flash-exp",
    contents=["What is this image?",
              types.Part.from_bytes(data=image.content, mime_type="image/jpeg")])

print(response.text)
```

### Multiple Images

Prompt with multiple images (any supported format, including base64 or PIL):

```python
from google import genai
from google.genai import types
import pathlib
import PIL.Image
import requests

image_path_1 = "path/to/your/image1.jpeg"  # Replace with the actual path to your first image
image_path_2 = "path/to/your/image2.jpeg" # Replace with the actual path to your second image
image_url_1 = "https://goo.gle/instrument-img" # Replace with the actual URL to your third image

pil_image = PIL.Image.open(image_path_1)

b64_image = types.Part.from_bytes(
    data=pathlib.Path(image_path_2).read_bytes(),
    mime_type="image/jpeg"
)

downloaded_image = requests.get(image_url_1)

client = genai.Client(api_key="GEMINI_API_KEY")
response = client.models.generate_content(
    model="gemini-2.0-flash-exp",
    contents=["What do these images have in common?",
              pil_image, b64_image, downloaded_image])

print(response.text)
```

Note: Inline data calls lack features available through the File API (metadata, listing, deleting).


### Large Image Payloads

For payloads > 20MB, use the File API:

```python
from google import genai

client = genai.Client(api_key="GEMINI_API_KEY")

img_path = "/path/to/Cajun_instruments.jpg"
file_ref = client.files.upload(file=img_path)
print(f'{file_ref=}')

client = genai.Client(api_key="GEMINI_API_KEY")
response = client.models.generate_content(
    model="gemini-2.0-flash-exp",
    contents=["What can you tell me about these instruments?",
              file_ref])

print(response.text)
```

The File API allows storing up to 20GB per project (max 2GB per file, stored for 48 hours).


## OpenAI Compatibility

Integrate Gemini into existing OpenAI workflows by updating three lines of code and using your Gemini API key.  See the Image understanding example for Base64 payload code.


## Prompting with Images

This tutorial shows uploading images via the File API or inline data.


## Technical Details (Images)

Gemini 2.0 Flash, 1.5 Pro, and 1.5 Flash support a maximum of 3,600 image files.  Supported MIME types:

* `image/png`
* `image/jpeg`
* `image/webp`
* `image/heic`
* `image/heif`


### Tokens

* **Gemini 1.0 Pro Vision:** Each image = 258 tokens.
* **Gemini 1.5 Flash & 1.5 Pro:** Images ≤ 384 pixels in both dimensions = 258 tokens. Larger images are tiled (768x768 pixels each, 258 tokens/tile).
* **Gemini 2.0 Flash:** Images ≤ 384 pixels in both dimensions = 258 tokens. Larger images are tiled (768x768 pixels each, 258 tokens/tile).


### Best Results

* Rotate images correctly before uploading.
* Avoid blurry images.
* For single images, place the text prompt after the image.


## Capabilities

This section details Gemini's vision capabilities, including object detection and bounding boxes.


### Get a Bounding Box for an Object

Gemini models return bounding box coordinates as relative widths/heights in [0, 1], scaled by 1000 and converted to integers (representing a 1000x1000 pixel version). Convert these to your original image's dimensions.

```python
from google import genai

client = genai.Client(api_key="GEMINI_API_KEY")

prompt = (
  "Return a bounding box for each of the objects in this image "
  "in [ymin, xmin, ymax, xmax] format.")

response = client.models.generate_content(
  model="gemini-1.5-pro",
  contents=[sample_file_1, prompt]) #sample_file_1 needs to be defined

print(response.text)
```

Bounding boxes enable object detection and localization in images and video.


### Key Benefits

* **Simple:** Easily integrate object detection.
* **Customizable:** Produce bounding boxes based on custom instructions (without training a custom model).


### Technical Details

* **Input:** Prompt and associated images/video frames.
* **Output:** Bounding boxes in `[y_min, x_min, y_max, x_max]` format (top-left origin). Coordinates are normalized to 0-1000.
* **Visualization:** AI Studio users see bounding boxes plotted in the UI.  For Python developers, see the 2D spatial understanding notebook or the experimental 3D pointing notebook.


### Normalize Coordinates

To convert normalized coordinates to pixel coordinates:

1. Divide each coordinate by 1000.
2. Multiply x-coordinates by the original image width.
3. Multiply y-coordinates by the original image height.

See the Object Detection cookbook example for more details.

```markdown
<!--The error in the results file is because `lint_md` is not a standard markdown linting function.  A markdown linter would need to be specified to resolve this.-->
```
