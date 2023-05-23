// ==UserScript==
// @name        Universal Speech-to-Text
// @namespace   VoiceRecorder
// @include     http://*
// @include     https://*
// @version     1
// @grant       none
// ==/UserScript==

(function() {
    'use strict';

    var isRecording = false;
    var mediaRecorder;
    var audioChunks = [];

    async function startRecording() {
        isRecording = true;
        const mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(mediaStream);

        mediaRecorder.addEventListener('dataavailable', (event) => {
            audioChunks.push(event.data);
        });

        mediaRecorder.start();
    }

    async function stopRecording() {
        isRecording = false;
        mediaRecorder.stop();

        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });

        // Reset audioChunks for the next recording
        audioChunks = [];

        const response = await fetch('https://chat.allemande.ai/stt', {
            method: 'POST',
            body: audioBlob
        });
        const transcript = await response.text();

        // Insert the transcript into the currently focused element
        const focusedElement = document.activeElement;
        if (focusedElement) {
            focusedElement.value = transcript;
        }
    }

    document.addEventListener('keydown', (event) => {
        // F2 key
        if (event.keyCode === 113) {
            if (isRecording) {
                stopRecording();
            } else {
                startRecording();
            }
        }
    });
})();
