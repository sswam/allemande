async function screenshot(element = null) {
  // Take screenshot
  const stream = await navigator.mediaDevices.getDisplayMedia({preferCurrentTab: true});
  const track = stream.getVideoTracks()[0];

  // Capture single frame
  const imageCapture = new ImageCapture(track);
  const bitmap = await imageCapture.grabFrame();

  // Stop screen capture
  track.stop();

  // Create canvas
  const canvas = document.createElement('canvas');

  if (element) {
    // If element is provided, crop to element
    const box = element.getBoundingClientRect();
    canvas.width = box.width;
    canvas.height = box.height;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(bitmap, -box.x, -box.y);
  } else {
    // If no element provided, capture full screenshot
    canvas.width = bitmap.width;
    canvas.height = bitmap.height;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(bitmap, 0, 0);
  }

  // Trigger download
  const link = document.createElement('a');
  link.download = 'screenshot.png';
  link.href = canvas.toDataURL('image/png');
  link.click();
}
