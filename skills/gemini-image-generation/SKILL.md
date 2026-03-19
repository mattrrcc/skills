---
name: gemini-image-generation
description: Generate images using Google's Gemini API (gemini-3.1-flash-image-preview model). Use when users want to generate, create, or produce images via Gemini, or when they ask for AI-generated images using Google's API.
license: Complete terms in LICENSE.txt
---

# Gemini Image Generation

Generate images using Google's Gemini API with the `gemini-3.1-flash-image-preview` model. This skill produces images from text prompts and can also handle image editing with mixed text+image inputs.

## Prerequisites

- A Google AI API key set as the `GOOGLE_API_KEY` environment variable (or passed to the client)
- Python packages: `google-genai`, `Pillow`

Install dependencies:
```bash
pip install google-genai pillow
```

## Core Workflow

### Text-to-Image Generation

```python
from google import genai
from google.genai import types
from PIL import Image

client = genai.Client()

prompt = "A description of the image you want to generate"
response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[prompt],
)

for part in response.parts:
    if part.text is not None:
        print(part.text)
    elif part.inline_data is not None:
        image = part.as_image()
        image.save("generated_image.png")
```

### Image Editing (Text + Image Input)

```python
from google import genai
from google.genai import types
from PIL import Image

client = genai.Client()

# Load an existing image
reference_image = Image.open("input.png")

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[
        "Edit this image to add a sunset background",
        reference_image,
    ],
)

for part in response.parts:
    if part.text is not None:
        print(part.text)
    elif part.inline_data is not None:
        image = part.as_image()
        image.save("edited_image.png")
```

### Generation with Configuration

```python
from google import genai
from google.genai import types

client = genai.Client()

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=["A futuristic cityscape at dusk"],
    config=types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"],
    ),
)

for part in response.parts:
    if part.text is not None:
        print(part.text)
    elif part.inline_data is not None:
        image = part.as_image()
        image.save("output.png")
```

## Important Notes

- The response may contain both text and image parts — always iterate over `response.parts` and check each part's type.
- `part.as_image()` returns a PIL `Image` object that can be saved, displayed, or further processed.
- `part.inline_data` is present when the part contains image data; `part.text` is present for text.
- The model name is `gemini-3.1-flash-image-preview` — this is the image generation variant of Gemini Flash.
- When specifying `response_modalities`, use `["TEXT", "IMAGE"]` to get both text descriptions and generated images.
- For best results, write detailed, descriptive prompts that specify style, composition, lighting, and subject matter.

## Dependencies

```bash
pip install google-genai pillow
```
