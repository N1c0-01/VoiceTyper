
import json
import os
from utils import get_app_dir

DEFAULT_CONFIG = {
    "hotkey": "right ctrl",
    "recording_mode": "hold",  # or "toggle"
    "show_notifications": True,
    "auto_start": False,

    # Transcription settings
    "transcription_backend": "local",  # "local" or "api"
    "openai_api_key": "",  # Required for API mode
    "local_model": "small",  # "tiny", "base", or "small"
    "language": "de",

    # UI settings
    "overlay_position": "Top Center",
    "saved_api_keys": []
}

class ConfigManager:
    def __init__(self, config_filename="config.json"):
        # Config should be next to the executable
        self.config_file = os.path.join(get_app_dir(), config_filename)
        self.config = DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.config.update(data)
            except Exception as e:
                print(f"Error loading config: {e}")

    def save(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save()
