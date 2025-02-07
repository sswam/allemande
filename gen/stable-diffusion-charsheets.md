Character Consistency in Stable Diffusion

A technique for achieving character consistency in Stable Diffusion using character sheets and LoRA training:

1. Create character sheets with 15 facial views using:
- OpenPose template for face angles
- Lineart template for segmentation
- Templates sized 1328x800 (must be divisible by 8)
- Controlnet for both templates

2. Key settings:
- Use txt2img with specific prompts for character features
- Apply img2img scaling with noise level 0.4-0.6
- Ultimate SD upscale recommended
- Output dimensions: 256x256 per image segment

3. Process:
- Generate base character sheet
- Create variations with different expressions (smiling, sad, angry)
- Split resulting images using provided Python script
- Use split images to train LoRA model

4. Considerations:
- Grid approach provides more consistent facial features than individual poses
- VRAM requirements: 16GB at 1328x800 (can reduce to 12GB at 1280x768)
- Focus on facial features first, then body features in subsequent iterations

The goal is creating unique AI-generated characters with consistent features across multiple images.
