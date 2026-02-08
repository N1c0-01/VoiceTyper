
import os
import io
import tempfile
import wave
import numpy as np
import logging

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

class TranscriberAPI:
    """
    Transcriber using OpenAI Whisper API.
    Fast and accurate, but requires internet and API key.
    """
    
    WHISPER_API_URL = "https://api.openai.com/v1/audio/transcriptions"
    
    def __init__(self, api_key=None, language="en"):
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests library required for API mode. Install with: pip install requests")
        
        self.api_key = api_key
        self.language = language
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required for API transcription mode")
    
    def transcribe(self, audio_data, sample_rate=16000):
        """
        Transcribe audio data using OpenAI Whisper API.
        Returns transcribed text.
        """
        import time
        
        if len(audio_data) == 0:
            return ""
        
        # TIMING: WAV conversion
        t0 = time.perf_counter()
        wav_buffer = io.BytesIO()
        audio_int16 = (audio_data * 32767).astype(np.int16)
        
        with wave.open(wav_buffer, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_int16.tobytes())
        
        wav_buffer.seek(0)
        t1 = time.perf_counter()
        logging.info(f"[TIMING] WAV conversion: {(t1-t0)*1000:.0f}ms")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            
            files = {
                "file": ("audio.wav", wav_buffer, "audio/wav"),
                "model": (None, "whisper-1"),
                "language": (None, self.language),
                "response_format": (None, "text")
            }
            
            # TIMING: API call
            t2 = time.perf_counter()
            response = requests.post(
                self.WHISPER_API_URL,
                headers=headers,
                files=files,
                timeout=30
            )
            t3 = time.perf_counter()
            logging.info(f"[TIMING] API call: {(t3-t2)*1000:.0f}ms")
            
            if response.status_code == 200:
                text = response.text.strip()
                logging.info(f"[TIMING] Total transcribe: {(t3-t0)*1000:.0f}ms")
                return text
            else:
                logging.error(f"API error {response.status_code}: {response.text}")
                return ""
                
        except requests.Timeout:
            logging.error("API request timed out")
            return ""
        except requests.RequestException as e:
            logging.error(f"API request failed: {e}")
            return ""
        except Exception as e:
            logging.error(f"Transcription error: {e}")
            return ""
