
import subprocess
import os
import tempfile
import numpy as np
import wave
import sys
from utils import get_resource_path

class Transcriber:
    def __init__(self, model_path="external/models/ggml-small.bin", whisper_path="external/whisper.exe", language="de"):
        # Use helper to resolve path in dev or frozen mode
        self.model_path = get_resource_path(model_path)
        self.whisper_path = get_resource_path(whisper_path)
        self.language = language
        
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model not found at {self.model_path}")
        if not os.path.exists(self.whisper_path):
            raise FileNotFoundError(f"Whisper binary not found at {self.whisper_path}")

    def transcribe(self, audio_data, sample_rate=16000):
        """
        Transcribe audio data (numpy array) to text.
        """
        if len(audio_data) == 0:
            return ""

        # Create temp wav file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_wav = tmp.name
        
        try:
            # Write WAV
            # Convert float32 to int16
            audio_int16 = (audio_data * 32767).astype(np.int16)
            with wave.open(tmp_wav, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(audio_int16.tobytes())

            # Call whisper
            # Command: whisper.exe -m model -f file -otxt -l en --no-timestamps
            cmd = [
                self.whisper_path,
                "-m", self.model_path,
                "-f", tmp_wav,
                "-otxt",        # Output text
                "-l", "en",     # Language English
                "--no-timestamps" # Clean output
            ]
            
            # Using partial matching or just capturing stdout
            # whisper.cpp plain output usually prints system info to stderr and text to stdout if -otxt is used?
            # Actually -otxt writes to a file <input>.txt. 
            # Let's check whisper.cpp usage. 
            # Default behavior prints to stdout with timestamps.
            # -otxt might save to file. 
            # Let's try capturing stdout without -otxt first, or reading the docs in my head.
            # PRD Section 3.2 says: "Parse stdout for transcribed text"
            # It also suggests command: wrapper.exe ... -otxt ...
            # If -otxt is used, it often writes to a file. 
            # Let's stick to standard stdout capture which is safer if we don't want file management.
            # But standard output has metadata.
            # Let's use --no-timestamps. The PRD suggests it.
            
            # Revised command to print to stdout cleanly if possible.
            # If -otxt is not provided, it prints to stdout.
            # We will filter out the system info (which is usually on stderr).
            
            cmd = [
                self.whisper_path,
                "-m", self.model_path,
                "-f", tmp_wav,
                "-l", self.language,
                "--no-timestamps"
            ]

            # Hide console window on Windows
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

            text = process.stdout.strip()
            return text

        except subprocess.TimeoutExpired:
            print("Transcription timed out")
            return ""
        except Exception as e:
            print(f"Transcription error: {e}")
            return ""
        finally:
            if os.path.exists(tmp_wav):
                os.remove(tmp_wav)

