// Optional: Audio visualization during recording
function setupAudioVisualization(stream) {
    const audioContext = new AudioContext();
    const source = audioContext.createMediaStreamSource(stream);
    const analyzer = audioContext.createAnalyser();
    source.connect(analyzer);

    // Then you can use analyzer.getByteTimeDomainData() or
    // analyzer.getByteFrequencyData() to create visualizations
    // using Canvas or other methods
}

Your HTML might include:
```html
<!-- For video preview -->
<video id="videoPreview" autoplay muted></video>

<!-- For audio preview -->
<audio id="audioPreview" controls></audio>
<!-- Optional: Canvas for audio visualization -->
<canvas id="audioVisualization"></canvas>
```


async function checkMediaPermissionsAlternative() {
    const audio = await navigator.permissions.query({ name: 'microphone' });
    const video = await navigator.permissions.query({ name: 'camera' });
    return {
        hasAudioPermission: audio.state === 'granted',
        hasVideoPermission: video.state === 'granted'
    };
}
```
