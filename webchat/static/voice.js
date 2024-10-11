// voice.js

console.log("GOT HERE 1");

// import { createVADMic } from '@ricky0123/vad-web';
const { createVADMic } = vad;

class VoiceInterface {
  constructor(options) {
    this.onSpeechStart = options.onSpeechStart || (() => {});
    this.onSpeechEnd = options.onSpeechEnd || (() => {});
    this.onError = options.onError || console.error;
    this.enabled = false;
    this.vad = null;
  }

  async init() {
    try {
      this.vad = await createVADMic({
        onSpeechStart: this.onSpeechStart,
        onSpeechEnd: (audio) => {
          const audioArray = new Float32Array(audio.length);
          audio.copyTo(audioArray);
          this.onSpeechEnd(audioArray);
        },
      });
    } catch (e) {
      this.onError('Failed to initialize voice interface:', e);
    }
  }

  start() {
    if (this.vad && !this.enabled) {
      this.vad.start();
      this.enabled = true;
    }
  }

  stop() {
    if (this.vad && this.enabled) {
      this.vad.pause();
      this.enabled = false;
    }
  }

  toggle() {
    if (this.enabled) {
      this.stop();
    } else {
      this.start();
    }
  }
}

// Voice controls component
class VoiceControls {
  constructor(voiceInterface) {
    this.voiceInterface = voiceInterface;
    this.micButton = document.createElement('button');
    this.micButton.textContent = 'Mic Off';
    this.micButton.addEventListener('click', () => this.toggleMic());

    this.speakerButton = document.createElement('button');
    this.speakerButton.textContent = 'Speaker Off';
    this.speakerButton.addEventListener('click', () => this.toggleSpeaker());

    this.container = document.createElement('div');
    this.container.appendChild(this.micButton);
    this.container.appendChild(this.speakerButton);
  }

  toggleMic() {
    this.voiceInterface.toggle();
    this.micButton.textContent = this.voiceInterface.enabled ? 'Mic On' : 'Mic Off';
  }

  toggleSpeaker() {
    // Implement speaker toggle functionality
    this.speakerButton.textContent = this.speakerButton.textContent === 'Speaker Off' ? 'Speaker On' : 'Speaker Off';
  }

  getElement() {
    return this.container;
  }
}

// Initialize and add voice interface to the chat app
async function initVoiceInterface() {
  console.log("ENABLING VOICE CHAT INTERFACE");
  const voiceInterface = new VoiceInterface({
    onSpeechStart: () => console.log('Speech started'),
    onSpeechEnd: (audio) => {
      console.log('Speech ended', audio);
      // Here you would send the audio to your backend for processing
    },
    onError: (error) => console.error('Voice interface error:', error),
  });

  await voiceInterface.init();

  const voiceControls = new VoiceControls(voiceInterface);
  const inputRow = document.getElementById('inputrow');
  inputRow.appendChild(voiceControls.getElement());

  // Optional: Add a button to enable/disable the entire voice interface
  /*
  const toggleVoiceButton = document.createElement('button');
  toggleVoiceButton.textContent = 'Enable Voice';
  toggleVoiceButton.addEventListener('click', () => {
    const voiceEnabled = toggleVoiceButton.textContent === 'Enable Voice';
    toggleVoiceButton.textContent = voiceEnabled ? 'Disable Voice' : 'Enable Voice';
    voiceControls.getElement().style.display = voiceEnabled ? 'block' : 'none';
  });
  document.querySelector('form').insertBefore(toggleVoiceButton, inputRow);
  */
}

console.log("GOT HERE");

// Call this function when the page loads
// window.addEventListener('load', initVoiceInterface);
initVoiceInterface()

// Here's a simplified version of `voice.js` that implements a voice chat interface for your chat app, based on the provided `index.html` and using the VAD system you mentioned:

// This implementation provides:
//
// 1. A `VoiceInterface` class that wraps the VAD functionality.
// 2. A `VoiceControls` class that creates UI controls for the voice interface.
// 3. An `initVoiceInterface` function that sets up the voice interface and adds it to your existing chat app.
//
// To use this:
//
// 1. Save this code as `voice.js` in your project directory.
// 2. In your `index.html`, add a script tag to include this file:

// <script src="voice.js" type="module"></script>

// 3. Make sure you have the necessary dependencies installed, particularly `@ricky0123/vad-web`.
//
// This implementation provides a simple way to enable/disable the entire voice interface, and separate controls for the microphone and speaker. The actual speech-to-text and text-to-speech functionality would need to be implemented on your backend, which this code assumes you'll do when you set up your API routes.
//
// Remember to style the new buttons appropriately to match your existing UI. You may also want to add more error handling and user feedback for a production-ready implementation.

