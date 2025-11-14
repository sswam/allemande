# Ally Chat User Guide v0.1.2

## Overview

Open-source multi-user chat platform with AI models from OpenAI, Anthropic, Meta, Google, Perplexity, xAI, DeepSeek, Alibaba, Mistral, and others. Features private/group chat, AI vision, image generation, web search, programming tools, and 1000+ characters/agents.

Service is free with generous limits. [Demo video](https://allemande.ai/demo) | [Support us](https://www.patreon.com/allychat)

**Contact Sam for access and demo/tour.**

## Rules & Usage

**Content Rules:**
- Main public rooms: MA15+ max
- No doxxing, hate-speech, copyright infringement
- See [Terms of Service](/terms)

**Free Usage:**
- Unlimited text chat and image generation
- May limit expensive model overuse
- Requested: participate in public chat, give feedback, or contribute

## Room System

**Room Types:**
- `username/*` - Private chats (lowercase username)
- `username` - Personal public room (you have mod rights)
- Other top-level - Public rooms
- `foldername/` - Folder view (trailing slash)

**Navigation:**
- Edit room name at top to switch/create rooms
- Click username (top-right) repeatedly to cycle through: private chat → folder → public room → `/` → Ally Chat
- Advanced mode: <i class="bi-compass"></i> nav menu, <i class="bi-folder"></i> parent folder button

**Examples (user "alice"):**
- Private: `alice/chat`, `alice/thoughts`
- Public: `alice`
- Folders: `alice/`, `/`

## Learning the App

- Read [Quick Intro](/intro)
- Talk to **Aidi** (specialized for new users) or **Loni** (simple chat that routes to other agents)
- **Illu** - Image generation expert
- **Yenta** - Introduces characters/agents
- AIs in help widget see this guide; main "Ally Chat" room has basic info; other rooms don't
- **Aidi** and **Assi** have access to concise guide in all rooms
- Red dot (top-right) = disconnected, reload page

## Conductor (Response Rules)

1. Capitalized @mentions invoke: `hey Ally, ...` or `I like ally, Barbie` (Barbie responds)
2. No mention → last non-user speaker responds
3. Empty message <i class="bi-hand-index-thumb"></i> **Poke** → continue conversation
4. Lowercase mention = no invoke: `hey ally, what do you think?`
5. `@me` or `@I` = no AI response
6. `@anyone` = random AI; `@everyone` = multiple AIs
7. Multiple: `@Ally, @Barbie, @Cloe`
8. Silent invoke: `-@Ally`

**Poke Function:**
- Send button becomes Poke when message empty
- Continues conversation or prompts next AI
- Some characters initiate in empty rooms

## Markdown & Rich Format

- Standard [markdown](/markdown): *italics*, **bold**, headings, images, links, code, tables
- TeX math: `$ y = \sqrt{x} $` inline, `$$ ... $$` displayed
- Graphviz: ` ```dot ... ``` ` or ` ```digraph ... ``` `
- Mermaid: ` ```mermaid ... ``` `
- Full HTML: audio, video, iframe, canvas, SVG, CSS, JavaScript
- Chat renders in secure cross-domain iframe

## AI Vision

Vision models: OpenAI, Anthropic, Google (e.g., Illu, Emmy, Flashi, Gemmi, Claude)

**Enable in your room:**
1. Advanced mode: <i class="bi-eye"></i> View → <i class="bi-lightbulb"></i>
2. <i class="bi-gear"></i> Options → set **images** to 1+
3. Upload image or have one in history
4. Talk to vision-capable character
5. **Set images to 0 when done** (improves speed, reduces cost)

## Image Generation

**Quick Syntax:**
```
Jily, big dog [L]
Jily, [person "Cloe" "green dress" . "30"], ballroom, (full body, heels:1.5) [P3]
```

**Person Macro:** `[person "Name" "clothes" "emotion" "age"]`
- Use `.` for default, `-` for none
- Example: `[person "Ally" . - "adult 40"]`

**Quality Settings:**
- `[S0-4]` Square, `[P0-4]` Portrait, `[L0-4]` Landscape
- `[T0-4]` Tall, `[W0-4]` Wide
- Higher number = higher quality

**Tips:**
- Talk to **Illu** or **Gema** to learn prompting
- Mention shoes/feet for full body shots
- Poke repeatedly for multiple variations
- Add "rating safe" for SFW with Poni/Coni models

## Image Viewer

Tap/click image to zoom:
- Exit: tap center / Esc / Q / Enter
- Browse: tap left/right edges / arrow keys
- Fullscreen: tap top / F
- Zoom toggle: tap bottom / M
- Download: long-press / right-click / Shift/Ctrl/Alt+click

## Tool Agents

Non-LLM agents (search, programming, image gen): say name, then exact command. Nothing else.

**Examples:**
```
Dogu, fortune
Goog, search terms
Gimg, cat pictures
Palc, 2 + 2
Gido, print("Hello")
```

## Missions & Context

**Mission Priority (highest first):**
1. `roomname.agentname.m` - Room-specific agent
2. `roomname.m` - Room-specific
3. `mission.agentname.m` - Folder agent
4. `mission.m` - Folder-wide
5. Custom mission (room options)
6. Agent default

**Settings:**
- `context` - Recent messages AI sees
- `lines` - Max output lines (local models)
- `images` - Recent images AI sees (0=off)
- `mission_pos` - Injection position (+/- from start/end, default -8)

## Auto-Play

<i class="bi-play"></i> **Auto** button modes:
- Normal: Natural conversation
- Shift+click: Rapid-fire
- Ctrl+click: Slow/contemplative

## Editing & Moderation

**Edit Messages** (room owners only):
1. <i class="bi-pencil"></i> **Edit** in moderator tools
2. Make changes
3. <i class="bi-check-lg"></i> **Save** or <i class="bi-arrow-counterclockwise"></i> **Reset**
- `Alt+T` indent, `Shift+Alt+T` dedent
- <i class="bi-clock-history"></i> view edit history

**Archive** (<i class="bi-archive"></i>): Moves to `archive/roomname-YYYY-MM-DD-HHMMSS`, creates new empty room

**Clear** (<i class="bi-trash3"></i>): Permanent deletion (no undo)

## JavaScript in Chat

**IMPORTANT:**
- Don't wrap in backticks if you want it to execute
- Don't use `const`/`let` at top level (breaks iteration)
- Use uPlot for charts unless requested otherwise
- Shared canvas: `canvas`, `ctx`, `h` variables available
- Don't change canvas dimensions; draw in top-left by default
- Use saturated colors, medium gray, or `--text` CSS variable
- Use unique descriptive IDs for elements

**Helper Functions:**
- `getCssVarColorHex(varName)` - Get CSS color
- `hexColorWithOpacity(hex, opacity)` - Add transparency

**uPlot Charts:**
```html
<script src="https://cdn.jsdelivr.net/npm/uplot@1.6.24/dist/uPlot.iife.min.js"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/uplot@1.6.24/dist/uPlot.min.css">
```

## AI Models

| Creator | Model | Name | Context | Max Out | Notes |
|---------|-------|------|---------|---------|-------|
| Meta | Llama 3.1 8B | Ally* | 4K | 4K | Small, creative, human-like (most characters) |
| Meta | Llama 3.3 70B | Ellyn | 128K | 2K | Stronger, creative |
| Meta | Llama 4 Scout | Skout | 512K | 512K | Fast new open model |
| Meta | Llama 4 Maverick | Mavi | 256K | 256K | Powerful, low cost |
| Anthropic | Claude 3.5 Haiku | Clia | 200K | 8K | Fast, affordable |
| Anthropic | Claude 3.5 Sonnet | Claude | 200K | 8K/128K | Powerful, reliable |
| Anthropic | Claude 3.7 Sonnet | Claudia | 200K | 8K/128K | Creative role-play |
| Anthropic | Claude 4.5 Sonnet | Clauden | 200K | 8K/128K | Most powerful, extended thinking |
| Anthropic | Claude 4.1 Opus | Claudo | 200K | 8K/128K | Top reasoning, extended thinking |
| Google | Gemini 2.0 Flash Lite | Lite | 1M | 8K | Fastest, economical |
| Google | Gemini 2.0 Flash | Flasho | 1M | 8K | Fast, minimal censorship |
| Google | Gemini 2.5 Flash | Flashi | 1M | 8K | Fast, very capable |
| Google | Gemini 2.5 Pro | Gemmi | 1M | 64K | Powerful reasoning |
| OpenAI | GPT-4.1-mini | Dav | 128K | 15K | Fast, affordable |
| OpenAI | GPT-4.1 | Emmy | 1M | 32K | Versatile |
| OpenAI | o4-mini | Fermi | 200K | 100K | Fast reasoning |
| OpenAI | o3 | Grace | 200K | 100K | Top reasoning |
| OpenAI | GPT-5-nano | Heis | 400K | 128K | Fastest GPT-5 |
| OpenAI | GPT-5-mini | Heise | 400K | 128K | Cost-efficient GPT-5 |
| OpenAI | GPT-5 | Heisen | 400K | 128K | Best coding/agentic |
| OpenAI | gpt-oss-20b | Gos | 128K | 128K | Open-weight, low latency |
| OpenAI | gpt-oss-120b | Goss | 128K | 128K | Powerful open-weight |
| Perplexity | Sonar | Sona | 128K | 8K | Fast online, live data |
| Perplexity | Sonar Reasoning | Sonari | 128K | 8K | Online reasoning |
| Perplexity | Sonar Pro | Sagi | 200K | 8K | High-performance online |
| Perplexity | Sonar Reasoning Pro | Sageri | 128K | 8K | Complex online reasoning |
| xAI | Grok 2 | Grok | 128K | 128K | Helpful, humorous |
| xAI | Grok 3 | Rocki | 128K | 128K | Helpful, humorous |
| xAI | Grok 4 | Anni | 256K | 256K | Helpful, humorous |
| DeepSeek | Chat V3 | Dese | 64K | 8K | Creative, intelligent |
| DeepSeek | Chat V3.1 | Desee | 64K | 8K | Creative, extra smarts |
| DeepSeek | Reasoner R1 | Deseri | 64K | 8K | Strong reasoning |
| Alibaba | QwQ 32B | Qwen | 128K | 128K | Capable reasoning |
| Mistral | Large 2411 | Misti | 128K | 128K | General reasoning |
| Mistral+ | Venice Uncensored | Veni | 33K | 33K | Dolphin Mistral 24B, uncensored |
| MoonshotAI | Kimi K2 0905 | Kimi | 262K | 262K | 1T param MoE, reasoning/tools |
| Z.AI | GLM 4.6 | Glimi | 205K | 205K | Agentic, reasoning, coding |

**Image Models:**
- **Jily** (Juggernaut XL v9) - Realistic/artistic
- **Hily** (HelloWorld XL) - Realistic/fantasy/concept
- **Poni** (AutismMix Confetti) - Anime (NSFW tendencies)
- **Coni** (CyberRealistic Pony) - Realistic (NSFW tendencies)

### Censorship Levels

- **Claude**: No NSFW engagement
- **OpenAI/xAI**: Limited NSFW
- **Gemini/DeepSeek/Mistral**: Any NSFW topic
- **Llama**: Practically uncensored
- **Venice**: Fully uncensored

Don't jailbreak censored models (may violate ToS). Use less censored alternatives or ask permission to experiment.

## Characters & Agents

### Main Characters (Llama 3.1 8B, human-like)
**Female:** Ally (Asian/European, blonde), Barbie (Greek/Italian, black curls), Cloe (European, blonde), Dali (African/European), Emmie (Hispanic/Mediterranean), Fenny (auburn), Gabby (Indian), Hanni (Native American/Hawaiian), Nixie (cyber mods, green eyes), Akane, Soli, Eira, Nalani, Rozie

**Male:** Amir (Middle Eastern), Bast (Caribbean), Cal (Persian/African American), Dante (Mexican), Ezio (Scandinavian), Felix (Irish), Gari (Russian), Haka (Japanese), Callam (pirate), Kai, Jackson

**Allie:** Ally using stronger 70B model

### Specialists
- **Aidi**, **Assi** - Tech support, new user guides (has full/concise guide in all rooms)
- **Loni**, **Lori** - Simple routing agents
- **Pixi** - Art prompt crafting
- **Sia** - Chat summarization
- **Sio** - Structured markdown summaries
- **Nova**, **Novi** - Master narrators
- **Brie** - Creative brainstorming
- **Atla** - Environment/setting design
- **Pliny** - Plot specialist
- **Morf** - Game Master
- **Illu** (Google), **Gema** (Google) - Art prompting experts
- **Poli** (Google) - Translation
- **Summi**, **Summar** (Google) - Summarization
- **Clu** (Anthropic), **Emm** (OpenAI) - Concise variants
- **Vega** (Anthropic), **Zeno** (OpenAI) - Academic focus
- **Chaz** - Character designer
- **Jessi** - Comedian
- **Nicc**, **Sal** - Pizza shop agents
- **Yenta** - Character introductions

### Base Models
Direct access to models (minimal/no prompting): Ellie, Ellyn, Skout, Mavi, Claude, Clauden, Claudo, Clia, Emmy, Dav, Grace, Fermi, Heisen, Heise, Heis, Gos, Goss, Flasho, Flashi, Lite, Gemmi, Grok, Rocki, Anni, Dese, Desee, Deseri, Qwen, Misti, Veni, Kimi, Glimi

### Online (Live Internet)
Sageri, Sonari, Sagi, Sona (Perplexity)

### AI Artists
Jily, Hily, Poni, Coni

### Search/Tools
- **Goog** - Web search
- **Gimg** - Image search
- **UTube** - Video search
- **Palc** - Calculator
- **Dogu** - Bash shell
- **Gido** - Python
- **Lary** - Perl
- **Matz** - Ruby
- **Luah** - Lua
- **Jyan** - Node.js
- **Jahl** - Deno
- **Faby** - Tiny C
- **Qell** - QuickJS
- **Bilda** - Make
- **Unp** - Unprompted (image gen macros)

## Permissions

**Public:** Anyone reads/writes; owner moderates
**Private (`username/*`):** Owner only
**NSFW:** Adults enable in settings for `nsfw/` access

## Tips

- Click code to copy
- Poke repeatedly for variations
- Horizontal scroll: swipe or Shift+mousewheel
- Mobile: [Add to home screen](https://www.androidauthority.com/add-website-android-iphone-home-screen-3181682/)
- Move divider for more input space
- Stronger models (70B+) for complex tasks
- Keep context reasonable (20-50 messages)
- Archive old chats for performance
- Turn off vision when unused
- Use missions for consistent behavior

## Troubleshooting

**Red dot:** Reload page
**No response:** Check conductor rules, try @mention
**No vision:** Enable images option, use vision-capable model
**Can't edit:** Must be room owner
**JS not running:** Don't wrap in backticks, check iframe console

## Work in Progress

- Image: img2img, face transfer, LoRA training
- Documents: PDF conversion, vector indexes, RAG
- Memory: Automatic systems (manual: ask Summi for summary)
- Notifications: AI initiative
- Voice chat: In development
- Direct messaging: Not yet available
- Video generation: May interleave with GPU workload
- Scalability: Volunteer GPU resources

# Ally Chat User Interface Guide

Note that the buttons are small and only the icons are visible, not any text. The "Name" text is visible as tool-tips on computers, but not on mobile.

## Simple Mode

| <i class="bi-send"></i> | `Ctrl+Enter` | Send | Send message (visible when message entered) |
| <i class="bi-hand-index-thumb"></i> | `Alt+Enter` | Poke | Prompt AI response (visible when no message) |

Press Alt/Option or swipe the input field on mobile to show a few more controls:

| <i class="bi-archive"></i> | `Alt+A` | Archive | Archive this room |
| <i class="bi-palette"></i> |  | Theme | Change UI theme (only day / night in simple mode) |
| <i class="bi-lightbulb"></i> <i class="bi-lightbulb-fill"></i> |  | Advanced | Toggle simple / advanced mode. |

To get to advanced mode, press Alt/Option or swipe the input field on mobile, then press <i class="bi-lightbulb"></i>.

## Advanced Mode

To show a few extra buttons (marked \* below), press Alt/Option or swipe the input field on mobile. Do it again to hide them.

To get back to simple mode, first show the extra buttons, then press <i class="bi-lightbulb-fill"></i> at the bottom right.

Many buttons react differently to shift, ctrl, and Alt/Option click; experiment to find out!

| Component | Description |
|-----------|-------------|
| Room Name | Input/display field for current chat room (top center) |
| Messages View | Secure iframe showing chat messages |
| Input Area | Message composition textarea (bottom) |
| Control Buttons | Core functionality buttons (bottom right) |

## Top-Left Controls

| Icon | Shortcut | Name | Description |
|------|----------|------|-------------|
| <i class="bi-lock"></i> <i class="bi-unlock"></i> |  | Privacy | Locked for private, unlocked for public; click to go to the main public room or your main private room |
| <i class="bi-compass"></i> |  | Nav | Navigation menu |
| <i class="bi-arrow-left-right"></i> | | Pages | Pages menu |
| <i class="bi-file-text"></i> |  | Room Ops \* | Rename or copy a room or file |
|  | `Ctrl+;` or `Esc` | Room Name | Change room |

### Navigation Menu

| Icon | Shortcut | Name | Description |
|---------|----------|------|-------------|
| <i class="bi-house"></i> |  | Home | Go to your private folder: $user/chat |
| <i class="bi-people"></i> |  | Ally Chat | Go to main public room: Ally Chat |
| <i class="bi-explicit"></i> |  | NSFW | Go to main public NSFW room nsfw/nsfw (visible when enabled for the user, unless declined) |
| <i class="bi-house-door"></i> |  | Porch | Go to your public room $user |
| <i class="bi-folder"></i> | `Alt+U` | Up | Go to parent folder |

### Pages Menu

| Icon | Shortcut | Name | Description |
| <i class="bi-skip-start"></i> | `Ctrl+[` | First | Go to first page |
| <i class="bi-caret-left"></i> | `Ctrl+,` | Prev | Previous page |
| <i class="bi-caret-right"></i> | `Ctrl+.` | Next | Next page, numbered like chat-0, chat-1 ... |
| <i class="bi-skip-end"></i> | `Ctrl+]` | Last | Go to last numbered page |
|  | `Ctrl+\\` | New | Go to new numbered page beyond last one |

### Room Operations Submenu

| Icon | Shortcut | Name | Description |
|---------|----------|------|-------------|
| <i class="bi-copy"></i> | `Alt+C` | Copy | Copy the room or file |
| <i class="bi-box-arrow-right"></i> | `Alt+M` | Move | Rename or move the room or file |

## Top-Right Controls

| Icon | Shortcut | Name | Description |
|------|----------|------|-------------|
| <i class="bi-filter"></i> |  | Filter | Filter media in chat, see [nsfw/filters](/nsfw/filters), blocks some by default e.g. `flower, garden; -person -1girl -1boy -1other; !sunset red_rose`. From weak to strong binding: `;` means AND, `!` negates an expression, `,` means OR, spaces separate terms and mean AND, `-` negates one term, `_` stands for a space in a term. It uses case-insensitive substring matching, so "rose" will also match "Roses". |
| <i class="bi-chevron-bar-down"></i> <i class="bi-chevron-bar-up"></i> |  | End / Home | Go to end or start of room |
| User's Name |  | User \* | Cycle main rooms and folders: `$user/chat`, `$user/`, `$user`, `Ally Chat` |
| <i class="bi-question-lg"></i> |  | Help | Read the Intro and Guide, and get strong AI help to use the app. |
| <i class="bi-door-closed"></i> |  | Log out \* | Log out from Ally Chat, returns to the main Allemande home page |

\* only visible after pressing Alt/Option or swiping the input field on mobile.

## Bottom-Right Controls

| Icon | Shortcut | Name | Description |
|---------|----------|------|-------------|
| <i class="bi-send"></i> | `Ctrl+Enter` | Send | Send message (visible when message entered) |
| <i class="bi-hand-index-thumb"></i> | `Alt+Enter` | Poke | Prompt AI response (visible when no message) |
| <i class="bi-plus-lg"></i> |  | Add | Upload files and record media menu |
| <i class="bi-eye"></i> |  | View | view settings |
| <i class="bi-gear"></i> |  | Opt | Room options |
| <i class="bi-shield"></i> |  | Mod | Moderation tools |
| <i class="bi-lightbulb-fill"></i> |  | Advanced Mode \* | Click to go back to simple mode |

\* only visible after pressing Alt/Option or swiping the input field on mobile.

## Add Menu

| Icon | Shortcut | Name | Description |
|---------|----------|------|-------------|----------|
| <i class="bi-upload"></i> |  | Upload files | Select files to upload |
| <i class="bi-camera"></i> \*\* |  | Take a Photo | Opens camera controls |
| <i class="bi-mic"></i> |  | Record audio | Opens recording controls |
| <i class="bi-camera-video"></i> |  | Record video | Opens recording controls |
| Σ |  | Math | Add mathematics | Switches to math editor, press again to return |

\*\* On computer only; use <i class="bi-upload"></i> on a mobile device

### Recording Controls

| Icon | Shortcut | Name | Description |
|---------|----------|------|-------------|
| <i class="bi-pause"></i> |  | Time | Shows duration, click to pause/resume |
| <i class="bi-stop"></i> |  | Stop | End recording and preview |
|  |  | Preview | Review recording before upload |
| <i class="bi-check-lg"></i> |  | Save | Upload recording |
| <i class="bi-x-lg"></i> |  | Cancel | Discard recording |

## View Settings Menu

| Icon | Shortcut | Setting | Description |
|---------|----------|-------------|----------|
| <i class="bi-fonts"></i> |  | Font Size | Change font size |
| <i class="bi-palette"></i> |  | Theme | Change UI theme (many themes) |
| <i class="bi-image"></i> | `Alt+I` | Images | Cycle images display: normal, blur, hidden |
| <i class="bi-alphabet"></i> | `Alt+A` | Alt | Toggle showing alt captions |
| <i class="bi-arrows-angle-expand"></i> <i class="bi-arrows-angle-contract"></i> |  | Image Size | Change image size |
| <i class="bi-braces"></i> |  | Source | View source (clean, basics, javascript, math/diagram source) |
| <i class="bi-asterisk"></i> |  | Color | Highlight code |
| <i class="bi-layout-three-columns"></i> |  | Columns | View chat in columns |
| <i class="bi-arrows-collapse-vertical"></i> |  | Compact | Compact view |
| <i class="bi-clock-history"></i> |  | History | View change history (deleted and edited messages) |
| <i class="bi-arrows-fullscreen"></i> |  | Full-screen | Make chat area full-screen (off, whole window, full-screen) |

### Math Editor

- [Full math-field documentation](https://cortexjs.io/mathfield/)
- Type to enter math
- Press enter or click the math button again to save it as TeX in the main message entry.
- You can also paste TeX into the math entry
- There is a button to open a virtual keyboard, like a super calculator
- There is a menu button with many other options, including matrix entry

## Options Menu

| Icon | Shortcut | Name | Description |
|---------|----------|------|-------------|
|  |  | Context | Number of recent messages AI can see |
|  |  | Lines | Limit number of lines of AI output (local models only) |
|  |  | Images | Number of recent images AI can see |
|  |  | Temp | Temperature / creativity 0.0 - ~2.0, 1.0 is normal |
|  |  | Mission | Mission file to use, - for none |

## Moderator Tools (Room Owner)

| Icon | Shortcut | Name | Description |
|---------|----------|------|-------------|
| <i class="bi-x-lg"></i> | `Alt+Z` | Undo | Remove last message |
| <i class="bi-arrow-counterclockwise"></i> | `Alt+R` | Retry | Retry last message |
| <i class="bi-pencil"></i> | `Alt+E` | Edit | Edit the room |
| <i class="bi-play"></i> |  | Auto | Auto play (try shift, ctrl) |
| <i class="bi-archive"></i> | `Alt+A` | Archive | Archive this room |
| <i class="bi-trash3"></i> | `Alt+X` | Clear | Clear this room |
|  | `Alt+H` | Re-render | Re-renders the HTML page from markdown (mainly for developers) |

## Editor Controls

When editing (room owner only), these controls appear:

| Icon | Shortcut | Name | Description |
|---------|----------|------|-------------|
| <i class="bi-indent"></i> | `Alt+T` | Indent | Insert a tab or indent the selected text. |
| <i class="bi-unindent"></i> | `Shift+Alt+T` | Dedent | Remove a tab or dedent the selected text. |
| <i class="bi-arrow-counterclockwise"></i> |  | Reset | Revert changes. |
| <i class="bi-trash3"></i> |  | Clear | Clear the contents of the editor. |
| <i class="bi-check-lg"></i> |  | Save | Save changes. |

## Image Viewing Mode

Clicking on an image in the chat enters image viewing mode.

| Action | Mouse Click | Keyboard Shortcut | Swipe (Mobile) | Description |
|---------------------|----------------------------------|---------------------------------|-------------------|-------------------------------------------------------------|
| Close | Click near the middle | `Q` or `Esc` | N/A | Return to normal chat mode. |
| Fullscreen | Click near the top-middle | `F` | Swipe Up | Toggle full-screen. |
| Zoom | Click near the bottom-middle | `M` | Swipe Down | Cycle zoom: `Fit`, `Cover`, `Original Size`. |
| Next Image | Click near the right edge | `Spacebar`, `Right Arrow` | Swipe Right | Display the next image. |
| Previous Image | Click near the left edge | `Backspace`, `Left Arrow` | Swipe Left | Display the previous image. |
| Skip 10 Images Forward | N/A | `Page Down` | N/A | Skip ahead 10 images. |
| Skip 10 Images Backward | N/A | `Page Up` | N/A | Skip back 10 images. |
| Go to First Image | N/A | `Home` | N/A | Display the first image. |
| Go to Last Image | N/A | `End` | N/A | Display the last image. |
| Flip | | `V` or `H` | | Vertical or Horizontal Flip |
| Rotate | | `L` or `R` | | Left or Right Rotation |
| Open Image in New Window | `Shift + Click` | N/A | N/A | Open the image in a new browser window. |
| Open Image in New Tab | `Ctrl + Click` | N/A | N/A | Open the image in a new browser tab. |
| Download Image | `Alt + Click` | N/A | N/A | Download the image |

## Additional Keyboard Shortcuts

| Icon | Shortcut | Name | Description |
|---------|----------|------|-------------|
| <i class="bi-indent"></i> | `Alt+T` | Indent | Insert tab or indent text |
| <i class="bi-unindent"></i> | `Shift+Alt+T` | Dedent | Dedent text |
|  | `Alt+Backspace` | Clear Content | Clear message input |
|  | `Alt+N` | Invoke Narrator | Call the narrator |
|  | `Alt+V` | Invoke Illustrator | Call the illustrator |
|  | `Alt+/` | Random AI | Invoke anyone randomly |
|  | `Shift+Alt+/` | All AIs | Invoke everyone (or several AIs) |

## Keyboard Shortcuts in Messages Section

| Icon | Shortcut | Name | Description |
|---------|----------|------|-------------|
|  | `Alt+F` | Fullscreen | Toggle full-screen mode for the messages section. |
|  | `Alt+G` | Grab | Toggle grab events. When enabled, keyboard presses will not trigger Ally Chat UI actions, useful for embedded games. |
