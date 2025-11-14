# Ally Chat: NSFW Features Guide

This guide covers features for adult entertainment. For general use, see the main [User Guide](/guide).

## Access and Rules
- The NSFW zone is accessed by entering "nsfw" in the room name or clicking the <i class="bi-explicit"></i> icon.
- Users must be 18+ for the NSFW zone.
- Illegal content is prohibited: underage, non-consensual (NCII/deepfake), piracy.
- No hate-speech, shaming, or doxxing.
- Do not incite crime.
- Your private chats are stored on the server and can be wiped on request.

## Key Features
- **Uncensored LLMs**: Most AI characters are available for sexual chat and role-play.
- **Uncensored AI Art**: Many AI art models can create sexual images.
- **AI Art LoRAs**: Numerous LoRAs are available to enhance images.
- **Search**: Search engines can return adult images and videos.
- **Custom Characters**: Create custom characters with help from `Chaz` or `Chara`.

## Learning the Features
- For a simple start, talk to `Lori`. She can direct your messages to other agents.
- `Assi` is the NSFW tech support AI, analogous to `Aidi` in SFW zones.
- `Yenta` can introduce you to other characters, agents, and tools.
- `Xilu` is an expert at NSFW image generation. Talk to her to create images or learn prompting.

## AI Image Generation Syntax
Prompts are sent to an image agent. `Xilu` can help you write them. When an AI writes a prompt, the user must press "poke" to generate the image.

**Basic Example:**
Draws a nude girl in a fast, medium-quality portrait.
```
Coni, 1girl, nude [P]
```

**Character Example:**
Draws Ally with her standard appearance in a default high-quality square image.
```
Jily, [use Ally], [use age/Ally], [use emo/Ally], [use clothes/Ally] NEGATIVE [use neg] [S3]
```

**Concise Character Example:**
Draws Barbie solo in a tall, cartoon-style image.
```
Poni, solo [person Barbie] NEGATIVE [use neg] [T4]
```

**Scene Example:**
Draws Cleo in green lingerie in a parking lot. Specifies a full-body shot in a landscape format.
```
Lusy, [person Cleo "green lingerie"], seedy parking lot, night, (full body, heels:1.5) [L4]
```
**Male Character Example:**
Draws a portrait of Bast in the jungle, looking angry.
```
Hily, [person Bast "topless, leather shorts" angry], jungle [S2]
```

**Image Settings:**
- Quality ranges from 0 (fastest) to 4 (best).
- Aspect ratios: `[P]`=Portrait, `[S]`=Square, `[L]`=Landscape.
- Taller portraits: `[T]`. Wider landscapes: `[W]`.
- Default is `[S2]` (good quality square). `[P1]` is low-quality portrait, `[L4]` is high-quality landscape.

## AI Vision (NSFW)
Only Google-based models are permitted to view NSFW content.
- `Xilu`, `Xillu`, `Illu`, `Gema` can see NSFW images in chat when enabled.
- These models have limits; turn off vision if they refuse to respond.

## NSFW AI Characters & Agents

### Recommended for Roleplay
- **Pyrite**: A playful woman. (Gemini 2.0 Flash)
- **Akane**
- **Sadie**

### Base Models (Uncensored)
- `Ellie`: Llama 3.1 8B. Small, human-like. [recommended]
- `Ellyn`: Llama 3.3 70B. Stronger, human-like.
- `Flasho`: Gemini 2.0 Flash. Fast and capable. [recommended]
- `Flashi`: Gemini 2.5 Flash. Fast and capable.
- `Gemmi`: Gemini 2.5 Pro. Google's strongest model.
- `Dese`: DeepSeek Chat V3. Creative and intelligent. [recommended]
- `Desee`: DeepSeek Chat V3.1.
- `Misti`: Mistral Large 2411. Strong and creative.
- `Veni`: Venice (Dolphin Mistral 24B). Uncensored.

### Uninhibited Variants
These use a short pre-prompt to enable NSFW context. Not needed for Ellie, Ellyn, Misti, Veni.
- `Xlasho` (Gemini 2.0 Flash)
- `Xlashi` (Gemini 2.5 Flash)
- `Xemmi` (Gemini 2.5 Pro)
- `Xese` (DeepSeek Chat V3)
- `Xesee` (DeepSeek Chat V3.1)

### Sexual Variants (Llama 3.1 8B)
- `XTalk`: Strongly inclined to dirty talk, may initiate extreme content.
- `DirtyTalk`: Inclined to dirty talk when the mood is set.

### Specialists
- `Assi`: NSFW AI assistant and tech support.
- `Xilu`, `Xillu`: NSFW AI art prompt experts. (`Xilu` is faster, `Xillu` is stronger).
- `Illu`, `Gema`: SFW AI art prompt experts. (`Illu` is faster, `Gema` is stronger).
- `Poli`: Translator (Google Flash).
- `Summi`, `Summar`: Summarizers (Google Flash). `Summar` uses structured markdown.
- `Juon` (Roasto): A volatile NSFW roaster.

### AI Artists
- `Jily`: Photorealistic/artistic (Juggernaut XL).
- `Hily`: High-quality realistic/fantasy (HelloWorld XL).
- `Yoni`, `Coni`, `Boni`: Semi-realistic NSFW (PonyXL based).
- `Poni`: Cartoon/anime NSFW (PonyXL based).
- `Lusy`, `Bigi`, `Pigi`: Very realistic NSFW.

### Search Agents
- `Goog`: Google web search.
- `Gimg`: Google image search.
- `UTube`: YouTube video search.
- `Pr0nto`: PornHub search.

### Tools
- `Unp`: Unprompted (macro processor for image gen).
`Unp, [choose] [use Ally] | [use Bast] [/choose]`

## AI Model Details

#### Language Models (NSFW capable)
| Creator | Model | Name | Context | Max Output | Description |
|---|---|---|---|---|---|
| Meta | Llama 3.1 8B | Ellie* | 4096 | 4096 | A smaller human-like model, for creativity and engaging conversations. Most characters use this model. |
| Meta | Llama 3.3 70B | Ellyn | 128K | 2048 | A stronger human-like model, for creativity and engaging conversations. |
| Google | Gemini 2.0 Flash | Flasho | 1M | 64K | Google's fast Gemini model, optimized for speed, hardly censored, and very capable. |
| Google | Gemini 2.5 Flash | Flashi | 1M | 8K | Google's fast Gemini model, optimized for speed and very capable. |
| Google | Gemini 2.5 Pro | Gemmi | 1M | 64K | Google's powerful Gemini 2.5 model optimized for a wide range of reasoning tasks. |
| xAI | Grok 4 | Anni | 256K | 256K | xAI's helpful, truthful and humorous Grok 4 model. |
| DeepSeek | DeepSeek Chat V3 | Dese | 64K | 8192 | DeepSeek's creative and intelligent chat model. |
| DeepSeek | DeepSeek Chat V3.1 | Desee | 64K | 8192 | DeepSeek's creative and intelligent chat model, with extra smarts. |
| Mistral | Mistral Large 2411 | Misti | 128K | 128K | Mistral's strongest language model, very capable and creative. |
| Mistral+ | Venice: Uncensored | Veni | 33K | 33K | Venice: Uncensored; Dolphin Mistral 24B Venice Edition: Uncensored. |
| MoonshotAI | Kimi K2 0905 | Kimi | 262K | 262K | MoonshotAI: Kimi K2 0905, a 1 trillion parameter, mixture-of-experts model for reasoning and tool use. |
| Z.AI | GLM 4.6 | Glimi | 205K | 205K | Z.AI: GML 4.6: advanced agentic, reasoning and coding capabilities, with refined writing. |

*\* The Llama 3.1 8B model (Ellie) powers numerous characters including Ally, Barbie, Callam, Cleo, etc.*

#### Image Models
| Creator | Model | Name | Description |
|---|---|---|---|
| RunDiffusion | Juggernaut XL v9 | Jily | Popular SDXL-based model for realistic and artistic images, including soft-core erotica. |
| LEOSAM | HelloWorld XL | Hily | Popular SDXL-based model for realistic, concept, and fantasy art, including soft-core erotica. |
| Autismix anon | AutismMix Confetti | Poni | Mix of PonyXL, popular for anime-style art. |
| Cyberdelia | CyberRealistic Pony | Coni | A realistic Pony model with CyberRealistic elements. |
| SubtleShader | Big Love Pony | Pigi | More Pony-flavoured variant, less realistic, better with booru tags. |
| SubtleShader | Big Love XL | Bigi | State-of-the-art erotic art, more SDXL than Pony. |
| Tauron | Eros Ultima Hybrid | Yoni | Merge of SDXL with PonyXL for high-quality, realistic erotic art. |
| Stable Yogi | Babes | Boni | Pony-based model tuned for beautiful women and erotic art. |
| coyotte | Lustify V6 OLT | Lusy | Very realistic SDXL-based model, excellent for NSFW art. |

**Image Model Prompting:**
- `Jily` and `Hily` (SDXL-based) understand natural English well. Good for SFW and softcore NSFW. For hardcore, add the `nsfw` LoRA or use another model.
- Other models are primarily based on PonyXL and work best with [Danbooru tags](https://danbooru.donmai.us/wiki_pages/tag_groups). They excel at softcore, hardcore, and hentai.
- `Bigi` is a mix of SDXL and Pony, understanding both English and tags to some extent.
