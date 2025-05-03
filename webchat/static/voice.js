// voice.js

console.log("GOT HERE 1");

// import { createVADMic } from '@ricky0123/vad-web';
// const { createVADMic } = vad;
// let chat;

// async function importChat() {
//   chat = await import('./chat.js');
// }

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
      this.vad = await vad.MicVAD.new({
        onSpeechStart: this.onSpeechStart,
        onSpeechEnd: (audio) => {
          // const audioArray = new Float32Array(audio.length);
          // audio.copyTo(audioArray);
          this.onSpeechEnd(audio);
        },
        // onFrameProcessed: this.onFrameProcessed
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

// Helper function to convert Float32Array to WAV Blob
function float32ArrayToWavBlob(audioData, sampleRate = 16000) {
  // Create WAV header
  const numChannels = 1;
  const bitsPerSample = 16;
  const blockAlign = numChannels * bitsPerSample / 8;
  const byteRate = sampleRate * blockAlign;
  const dataSize = audioData.length * 2; // 16-bit samples
  const headerSize = 44;
  const totalSize = headerSize + dataSize;
  
  const buffer = new ArrayBuffer(totalSize);
  const view = new DataView(buffer);
  
  // Write WAV header
  const writeString = (offset, string) => {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  };
  
  writeString(0, 'RIFF');
  view.setUint32(4, totalSize - 8, true);
  writeString(8, 'WAVE');
  writeString(12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true); // PCM format
  view.setUint16(22, numChannels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, byteRate, true);
  view.setUint16(32, blockAlign, true);
  view.setUint16(34, bitsPerSample, true);
  writeString(36, 'data');
  view.setUint32(40, dataSize, true);
  
  // Write audio data
  const samples = new Int16Array(audioData.length);
  for (let i = 0; i < audioData.length; i++) {
    const s = Math.max(-1, Math.min(1, audioData[i]));
    samples[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
  }
  
  const samplesBytes = new Uint8Array(samples.buffer);
  const audioDataView = new Uint8Array(buffer, 44);
  audioDataView.set(samplesBytes);
  
  return new Blob([buffer], { type: 'audio/wav' });
}

// Initialize and add voice interface to the chat app
async function initVoiceInterface() {
  console.log("ENABLING VOICE CHAT INTERFACE");
  const voiceInterface = new VoiceInterface({
    onSpeechStart: () => console.log('Speech started'),
    onSpeechEnd: async (audio) => {
      console.log('Speech ended, converting to WAV...');
      
      const wavBuffer = vad.utils.encodeWAV(audio);
    
      // Create a Blob from the WAV buffer
      const wavBlob = new Blob([wavBuffer], { type: 'audio/wav' });
      
      // Create a File object from the Blob with a timestamp in the filename
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const file = new File([wavBlob], `voice_recording_${timestamp}.wav`, { type: 'audio/wav' });
      
      // Use the upload_files function from chat.js with an array of files
      try {
        await chat.upload_files([file], true);
      } catch (err) {
        console.error('Failed to upload audio:', err);
        this.onError('Failed to upload audio: ' + err.message);
      }
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

