# Welcome to Ally Chat

Ally Chat is a unique multi-user chat platform, with access to numerous top-quality AI models from providers including OpenAI, Anthropic, Meta, Google, Perplexity, xAI, DeepSeek, Alibaba Cloud, Open Router, Stability AI, and the Civitai community.

The app is fully open source. The service is free to use, with full functionality and generous limits; or you can pay if you feel like it!

This is perhaps the only AI chat service in the world where you can talk with all the most powerful AI models together in once place. You can get them talking to each other, and checking each-other's work. You can invite your friends to join in too.

Novel features include:

- private chat, and group chat with multiple AI and human participants
- very performant: create new rooms instantly, switch rooms instantly
- markdown-based chat with complete HTML support:
  (images, videos, embeds, diagrams, SVG, CSS, JS; everything)
- The chat is displayed in a secure cross-domain iframe,
  so JavaScript in the chat is not very dangerous.
- Graphviz and Mermaid diagrams, TeX Math, any sort of charts, etc.
- quality AI art with SDXL models, and assisted prompting; not censored
- a flexible room file system; private, public and group chats
- undo, retry and edit the chat history; archive or clear old chat rooms
- a numbered "chapters" system, to split up your chats for performance
- a "conductor" that manages AI responses based on mentions and cues
- a shared canvas for collaborative drawing using JavaScript
- AIs can teach you about the app, including all the models and agents
- a column view option, to make the most of your screen
- web, image, video search; programming tools such as Bash and Python
- the whole app is open source; you can potentially run it at home
- a cast of more than 100 characters, specialist agents, and tools
- custom agents and missions, adjust context and other settings mid-chat
- a wide range of styles, support for custom styles and JavaScript
- we value free speech, and include access to various uncensored AIs

Paying users enjoy higher limits, and custom feature requests. You can come up with good ideas, and help make Ally Chat awesome. 🔥

## Getting Help

Open the help widget by clicking the `i` button, and talk to Flashi. He is a quick and excellent helper!

In the help widget, AIs have access to a lot of info about the app and the cast of AI characters. In regular chat rooms, they don't.

Ally, Barbie and friends are good for friendly human-like chat. They aren't perfect, so retry if they say something weird!

Talk to Illu or Gema if you'd like to make images. They are image generation experts.

Emmy, Claude, Gemmi and others are very strong and capable to assist you with nearly anything.

You can also talk to Sam, the developer, or read the [User Guide](guide) for more information.

## How to Talk with AIs

1. To talk with a specific AI, use their name in your message:
   - At the start: "Ally, how are you?"
   - At the end: "Can you help me learn to use the app, Flashi?"
   - Using @: "@Illu, I want to draw a camel!"

2. Sometimes you need to "poke" the chat to get the next AI to respond.
   - When AIs are talking to each other...
   - Leave the message box empty.
   - Click "Poke" to let them continue.

   Example:

   > You: Illu, I'd like to draw a rainbow.
   >
   > Illu: <details><summary>Thinking</summary> ... </details>
   >
   >   Illy, landscape, grassland, mountains, (vibrant rainbow:1.5), (majestic mountains:1.2), lush grassland, scenic view, clear sky, sunny, peaceful, [use photo], lens flare, sunlight, bokeh NEGATIVE (deformed, blurry, bad anatomy:2), unrealistic, ugly, watermark [sets width=1344 height=768 hq=1.5 steps=30]
   >
   > ***[you press poke here]***
   >
   > Illy: [generates image]

3. Other Hints
   - If you don't use a name, the last person who spoke will respond
   - Sometimes the system may think you are talking to yourself, if you mention your own name or send two messages in a row. Try saying an AI's name.
   - Say "someone" or "anyone" to get a response from a random AI.
   - Say "everyone" to get multiple responses.

## Privacy

The [Ally Chat](Ally+Chat) room is public. Press the padlock icon at top left to switch to your private area, and press it again to return to the main chat room.

## Image Gen

IMPORTANT: The agents Illu (as distinct from Illy) and Gema are experts on image gen. We can talk to them to learn more about image gen prompting.

This asks Illy, an image gen AI, to draw a big dog, in a wider landscape image:

    Illy, big dog [use landscape]

This draws Cleo in a green dress in a ballroom, with her default cheery expression, at the age of 30, in a tall image. Try to get a full body shot by mentioning shoes or feet!

    Illy, [person Cleo "green dress" . 30], ballroom, (full body, heels:1.5)  [use portrait_tall]

## Examples of Advanced Syntax

### Markdown

The chat format is markdown, including tables, code, links, images, etc.

### HTML and SVG

We can safely embed any HTML or SVG:

<iframe width="560" height="315" src="https://www.youtube.com/embed/dQw4w9WgXcQ?si=wbdyVVoV5BaF7uqb"></iframe>

Don't quote such in backticks if you want them to render in the chat.

### TeX math

Inline math goes between dollar signs, like $ y = \sqrt{x} $.

Displayed math goes between double dollar signs:

$$ y = \sqrt{x} $$

### Graphviz

Please use transparent backgrounds and medium gray edges and edge text for better visibility in any theme, unless asked otherwise.

```dot
graph {
    bgcolor="transparent"
    node [style=filled, fillcolor="#808080"]
    edge [color="#808080"]
    A -- B -- C -- A
}
```

```dot
digraph G {
    bgcolor="transparent"
    node [style=filled, fillcolor="#808080"]
    edge [color="#808080"]
    A -> B;
    B -> C;
}
```

### Mermaid Diagrams

```mermaid
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#808080',
    'primaryTextColor': '#ffffff',
    'primaryBorderColor': '#404040',
    'lineColor': '#808080',
    'secondaryColor': '#808080',
    'tertiaryColor': '#808080'
  }
}}%%
flowchart TD
    A[Start] --> B{Decision?}

    B -->|Yes| C[Do something]
    B -->|No| D[Do something else]
    C --> E["End (or is it)?"]
    D --> E
```

Note: We need to quote labels that contain parentheses.

### Drawing an inline chart with uPlot, and our helper functions

Note that uPlot defaults to "time" on the x-axis, so turn that off unless needed.

<script src="https://cdn.jsdelivr.net/npm/uplot@1.6.24/dist/uPlot.iife.min.js"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/uplot@1.6.24/dist/uPlot.min.css">
<div id="smartphone_market_share_1"></div>

<script>
data = [
    [0, 1, 2, 3, 4],
    [22.1, 19.4, 13.3, 11.2, 7.8]
];

textColor = getCssVarColorHex("--text");
gridColor = hexColorWithOpacity(textColor, 0.1);
fillColor = hexColorWithOpacity(textColor, 0.05);

companies = ["Samsung", "Apple", "Xiaomi", "OPPO", "vivo"];

opts = {
    title: "Global Smartphone Market Share Q3 2023 (%)",
    width: 600,
    height: 300,
    series: [
        {
            label: "Company"
        },
        {
            label: "Market Share %",
            stroke: textColor,
            fill: fillColor,
            paths: uPlot.paths.bars({size: [0.6, 100]}),
        }
    ],
    scales: {
        x: {
            time: false,
            range: [-0.5, 4.5]
        }
    },
    axes: [
        {
            values: (self, splits) => splits.map(i => companies[i]),
            stroke: textColor,
            grid: {stroke: gridColor},
            size: 70  // Give more space for labels
        },
        {
            stroke: textColor,
            grid: {stroke: gridColor}
        }
    ]
};

uplot = new uPlot(opts, data, document.getElementById("smartphone_market_share_1"))
</script>

IMPORTANT:
- N.B. NOTE WELL! Please do NOT quote JavaScript in triple-backticks or indent the whole block if you want it to run in the browser, i.e. in the chat app.
- N.B. NOTE WELL! Please do NOT use `const` or `let` at the top level, as they will break other JavaScript code in other messages when we use the same variable names, e.g. iterating on code.
- Please use uPlot for charts where possible, unless another library or manual JS is requested. You need to pull in the required uPlot JavaScript and CSS first.
- Don't use the shared canvas (global canvas, ctx) unless requested, it's easier to use a fresh inline canvas.
- For graphics and interaction, it's better to use this direct method in the browser rather than one of the JavaScript agents, which cannot yet return images.
- If the user wants to see the code, they can enable our view -> code option.
- You can add canvases, divs, svg, etc inline in the chat as needed. Please use unique descriptive IDs when doing so.

### AI Artists
- Using the AI art models directly can be a bit technical. New users can talk to Illu and Gema, who have extensive knowledge about how to create good prompts, and all the options and settings that the models understand. Illu the "AI art prompting expert" is distinct from Illy the AI art model.
- **Illy**: High-quality image generation using Juggernaut XL, can draw every character.

### Search Agents
- **Goog**: Google web search
- **Gimg**: Google image search
- **UTube**: YouTube search

### Select Tools
- **Palc**: Calculator
- **Dogu**: Bash shell
- **Gido**: Python

Examples:

Palc, sqrt(2) / sin(pi/4)

Dogu, look wizard

Dogu, web-text https://beebom.com/cool-interesting-websites/

Gido, import html ; print(html.escape("&&&"))

### Side by Side Formatting

<style class="hide">
.doc-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(30rem, 1fr));
  gap: 1em;
  max-width: 63rem;
}
</style>

<div class="doc-container" markdown="1">

<div markdown="1">
# Welcome to Markdown!

Hello, world! This is markdown.
</div>
<div markdown="1">

```markdown
# Welcome to Markdown!

Hello, world! This is markdown.
```
</div>

<div markdown="1">
## Text Formatting

You can make text *italic*.
</div>
<div markdown="1">

```markdown
## Text Formatting

You can make text *italic*.
```
</div>
