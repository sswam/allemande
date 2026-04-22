Features marked WIP are not visible in the app yet.

## Bottom-Right Controls

| <i class="bi-headset"></i> |  | Audio | Audio settings - WIP |

## View Settings Menu

| Icon | Shortcut | Setting | Description |
|---------|----------|-------------|----------|
| <i class="bi-fonts"></i> |  | Font Size | Change font size |
| <i class="bi-palette"></i> |  | Theme | Change UI theme (many themes) |
| <i class="bi-hash"></i> |  | IDs | View message IDs - WIP |
| <i class="bi-image"></i> | `Alt+I` | Images | Cycle images display: normal, blur, hidden |
| <i class="bi-alphabet"></i> | `Alt+A` | Alt | Toggle showing alt captions |
| <i class="bi-arrows-angle-expand"></i> <i class="bi-arrows-angle-contract"></i> |  | Image Size | Change image size |
| <i class="bi-braces"></i> |  | Source | View source (clean, basics, javascript, math/diagram source) |
| <i class="bi-asterisk"></i> |  | Color | Highlight code |
| <svg width="20" height="20" fill="currentColor" viewBox="0 0 16 16"><ellipse cx="7.6" cy="4.3" rx="4" ry="3"/><ellipse cx="11.7" cy="4.6" rx="4" ry="3"/><ellipse cx="6.9" cy="8.5" rx="4" ry="3"/><ellipse cx="10.7" cy="7.3" rx="4" ry="3"/><ellipse cx="4.3" cy="6.3" rx="4" ry="3"/><ellipse cx="3.22" cy="12.3" rx="1.2" ry=".9"/><ellipse cx="1.4" cy="14.1" rx=".8" ry=".6"/></svg> |  | Details | View thoughts and details - WIP |
| <i class="bi-easel"></i> |  | Canvas | View shared canvas - WIP |
| <i class="bi-book"></i> | `Alt+C` | Clean | Clean reading view - WIP |
| <i class="bi-layout-three-columns"></i> |  | Columns | View chat in columns |
| <i class="bi-arrows-collapse-vertical"></i> |  | Compact | Compact view |
| <i class="bi-clock-history"></i> |  | History | View change history (deleted and edited messages) |
| <i class="bi-arrows-fullscreen"></i> |  | Full-screen | Make chat area full-screen (off, whole window, full-screen) |
|  |  | Items | Number of search results to show - WIP |

## Audio Settings Menu

WIP: not yet visible in the app

| Icon | Shortcut | Name | Description |
|---------|----------|------|-------------|
|  |  | STT | Speech to text |
|  |  | TTS | Text to speech |
|  |  | VAD | Voice activity detection |
|  |  | Auto | Automatic voice chat |
|  |  | Voice | Set TTS voice |

## Moderator Tools (Room Owner)

| <i class="bi-book"></i> |  | Clean | Clean up room, removes messages from specialists - WIP |


| <i class="bi-filter"></i> |  | Filter | Filter media in chat, see [nsfw/filters](/nsfw/filters), blocks some by default e.g. `flower, garden; -person -1girl -1boy -1other; !sunset red_rose`. From weak to strong binding: `;` means AND, `!` negates an expression, `,` means OR, spaces separate terms and mean AND, `-` negates one term, `_` stands for a space in a term. It uses case-insensitive substring matching, so "rose" will also match "Roses". |


- The shared canvas (experimental) is already set up. Don't change its dimensions, which are set to the full screen size. The background is transparent to respect the user's theme, probably not white or black. You can clear to some other background color but only if needed. You can draw or draw in saturated colors or medium gray, which is visible in most themes, or use the --text CSS variable which definitely contrasts with the background.
- Please use the TOP LEFT part of the canvas by default. Don't center in the canvas or try to fill the width or height unless requested. If you use another part it can be hard for the user to view it all.


| <i class="bi-eye"></i> |  | View | view settings |
| <i class="bi-shield"></i> |  | Mod | Moderation tools |
| User's Name |  | User \* | Cycle main rooms and folders: `$user/chat`, `$user/`, `$user`, `Ally Chat` |

| <i class="bi-play"></i> |  | Auto | Auto play (try shift, ctrl) |

|  |  | Mission | Mission file to use, - for none |

You can set a custom mission file name to use in room options. Omit the .m suffix in this case.



| Creator       | Model                 | Name    | Context | Max Output    | Input Price / M | Output Price / M | Description                                                                                                      |
|---------------|-----------------------|---------|---------|---------------|-----------------|------------------|------------------------------------------------------------------------------------------------------------------|
| Meta          | Llama 3.1 8B          | Elly    | 4K      | 4K            | N/A             | N/A              | A small human-like model, for creativity and engaging conversations. Most characters use this model.             |
| Meta          | Llama 3.3 70B         | Ellyn   | 128K    | 2048          | $0.10           | $0.32            | A stronger human-like model, for creativity and engaging conversations.                                          |
| Meta          | Llama 4 Scout         | Skout   | 512K    | 512K          | $0.08           | $0.30            | A fast new open model from Meta.                                                                                 |
| Meta          | Llama 4 Maverick      | Mavi    | 256K    | 256K          | $0.15           | $0.60            | A powerful new open model from Meta, achieving high performance at low cost.                                     |
| Anthropic     | Claude 4.5 Haiku      | Clia    | 200K    | 8K            | $0.80           | $4.00            | Anthropic's fast and affordable model for quick, creative conversations.                                         |
| Anthropic     | Claude 4.6 Sonnet     | Claude  | 200K    | 8K / 128K [1] | $3.00           | $15.00           | Anthropic's most powerful model; supports extended thinking.                                                     |
| Anthropic     | Claude 4.7 Opus       | Claudo  | 200K    | 8K / 128K [1] | $5.00           | $25.00           | Anthropic's most powerful reasoning model; supports extended thinking.                                           |
| Google        | Gemma 3 27B           | Gemma   | 128K    | 128K          | $0.08           | $0.16            | Google's open source Gemma language model, version 3.                                                            |
| Google        | Gemma 4 26B A4B       | Gema    | 256K    | 256K          | $0.13           | $0.40            | Google's open source Gemma language model, version 4 - mixture of experts.                                       |
| Google        | Gemma 4 31B           | Gem     | 256K    | 256K          | $0.14           | $0.40            | Google's open source Gemma language model, version 4 - full dense model.                                         |
| Google        | Gemini 2.5 Flash Lite | Lite    | 1M      | 8K            | $0.10           | $0.40            | Google's fastest Gemini model, optimized for speed and economy.                                                  |
| Google        | Gemini 2.0 Flash      | Flasho  | 1M      | 8K            | $0.10           | $0.40            | Google's fast Gemini model, optimized for speed, hardly censored, and very capable.                              |
| Google        | Gemini 2.5 Flash      | Flashi  | 1M      | 8K            | $0.30           | $2.50            | Google's fast Gemini model, optimized for speed and very capable.                                                |
| Google        | Gemini 2.5 Pro        | Gemmi   | 1M      | 64K           | $1.25 [2]       | $10.00 [2]       | Google's powerful Gemini 2.5 model optimized for a wide range of reasoning tasks.                                |
| Google        | Gemini 3 Pro          | Gemi    | 1M      | 64K           | $2 [2]          | $12.00 [2]       | Google's most powerful Gemini 3 model optimized for a wide range of reasoning tasks.                             |
| OpenAI        | GPT-4.1-mini          | Dav     | 128K    | 15K           | $0.40           | $1.60            | OpenAI's fast and affordable model, ideal for efficient interactions.                                            |
| OpenAI        | GPT-4.1               | Emmy    | 1M      | 32K           | $2              | $8.00            | OpenAI's adaptable and versatile model, perfect for varied conversations.                                        |
| OpenAI        | GPT-4o                | Emmo    | 128K    | 16K           | $2.5            | $10.00           | OpenAI's adaptable and versatile model, perfect for varied conversations (similar to 4.1 but more expensive)     |
| OpenAI        | o4-mini               | Fermi   | 200K    | 100K          | $1.10           | $4.40            | OpenAI's fast and affordable model, ideal for efficient reasoning.                                               |
| OpenAI        | o3                    | Grace   | 200K    | 100K          | $10.00          | $40.00           | OpenAI's most powerful reasoning model for advanced applications.                                                |
| OpenAI        | GPT-5-nano            | Heis    | 400K    | 128K          | $0.05           | $0.40            | OpenAI's fastest, most cost-efficient version of GPT-5.                                                          |
| OpenAI        | GPT-5-mini            | Heise   | 400K    | 128K          | $0.25           | $2.00            | OpenAI's faster, cost-efficient version of GPT-5 for well-defined tasks.                                         |
| OpenAI        | GPT-5                 | Heisen  | 400K    | 128K          | $1.25           | $10.00           | OpenAI's best model for coding and agentic tasks across domains.                                                 |
| OpenAI        | gpt-oss-20b           | Gos     | 128K    | 128K          | $0.04           | $0.15            | OpenAI's medium-sized open-weight model for low latency domains.                                                 |
| OpenAI        | gpt-oss-120b          | Goss    | 128K    | 128K          | $0.072          | $0.28            | OpenAI's most powerful open-weight model, fits into an H100 GPU.                                                 |
| Perplexity    | Sonar                 | Sona    | 128K    | 8K            | $1              | $1               | Perplexity's fastest and most affordable Online model with live internet data.                                   |
| Perplexity    | Sonar Reasoning       | Sonari  | 128K    | 8K            | $1 [3]          | $5               | Online model with live internet data, focusing on reasoning abilities, search costs are much lower than for Pro. |
| Perplexity    | Sonar Pro             | Sagi    | 200K    | 8K            | $3 [3]          | $15              | Online model with live internet data; Perplexity's high-performance option. Includes search costs.               |
| Perplexity    | Sonar Reasoning Pro   | Sageri  | 128K    | 8K            | $2 [3]          | $8               | Online model with live internet data, specializing in complex reasoning tasks. $5/1000 search queries.           |
| xAI           | Grok 3                | Rocki   | 128K    | 128K          | $3              | $15              | xAI's helpful, truthful and humorous Grok 3 model.                                                               |
| xAI           | Grok 3 Mini           | Gokk    | 128K    | 128K          | $0.30           | $0.50            | Fast and efficient mini version of Grok 3.                                                                       |
| xAI           | Grok 4                | Grok    | 256K    | 256K          | $3              | $15              | xAI's helpful, truthful and humorous Grok 4 model.                                                               |
| xAI           | Grok 4 Fast           | Gok     | 2M      | 2M            | $0.20           | $0.50            | Ultra-fast Grok 4 with extended context for standard tasks.                                                      |
| xAI           | Grok Code Fast        | Groc    | 256K    | 256K          | $0.20           | $1.50            | Specialized fast model optimized for code generation and analysis.                                               |
| DeepSeek      | DeepSeek Chat V3      | Dese    | 64K     | 8192          | $0.20           | $0.80            | DeepSeek's creative and intelligent chat model.                                                                  |
| DeepSeek      | DeepSeek Chat V3.2    | Desee   | 64K     | 8192          | $0.27           | $1.10            | DeepSeek's creative and intelligent chat model, with extra smarts.                                               |
| DeepSeek      | DeepSeek Reasoner R1  | Deseri  | 64K     | 8192          | $0.55           | $2.19            | DeepSeek's strong and creative reasoning model.                                                                  |
| Alibaba Cloud | QwQ 32B               | Qwen    | 128K    | 128K          | N/A             | N/A              | Qwen is a reasoning model from Alibaba Cloud, strong at various tasks, and able to run on consumer GPUs.         |
| Mistral       | Mistral Large 2411    | Misti   | 128K    | 128K          | $2              | $6               | Mistral's general-purpose reasoning model, strong at various tasks.                                              |
| Mistral+      | Venice Uncensored 1.1 | Veni    | 32K     | 32K           | $0.20           | $0.90            | Venice Uncensored 1.1; Dolphin Mistral 24B Venice Edition.                                                       |
| Mistral+      | Venice Role Play      | Venni   | 128K    | 128K          | $0.50           | $2               | Venice Role Play Uncensored.                                                                                     |
| MoonshotAI    | Kimi K2 0905          | Kimi    | 262K    | 262K          | $0.39           | $1.90            | MoonshotAI: Kimi K2 0905, a 1 trillion parameter, mixture-of-experts model for reasoning and tool use.           |
| MoonshotAI    | Kimi K2.5             | Kimmi   | 262K    | 262K          | $0.45           | $2.50            | MoonshotAI: Kimi K2.5, native multimodal, strong in general reasoning, visual coding, and tool-calling.          |
| Z.AI          | GLM 4.6               | Glimi   | 205K    | 205K          | $0.50           | $1.90            | Z.AI: GLM 4.6: advanced agentic, reasoning and coding capabilities, with refined writing.                        |

* The Llama model powers numerous characters and agents including Ally, Barbie, Callam, Cleo, etc.

1. Claude 4's larger output window is not yet enabled in our app.
2. Gemini 2.5 Pro pricing: input/M: $1.25 (<=200K) / $2.50 (>200K), output/M: $10.00 (<=200K) / $15.00 (>200K)
   Gemini 3 Pro pricing: input/M: $2 (<=200K) / $4 (>200K), output/M: $12.00 (<=200K) / $18.00 (>200K)
3. Only the Perplexity models have access to search the internet. They incur search costs of $5 per 1000 searches.
   Other models can search using the Goog tool, and fetch pages using `Dogu, web-text URL`.


#### Language Models (NSFW capable)

| Creator    | Model                 | Name   | Context | Max Output | Input Price / M | Output Price / M | Description                                                                                             |
|------------|-----------------------|--------|---------|------------|-----------------|------------------|---------------------------------------------------------------------------------------------------------|
| Meta       | Llama 3.1 8B          | Elly   | 4096    | 4096       | N/A             | N/A              | A smaller human-like model, for creativity and engaging conversations. Most characters use this model.  |
| Meta       | Llama 3.3 70B         | Ellyn  | 128K    | 2048       | $0.10           | $0.32            | A stronger human-like model, for creativity and engaging conversations.                                 |
| Google     | Gemma 3 27B           | Gemma  | 128K    | 128K       | $0.08           | $0.16            | Google's open source Gemma language model, version 3.                                                   |
| Google     | Gemma 4 26B A4B       | Gema   | 256K    | 256K       | $0.13           | $0.40            | Google's open source Gemma language model, version 4 - mixture of experts.                              |
| Google     | Gemma 4 31B           | Gem    | 256K    | 256K       | $0.14           | $0.40            | Google's open source Gemma language model, version 4 - full dense model.                                |
| Google     | Gemini 2.5 Flash Lite | Lite   | 1M      | 8K         | $0.10           | $0.40            | Google's fastest Gemini model, optimized for speed and economy.                                         |
| Google     | Gemini 2.0 Flash      | Flasho | 1M      | 64K        | $0.10           | $0.40            | Google's fast Gemini model, optimized for speed, hardly censored, and very capable.                     |
| Google     | Gemini 2.5 Flash      | Flashi | 1M      | 8K         | $0.30           | $2.50            | Google's fast Gemini model, optimized for speed and very capable.                                       |
| Google     | Gemini 2.5 Pro        | Gemmi  | 1M      | 64K        | $1.25 [1]       | $10.00 [1]       | Google's powerful Gemini 2.5 model optimized for a wide range of reasoning tasks.                       |
| Google     | Gemini 3 Pro          | Gemi   | 1M      | 64K        | $2 [1]          | $12.00 [1]       | Google's most powerful Gemini 3 model optimized for a wide range of reasoning tasks.                    |
| xAI        | Grok 4                | Grok   | 256K    | 256K       | $3              | $15              | xAI's helpful, truthful and humorous Grok 4 model.                                                      |
| xAI        | Grok 4 Fast           | Gok    | 2M      | 2M         | $0.20           | $0.50            | Ultra-fast Grok 4 with extended context for standard tasks.                                             |
| DeepSeek   | DeepSeek Chat V3      | Dese   | 64K     | 8192       | $0.20           | $0.80            | DeepSeek's creative and intelligent chat model.                                                         |
| DeepSeek   | DeepSeek Chat V3.2    | Desee  | 64K     | 8192       | $0.27           | $1.10            | DeepSeek's creative and intelligent chat model, with extra smarts.                                      |
| Mistral    | Mistral Large 2411    | Misti  | 128K    | 128K       | $2              | $6               | Mistral's strongest language model, very capable and creative.                                          |
| Mistral+   | Venice Uncensored 1.1 | Veni   | 32K     | 32K        | $0.20           | $0.90            | Venice Uncensored 1.1; Dolphin Mistral 24B Venice Edition.                                              |
| Mistral+   | Venice Role Play      | Venni  | 128K    | 128K       | $0.50           | $2               | Venice Role Play Uncensored.                                                                            |
| MoonshotAI | Kimi K2 0905          | Kimi   | 262K    | 262K       | $0.39           | $1.90            | MoonshotAI: Kimi K2 0905, a 1 trillion parameter, mixture-of-experts model for reasoning and tool use.  |
| MoonshotAI | Kimi K2.5             | Kimmi  | 262K    | 262K       | $0.45           | $2.50            | MoonshotAI: Kimi K2.5, native multimodal, strong in general reasoning, visual coding, and tool-calling. |
| Z.AI       | GLM 4.6               | Glimi  | 205K    | 205K       | $0.50           | $1.90            | Z.AI: GLM 4.6: advanced agentic, reasoning and coding capabilities, with refined writing.               |

* The Llama 3.1 8B model (Elly) powers numerous characters and agents including Ally, Barbie, Callam, Cleo, etc.

1. Gemini 2.5 Pro pricing: input/M: $1.25 (<=200K) / $2.50 (>200K), output/M: $10.00 (<=200K) / $15.00 (>200K)
   Gemini 3 Pro pricing: input/M: $2 (<=200K) / $4 (>200K), output/M: $12.00 (<=200K) / $18.00 (>200K)
