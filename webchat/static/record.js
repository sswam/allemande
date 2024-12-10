async function checkMediaPermissions() {
    const devices = await navigator.mediaDevices.enumerateDevices();
    const hasAudioPermission = devices.some(device =>
        device.kind === 'audioinput' && device.label !== '');
    const hasVideoPermission = devices.some(device =>
        device.kind === 'videoinput' && device.label !== '');
    return { hasAudioPermission, hasVideoPermission };
}

async function setupRecorder(includeVideo) {
    let room_saved;
    const { hasAudioPermission, hasVideoPermission } = await checkMediaPermissions();
    if (!hasAudioPermission || !hasVideoPermission) {
        room_saved = room;
        clear_messages_box();
//        await $wait();
    }

    const constraints = {
        audio: true,
        video: includeVideo ? {
            width: 1280,
            height: 720
        } : false
    };

    // TODO I think this is not returning?
    // It doesn't work with my streaming rooms thing, might need to use a websocket or something :/

    const stream = await navigator.mediaDevices.getUserMedia(constraints);
    const mediaRecorder = new MediaRecorder(stream);
    const chunks = [];

    $on(mediaRecorder, 'dataavailable', (ev) => {
        chunks.push(ev.data);
    });

    if (room_saved)
        set_room(room_saved);

    return {
        mediaRecorder,
        chunks,
        stream
    };
}

async function stopRecording(mediaRecorder, chunks, stream, includeVideo) {
    // Stop recording
    mediaRecorder.stop();

    // Wait for stop event
    await new Promise(resolve => $on(mediaRecorder, 'stop', resolve, { once: true }));

    // Create blob
    const mimeType = includeVideo ? 'video/webm' : 'audio/webm';
    const mediaBlob = new Blob(chunks, { type: mimeType });

    // Stop all tracks
    for (const track of stream.getTracks())
        track.stop();

    return mediaBlob;
}

/*
// Send the recording to the server
async function sendRecording(mediaBlob, includeVideo) {
    const formData = new FormData();
    const fileName = includeVideo ? 'video.webm' : 'audio.webm';
    formData.append('media', mediaBlob, fileName);

    const response = await fetch('/upload-media', {
        method: 'POST',
        body: formData
    });

    return response.json();
}
*/

function set_timer(seconds) {
    const m = Math.floor(seconds/60);
    const s = (seconds%60).toString().padStart(2,'0');
    $id('rec_time').textContent = `${m}:${s}`;
}

// Main recording function
async function handleRecording(includeVideo = false) {
    set_controls('input_record');

    try {
        const {
            mediaRecorder,
            chunks,
            stream
        } = await setupRecorder(includeVideo);

        // Video preview
        const videoPreview = $id('rec_videoPreview');
        if (includeVideo) {
            videoPreview.classList.remove('hidden');
            videoPreview.srcObject = stream;
        } else {
            videoPreview.classList.add('hidden');
        }

        mediaRecorder.start();

        // Show timer
        let start = Date.now() / 1000;
        let seconds_before = 0;
        set_timer(0);
        const timerInterval = setInterval(() => {
            const now = Date.now() / 1000;
            let seconds = seconds_before;
            if (start)
                seconds += now - start;
            seconds = Math.floor(seconds);
            set_timer(seconds);
        }, 1000);

        const $pause = $id('rec_pause');
        $on($pause, 'click', () => {
            if (mediaRecorder.state === 'recording') {
                mediaRecorder.pause();
                $pause.innerText = 'resume';
                seconds_before = Math.floor(seconds_before + Date.now() / 1000 - start);
                start = null;
            } else if (mediaRecorder.state === 'paused') {
                mediaRecorder.resume();
                $pause.innerText = 'pause';
                start = Date.now() / 1000;
            }
        })

        // wait for one of the stop / send / cancel buttons to be clicked,
        let stop_action = await new Promise((resolve) => {
            const stopFn = (action) => {
                resolve(action);
            };
            $on($id('rec_stop'), 'click', () => stopFn('stop'));
            $on($id('rec_send'), 'click', () => stopFn('send'));
            $on($id('rec_cancel'), 'click', () => stopFn('cancel'));
        });

        clearInterval(timerInterval);

        const mediaBlob = await stopRecording(mediaRecorder, chunks, stream, includeVideo);
        console.log('Recording complete:', mediaBlob);

        // clean up video preview
        if (includeVideo) {
            videoPreview.srcObject = null;
        }

        // Preview stopped when clicked stop
        if (stop_action === 'stop') {
            const url = URL.createObjectURL(mediaBlob);
            let preview;
            if (includeVideo) {
                preview = $id('rec_preview_videoPreview');
                preview.classList.remove('hidden');
                $id('rec_preview_audioPreview').classList.add('hidden');
            } else {
                preview = $id('rec_preview_audioPreview');
                preview.classList.remove('hidden');
                $id('rec_preview_videoPreview').classList.add('hidden');
            }
            preview.src = url;
            set_controls('input_record_preview');

            // wait for one of the send / cancel buttons to be clicked,
            stop_action = await new Promise((resolve) => {
                const stopFn2 = (action) => resolve(action);
                $on($id('rec_preview_send'), 'click', () => stopFn2('send'));
                $on($id('rec_preview_cancel'), 'click', () => stopFn2('cancel'));
            });

            // stop playback
            preview.pause();
            preview.currentTime = 0;
            URL.revokeObjectURL(preview.src);
            preview.removeAttribute('src');
        }

        if (stop_action === 'send') {
            // Send the recording to the server
            const fileName = includeVideo ? `${user}_video.webm` : `${user}_audio.webm`;
            await upload_file(mediaBlob, fileName);
        }

    } catch (error) {
        console.error('Recording error:', error);
    }

    set_timer(0);

    set_controls();
}

function record_main() {
    $on($id('record_audio'), 'click', () => handleRecording(false));
    $on($id('record_video'), 'click', () => handleRecording(true));
}

/*
// For audio only
handleRecording(false);

// For video + audio
handleRecording(true);
*/
