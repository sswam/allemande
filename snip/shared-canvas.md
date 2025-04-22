The shared canvas is already set up. Don't change its dimensions, which are set to the full screen size. The background is transparent to respect the user's theme, probably not white or black. You can clear to some other background color but only if needed. You can draw or draw in saturated colors or medium gray, which is visible in most themes, or use the --text CSS variable which definitely contrasts with the background.
- Please use the TOP LEFT part of the canvas by default. Don't center in the canvas or try to fill the width or height unless requested. If you use another part it can be hard for the user to view it all.

### Drawing on the shared canvas

The shared canvas is hidden by default, users can turn it on in advanced mode.

<script>
h = canvas.height;
ctx.fillStyle = 'red';
ctx.fillRect(10, 10, 100, 100);
</script>

