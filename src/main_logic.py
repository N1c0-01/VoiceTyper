
import threading
import logging
import time
import os

from config import ConfigManager
from audio_recorder import AudioRecorder
from keyboard_injector import TextInjector
from hotkey_manager import HotkeyManager
from utils import setup_logging, notify, get_app_dir
import model_manager

class VoiceTyperApp:
    def __init__(self):
        # Ensure logs directory exists and use it
        logs_dir = os.path.join(get_app_dir(), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        log_path = os.path.join(logs_dir, "voice_typer.log")
        setup_logging(log_path)
        logging.info("Initializing VoiceTyper...")
        
        self.config = ConfigManager()
        self.recorder = AudioRecorder()
        
        # Initialize transcriber based on config
        self.transcriber = self._init_transcriber()

        self.injector = TextInjector()
        
        # State
        self.processing_thread = None
        self.on_state_change = None  # UI callback: ("recording"|"processing"|"done"|"idle")

        # Hotkey Manager needs to be last
        self.hotkey_manager = HotkeyManager(
            self.config,
            self.start_recording,
            self.stop_recording
        )

        logging.info("VoiceTyper initialized and ready.")

    def _notify_state(self, state):
        if self.on_state_change:
            self.on_state_change(state)

    def start_recording(self):
        logging.info("Starting recording...")
        self.recorder.start()
        self._notify_state("recording")

    def stop_recording(self):
        logging.info("Stopping recording...")
        audio_data = self.recorder.stop()

        if len(audio_data) == 0:
            logging.warning("No audio recorded.")
            self._notify_state("idle")
            return

        self._notify_state("processing")

        # Start processing in background
        self.processing_thread = threading.Thread(
            target=self.process_audio,
            args=(audio_data,)
        )
        self.processing_thread.start()

    def process_audio(self, audio_data):
        import time
        t_start = time.perf_counter()

        logging.info(f"Processing {len(audio_data)} samples...")
        if not self.transcriber:
            logging.error("Transcriber not available")
            self._notify_state("idle")
            return

        try:
            text = self.transcriber.transcribe(audio_data)
        except Exception as e:
            logging.error(f"Transcription failed: {e}")
            self._notify_state("idle")
            return

        t_transcribed = time.perf_counter()

        if text:
            logging.info(f"Transcribed: '{text}'")
            self.injector.inject(text)
            t_injected = time.perf_counter()
            logging.info(f"[TIMING] Full pipeline: {(t_injected-t_start)*1000:.0f}ms (transcribe: {(t_transcribed-t_start)*1000:.0f}ms, inject: {(t_injected-t_transcribed)*1000:.0f}ms)")
            self._notify_state("done")
        else:
            logging.info("No text transcribed.")
            self._notify_state("idle")

    def run(self):
        # Keep main thread alive for hotkeys
        logging.info("App running. Press hotkey to record.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.cleanup()

    def reload_after_settings(self):
        """Re-initialize components that depend on config values."""
        logging.info("Reloading after settings change...")
        # Re-init transcriber (backend / model / key may have changed)
        self.transcriber = self._init_transcriber()
        # Re-init hotkey (key or mode may have changed)
        self.hotkey_manager.config = self.config
        self.hotkey_manager.setup_hotkey()
        logging.info("Reload complete.")

    def cleanup(self):
        logging.info("Cleaning up...")
        if self.hotkey_manager:
            self.hotkey_manager.cleanup()

    def _init_transcriber(self):
        """Initialize the appropriate transcriber based on config."""
        backend = self.config.get("transcription_backend", "local")
        language = self.config.get("language", "en")

        if backend == "api":
            api_key = self.config.get("openai_api_key", "")
            if not api_key:
                logging.error("API mode selected but no API key provided")
                notify("Error", "API key required for cloud transcription")
                return None
            try:
                from transcriber_api import TranscriberAPI
                logging.info("Using OpenAI Whisper API backend (fast)")
                return TranscriberAPI(api_key=api_key, language=language)
            except Exception as e:
                logging.error(f"Failed to init API transcriber: {e}")
                notify("Error", f"API transcriber failed: {e}")
                return None
        else:
            # Local whisper.cpp — use model_manager for path resolution
            model_name = self.config.get("local_model", "small")

            # Check if model is installed
            if not model_manager.is_model_installed(model_name):
                # Try to fall back to any installed model
                installed = model_manager.get_installed_models()
                if installed:
                    model_name = installed[0]
                    logging.warning(f"Configured model not installed, falling back to '{model_name}'")
                    self.config.set("local_model", model_name)
                else:
                    logging.warning("No local models installed. Please download one from Settings > Transcription.")
                    notify("No Model", "Download a model in Settings to use local mode")
                    return None

            model_path = model_manager.get_model_path(model_name)

            try:
                from transcriber import Transcriber
                from utils import get_resource_path
                whisper_exe = get_resource_path("external/whisper.exe")
                logging.info(f"Using local whisper.cpp backend with '{model_name}' model at {model_path}, language={language}")
                return Transcriber(model_path=model_path, whisper_path=whisper_exe, language=language)
            except Exception as e:
                logging.error(f"Failed to init local transcriber: {e}")
                notify("Error", f"Local transcriber failed: {e}")
                return None
