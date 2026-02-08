
import keyboard
import threading
import time
from config import ConfigManager

class HotkeyManager:
    def __init__(self, config: ConfigManager, on_start_recording, on_stop_recording):
        self.config = config
        self.on_start_recording = on_start_recording
        self.on_stop_recording = on_stop_recording
        self.is_recording = False
        self.lock = threading.Lock()
        self._hook = None

        self.setup_hotkey()

    def setup_hotkey(self):
        hotkey = self.config.get("hotkey", "ctrl_r")
        mode = self.config.get("recording_mode", "hold")

        print(f"Setting up hotkey: {hotkey} in {mode} mode")

        # Clean up any existing hooks
        keyboard.unhook_all()
        self._hook = None

        if mode == "hold":
            # Use a global hook that intercepts and suppresses the hotkey
            def hook_callback(event):
                if event.name == hotkey:
                    if event.event_type == keyboard.KEY_DOWN:
                        self._on_press_hold(event)
                    elif event.event_type == keyboard.KEY_UP:
                        self._on_release_hold(event)
                    return False  # Suppress this key
                return True  # Let other keys through

            self._hook = keyboard.hook(hook_callback, suppress=True)

        elif mode == "toggle":
            def hook_callback(event):
                if event.name == hotkey and event.event_type == keyboard.KEY_DOWN:
                    self._on_toggle()
                    return False  # Suppress
                return True

            self._hook = keyboard.hook(hook_callback, suppress=True)

    def _on_press_hold(self, event):
        with self.lock:
            if not self.is_recording:
                self.is_recording = True
                self.on_start_recording()

    def _on_release_hold(self, event):
        with self.lock:
            if self.is_recording:
                self.is_recording = False
                self.on_stop_recording()

    def _on_toggle(self):
        with self.lock:
            if self.is_recording:
                self.is_recording = False
                self.on_stop_recording()
            else:
                self.is_recording = True
                self.on_start_recording()

    def cleanup(self):
        keyboard.unhook_all()
