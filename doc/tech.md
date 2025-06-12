How I create realistic images with SDXL and Pony models:

- Juggernaut XL or CyberRealistic Pony
- prompting: raw, realistic, photo \(medium\)  NEG: (anime, cartoon, 3d:2)
- Automatic1111 API (obsolete, but works)
- hires fix 1.5
- adetailer * 3
- Perturbed-Attention Guidance (PAG)
- unprompted (macros)
- realism LoRAs: <lora:RealSkin_xxXL_v1:2>, <lora:Pony Realism Slider:2>
- <lora:is_pretty:??> is pretty and <lora:ugly:??> uglylora with -ve or +ve weights
- macros to generate random characters / faces
- 3 or 4 random character LoRA mixins with different weights, for better faces in Pony
- there's a great 'boring' LoRA, which no one uses correctly
- AI-assisted prompting, with visual feedback

You can try my free app, Ally Chat, if you like. It automates most of this.


Example prompt for JuggernautXL:

solo, [person "Ally" "white blouse"], facing viewer, realistic skin texture, detailed facial features, simple gradient background, [use photo] <lora:add-detail-xl:1> more detailed <lora:RealSkin_xxXL_v1:2> more realistic skin NEGATIVE (ugly, bad anatomy:2) [S4]

For Cyberrealistic Pony just add one LoRA, should add the "pony boilerplate":

<lora:Pony Realism Slider:2> more realistic images and people
