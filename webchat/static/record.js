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
    if (!hasAudioPermission || !hasVideoPermission) {
        room_saved = chat.room;
        chat.clear_messages_box();
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

// Main recording function
async function handleRecording(includeVideo = false) {
    await $import("icons");
    icons = modules.icons.icons;

    chat.set_controls('input_record');

    try {
        const {
            mediaRecorder,
            chunks,
            stream
        } = await setupRecorder(includeVideo);

        // Video preview
        const videoPreview = $id('rec_videoPreview');
        if (includeVideo) {
            show("rec_videoPreview");
            videoPreview.srcObject = stream;
        } else {
            hide("rec_videoPreview");
        }

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
        }

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
        })

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
            } else {
                preview = $id('rec_preview_audioPreview');
                show("rec_preview_audioPreview");
                hide("rec_preview_videoPreview");
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

    $on($id('add_record_audio'), 'click', () => handleRecording(false));
    $on($id('add_record_video'), 'click', () => handleRecording(true));
}

/*
// For audio only
handleRecording(false);

// For video + audio
handleRecording(true);
*/
