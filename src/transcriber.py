import subprocess
import os
import tempfile
import numpy as np
import wave
from utils import get_resource_path


class Transcriber:
    """Local speech-to-text using whisper.cpp."""

    def __init__(self, model_path="external/models/ggml-small.bin", whisper_path="external/whisper.exe", language="de"):
        self.model_path = get_resource_path(model_path)
        self.whisper_path = get_resource_path(whisper_path)
        self.language = language

        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model not found at {self.model_path}")
        if not os.path.exists(self.whisper_path):
            raise FileNotFoundError(f"Whisper binary not found at {self.whisper_path}")

    def transcribe(self, audio_data, sample_rate=16000):
        """Transcribe audio data (numpy float32 array) to text."""
        if len(audio_data) == 0:
            return ""

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_wav = tmp.name

        try:
            # Convert float32 to int16 and write WAV
            audio_int16 = (audio_data * 32767).astype(np.int16)
            with wave.open(tmp_wav, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(audio_int16.tobytes())

            # Run whisper.cpp — stdout captures transcribed text, stderr has system info
            cmd = [
                self.whisper_path,
                "-m", self.model_path,
                "-f", tmp_wav,
                "-l", self.language,
                "--no-timestamps"
            ]

            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=60,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            if process.returncode != 0:
                print(f"Whisper Error: {process.stderr}")
                return ""

            return process.stdout.strip()

        except subprocess.TimeoutExpired:
            print("Transcription timed out")
            return ""
        except Exception as e:
            print(f"Transcription error: {e}")
            return ""
        finally:
            if os.path.exists(tmp_wav):
                os.remove(tmp_wav)
