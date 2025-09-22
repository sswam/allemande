# Ally Chat Showcase

Welcome to a showcase of Ally Chat's format features! This example will cover basic text, advanced features like images and AI interaction, and code/table display.

This shows how our **bb format** works - it combines markdown, HTML, and playscript-style chat using tabs.

## Basic Text Formatting

This is normal text.

This is *italicized* text.

This is **bold** text.

This is ***bold and italicized*** text.

This is `inline code`.

## Lists

### Unordered List

- Item 1
- Item 2
   - Subitem 2.1
   - Subitem 2.2
- Item 3

### Ordered List

1. First item
2. Second item
3. Third item

## Links

Here's a link to [Allemande AI](https://allemande.ai)!

## Images

Here's an image from an URL:
![An Allemande AI Logo](https://allemande.ai/assets/logo-44b87380.png)

Here's an Image generated using AI and inserted into the bb format:
![#2692827117 Jily, a cat wearing a hat [L3] ---- a cat wearing a hat](a-cat-wearing-a-hat-sets-hq-1-width-1024-height-1024-hires-0-0-steps-15_2692827117.jpg)

## Blockquotes

> This is a blockquote. It can span multiple lines.
> This is the second line of the blockquote.

## Code Blocks

```python
def greet(name):
    print(f"Hello, {name}!")

greet("Ally Chat User")
```

## Tables

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Row 1, Col 1 | Row 1, Col 2 | Row 1, Col 3 |
| Row 2, Col 1 | Row 2, Col 2 | Row 2, Col 3 |
| Row 3, Col 1 | Row 3, Col 2 | Row 3, Col 3 |

## Horizontal Rule

---

## AI Interaction Example

Sam:	Loni, can you generate a landscape image with a castle on a hill, using Jily?
Loni:	Certainly Sam! Here's a prompt to generate a landscape with a castle on a hill
	```
	Jily, masterpiece, landscape, castle on a hill, fantasy, rolling hills, trees, sky, cmnt <lora:Monet_XL:0.9> <lora:boring:-1> [L3]
	```
Hily:	![#1122334455 masterpiece, landscape, castle on a hill, fantasy, rolling hills, trees, sky, cmnt &lt;lora:Monet_XL:0.9&gt; &lt;lora:boring:-1&gt; [L3]](castle-landscape.jpg)

## Advanced Features

### Removing Messages

Sam:	<ac rm=2>  *(removes message #2)*

### Styling

Ally:	Hello there, here's how to get my attention! <i class="bi-camera-3d-fill"></i>

### Tool Listing

Sam:	Loraz, style
Loraz:	## style

	| <lora:name:weight> | required trigger words | info |
	|--|--|--|
	| <lora:hands_sdxl:1> | perfection style | better hands and feet for SDXL models |
	| <lora:hands_pony:1> | perfection style | better hands and feet for PonyXL models |
	| <lora:Monet_XL:0.9> | cmnt | Monet oil painting style |
	| <lora:van-gogh-sdxl:0.7> | style of Vincent van Gogh | Van Gogh oil painting style, weight 0.5 to 1, NOTE: may need to omit trigger for male subjects, to avoid drawing Vincent himself! |
	| <lora:ncpy43 style:1> | ncpy43 style, watercolor sketch, illustration, watercolor painting | watercolor sketch style (Pony) |

### Thinking
Loni:	<think>
	I am planning my next move!
	</think>
	Here's how to do it...

### Playing with MS paint style on a cat

Sam:	```
	Jily, a cat, MSPaint drawing, <lora:SDXL_MSPaint_Portrait:1> [L3]
	```
Jily:	![#348593746 Jily, a cat, MSPaint drawing, &lt;lora:SDXL_MSPaint_Portrait:1&gt; [L3] ---- a cat, MSPaint drawing, &lt;lora:SDXL_MSPaint_Portrait:1&gt;](a-cat-mspaint.jpg)

Sam:	@me Testing

Sam:	Hey, Ally, what's up?
