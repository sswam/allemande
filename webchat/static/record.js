let chat;

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
    if (!hasAudioPermission || (!hasVideoPermission && includeVideo)) {
        room_saved = chat.room;
        chat.clear_messages_box();
//        await $wait();
    }

    const constraints = {
        audio: !includeVideo || includeVideo === 'video',
        video: includeVideo ? {
            width: 1280,
            height: 720
        } : false
    };

    // TODO I think this is not returning?
    // It doesn't work with my streaming rooms thing, might need to use a websocket or something :/

    const stream = await navigator.mediaDevices.getUserMedia(constraints);
    const mediaRecorder = includeVideo === 'photo' ? null : new MediaRecorder(stream);
    const chunks = [];

    if (mediaRecorder) {
        $on(mediaRecorder, 'dataavailable', (ev) => {
            chunks.push(ev.data);
        });
    }

    if (room_saved)
        chat.set_room(room_saved);

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

function set_timer(seconds) {
    const m = Math.floor(seconds/60);
    const s = (seconds%60).toString().padStart(2,'0');
    $id('rec_time').textContent = `${m}:${s}`;
}

async function capturePhoto(stream) {
    const videoPreview = $id('rec_videoPreview');
    const canvas = document.createElement('canvas');
    canvas.width = videoPreview.videoWidth;
    canvas.height = videoPreview.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(videoPreview, 0, 0, canvas.width, canvas.height);

    const photoBlob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.95));

    // Stop all tracks
    for (const track of stream.getTracks())
        track.stop();

    return photoBlob;
}

// Main recording function
async function handleRecording(recording_type) {
    const includeVideo = recording_type === "video" || recording_type === "photo";
    await $import("icons");
    icons = modules.icons.icons;

    chat.set_controls('input_record');

    try {
        const {
            mediaRecorder,
            chunks,
            stream
        } = await setupRecorder(includeVideo ? recording_type : false);

        // Video preview
        const videoPreview = $id('rec_videoPreview');
        if (includeVideo) {
            show("rec_videoPreview");
            videoPreview.srcObject = stream;
        } else {
            hide("rec_videoPreview");
        }

        setTimeout(chat.controls_resized, 500);  // TODO fix this properly somehow

        // Photo mode: show preview and capture button, no recording
        if (recording_type === "photo") {
            hide("rec_time");
            hide("rec_stop");
            hide("rec_cancel");
            show("rec_save");

            // Wait for capture button
            const action = await new Promise((resolve) => {
                $on($id('rec_save'), 'click', () => resolve('capture'));
                $on($id('rec_cancel'), 'click', () => resolve('cancel'));
            });

            if (action === 'cancel') {
                // Stop all tracks
                for (const track of stream.getTracks())
                    track.stop();
                videoPreview.srcObject = null;
                chat.set_controls();
                return;
            }

            // Capture photo
            const photoBlob = await capturePhoto(stream);
            videoPreview.srcObject = null;

            show("rec_cancel");

            // Show photo preview
            const url = URL.createObjectURL(photoBlob);
            const preview = $id('rec_preview_imagePreview');
            show("rec_preview_imagePreview");
            hide("rec_preview_videoPreview");
            hide("rec_preview_audioPreview");
            preview.src = url;
            chat.set_controls('input_record_preview');

            // Wait for save/cancel
            const save_action = await new Promise((resolve) => {
                $on($id('rec_preview_save'), 'click', () => resolve('save'));
                $on($id('rec_preview_cancel'), 'click', () => resolve('cancel'));
            });

            URL.revokeObjectURL(preview.src);
            preview.removeAttribute('src');

            if (save_action === 'save') {
                const fileName = `${user}_photo.jpg`;
                const save_button = 'rec_preview_save';
                chat.active_set(save_button);
                if (!await chat.add_upload_file_link(chat.upload_file(photoBlob, fileName, true)))
                    await chat.error(save_button);
                chat.active_reset(save_button);
            }

            chat.set_controls();
            return;
        }

        show("rec_time");
        show("rec_stop");
        show("rec_cancel");
        show("rec_save");

        chat.controls_resized();

        // Recording mode (audio/video)
        mediaRecorder.start();

        // Show timer
        let start = Date.now() / 1000;
        let seconds_before = 0;
        const $timer = $id('rec_time');
        chat.active_set("rec_time");
        set_timer(0);

        const update_timer = () => {
            const now = Date.now() / 1000;
            let seconds = seconds_before;
            seconds += now - start;
            seconds = Math.floor(seconds);
            set_timer(seconds);
        };

        const timerInterval = setInterval(() => {
            if (start)
                update_timer();
        }, 1000);

        $on($timer, 'click', () => {
            if (mediaRecorder.state === 'recording') {
                mediaRecorder.pause();

                $timer.innerHTML = icons["pause"];
                $timer.title = 'resume reording';

                seconds_before = Math.floor(seconds_before + Date.now() / 1000 - start);
                start = null;
                chat.active_reset("rec_time");
            } else if (mediaRecorder.state === 'paused') {
                mediaRecorder.resume();
                start = Date.now() / 1000;
                chat.active_set("rec_time");
                update_timer();
                $timer.title = 'pause recording';
            }
        });

        let save_button;

        // wait for one of the stop / save / cancel buttons to be clicked,
        let stop_action = await new Promise((resolve) => {
            const stopFn = (action) => {
                resolve(action);
            };
            save_button = 'rec_save';
            $on($id('rec_stop'), 'click', () => stopFn('stop'));
            $on($id('rec_save'), 'click', () => stopFn('save'));
            $on($id('rec_cancel'), 'click', () => stopFn('cancel'));
        });

        clearInterval(timerInterval);
        set_timer(0);
        chat.active_reset("rec_time");

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
                show("rec_preview_videoPreview");
                hide("rec_preview_audioPreview");
                hide("rec_preview_imagePreview");
            } else {
                preview = $id('rec_preview_audioPreview');
                show("rec_preview_audioPreview");
                hide("rec_preview_videoPreview");
                hide("rec_preview_imagePreview");
            }
            preview.src = url;
            chat.set_controls('input_record_preview');

            // wait for one of the save / cancel buttons to be clicked,
            stop_action = await new Promise((resolve) => {
                const stopFn2 = (action) => resolve(action);
                save_button = 'rec_preview_save';
                $on($id('rec_preview_save'), 'click', () => stopFn2('save'));
                $on($id('rec_preview_cancel'), 'click', () => stopFn2('cancel'));
            });

            // stop playback
            preview.pause();
            preview.currentTime = 0;
            URL.revokeObjectURL(preview.src);
            preview.removeAttribute('src');
        }

        if (stop_action === 'save') {
            // Send the recording to the server
            const fileName = includeVideo ? `${user}_video.webm` : `${user}_audio.webm`;
            chat.active_set(save_button);
            if (!await chat.add_upload_file_link(chat.upload_file(mediaBlob, fileName, true)))
                await chat.error(save_button);
            chat.active_reset(save_button);
        }

    } catch (err) {
        console.error('Recording error:', err);
    }

    set_timer(0);

    chat.set_controls();
}


async function record_main() {
    chat = await $import("chat");

    $on($id('add_photo'), 'click', () => handleRecording("photo"));
    $on($id('add_record_audio'), 'click', () => handleRecording("audio"));
    $on($id('add_record_video'), 'click', () => handleRecording("video"));
}

// ## Notes for HTML:
// For photo mode, the `rec_save` button should have a camera/capture icon (like a camera shutter). The button label/title should change to something like "Take Photo" or "Capture" in photo mode vs "Save Recording" in audio/video mode. You might want to add this in the HTML/CSS or I can help with that if needed.
