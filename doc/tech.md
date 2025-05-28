- CyberRealistic Pony
- Juggernaut XL
- a1111 webui API
- hires fix
- adetailer
- unprompted
- Gemini 2.0 Flash
- Llama 3.1 8B
- Ally Chat, my FLOSS AI chat service (closed beta)


Creating realistic images with SDXL and Pony models:

- you could try my free app, Ally Chat, if you like. It automates all of this & much more, with AI-assisted prompting too. Setting this up yourself, or similar, is quite a process.
- prompting: e.g. raw, realistic, photo (medium). My [use photo] macro does this ...
- negative prompting: e.g. (anime, cartoon, 3d:2) ... and also this
- I use automatic1111 API, hires-fix, adetailer, PAG option, unprompted macro processor
- Note: automatic1111 is unmaintained, obsolescent, but still works
- for SDXL models, JuggernautXL is most popular and very realistic, I call this Illy
- for PonyXL models, Cyberrealistic Pony is popular and quite realistic, I call this Coni
- can make it more realistic using certain LoRAs: e.g. <lora:add-detail-xl:1> more detailed, <lora:RealSkin_xxXL_v1:2> more realistic skin, <lora:Pony Realism Slider:2> more realistic images and people
- there's an 'anti-boring' LoRA which no one uses correctly

The two images are the same non-LoRA character, using each model and these techniques with simple prompts. I didn't cherry pick at all, these are the first images it made for the prompts. The images aren't special, but they are quite realistic. The [person "Ally"] part fills in her details, which are pretty simple.

The prompt for JuggernautXL:

solo, [person "Ally" "white blouse"], facing viewer, realistic skin texture, detailed facial features, simple gradient background, [use photo] <lora:add-detail-xl:1> more detailed <lora:RealSkin_xxXL_v1:2> more realistic skin NEGATIVE (ugly, bad anatomy:2) [S4]

The prompt for Cyberrealistic Pony just adds one LoRA, you also should add "pony boilerplate":

<lora:Pony Realism Slider:2> more realistic images and people
