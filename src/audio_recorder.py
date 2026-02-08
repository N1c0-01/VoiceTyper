
import sounddevice as sd
import numpy as np
import threading
import wave
import os

class AudioRecorder:
    def __init__(self, sample_rate=16000, channels=1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.recording = False
        self.frames = []
        self.stream = None
        self.lock = threading.Lock()

    def _callback(self, indata, frames, time, status):
        """Callback for sounddevice stream."""
        if status:
            print(f"Audio status: {status}")
        if self.recording:
            with self.lock:
                self.frames.append(indata.copy())

    def start(self):
        """Start recording audio."""
        if self.recording:
            return
        self.recording = True
        self.frames = []
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            callback=self._callback
        )
        self.stream.start()

    def stop(self):
        """Stop recording and return the audio data as a numpy array."""
        if not self.recording:
            return None
        
        self.recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        with self.lock:
            if not self.frames:
                return np.array([], dtype=np.float32)
            return np.concatenate(self.frames, axis=0)

    def save_wav(self, filename, audio_data):
        """Save numpy array to WAV file (helper for debugging/transcription)."""
        # Ensure float32 is converted to int16 for standard WAV
        audio_int16 = (audio_data * 32767).astype(np.int16)
        
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 2 bytes for 16-bit
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_int16.tobytes())
